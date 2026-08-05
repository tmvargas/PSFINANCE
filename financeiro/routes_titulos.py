# financeiro/routes_titulos.py
import os
import uuid as uuid_lib
from datetime import date, datetime
from pathlib import Path

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from . import bp_financeiro
from .regras_empresa_centro import (
    listar_empresas_centros_ativos,
    validar_conta_da_empresa,
    validar_empresa_centro,
)
from database import SessionLocal
from models import Baixa, Conta, Credor, Documento, PlanoDeContas, Titulo, TituloAnexo


def get_session():
    return SessionLocal()


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_float(value: str | None):
    if value is None:
        return None

    s = str(value).strip()
    if not s:
        return None

    # limpa moeda e espaços
    s = s.replace("R$", "").replace(" ", "")

    # Casos:
    # 1) "1.234,56"  -> pt-BR (ponto milhar, vírgula decimal)
    # 2) "1234,56"   -> vírgula decimal
    # 3) "1234.56"   -> ponto decimal (padrão)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    else:
        # se tiver mais de um ponto, mantém o último como decimal
        if s.count(".") > 1:
            parts = s.split(".")
            s = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return float(s)
    except Exception:
        return None



def _uploads_dir() -> Path:
    # guarda dentro da pasta do app (não versionada)
    base = current_app.instance_path if current_app else "instance"
    p = Path(base) / "uploads" / "titulos"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _titulo_saldo_aberto(session, id_titulo: int) -> float:
    titulo = (
        session.query(Titulo)
        .filter(Titulo.id_titulo == id_titulo, Titulo.deleted.is_(False))
        .first()
    )
    if not titulo:
        return 0.0

    baixado = (
        session.query(func.coalesce(func.sum(Baixa.valor_baixa), 0))
        .filter(
            Baixa.deleted.is_(False),
            Baixa.id_titulo == id_titulo,
        )
        .scalar()
    )
    total = float(titulo.valor or 0)
    baixado = float(baixado or 0)
    return max(0.0, total - baixado)


# ----------------------------------------------------------------------
# LISTAR TÍTULOS (filtro por mês/ano do VENCIMENTO)
# ----------------------------------------------------------------------
@bp_financeiro.route("/titulos")
def listar_titulos():
    session = get_session()

    hoje = date.today()
    mes = request.args.get("mes", type=int) or hoje.month
    ano = request.args.get("ano", type=int) or hoje.year

    if mes < 1 or mes > 12:
        mes = hoje.month

    data_ini = date(ano, mes, 1)
    data_fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)

    titulos = (
        session.query(Titulo)
        .options(
            joinedload(Titulo.credor),
            joinedload(Titulo.empresa),
            joinedload(Titulo.centro_custo),
            joinedload(Titulo.plano),
            joinedload(Titulo.documento),  # requer relationship via id_doc
        )
        .filter(
            Titulo.deleted.is_(False),
            Titulo.vencimento >= data_ini,
            Titulo.vencimento < data_fim,
        )
        .order_by(Titulo.vencimento.asc(), Titulo.id_titulo.desc())
        .all()
    )

    baixas_soma = dict(
        session.query(
            Baixa.id_titulo,
            func.coalesce(func.sum(Baixa.valor_baixa), 0).label("soma"),
        )
        .filter(
            Baixa.deleted.is_(False),
            Baixa.id_titulo.in_([t.id_titulo for t in titulos] or [-1]),
        )
        .group_by(Baixa.id_titulo)
        .all()
    )

    rows = []
    total_valor = 0.0
    total_baixado = 0.0
    total_aberto = 0.0

    for t in titulos:
        valor = float(t.valor or 0)
        baixado = float(baixas_soma.get(t.id_titulo, 0) or 0)
        aberto = max(0.0, valor - baixado)

        total_valor += valor
        total_baixado += baixado
        total_aberto += aberto

        doc_label = ""
        if getattr(t, "documento", None) is not None:
            doc_label = f"{t.documento.tipo_doc} - {t.documento.nome_doc}"
        else:
            # fallback se ainda existir campo string antigo
            doc_label = getattr(t, "documento", "") or ""

        rows.append(
            {
                "id": t.id_titulo,
                "doc_label": doc_label,
                "nr_documento": t.nr_documento,
                "credor": t.credor.nome if t.credor else "",
                "empresa": f"{t.empresa.codigo} - {t.empresa.nome}" if t.empresa else "",
                "centro_custo": f"{t.centro_custo.codigo} - {t.centro_custo.nome}" if t.centro_custo else "",
                "plano": f"{t.plano.cod_estrutural} - {t.plano.nome_conta}" if t.plano else "",
                "emissao": t.emissao.strftime("%d/%m/%Y") if t.emissao else "",
                "vencimento": t.vencimento.strftime("%d/%m/%Y") if t.vencimento else "",
                "valor": valor,
                "baixado": baixado,
                "aberto": aberto,
            }
        )

    meses = [
        (1, "Jan"), (2, "Fev"), (3, "Mar"), (4, "Abr"),
        (5, "Mai"), (6, "Jun"), (7, "Jul"), (8, "Ago"),
        (9, "Set"), (10, "Out"), (11, "Nov"), (12, "Dez"),
    ]
    anos = list(range(hoje.year - 3, hoje.year + 2))

    session.close()
    return render_template(
        "titulos_list.html",
        titulos=rows,
        mes=mes,
        ano=ano,
        meses=meses,
        anos=anos,
        total_valor=total_valor,
        total_baixado=total_baixado,
        total_aberto=total_aberto,
    )


# ----------------------------------------------------------------------
# NOVO / EDITAR TÍTULO
# ----------------------------------------------------------------------
@bp_financeiro.route("/titulos/novo", methods=["GET", "POST"])
def novo_titulo():
    return _upsert_titulo(None)


@bp_financeiro.route("/titulos/<int:id_titulo>/editar", methods=["GET", "POST"])
def editar_titulo(id_titulo: int):
    return _upsert_titulo(id_titulo)


@bp_financeiro.route("/titulos/<int:id_titulo>/copiar", methods=["GET", "POST"])
def copiar_titulo(id_titulo: int):
    return _upsert_titulo(None, id_titulo_copia=id_titulo)


def _upsert_titulo(id_titulo: int | None, id_titulo_copia: int | None = None):
    session = get_session()

    titulo_obj = None
    titulo_base = None
    anexos = []
    modo_copia = id_titulo is None and id_titulo_copia is not None

    if id_titulo is not None or id_titulo_copia is not None:
        id_busca = id_titulo if id_titulo is not None else id_titulo_copia
        titulo_base = (
            session.query(Titulo)
            .options(
                joinedload(Titulo.anexos),
                joinedload(Titulo.credor),
                joinedload(Titulo.empresa),
                joinedload(Titulo.centro_custo),
                joinedload(Titulo.plano),
                joinedload(Titulo.documento),
            )
            .filter(Titulo.id_titulo == id_busca, Titulo.deleted.is_(False))
            .first()
        )
        if not titulo_base:
            session.close()
            flash("Título não encontrado.", "erro")
            return redirect(url_for("financeiro.listar_titulos"))

        if modo_copia:
            titulo_obj = None
            anexos = []
        else:
            titulo_obj = titulo_base
            anexos = [a for a in (titulo_obj.anexos or []) if not getattr(a, "deleted", False)]

    credores = (
        session.query(Credor)
        .filter(Credor.deleted.is_(False))
        .order_by(Credor.nome)
        .all()
    )
    planos = (
        session.query(PlanoDeContas)
        .filter(
            PlanoDeContas.deleted.is_(False),
            PlanoDeContas.cod_estrutural.like("2.%"),  # ✅ só grupo 2
        )
        .order_by(PlanoDeContas.cod_estrutural)
        .all()
    )

    documentos = (
        session.query(Documento)
        .filter(Documento.deleted.is_(False))
        .order_by(Documento.tipo_doc)
        .all()
    )
    empresas_view, centros_custo_view = listar_empresas_centros_ativos(session)

    if request.method == "POST":
        id_doc = request.form.get("id_doc", type=int)
        nr_documento = (request.form.get("nr_documento") or "").strip()
        id_credor = request.form.get("id_credor", type=int)
        id_empresa = request.form.get("id_empresa", type=int)
        id_centro_custo = request.form.get("id_centro_custo", type=int)
        id_plano = request.form.get("id_plano", type=int)
        valor = _parse_float(request.form.get("valor"))
        emissao = _parse_date(request.form.get("emissao"))
        vencimento = _parse_date(request.form.get("vencimento"))
        observacao = (request.form.get("observacao") or "").strip()


        erros = []
        if not id_doc:
            erros.append("Documento é obrigatório.")
        if not nr_documento:
            erros.append("Número do documento é obrigatório.")
        if not id_credor:
            erros.append("Credor é obrigatório.")
        erros_empresa_centro, _empresa, _centro = validar_empresa_centro(session, id_empresa, id_centro_custo)
        erros.extend(erros_empresa_centro)
        if not id_plano:
            erros.append("Plano financeiro é obrigatório.")
        if valor is None or valor <= 0:
            erros.append("Valor inválido.")
        if not emissao:
            erros.append("Data de emissão inválida.")
        if not vencimento:
            erros.append("Data de vencimento inválida.")

        if id_doc:
            doc = (
                session.query(Documento)
                .filter(Documento.id_doc == id_doc, Documento.deleted.is_(False))
                .first()
            )
            if not doc:
                erros.append("Documento selecionado não existe.")

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            if titulo_obj is None:
                titulo_obj = Titulo(
                    id_doc=id_doc,
                    nr_documento=nr_documento,
                    id_credor=id_credor,
                    id_empresa=id_empresa,
                    id_centro_custo=id_centro_custo,
                    id_plano=id_plano,
                    valor=valor,
                    emissao=emissao,
                    vencimento=vencimento,
                    observacao=observacao or None,

                )
                session.add(titulo_obj)
                session.flush()
            else:
                baixado = (
                    session.query(func.coalesce(func.sum(Baixa.valor_baixa), 0))
                    .filter(Baixa.deleted.is_(False), Baixa.id_titulo == titulo_obj.id_titulo)
                    .scalar()
                )
                baixado = float(baixado or 0)
                if valor < baixado - 0.0001:
                    flash(f"Não é possível definir valor menor que o já baixado (R$ {baixado:.2f}).", "erro")
                    session.close()
                    return redirect(url_for("financeiro.editar_titulo", id_titulo=titulo_obj.id_titulo))

                titulo_obj.id_doc = id_doc
                titulo_obj.nr_documento = nr_documento
                titulo_obj.id_credor = id_credor
                titulo_obj.id_empresa = id_empresa
                titulo_obj.id_centro_custo = id_centro_custo
                titulo_obj.id_plano = id_plano
                titulo_obj.valor = valor
                titulo_obj.emissao = emissao
                titulo_obj.vencimento = vencimento
                titulo_obj.observacao = observacao
      


            files = request.files.getlist("arquivos")
            files = [f for f in files if f and f.filename]
            if files:
                existentes = (
                    session.query(TituloAnexo)
                    .filter(
                        TituloAnexo.deleted.is_(False),
                        TituloAnexo.id_titulo == titulo_obj.id_titulo,
                    )
                    .count()
                )
                if existentes + len(files) > 5:
                    flash("Limite de 5 anexos por título.", "erro")
                else:
                    updir = _uploads_dir()
                    for f in files:
                        ext = os.path.splitext(f.filename)[1]
                        safe_name = f"{uuid_lib.uuid4().hex}{ext}"
                        path = updir / safe_name
                        f.save(path)

                        an = TituloAnexo(
                            id_titulo=titulo_obj.id_titulo,
                            nome_arquivo=f.filename,
                            caminho_arquivo=str(path),
                        )
                        session.add(an)

            session.commit()
            session.close()
            if modo_copia:
                flash("Cópia do título salva com sucesso!", "sucesso")
            else:
                flash("Título salvo com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_titulos"))

    hoje_str = date.today().isoformat()

    titulo_view = None
    titulo_ref = titulo_obj or titulo_base
    if titulo_ref is not None:
        titulo_view = {
            "id_titulo": None if modo_copia else titulo_ref.id_titulo,
            "id_doc": getattr(titulo_ref, "id_doc", None),
            "nr_documento": titulo_ref.nr_documento,
            "id_credor": titulo_ref.id_credor,
            "id_empresa": getattr(titulo_ref, "id_empresa", None),
            "id_centro_custo": getattr(titulo_ref, "id_centro_custo", None),
            "id_plano": titulo_ref.id_plano,
            "valor": float(titulo_ref.valor or 0),
            "emissao": titulo_ref.emissao,        # date (tem isoformat)
            "vencimento": titulo_ref.vencimento,  # date (tem isoformat)
            "observacao": getattr(titulo_ref, "observacao", "") or "",

        }

    anexos_view = [{"id_anexo": a.id_anexo, "nome_arquivo": a.nome_arquivo} for a in anexos]
    credores_view = [{"id_credor": c.id_credor, "nome": c.nome} for c in credores]
    
    planos_view = [{
    "id_plano": p.id_plano,
    "cod_estrutural": p.cod_estrutural,
    "nome_conta": p.nome_conta,
    "tipo": p.tipo,  # ✅ necessário para desabilitar no template
} for p in planos]


    documentos_view = [{"id_doc": d.id_doc, "tipo_doc": d.tipo_doc, "nome_doc": d.nome_doc} for d in documentos]

    session.close()
    return render_template(
        "titulo_form.html",
        titulo=titulo_view,
        anexos=anexos_view,
        credores=credores_view,
        empresas=empresas_view,
        centros_custo=centros_custo_view,
        planos=planos_view,
        documentos=documentos_view,
        hoje=hoje_str,
        modo_copia=modo_copia,
        titulo_original=titulo_base.id_titulo if titulo_base else None,
    )


# ----------------------------------------------------------------------
# EXCLUIR TÍTULO (somente se NÃO tiver baixa)
# ----------------------------------------------------------------------
@bp_financeiro.route("/titulos/<int:id_titulo>/excluir", methods=["POST"])
def excluir_titulo(id_titulo: int):
    session = get_session()

    titulo = (
        session.query(Titulo)
        .filter(Titulo.id_titulo == id_titulo, Titulo.deleted.is_(False))
        .first()
    )
    if not titulo:
        session.close()
        flash("Título não encontrado.", "erro")
        return redirect(url_for("financeiro.listar_titulos"))

    tem_baixa = (
        session.query(Baixa.id_baixa)
        .filter(Baixa.deleted.is_(False), Baixa.id_titulo == id_titulo)
        .first()
        is not None
    )
    if tem_baixa:
        session.close()
        flash("Não é possível excluir um título que possui baixa (mesmo parcial).", "erro")
        return redirect(url_for("financeiro.listar_titulos"))

    titulo.deleted = True
    session.commit()
    session.close()

    flash("Título excluído com sucesso.", "sucesso")
    return redirect(url_for("financeiro.listar_titulos"))


# ----------------------------------------------------------------------
# BAIXAR TÍTULO
# ----------------------------------------------------------------------
@bp_financeiro.route("/titulos/<int:id_titulo>/baixar", methods=["GET", "POST"])
def baixar_titulo(id_titulo: int):
    session = get_session()

    titulo = (
        session.query(Titulo)
        .options(
            joinedload(Titulo.credor),
            joinedload(Titulo.empresa),
            joinedload(Titulo.plano),
            joinedload(Titulo.documento),
        )
        .filter(Titulo.id_titulo == id_titulo, Titulo.deleted.is_(False))
        .first()
    )
    if not titulo:
        session.close()
        flash("Título não encontrado.", "erro")
        return redirect(url_for("financeiro.listar_titulos"))

    saldo_aberto = _titulo_saldo_aberto(session, id_titulo)

    contas = (
        session.query(Conta)
        .filter(
            Conta.deleted.is_(False),
            Conta.id_empresa == titulo.id_empresa,
        )
        .order_by(Conta.descricao)
        .all()
    )
    contas_view = [{"id": c.id_conta, "descricao": c.descricao, "id_empresa": c.id_empresa} for c in contas]

    if request.method == "POST":
        data_baixa = _parse_date(request.form.get("data"))
        id_conta = request.form.get("id_conta", type=int)
        valor_baixa = _parse_float(request.form.get("valor_baixa"))

        erros = []
        if not titulo.id_empresa:
            erros.append("Título sem empresa vinculada não pode ser baixado.")
        if not data_baixa:
            erros.append("Data da baixa inválida.")
        if valor_baixa is None or valor_baixa <= 0:
            erros.append("Valor da baixa inválido.")
        if valor_baixa is not None and valor_baixa > saldo_aberto + 0.0001:
            erros.append(f"Valor da baixa não pode ser maior que o saldo em aberto (R$ {saldo_aberto:.2f}).")

        erros_conta, conta = validar_conta_da_empresa(session, id_conta, titulo.id_empresa)
        erros.extend(erros_conta)

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            bx = Baixa(
                data=data_baixa,
                id_conta=conta.id_conta,
                id_titulo=id_titulo,
                valor_baixa=valor_baixa,
            )
            session.add(bx)
            session.commit()
            session.close()
            flash("Baixa registrada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_baixas_titulo", id_titulo=id_titulo))

    titulo_view = {
        "id": titulo.id_titulo,
        "nr_documento": titulo.nr_documento,
        "credor": titulo.credor.nome if titulo.credor else "",
        "empresa": f"{titulo.empresa.codigo} - {titulo.empresa.nome}" if titulo.empresa else "",
        "plano": f"{titulo.plano.cod_estrutural} - {titulo.plano.nome_conta}" if titulo.plano else "",
        "valor": float(titulo.valor or 0),
        "saldo_aberto": float(saldo_aberto or 0),
    }
    session.close()
    return render_template(
        "titulo_baixa_form.html",
        titulo=titulo_view,
        contas=contas_view,
        hoje=date.today().isoformat(),
    )


# ----------------------------------------------------------------------
# LISTAR BAIXAS DO TÍTULO
# ----------------------------------------------------------------------
@bp_financeiro.route("/titulos/<int:id_titulo>/baixas")
def listar_baixas_titulo(id_titulo: int):
    session = get_session()

    titulo = (
        session.query(Titulo)
        .options(joinedload(Titulo.credor), joinedload(Titulo.documento))
        .filter(Titulo.id_titulo == id_titulo, Titulo.deleted.is_(False))
        .first()
    )
    if not titulo:
        session.close()
        flash("Título não encontrado.", "erro")
        return redirect(url_for("financeiro.listar_titulos"))

    baixas = (
        session.query(Baixa)
        .options(joinedload(Baixa.conta))
        .filter(Baixa.deleted.is_(False), Baixa.id_titulo == id_titulo)
        .order_by(Baixa.data.desc(), Baixa.id_baixa.desc())
        .all()
    )

    baixas_view = []
    total = 0.0
    for b in baixas:
        v = float(b.valor_baixa or 0)
        total += v
        baixas_view.append(
            {
                "id_baixa": b.id_baixa,
                "data": b.data.strftime("%d/%m/%Y") if b.data else "",
                "conta": b.conta.descricao if b.conta else "",
                "valor": v,
                "conciliado": bool(getattr(b, "conciliado", False)),
            }
        )

    session.close()
    return render_template(
        "titulo_baixas_list.html",
        titulo={
            "id": titulo.id_titulo,
            "nr_documento": titulo.nr_documento,
            "credor": titulo.credor.nome if titulo.credor else "",
            "valor": float(titulo.valor or 0),
        },
        baixas=baixas_view,
        total_baixas=total,
        saldo_aberto=_titulo_saldo_aberto(get_session(), id_titulo),
    )


# ----------------------------------------------------------------------
# EXCLUIR BAIXA (somente se NÃO conciliada)
# ----------------------------------------------------------------------
@bp_financeiro.route("/baixas/<int:id_baixa>/excluir", methods=["POST"])
def excluir_baixa(id_baixa: int):
    session = get_session()

    bx = (
        session.query(Baixa)
        .filter(Baixa.id_baixa == id_baixa, Baixa.deleted.is_(False))
        .first()
    )
    if not bx:
        session.close()
        flash("Baixa não encontrada.", "erro")
        return redirect(url_for("financeiro.listar_titulos"))

    if bool(getattr(bx, "conciliado", False)):
        session.close()
        flash("Não é possível excluir uma baixa conciliada.", "erro")
        return redirect(url_for("financeiro.listar_baixas_titulo", id_titulo=bx.id_titulo))

    bx.deleted = True
    session.commit()
    id_titulo = bx.id_titulo
    session.close()

    flash("Baixa excluída com sucesso.", "sucesso")
    return redirect(url_for("financeiro.listar_baixas_titulo", id_titulo=id_titulo))


# ----------------------------------------------------------------------
# DOWNLOAD / EXCLUIR ANEXO
# (mantive nomes '..._titulo' para bater com seu template)
# ----------------------------------------------------------------------
@bp_financeiro.route("/titulos/anexos/<int:id_anexo>/download")
def download_anexo_titulo(id_anexo: int):
    return download_anexo(id_anexo)


@bp_financeiro.route("/titulos/anexos/<int:id_anexo>/excluir", methods=["POST", "GET"])
def excluir_anexo_titulo(id_anexo: int):
    # teu template usa <a href>, então aceitamos GET também
    return excluir_anexo(id_anexo)


@bp_financeiro.route("/anexos/<int:id_anexo>/download")
def download_anexo(id_anexo: int):
    session = get_session()
    an = (
        session.query(TituloAnexo)
        .filter(TituloAnexo.id_anexo == id_anexo, TituloAnexo.deleted.is_(False))
        .first()
    )
    if not an:
        session.close()
        flash("Anexo não encontrado.", "erro")
        return redirect(url_for("financeiro.listar_titulos"))

    path = getattr(an, "caminho_arquivo", None) or ""
    nome = an.nome_arquivo or "anexo"
    session.close()

    if not path or not os.path.exists(path):
        flash("Arquivo físico do anexo não foi encontrado.", "erro")
        return redirect(url_for("financeiro.listar_titulos"))

    return send_file(path, as_attachment=True, download_name=nome)


@bp_financeiro.route("/anexos/<int:id_anexo>/excluir", methods=["POST", "GET"])
def excluir_anexo(id_anexo: int):
    session = get_session()
    an = (
        session.query(TituloAnexo)
        .filter(TituloAnexo.id_anexo == id_anexo, TituloAnexo.deleted.is_(False))
        .first()
    )
    if not an:
        session.close()
        flash("Anexo não encontrado.", "erro")
        return redirect(url_for("financeiro.listar_titulos"))

    id_titulo = an.id_titulo
    an.deleted = True
    session.commit()
    session.close()

    flash("Anexo excluído com sucesso.", "sucesso")
    return redirect(url_for("financeiro.editar_titulo", id_titulo=id_titulo))
