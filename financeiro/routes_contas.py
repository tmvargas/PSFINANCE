# financeiro/routes_contas.py
from datetime import date, datetime, timedelta
from sqlalchemy import case, func, or_
from sqlalchemy.orm import joinedload
from flask import render_template, request, redirect, url_for, flash, session as flask_session
from datetime import date

from . import bp_financeiro
from .regras_empresa_centro import (
    listar_empresas_centros_ativos,
    resolver_filtro_empresa_memorizado,
    validar_conta_da_empresa,
    validar_empresa_ativa,
    validar_empresa_centro,
)
from database import SessionLocal

from models import (
    Empresa,
    Conta,
    MovimentacaoConta,
    PlanoDeContas,
    Baixa,
    Titulo,
    Documento,
)

def get_session():
    return SessionLocal()


def _compor_documento_extrato(documento, descricao):
    componentes = [
        getattr(documento, "tipo_doc", None),
        getattr(documento, "nome_doc", None),
        descricao,
    ]
    componentes_normalizados = []
    for componente in componentes:
        texto = str(componente or "").strip().strip("-").strip()
        if texto:
            componentes_normalizados.append(texto)
    return " - ".join(componentes_normalizados)


def _empresas_ativas_e_filtro(session):
    empresas = (
        session.query(Empresa)
        .filter(Empresa.deleted.is_(False))
        .order_by(Empresa.codigo, Empresa.nome)
        .all()
    )
    empresas_view = [
        {"id": empresa.id_empresa, "label": f"{empresa.codigo} - {empresa.nome}"}
        for empresa in empresas
    ]
    id_empresa = resolver_filtro_empresa_memorizado(
        empresas_view, request.args, flask_session
    )
    return empresas_view, id_empresa


def parse_money_ptbr(valor_str: str) -> float:
    '''Formata valores no backend'''
    s = (valor_str or "").strip()
    if not s:
        raise ValueError("vazio")

    s = s.replace("R$", "").replace(" ", "")

    # Se tem vírgula, assume pt-BR (milhar "." e decimal ",")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # Sem vírgula: assume decimal "."
        s = s.replace(",", "")

    return float(s)


def conta_to_view(conta):
    empresa = getattr(conta, "empresa", None)
    tipos = {
        "corrente": "Corrente", "aplicacao": "Aplicação", "caixa": "Caixa",
        "cartao_credito": "Cartão de crédito",
    }
    return {
        "id": conta.id_conta,
        "descricao": conta.descricao,
        "empresa": f"{empresa.codigo} - {empresa.nome}" if empresa else "",
        "id_empresa": getattr(conta, "id_empresa", None),
        "tipo": conta.tipo,
        "tipo_label": tipos.get(conta.tipo, conta.tipo),
        "dia_vencimento_cartao": conta.dia_vencimento_cartao,
        "id_banco": conta.id_banco or "",
        "saldo_inicial": float(conta.saldo_inicial or 0),
        "data_saldo_inicial": conta.data_saldo_inicial.strftime("%d/%m/%Y") if conta.data_saldo_inicial else "",
        "data_saldo_inicial_input": conta.data_saldo_inicial.strftime("%Y-%m-%d") if conta.data_saldo_inicial else "",
        "saldo_atual": conta.saldo_atual,
    }


# ----------------------------------------------------------------------
# LISTAGEM DE CONTAS (com saldo)
# ----------------------------------------------------------------------
@bp_financeiro.route("/contas")
def listar_contas():
    session = get_session()

    contas = (
        session.query(Conta)
        .filter(Conta.deleted.is_(False))
        .order_by(Conta.descricao)
        .all()
    )

    contas_view = []
    total_saldo = 0.0

    for c in contas:
        saldo_atual = c.saldo_atual
        total_saldo += saldo_atual

        contas_view.append(conta_to_view(c))

    session.close()
    return render_template(
        "contas_list.html",
        contas=contas_view,
        total_saldo=total_saldo,
    )


# ----------------------------------------------------------------------
# CADASTRAR NOVA CONTA
# ----------------------------------------------------------------------
@bp_financeiro.route("/contas/nova", methods=["GET", "POST"])
def nova_conta():
    session = get_session()

    if request.method == "POST":
        descricao = (request.form.get("descricao") or "").strip()
        id_empresa = request.form.get("id_empresa", type=int)
        tipo = (request.form.get("tipo") or "").strip()
        dia_vencimento_cartao = request.form.get("dia_vencimento_cartao", type=int)
        id_banco = (request.form.get("id_banco") or "").strip()
        saldo_inicial_str = (request.form.get("saldo_inicial") or "").replace(",", ".").strip()
        data_saldo_str = (request.form.get("data_saldo_inicial") or "").strip()

        erros = []

        if not descricao:
            erros.append("Descrição da conta é obrigatória.")
        erros_empresa, _empresa = validar_empresa_ativa(session, id_empresa)
        erros.extend(erros_empresa)

        if tipo not in ("corrente", "aplicacao", "caixa", "cartao_credito"):
            erros.append("Tipo de conta inválido.")
        if tipo == "cartao_credito" and not 1 <= (dia_vencimento_cartao or 0) <= 31:
            erros.append("Informe o dia de vencimento do cartão entre 1 e 31.")
        if tipo != "cartao_credito":
            dia_vencimento_cartao = None

        # saldo inicial (opcional)
        saldo_inicial = 0.0
        if saldo_inicial_str:
            try:
                saldo_inicial = float(saldo_inicial_str)
            except Exception:
                erros.append("Saldo inicial inválido.")

        # data do saldo inicial (opcional, mas faz sentido ter se tiver saldo)
        data_saldo_inicial = None
        if data_saldo_str:
            try:
                data_saldo_inicial = datetime.strptime(data_saldo_str, "%Y-%m-%d").date()
            except Exception:
                erros.append("Data do saldo inicial inválida.")
        else:
            if saldo_inicial_str:
                erros.append("Informe a data do saldo inicial quando preencher o valor.")

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            conta = Conta(
                descricao=descricao,
                id_empresa=id_empresa,
                tipo=tipo,
                dia_vencimento_cartao=dia_vencimento_cartao,
                id_banco=id_banco or None,
                saldo_inicial=saldo_inicial,
                data_saldo_inicial=data_saldo_inicial,
            )
            session.add(conta)
            session.commit()
            session.close()

            flash("Conta cadastrada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_contas"))

    hoje = date.today().isoformat()
    empresas_view, _centros_custo_view = listar_empresas_centros_ativos(session)
    session.close()

    # conta=None porque é cadastro
    return render_template(
        "conta_form.html",
        conta=None,
        empresas=empresas_view,
        hoje=hoje,
    )


# ----------------------------------------------------------------------
# EDITAR CONTA
# ----------------------------------------------------------------------
@bp_financeiro.route("/contas/<int:id_conta>/editar", methods=["GET", "POST"])
def editar_conta(id_conta):
    session = get_session()

    conta = (
        session.query(Conta)
        .filter(Conta.id_conta == id_conta, Conta.deleted.is_(False))
        .first()
    )

    if not conta:
        session.close()
        flash("Conta não encontrada.", "erro")
        return redirect(url_for("financeiro.listar_contas"))

    if request.method == "POST":
        descricao = (request.form.get("descricao") or "").strip()
        id_empresa = request.form.get("id_empresa", type=int)
        tipo = (request.form.get("tipo") or "").strip()
        dia_vencimento_cartao = request.form.get("dia_vencimento_cartao", type=int)
        id_banco = (request.form.get("id_banco") or "").strip()
        saldo_inicial_str = (request.form.get("saldo_inicial") or "").replace(",", ".").strip()
        data_saldo_str = (request.form.get("data_saldo_inicial") or "").strip()

        erros = []

        if not descricao:
            erros.append("Descrição da conta é obrigatória.")
        erros_empresa, _empresa = validar_empresa_ativa(session, id_empresa)
        erros.extend(erros_empresa)

        if tipo not in ("corrente", "aplicacao", "caixa", "cartao_credito"):
            erros.append("Tipo de conta inválido.")
        if tipo == "cartao_credito" and not 1 <= (dia_vencimento_cartao or 0) <= 31:
            erros.append("Informe o dia de vencimento do cartão entre 1 e 31.")
        if tipo != "cartao_credito":
            dia_vencimento_cartao = None

        # saldo inicial (opcional)
        saldo_inicial = conta.saldo_inicial or 0.0
        if saldo_inicial_str:
            try:
                saldo_inicial = float(saldo_inicial_str)
            except Exception:
                erros.append("Saldo inicial inválido.")
        else:
            # se campo veio vazio, consideramos 0
            saldo_inicial = 0.0

        # data do saldo inicial
        data_saldo_inicial = None
        if data_saldo_str:
            try:
                data_saldo_inicial = datetime.strptime(data_saldo_str, "%Y-%m-%d").date()
            except Exception:
                erros.append("Data do saldo inicial inválida.")
        else:
            if saldo_inicial_str and float(saldo_inicial_str) != 0.0:
                erros.append("Informe a data do saldo inicial quando preencher o valor.")

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            conta.descricao = descricao
            conta.id_empresa = id_empresa
            conta.tipo = tipo
            conta.dia_vencimento_cartao = dia_vencimento_cartao
            conta.id_banco = id_banco or None
            conta.saldo_inicial = saldo_inicial
            conta.data_saldo_inicial = data_saldo_inicial

            session.commit()
            session.close()

            flash("Conta atualizada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_contas"))

    # GET → carrega dados atuais
    hoje = date.today().isoformat()

    # valor default dos campos
    conta_view = conta_to_view(conta)
    empresas_view, _centros_custo_view = listar_empresas_centros_ativos(session)

    session.close()

    return render_template(
        "conta_form.html",
        conta=conta_view,
        empresas=empresas_view,
        hoje=hoje,
    )


# ----------------------------------------------------------------------
# DESATIVAR CONTA (soft delete)
# ----------------------------------------------------------------------
@bp_financeiro.route("/contas/<int:id_conta>/desativar", methods=["POST"])
def desativar_conta(id_conta):
    session = get_session()

    conta = (
        session.query(Conta)
        .filter(Conta.id_conta == id_conta, Conta.deleted.is_(False))
        .first()
    )

    if not conta:
        session.close()
        flash("Conta não encontrada.", "erro")
        return redirect(url_for("financeiro.listar_contas"))

    conta.deleted = True
    session.commit()
    session.close()

    flash("Conta desativada com sucesso.", "sucesso")
    return redirect(url_for("financeiro.listar_contas"))


@bp_financeiro.route("/contas/inativas")
def listar_contas_inativas():
    session = get_session()

    contas = (
        session.query(Conta)
        .filter(Conta.deleted.is_(True))
        .order_by(Conta.descricao)
        .all()
    )

    contas_view = []
    total_saldo = 0.0

    for c in contas:
        saldo_atual = c.saldo_atual
        total_saldo += saldo_atual

        contas_view.append(conta_to_view(c))

    session.close()
    return render_template(
        "contas_inativas.html",
        contas=contas_view,
        total_saldo=total_saldo,
    )


@bp_financeiro.route("/contas/<int:id_conta>/reativar", methods=["POST"])
def reativar_conta(id_conta):
    session = get_session()

    conta = (
        session.query(Conta)
        .filter(Conta.id_conta == id_conta, Conta.deleted.is_(True))
        .first()
    )

    if not conta:
        session.close()
        flash("Conta não encontrada ou já está ativa.", "erro")
        return redirect(url_for("financeiro.listar_contas_inativas"))

    erros_empresa, _empresa = validar_empresa_ativa(
        session,
        conta.id_empresa,
        "Conta sem empresa vinculada não pode ser reativada.",
    )
    if erros_empresa:
        session.close()
        for erro in erros_empresa:
            flash(erro, "erro")
        return redirect(url_for("financeiro.listar_contas_inativas"))

    conta.deleted = False
    session.commit()
    session.close()

    flash("Conta reativada com sucesso.", "sucesso")
    return redirect(url_for("financeiro.listar_contas"))


# ----------------------------------------------------------------------
# NOVA MOVIMENTAÇÃO (Entrada / Saída / Transferência)
# ----------------------------------------------------------------------
@bp_financeiro.route("/movimentacoes/nova", methods=["GET", "POST"])
def nova_movimentacao():
    session = get_session()

    if request.method == "POST":
        conta_origem = None
        conta_destino = None
        plano = None

        tipo = (request.form.get("tipo") or "").strip()  # E / S / T
        data_str = (request.form.get("data") or "").strip()
        documento = (request.form.get("documento") or "AV").strip() or "AV"
        nr_documento = (request.form.get("nr_documento") or "NA").strip() or "NA"
        descricao = (request.form.get("descricao") or "").strip()
        valor_raw = (request.form.get("valor") or "").strip()
        id_empresa = request.form.get("id_empresa", type=int)
        id_centro_custo = request.form.get("id_centro_custo", type=int)

        # Campos conforme tipo
        id_conta_unica = request.form.get("id_conta")               # Entrada / Saída
        id_conta_origem = request.form.get("id_conta_origem")       # Transferência
        id_conta_destino = request.form.get("id_conta_destino")     # Transferência

        id_plano = request.form.get("id_plano")


        erros = []


        if tipo not in ("E", "S", "T"):
            erros.append("Selecione um tipo de movimentação válido.")
        if tipo == "T":
            erros_empresa_centro, _empresa = validar_empresa_ativa(session, id_empresa)
            id_centro_custo = None
        else:
            erros_empresa_centro, _empresa, _centro = validar_empresa_centro(
                session, id_empresa, id_centro_custo
            )
        erros.extend(erros_empresa_centro)

        doc_obj = None
        if not documento:
            erros.append("Selecione o documento.")
        else:
            doc_obj = (
                session.query(Documento)
                .filter(Documento.deleted.is_(False), Documento.tipo_doc == documento)
                .first()
            )
            if not doc_obj:
                erros.append("Documento inválido.")

        # data
        try:
            data_mov = datetime.strptime(data_str, "%Y-%m-%d").date()
        except Exception:
            data_mov = None
            erros.append("Data da movimentação inválida.")

        # valor
        try:
            valor = parse_money_ptbr(valor_raw)
            if valor <= 0:
                erros.append("Valor deve ser maior que zero.")
        except Exception:
            valor = None
            erros.append("Valor inválido.")

        # ---------------- TIPOS ----------------
        if tipo == "E":
            # Entrada: uma única conta (destino)
            id_conta = int(id_conta_unica) if id_conta_unica and id_conta_unica.isdigit() else None
            erros_conta, conta_destino = validar_conta_da_empresa(
                session,
                id_conta,
                id_empresa,
                "Selecione a conta da entrada.",
            )
            erros.extend(erros_conta)

            # plano financeiro (grupo 1, analítica)
            if not id_plano:
                erros.append("Selecione o plano financeiro (grupo 1, conta analítica).")
            else:
                plano = (
                    session.query(PlanoDeContas)
                    .filter(
                        PlanoDeContas.id_plano == int(id_plano),
                        PlanoDeContas.deleted.is_(False),
                        func.lower(PlanoDeContas.tipo) == "analitica",
                        PlanoDeContas.cod_estrutural.like("1.%"),
                    )
                    .first()
                )
                if not plano:
                    erros.append("Plano inválido. Para entradas, selecione conta analítica do grupo 1.")

        elif tipo == "S":
            # Saída: uma única conta (origem)
            id_conta = int(id_conta_unica) if id_conta_unica and id_conta_unica.isdigit() else None
            erros_conta, conta_origem = validar_conta_da_empresa(
                session,
                id_conta,
                id_empresa,
                "Selecione a conta da saída.",
            )
            erros.extend(erros_conta)

            # plano financeiro (grupo 2, analítica)
            if not id_plano:
                erros.append("Selecione o plano financeiro (grupo 2, conta analítica).")
            else:
                plano = (
                    session.query(PlanoDeContas)
                    .filter(
                        PlanoDeContas.id_plano == int(id_plano),
                        PlanoDeContas.deleted.is_(False),
                        func.lower(PlanoDeContas.tipo) == "analitica",
                        PlanoDeContas.cod_estrutural.like("2.%"),
                    )
                    .first()
                )
                if not plano:
                    erros.append("Plano inválido. Para saídas, selecione conta analítica do grupo 2.")

        elif tipo == "T":
            # Transferência: conta origem + conta destino, sem plano
            id_origem = int(id_conta_origem) if id_conta_origem and id_conta_origem.isdigit() else None
            erros_origem, conta_origem = validar_conta_da_empresa(
                session,
                id_origem,
                id_empresa,
                "Selecione a conta de origem da transferência.",
            )
            erros.extend(erros_origem)

            id_destino = int(id_conta_destino) if id_conta_destino and id_conta_destino.isdigit() else None
            erros_destino, conta_destino = validar_conta_da_empresa(
                session,
                id_destino,
                id_empresa,
                "Selecione a conta de destino da transferência.",
            )
            erros.extend(erros_destino)

            if conta_origem and conta_destino and conta_origem.id_conta == conta_destino.id_conta:
                erros.append("Conta de origem e destino não podem ser a mesma na transferência.")

            # plano não pode ser usado em transferência
            id_plano = None

        # Se houver erros, mostra e volta para o form
        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            mov = MovimentacaoConta(
                tipo=tipo,
                data=data_mov,
                documento=doc_obj,
                nr_documento=nr_documento,
                descricao=descricao,
                valor=valor,
                id_conta_origem=conta_origem.id_conta if conta_origem else None,
                id_conta_destino=conta_destino.id_conta if conta_destino else None,
                id_empresa=id_empresa,
                id_centro_custo=id_centro_custo,
                id_plano=plano.id_plano if plano else None,
            )
            session.add(mov)
            session.commit()
            session.close()

            flash("Movimentação registrada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_contas"))

    # --------- GET: carregar listas para o formulário ---------
        # GET: carregar combos
    contas = (
        session.query(Conta)
        .filter(Conta.deleted.is_(False))
        .order_by(Conta.descricao)
        .all()
    )

    planos_entrada = (
        session.query(PlanoDeContas)
        .filter(PlanoDeContas.deleted.is_(False))
        .filter(PlanoDeContas.cod_estrutural.like("1.%"))  # grupo 1
        .order_by(PlanoDeContas.cod_estrutural)
        .all()
    )

    planos_saida = (
        session.query(PlanoDeContas)
        .filter(PlanoDeContas.deleted.is_(False))
        .filter(PlanoDeContas.cod_estrutural.like("2.%"))  # grupo 2
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

    contas_view = [
        {"id": c.id_conta, "descricao": c.descricao, "id_empresa": c.id_empresa}
        for c in contas
    ]

    planos_entrada_view = [
        {"id": p.id_plano, "codigo": p.cod_estrutural, "nome": p.nome_conta, "tipo" : p.tipo}
        for p in planos_entrada
    ]
    planos_saida_view = [
        {"id": p.id_plano, "codigo": p.cod_estrutural, "nome": p.nome_conta, "tipo" : p.tipo}
        for p in planos_saida
    ]

    session.close()
    return render_template(
        "movimentacao_form.html",
        movimentacao=None,
        contas=contas_view,
        planos_entrada=planos_entrada_view,
        planos_saida=planos_saida_view,
        documentos=documentos,
        empresas=empresas_view,
        centros_custo=centros_custo_view,
        hoje=date.today().isoformat(),
    )



# ----------------------------------------------------------------------
# LISTAR MOVIMENTAÇÕES
# ----------------------------------------------------------------------
@bp_financeiro.route("/movimentacoes")
def listar_movimentacoes():
    session = get_session()

    movs = (
        session.query(MovimentacaoConta)
        .filter(MovimentacaoConta.deleted.is_(False))
        .order_by(MovimentacaoConta.data.desc(), MovimentacaoConta.id_movimentacao.desc())
        .all()
    )

    movs_view = []
    for m in movs:
        tipo_label = {
            "E": "Entrada",
            "S": "Saída",
            "T": "Transferência",
        }.get(m.tipo, m.tipo)

        conta_origem_desc = getattr(getattr(m, "conta_origem", None), "descricao", None)
        conta_destino_desc = getattr(getattr(m, "conta_destino", None), "descricao", None)
        plano_desc = None
        if getattr(m, "plano", None) is not None:
            plano_desc = f"{m.plano.cod_estrutural} - {m.plano.nome_conta}"

        movs_view.append({
            "id": m.id_movimentacao,
            "tipo": m.tipo,
            "tipo_label": tipo_label,
            "data": m.data.strftime("%d/%m/%Y") if m.data else "",
            "documento": m.documento,
            "nr_documento": m.nr_documento,
            "descricao": m.descricao,
            "valor": float(m.valor or 0),
            "conta_origem": conta_origem_desc,
            "conta_destino": conta_destino_desc,
            "empresa": f"{m.empresa.codigo} - {m.empresa.nome}" if m.empresa else "",
            "centro_custo": f"{m.centro_custo.codigo} - {m.centro_custo.nome}" if m.centro_custo else "",
            "plano": plano_desc,
        })

    session.close()
    return render_template("movimentacoes_list.html", movimentacoes=movs_view)


# ----------------------------------------------------------------------
# EDITAR MOVIMENTAÇÃO
# ----------------------------------------------------------------------
@bp_financeiro.route("/movimentacoes/<int:id_mov>/editar", methods=["GET", "POST"])
def editar_movimentacao(id_mov):
    session = get_session()

    mov = (
        session.query(MovimentacaoConta)
        .filter(
            MovimentacaoConta.id_movimentacao == id_mov,
            MovimentacaoConta.deleted.is_(False),
        )
        .first()
    )

    if not mov:
        session.close()
        flash("Movimentação não encontrada.", "erro")
        return redirect(url_for("financeiro.listar_movimentacoes"))

    if request.method == "POST":
        erros = []
        tipo = (request.form.get("tipo") or "").strip()  # E / S / T
        data_str = (request.form.get("data") or "").strip()

        # --- documento (vem do <select name="documento"> como sigla: "AV", "NF", etc)
        doc_sigla = (request.form.get("documento") or "").strip()
        if not doc_sigla:
            erros.append("Selecione o documento.")
            doc_obj = None
        else:
            doc_obj = (
                session.query(Documento)
                .filter(Documento.deleted.is_(False), Documento.tipo_doc == doc_sigla)
                .first()
            )
            if not doc_obj:
                erros.append("Documento selecionado não encontrado.")

        
        nr_documento = (request.form.get("nr_documento") or "NA").strip() or "NA"
        descricao = (request.form.get("descricao") or "").strip()
        valor_raw = (request.form.get("valor") or "").strip()
        id_empresa = request.form.get("id_empresa", type=int)
        id_centro_custo = request.form.get("id_centro_custo", type=int)

        id_conta_unica = request.form.get("id_conta")
        id_conta_origem = request.form.get("id_conta_origem")
        id_conta_destino = request.form.get("id_conta_destino")

        id_plano = request.form.get("id_plano")


        if tipo not in ("E", "S", "T"):
            erros.append("Selecione um tipo de movimentação válido.")
        if tipo == "T":
            erros_empresa_centro, _empresa = validar_empresa_ativa(session, id_empresa)
            id_centro_custo = None
        else:
            erros_empresa_centro, _empresa, _centro = validar_empresa_centro(
                session, id_empresa, id_centro_custo
            )
        erros.extend(erros_empresa_centro)

        # data
        try:
            data_mov = datetime.strptime(data_str, "%Y-%m-%d").date()
        except Exception:
            data_mov = None
            erros.append("Data da movimentação inválida.")

        # valor
        
        try:
            valor = parse_money_ptbr(valor_raw)  # <-- aqui
            if valor <= 0:
                erros.append("Valor deve ser maior que zero.")
        except Exception:
            valor = None
            erros.append("Valor inválido.")

        conta_origem = None
        conta_destino = None
        plano = None

        if tipo == "E":
            id_conta = int(id_conta_unica) if id_conta_unica and id_conta_unica.isdigit() else None
            erros_conta, conta_destino = validar_conta_da_empresa(
                session,
                id_conta,
                id_empresa,
                "Selecione a conta da entrada.",
            )
            erros.extend(erros_conta)

            if not id_plano:
                erros.append("Selecione o plano financeiro (grupo 1, conta analítica).")
            else:
                plano = (
                    session.query(PlanoDeContas)
                    .filter(
                        PlanoDeContas.id_plano == int(id_plano),
                        PlanoDeContas.deleted.is_(False),
                        PlanoDeContas.cod_estrutural.like("1.%"),
                    )
                    .first()
                )
                if not plano:
                    erros.append("Plano inválido. Para entradas, selecione conta analítica do grupo 1.")

        elif tipo == "S":
            id_conta = int(id_conta_unica) if id_conta_unica and id_conta_unica.isdigit() else None
            erros_conta, conta_origem = validar_conta_da_empresa(
                session,
                id_conta,
                id_empresa,
                "Selecione a conta da saída.",
            )
            erros.extend(erros_conta)

            if not id_plano:
                erros.append("Selecione o plano financeiro (grupo 2, conta analítica).")
            else:
                plano = (
                    session.query(PlanoDeContas)
                    .filter(
                        PlanoDeContas.id_plano == int(id_plano),
                        PlanoDeContas.deleted.is_(False),
                        PlanoDeContas.cod_estrutural.like("2.%"),
                    )
                    .first()
                )
                if not plano:
                    erros.append("Plano inválido. Para saídas, selecione conta analítica do grupo 2.")

        elif tipo == "T":
            id_origem = int(id_conta_origem) if id_conta_origem and id_conta_origem.isdigit() else None
            erros_origem, conta_origem = validar_conta_da_empresa(
                session,
                id_origem,
                id_empresa,
                "Selecione a conta de origem da transferência.",
            )
            erros.extend(erros_origem)

            id_destino = int(id_conta_destino) if id_conta_destino and id_conta_destino.isdigit() else None
            erros_destino, conta_destino = validar_conta_da_empresa(
                session,
                id_destino,
                id_empresa,
                "Selecione a conta de destino da transferência.",
            )
            erros.extend(erros_destino)

            if conta_origem and conta_destino and conta_origem.id_conta == conta_destino.id_conta:
                erros.append("Conta de origem e destino não podem ser a mesma na transferência.")

            id_plano = None

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            mov.tipo = tipo
            mov.data = data_mov
            mov.documento = doc_obj          # relationship -> precisa ser instância
            mov.id_doc = doc_obj.id_doc      # garante o FK, se existir no model
            mov.nr_documento = nr_documento
            mov.descricao = descricao
            mov.valor = valor
            mov.id_conta_origem = conta_origem.id_conta if conta_origem else None
            mov.id_conta_destino = conta_destino.id_conta if conta_destino else None
            mov.id_empresa = id_empresa
            mov.id_centro_custo = id_centro_custo
            mov.id_plano = plano.id_plano if plano else None

            session.commit()
            session.close()

            flash("Movimentação atualizada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_movimentacoes"))

    # GET – carregar dados para o formulário
    contas = (
        session.query(Conta)
        .filter(Conta.deleted.is_(False))
        .order_by(Conta.descricao)
        .all()
    )

    planos_entrada = (
        session.query(PlanoDeContas)
        .filter(
            PlanoDeContas.deleted.is_(False),
            PlanoDeContas.cod_estrutural.like("1.%"),
        )
        .order_by(PlanoDeContas.cod_estrutural)
        .all()
    )

    planos_saida = (
        session.query(PlanoDeContas)
        .filter(
            PlanoDeContas.deleted.is_(False),
            PlanoDeContas.cod_estrutural.like("2.%"),
        )
        .order_by(PlanoDeContas.cod_estrutural)
        .all()
    )

    contas_view = [
        {
            "id": c.id_conta,
            "descricao": c.descricao,
            "id_empresa": c.id_empresa,
            "tipo": c.tipo,
        }
        for c in contas
    ]

    planos_entrada_view = [{
        "id": p.id_plano,
        "codigo": p.cod_estrutural,
        "nome": p.nome_conta,
        "tipo": (p.tipo or "").lower(),   # "analitica" / "totalizadora"
    } for p in planos_entrada]

    planos_saida_view = [{
        "id": p.id_plano,
        "codigo": p.cod_estrutural,
        "nome": p.nome_conta,
        "tipo": (p.tipo or "").lower(),
    } for p in planos_saida]

    empresas_view, centros_custo_view = listar_empresas_centros_ativos(session)

    mov_view = {
        "id": mov.id_movimentacao,
        "tipo": mov.tipo,
        "data": mov.data.strftime("%Y-%m-%d") if mov.data else "",
        "documento": mov.documento,
        "nr_documento": mov.nr_documento,
        "descricao": mov.descricao or "",
        "valor": float(mov.valor or 0),
        # Para E/S usamos um campo único de conta:
        "id_conta": mov.id_conta_destino if mov.tipo == "E" else mov.id_conta_origem if mov.tipo == "S" else None,
        # Para T:
        "id_conta_origem": mov.id_conta_origem,
        "id_conta_destino": mov.id_conta_destino,
        "id_empresa": getattr(mov, "id_empresa", None),
        "id_centro_custo": getattr(mov, "id_centro_custo", None),
        "id_plano": mov.id_plano,
    }

    documentos = (
        session.query(Documento)
        .filter(Documento.deleted.is_(False))
        .order_by(Documento.tipo_doc)
        .all()
    )

    hoje = date.today().isoformat()
    session.close()

    return render_template(
        "movimentacao_edit_form.html",
        movimentacao=mov_view,
        contas=contas_view,
        planos_entrada=planos_entrada_view,
        planos_saida=planos_saida_view,
        documentos=documentos,
        empresas=empresas_view,
        centros_custo=centros_custo_view,
        hoje=date.today().isoformat(),
    )


# ----------------------------------------------------------------------
# EXCLUIR MOVIMENTAÇÃO (soft delete)
# ----------------------------------------------------------------------
@bp_financeiro.route("/movimentacoes/<int:id_mov>/excluir", methods=["POST"])
def excluir_movimentacao(id_mov):
    session = get_session()

    mov = (
        session.query(MovimentacaoConta)
        .filter(
            MovimentacaoConta.id_movimentacao == id_mov,
            MovimentacaoConta.deleted.is_(False),
        )
        .first()
    )

    if not mov:
        session.close()
        flash("Movimentação não encontrada.", "erro")
        return redirect(url_for("financeiro.listar_movimentacoes"))

    # 🔒 Regra: não pode excluir movimentação conciliada
    if getattr(mov, "conciliado", False):
        session.close()
        flash("Não é possível excluir uma movimentação conciliada.", "erro")
        return redirect(url_for("financeiro.listar_movimentacoes"))

    mov.deleted = True
    session.commit()
    session.close()

    flash("Movimentação excluída com sucesso.", "sucesso")
    return redirect(url_for("financeiro.listar_movimentacoes"))



# ----------------------------------------------------------------------
# ANÁLISE DE RESULTADOS (tipo DRE) POR MÊS
# ----------------------------------------------------------------------
@bp_financeiro.route("/analise", methods=["GET"])
def analise_resultados():
    session = get_session()
    empresas_view, id_empresa = _empresas_ativas_e_filtro(session)

    # --- Lê mês/ano da URL ou usa mês atual ---
    hoje = date.today()
    mes_str = request.args.get("mes")
    ano_str = request.args.get("ano")

    try:
        mes = int(mes_str) if mes_str else hoje.month
    except ValueError:
        mes = hoje.month

    try:
        ano = int(ano_str) if ano_str else hoje.year
    except ValueError:
        ano = hoje.year

    if mes < 1 or mes > 12:
        mes = hoje.month

    # data inicial e final do período
    data_ini = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1)
    else:
        data_fim = date(ano, mes + 1, 1)

    # ---------------------------------------------------
    # 1) MOVIMENTAÇÕES (ENTRADAS/SAÍDAS) - IGNORA T (transferência)
    # ---------------------------------------------------

    # Receitas por conta analítica (grupo 1, tipo 'E')
    mov_receitas_query = (
        session.query(
            MovimentacaoConta.id_plano,
            func.sum(MovimentacaoConta.valor).label("valor"),
        )
        .join(PlanoDeContas, MovimentacaoConta.id_plano == PlanoDeContas.id_plano)
        .filter(
            MovimentacaoConta.deleted.is_(False),
            PlanoDeContas.deleted.is_(False),
            MovimentacaoConta.tipo == "E",  # Entrada
            MovimentacaoConta.data >= data_ini,
            MovimentacaoConta.data < data_fim,
            PlanoDeContas.cod_estrutural.like("1%"),  # grupo 1
        )
    )
    if id_empresa:
        mov_receitas_query = mov_receitas_query.filter(MovimentacaoConta.id_empresa == id_empresa)
    mov_receitas_rows = mov_receitas_query.group_by(MovimentacaoConta.id_plano).all()
    mov_receitas_por_plano = {
        row.id_plano: float(row.valor or 0) for row in mov_receitas_rows
    }

    # Despesas por conta analítica (grupo 2, tipo 'S')
    mov_despesas_query = (
        session.query(
            MovimentacaoConta.id_plano,
            func.sum(MovimentacaoConta.valor).label("valor"),
        )
        .join(PlanoDeContas, MovimentacaoConta.id_plano == PlanoDeContas.id_plano)
        .filter(
            MovimentacaoConta.deleted.is_(False),
            PlanoDeContas.deleted.is_(False),
            MovimentacaoConta.tipo == "S",  # Saída
            MovimentacaoConta.data >= data_ini,
            MovimentacaoConta.data < data_fim,
            PlanoDeContas.cod_estrutural.like("2%"),  # grupo 2
        )
    )
    if id_empresa:
        mov_despesas_query = mov_despesas_query.filter(MovimentacaoConta.id_empresa == id_empresa)
    mov_despesas_rows = mov_despesas_query.group_by(MovimentacaoConta.id_plano).all()
    mov_despesas_por_plano = {
        row.id_plano: float(row.valor or 0) for row in mov_despesas_rows
    }

    # ---------------------------------------------------
    # 2) BAIXAS DE TÍTULOS (CASH BASIS DOS TÍTULOS)
    #    - Usa plano financeiro do TÍTULO (grupo 1 = receita, grupo 2 = despesa)
    # ---------------------------------------------------

    # Receitas via BAIXAS (títulos de grupo 1)
    baixas_receitas_query = (
        session.query(
            Titulo.id_plano.label("id_plano"),
            func.sum(Baixa.valor_baixa).label("valor"),
        )
        .join(Titulo, Baixa.id_titulo == Titulo.id_titulo)
        .join(PlanoDeContas, Titulo.id_plano == PlanoDeContas.id_plano)
        .filter(
            Baixa.deleted.is_(False),
            Titulo.deleted.is_(False),
            PlanoDeContas.deleted.is_(False),
            Baixa.data >= data_ini,
            Baixa.data < data_fim,
            PlanoDeContas.cod_estrutural.like("1%"),  # grupo 1
        )
    )
    if id_empresa:
        baixas_receitas_query = baixas_receitas_query.filter(Titulo.id_empresa == id_empresa)
    baixas_receitas_rows = baixas_receitas_query.group_by(Titulo.id_plano).all()
    baixas_receitas_por_plano = {
        row.id_plano: float(row.valor or 0) for row in baixas_receitas_rows
    }

    # Despesas via BAIXAS (títulos de grupo 2)
    baixas_despesas_query = (
        session.query(
            Titulo.id_plano.label("id_plano"),
            func.sum(Baixa.valor_baixa).label("valor"),
        )
        .join(Titulo, Baixa.id_titulo == Titulo.id_titulo)
        .join(PlanoDeContas, Titulo.id_plano == PlanoDeContas.id_plano)
        .filter(
            Baixa.deleted.is_(False),
            Titulo.deleted.is_(False),
            PlanoDeContas.deleted.is_(False),
            Baixa.data >= data_ini,
            Baixa.data < data_fim,
            PlanoDeContas.cod_estrutural.like("2%"),  # grupo 2
        )
    )
    if id_empresa:
        baixas_despesas_query = baixas_despesas_query.filter(Titulo.id_empresa == id_empresa)
    baixas_despesas_rows = baixas_despesas_query.group_by(Titulo.id_plano).all()
    baixas_despesas_por_plano = {
        row.id_plano: float(row.valor or 0) for row in baixas_despesas_rows
    }

    # ---------------------------------------------------
    # 3) TOTAL POR CONTA ANALÍTICA (movimentações + baixas)
    # ---------------------------------------------------

    # todas contas de receitas (grupo 1)
    planos_receita = (
        session.query(PlanoDeContas)
        .filter(
            PlanoDeContas.deleted.is_(False),
            PlanoDeContas.cod_estrutural.like("1%"),
        )
        .order_by(PlanoDeContas.cod_estrutural)
        .all()
    )

    # todas contas de despesas (grupo 2)
    planos_despesa = (
        session.query(PlanoDeContas)
        .filter(
            PlanoDeContas.deleted.is_(False),
            PlanoDeContas.cod_estrutural.like("2%"),
        )
        .order_by(PlanoDeContas.cod_estrutural)
        .all()
    )

    # mapa id_plano -> código para facilitar agregação por prefixo
    cod_por_id = {p.id_plano: p.cod_estrutural for p in planos_receita + planos_despesa}

    # valor base por conta analítica (grupo 1)
    base_receitas_por_id = {}
    for id_plano, cod in cod_por_id.items():
        if not cod.startswith("1"):
            continue
        v_mov = mov_receitas_por_plano.get(id_plano, 0.0)
        v_bx = baixas_receitas_por_plano.get(id_plano, 0.0)
        total = v_mov + v_bx
        if abs(total) > 0.0001:
            base_receitas_por_id[id_plano] = total

    # valor base por conta analítica (grupo 2)
    base_despesas_por_id = {}
    for id_plano, cod in cod_por_id.items():
        if not cod.startswith("2"):
            continue
        v_mov = mov_despesas_por_plano.get(id_plano, 0.0)
        v_bx = baixas_despesas_por_plano.get(id_plano, 0.0)
        total = v_mov + v_bx
        if abs(total) > 0.0001:
            base_despesas_por_id[id_plano] = total

    # ---------------------------------------------------
    # 4) AGREGAÇÃO NAS CONTAS TOTALIZADORAS (por prefixo de código)
    # ---------------------------------------------------
    def agrega_por_prefixo(planos_lista, base_por_id):
        """
        Para cada conta (totalizadora ou analítica),
        soma o valor de TODAS as contas analíticas
        cujo código estrutural começa com o código dela.
        """
        resultado = []

        # só queremos códigos das analíticas que realmente têm movimento
        ids_analiticas = list(base_por_id.keys())

        for plano in planos_lista:
            prefixo = plano.cod_estrutural or ""
            soma = 0.0

            for id_ana in ids_analiticas:
                cod_ana = cod_por_id[id_ana]
                # regra simples de prefixo: "1.01" soma "1.01" e "1.01.001", etc.
                if cod_ana == prefixo or cod_ana.startswith(prefixo + "."):
                    soma += base_por_id[id_ana]

            if abs(soma) > 0.0001:
                resultado.append(
                    {
                        "id_plano": plano.id_plano,
                        "cod": plano.cod_estrutural,
                        "nome": plano.nome_conta,
                        "tipo": plano.tipo,  # totalizadora / analítica
                        "valor": soma,
                    }
                )

        return resultado

    receitas_view = agrega_por_prefixo(planos_receita, base_receitas_por_id)
    despesas_view = agrega_por_prefixo(planos_despesa, base_despesas_por_id)

    # totais sem dupla contagem: soma só das contas analíticas
    total_receitas = sum(base_receitas_por_id.values())
    total_despesas = sum(base_despesas_por_id.values())
    resultado = total_receitas - total_despesas

   

    meses = [
        (1, "Jan"), (2, "Fev"), (3, "Mar"), (4, "Abr"),
        (5, "Mai"), (6, "Jun"), (7, "Jul"), (8, "Ago"),
        (9, "Set"), (10, "Out"), (11, "Nov"), (12, "Dez"),
    ]
    anos = list(range(hoje.year - 3, hoje.year + 2))

    session.close()

    return render_template(
        "analise_resultados.html",
        mes=mes,
        ano=ano,
        data_ini=data_ini,
        data_fim=data_fim,
        meses=meses,
        anos=anos,
        receitas=receitas_view,
        despesas=despesas_view,
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        resultado=resultado,
        timedelta=timedelta,  
        empresas=empresas_view,
        id_empresa=id_empresa,
    )


# ----------------------------------------------------------------------
# DETALHE DA CONTA NA ANÁLISE DE RESULTADOS
# ----------------------------------------------------------------------
@bp_financeiro.route("/analise/conta/<int:id_plano>", methods=["GET"])
def detalhe_conta_resultado(id_plano):
    session = get_session()
    empresas_view, id_empresa = _empresas_ativas_e_filtro(session)

    hoje = date.today()
    mes_str = request.args.get("mes")
    ano_str = request.args.get("ano")

    try:
        mes = int(mes_str) if mes_str else hoje.month
    except ValueError:
        mes = hoje.month

    try:
        ano = int(ano_str) if ano_str else hoje.year
    except ValueError:
        ano = hoje.year

    if mes < 1 or mes > 12:
        mes = hoje.month

    data_ini = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1)
    else:
        data_fim = date(ano, mes + 1, 1)

    # Plano
    plano = (
        session.query(PlanoDeContas)
        .filter(
            PlanoDeContas.id_plano == id_plano,
            PlanoDeContas.deleted.is_(False),
        )
        .first()
    )
    if not plano:
        session.close()
        flash("Plano financeiro não encontrado.", "erro")
        return redirect(url_for("financeiro.analise_resultados"))

    # Movimentações E/S dessa conta
    movs_query = (
        session.query(MovimentacaoConta, Conta)
        .outerjoin(Conta, MovimentacaoConta.id_conta_destino == Conta.id_conta)
        .filter(
            MovimentacaoConta.deleted.is_(False),
            MovimentacaoConta.id_plano == id_plano,
            MovimentacaoConta.tipo.in_(["E", "S"]),
            MovimentacaoConta.data >= data_ini,
            MovimentacaoConta.data < data_fim,
        )
    )
    if id_empresa:
        movs_query = movs_query.filter(MovimentacaoConta.id_empresa == id_empresa)
    movs = movs_query.order_by(MovimentacaoConta.data, MovimentacaoConta.id_movimentacao).all()

    movs_view = []
    total_movs = 0.0
    for mov, conta in movs:
        valor = float(mov.valor or 0)
        total_movs += valor
        movs_view.append(
            {
                "data": mov.data.strftime("%d/%m/%Y") if mov.data else "",
                "tipo": mov.tipo,
                "documento": mov.documento,
                "nr_documento": mov.nr_documento,
                "descricao": mov.descricao or "",
                "conta": conta.descricao if conta else "",
                "valor": valor,
            }
        )

    # Baixas de títulos dessa conta de plano
    baixas_query = (
        session.query(Baixa, Titulo, Conta)
        .join(Titulo, Baixa.id_titulo == Titulo.id_titulo)
        .join(Conta, Baixa.id_conta == Conta.id_conta)
        .filter(
            Baixa.deleted.is_(False),
            Titulo.deleted.is_(False),
            Titulo.id_plano == id_plano,
            Baixa.data >= data_ini,
            Baixa.data < data_fim,
        )
    )
    if id_empresa:
        baixas_query = baixas_query.filter(Titulo.id_empresa == id_empresa)
    baixas = baixas_query.order_by(Baixa.data, Baixa.id_baixa).all()

    baixas_view = []
    total_baixas = 0.0
    for bx, titulo, conta in baixas:
        valor = float(bx.valor_baixa or 0)
        total_baixas += valor
        baixas_view.append(
            {
                "data": bx.data.strftime("%d/%m/%Y") if bx.data else "",
                "documento": titulo.documento,
                "nr_documento": titulo.nr_documento,
                "credor": titulo.credor.nome if titulo.credor else "",
                "conta": conta.descricao if conta else "",
                "valor": valor,
            }
        )

    total_geral = total_movs + total_baixas

    meses = [
        (1, "Jan"), (2, "Fev"), (3, "Mar"), (4, "Abr"),
        (5, "Mai"), (6, "Jun"), (7, "Jul"), (8, "Ago"),
        (9, "Set"), (10, "Out"), (11, "Nov"), (12, "Dez"),
    ]

    session.close()

    return render_template(
        "analise_resultados_detalhe.html",
        plano=plano,
        mes=mes,
        ano=ano,
        data_ini=data_ini,
        data_fim=data_fim,
        meses=meses,
        movimentacoes=movs_view,
        baixas=baixas_view,
        total_movs=total_movs,
        total_baixas=total_baixas,
        total_geral=total_geral,
        empresas=empresas_view,
        id_empresa=id_empresa,
    )


    # ---------------------------------------------------
    # 1) MOVIMENTAÇÕES (ENTRADAS/SAÍDAS) - IGNORA T (transferência)
    # ---------------------------------------------------

    # Receitas por conta analítica (grupo 1, tipo 'E')
    mov_receitas_rows = (
        session.query(
            MovimentacaoConta.id_plano,
            func.sum(MovimentacaoConta.valor).label("valor"),
        )
        .join(PlanoDeContas, MovimentacaoConta.id_plano == PlanoDeContas.id_plano)
        .filter(
            MovimentacaoConta.deleted.is_(False),
            PlanoDeContas.deleted.is_(False),
            MovimentacaoConta.tipo == "E",  # Entrada
            MovimentacaoConta.data >= data_ini,
            MovimentacaoConta.data < data_fim,
            PlanoDeContas.cod_estrutural.like("1%"),  # grupo 1
        )
        .group_by(MovimentacaoConta.id_plano)
        .all()
    )
    mov_receitas_por_plano = {
        row.id_plano: float(row.valor or 0) for row in mov_receitas_rows
    }

    # Despesas por conta analítica (grupo 2, tipo 'S')
    mov_despesas_rows = (
        session.query(
            MovimentacaoConta.id_plano,
            func.sum(MovimentacaoConta.valor).label("valor"),
        )
        .join(PlanoDeContas, MovimentacaoConta.id_plano == PlanoDeContas.id_plano)
        .filter(
            MovimentacaoConta.deleted.is_(False),
            PlanoDeContas.deleted.is_(False),
            MovimentacaoConta.tipo == "S",  # Saída
            MovimentacaoConta.data >= data_ini,
            MovimentacaoConta.data < data_fim,
            PlanoDeContas.cod_estrutural.like("2%"),  # grupo 2
        )
        .group_by(MovimentacaoConta.id_plano)
        .all()
    )
    mov_despesas_por_plano = {
        row.id_plano: float(row.valor or 0) for row in mov_despesas_rows
    }

@bp_financeiro.route("/extrato", methods=["GET", "POST"])
def extrato_conta():
    session = get_session()
    empresas_view, id_empresa = _empresas_ativas_e_filtro(session)

    hoje = date.today()

    data_ini_str = request.args.get("data_ini")
    data_fim_str = request.args.get("data_fim")
    id_conta_str = request.args.get("id_conta")

    # datas padrão: mês atual
    try:
        if data_ini_str:
            d_ini = datetime.strptime(data_ini_str, "%Y-%m-%d").date()
        else:
            d_ini = date(hoje.year, hoje.month, 1)
    except ValueError:
        d_ini = date(hoje.year, hoje.month, 1)

    try:
        if data_fim_str:
            d_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
        else:
            d_fim = hoje
    except ValueError:
        d_fim = hoje

    # lista de contas para o select
    contas_query = (
        session.query(Conta)
        .filter(Conta.deleted.is_(False))
    )
    if id_empresa:
        contas_query = contas_query.filter(Conta.id_empresa == id_empresa)
    contas = contas_query.order_by(Conta.descricao).all()

    conta_sel = None

    if id_conta_str:
        try:
            id_conta = int(id_conta_str)
        except ValueError:
            id_conta = None

        if id_conta:
            conta_sel = (
                session.query(Conta)
                .filter(
                    Conta.id_conta == id_conta,
                    Conta.deleted.is_(False),
                    *([Conta.id_empresa == id_empresa] if id_empresa else []),
                )
                .first()
            )

    # Se for POST, salvar conciliação (antes de recalcular o extrato)
    if request.method == "POST" and conta_sel:
        # IDs marcados como conciliados na tela
        marcados_mov = set()
        marcados_bx = set()
        for key in request.form.keys():
            if key.startswith("mov_"):
                try:
                    marcados_mov.add(int(key.split("_", 1)[1]))
                except ValueError:
                    pass
            elif key.startswith("bx_"):
                try:
                    marcados_bx.add(int(key.split("_", 1)[1]))
                except ValueError:
                    pass

        # Trazer os objetos do período para atualizar flag
        movs_periodo_db = (
            session.query(MovimentacaoConta)
            .filter(
                MovimentacaoConta.deleted.is_(False),
                MovimentacaoConta.data >= d_ini,
                MovimentacaoConta.data <= d_fim,
                or_(
                    MovimentacaoConta.id_conta_destino == conta_sel.id_conta,
                    MovimentacaoConta.id_conta_origem == conta_sel.id_conta,
                ),
            )
            .all()
        )

        for m in movs_periodo_db:
            m.conciliado = m.id_movimentacao in marcados_mov

        baixas_periodo_db = (
            session.query(Baixa)
            .filter(
                Baixa.deleted.is_(False),
                Baixa.data >= d_ini,
                Baixa.data <= d_fim,
                Baixa.id_conta == conta_sel.id_conta,
            )
            .all()
        )

        for b in baixas_periodo_db:
            b.conciliado = b.id_baixa in marcados_bx

        session.commit()
        flash("Conciliação salva com sucesso.", "sucesso")

    # --------------------------------
    # A partir daqui, construção do extrato (igual para GET e POST)
    # --------------------------------
    extrato_linhas = []
    saldo_inicial = None
    saldo_final = None
    total_entradas = 0.0
    total_saidas = 0.0

    if conta_sel:
        # saldo inicial: saldo_inicial da conta + tudo antes de d_ini
        saldo = float(conta_sel.saldo_inicial or 0)

        saldo_movimentos_anteriores = (
            session.query(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                (MovimentacaoConta.tipo == "E")
                                & (MovimentacaoConta.id_conta_destino == conta_sel.id_conta),
                                MovimentacaoConta.valor,
                            ),
                            (
                                (MovimentacaoConta.tipo == "S")
                                & (MovimentacaoConta.id_conta_origem == conta_sel.id_conta),
                                -MovimentacaoConta.valor,
                            ),
                            (
                                (MovimentacaoConta.tipo == "T")
                                & (MovimentacaoConta.id_conta_destino == conta_sel.id_conta),
                                MovimentacaoConta.valor,
                            ),
                            (
                                (MovimentacaoConta.tipo == "T")
                                & (MovimentacaoConta.id_conta_origem == conta_sel.id_conta),
                                -MovimentacaoConta.valor,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                )
            )
            .filter(
                MovimentacaoConta.deleted.is_(False),
                MovimentacaoConta.data < d_ini,
                or_(
                    MovimentacaoConta.id_conta_destino == conta_sel.id_conta,
                    MovimentacaoConta.id_conta_origem == conta_sel.id_conta,
                ),
            )
            .scalar()
        )
        saldo += float(saldo_movimentos_anteriores or 0)

        total_baixas_anteriores = (
            session.query(func.coalesce(func.sum(Baixa.valor_baixa), 0))
            .filter(
                Baixa.deleted.is_(False),
                Baixa.data < d_ini,
                Baixa.id_conta == conta_sel.id_conta,
            )
            .scalar()
        )
        saldo -= float(total_baixas_anteriores or 0)

        saldo_inicial = saldo

        # movimentações no período (com flag conciliado)
        movs_periodo = (
            session.query(MovimentacaoConta)
            .options(joinedload(MovimentacaoConta.documento))
            .filter(
                MovimentacaoConta.deleted.is_(False),
                MovimentacaoConta.data >= d_ini,
                MovimentacaoConta.data <= d_fim,
                or_(
                    MovimentacaoConta.id_conta_destino == conta_sel.id_conta,
                    MovimentacaoConta.id_conta_origem == conta_sel.id_conta,
                ),
            )
            .order_by(MovimentacaoConta.data, MovimentacaoConta.id_movimentacao)
            .all()
        )

        # baixas no período (com título e flag conciliado)
        baixas_periodo = (
            session.query(Baixa, Titulo)
            .options(joinedload(Titulo.documento))
            .join(Titulo, Baixa.id_titulo == Titulo.id_titulo)
            .filter(
                Baixa.deleted.is_(False),
                Titulo.deleted.is_(False),
                Baixa.data >= d_ini,
                Baixa.data <= d_fim,
                Baixa.id_conta == conta_sel.id_conta,
            )
            .order_by(Baixa.data, Baixa.id_baixa)
            .all()
        )

        linhas = []

        # Movimentações (Entradas / Saídas / Transferências)
        for m in movs_periodo:
            valor = float(m.valor or 0)
            entrada = 0.0
            saida = 0.0

            if m.tipo == "E" and m.id_conta_destino == conta_sel.id_conta:
                natureza = "Entrada"
                entrada = valor
            elif m.tipo == "S" and m.id_conta_origem == conta_sel.id_conta:
                natureza = "Saída"
                saida = valor
            elif m.tipo == "T":
                if m.id_conta_destino == conta_sel.id_conta:
                    natureza = "Transf. entrada"
                    entrada = valor
                else:
                    natureza = "Transf. saída"
                    saida = valor
            else:
                natureza = m.tipo or ""

            linhas.append(
                {
                    "origem_tipo": "mov",
                    "id": m.id_movimentacao,
                    "conciliado": bool(m.conciliado),
                    "data": m.data,
                    "tipo": natureza,
                    "origem": "Movimentação",
                    "documento": _compor_documento_extrato(m.documento, m.nr_documento),
                    "nr_documento": "",
                    "descricao": m.descricao or "",
                    "entrada": entrada,
                    "saida": saida,
                }
            )

        # Baixas de título (saída)
        for b, t in baixas_periodo:
            valor = float(b.valor_baixa or 0)
            linhas.append(
                {
                    "origem_tipo": "bx",
                    "id": b.id_baixa,
                    "conciliado": bool(b.conciliado),
                    "data": b.data,
                    "tipo": "Baixa de título",
                    "origem": "Baixa",
                    "documento": _compor_documento_extrato(t.documento, t.nr_documento),
                    "nr_documento": "",
                    "descricao": t.observacao or "",
                    "id_titulo": t.id_titulo,
                    "id_parcela": b.id_parcela,
                    "numero_parcela": (
                        b.parcela.numero_parcela
                        if getattr(b, "parcela", None)
                        else None
                    ),
                    "entrada": 0.0,
                    "saida": valor,
                }
            )

        # ordena por data
        linhas.sort(key=lambda x: (x["data"] or date.min, x["origem_tipo"], x["id"]))

        # compõe saldo linha a linha
        saldo_corrente = saldo_inicial
        for lin in linhas:
            saldo_corrente += lin["entrada"] - lin["saida"]
            lin["data_str"] = lin["data"].strftime("%d/%m/%Y") if lin["data"] else ""
            lin["entrada_str"] = f"{lin['entrada']:.2f}" if lin["entrada"] else ""
            lin["saida_str"] = f"{lin['saida']:.2f}" if lin["saida"] else ""
            lin["saldo"] = saldo_corrente
            lin["saldo_str"] = f"{saldo_corrente:.2f}"
            total_entradas += lin["entrada"]
            total_saidas += lin["saida"]

        extrato_linhas = linhas
        saldo_final = saldo_corrente

        # --- Converte para estruturas simples antes de fechar a sessão ---

    contas_view = [
        {
            "id_conta": c.id_conta,
            "descricao": c.descricao,
        }
        for c in contas
    ]

    conta_view = None
    if conta_sel:
        conta_view = {
            "id_conta": conta_sel.id_conta,
            "descricao": conta_sel.descricao,
        }

        # --- Converte para estruturas simples antes de fechar a sessão ---

    contas_view = [
        {
            "id_conta": c.id_conta,
            "descricao": c.descricao,
        }
        for c in contas
    ]

    conta_view = None
    if conta_sel:
        conta_view = {
            "id_conta": conta_sel.id_conta,
            "descricao": conta_sel.descricao,
        }

    session.close()

    return render_template(
        "extrato_conta.html",
        contas=contas_view,
        conta_selecionada=conta_view,
        data_ini=d_ini,
        data_fim=d_fim,
        extrato=extrato_linhas,
        saldo_inicial=saldo_inicial,
        saldo_final=saldo_final,
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        empresas=empresas_view,
        id_empresa=id_empresa,
    )



    # ---------------------------------------------------
    # 2) BAIXAS DE TÍTULOS (CASH BASIS DOS TÍTULOS)
    #    - Usa plano financeiro do TÍTULO (grupo 1 = receita, grupo 2 = despesa)
    # ---------------------------------------------------

    # Receitas via BAIXAS (títulos de grupo 1)
    baixas_receitas_rows = (
        session.query(
            Titulo.id_plano.label("id_plano"),
            func.sum(Baixa.valor_baixa).label("valor"),
        )
        .join(Titulo, Baixa.id_titulo == Titulo.id_titulo)
        .join(PlanoDeContas, Titulo.id_plano == PlanoDeContas.id_plano)
        .filter(
            Baixa.deleted.is_(False),
            Titulo.deleted.is_(False),
            PlanoDeContas.deleted.is_(False),
            Baixa.data >= data_ini,
            Baixa.data < data_fim,
            PlanoDeContas.cod_estrutural.like("1%"),  # grupo 1
        )
        .group_by(Titulo.id_plano)
        .all()
    )
    baixas_receitas_por_plano = {
        row.id_plano: float(row.valor or 0) for row in baixas_receitas_rows
    }

    # Despesas via BAIXAS (títulos de grupo 2)
    baixas_despesas_rows = (
        session.query(
            Titulo.id_plano.label("id_plano"),
            func.sum(Baixa.valor_baixa).label("valor"),
        )
        .join(Titulo, Baixa.id_titulo == Titulo.id_titulo)
        .join(PlanoDeContas, Titulo.id_plano == PlanoDeContas.id_plano)
        .filter(
            Baixa.deleted.is_(False),
            Titulo.deleted.is_(False),
            PlanoDeContas.deleted.is_(False),
            Baixa.data >= data_ini,
            Baixa.data < data_fim,
            PlanoDeContas.cod_estrutural.like("2%"),  # grupo 2
        )
        .group_by(Titulo.id_plano)
        .all()
    )
    baixas_despesas_por_plano = {
        row.id_plano: float(row.valor or 0) for row in baixas_despesas_rows
    }

    # ---------------------------------------------------
    # 3) TOTAL POR CONTA ANALÍTICA (movimentações + baixas)
    # ---------------------------------------------------
    # vamos somar por id_plano ANÁLITICO (a apropriação sempre é na analítica)

    # todas contas de receitas (grupo 1)
    planos_receita = (
        session.query(PlanoDeContas)
        .filter(
            PlanoDeContas.deleted.is_(False),
            PlanoDeContas.cod_estrutural.like("1%"),
        )
        .order_by(PlanoDeContas.cod_estrutural)
        .all()
    )

    # todas contas de despesas (grupo 2)
    planos_despesa = (
        session.query(PlanoDeContas)
        .filter(
            PlanoDeContas.deleted.is_(False),
            PlanoDeContas.cod_estrutural.like("2%"),
        )
        .order_by(PlanoDeContas.cod_estrutural)
        .all()
    )

    
    # mapa id_plano -> código para facilitar agregação por prefixo
    cod_por_id = {p.id_plano: p.cod_estrutural for p in planos_receita + planos_despesa}

    # valor base por conta analítica (grupo 1)
    base_receitas_por_id = {}
    for id_plano, cod in cod_por_id.items():
        if not cod.startswith("1"):
            continue
        v_mov = mov_receitas_por_plano.get(id_plano, 0.0)
        v_bx = baixas_receitas_por_plano.get(id_plano, 0.0)
        total = v_mov + v_bx
        if abs(total) > 0.0001:
            base_receitas_por_id[id_plano] = total

    # valor base por conta analítica (grupo 2)
    base_despesas_por_id = {}
    for id_plano, cod in cod_por_id.items():
        if not cod.startswith("2"):
            continue
        v_mov = mov_despesas_por_plano.get(id_plano, 0.0)
        v_bx = baixas_despesas_por_plano.get(id_plano, 0.0)
        total = v_mov + v_bx
        if abs(total) > 0.0001:
            base_despesas_por_id[id_plano] = total

    # ---------------------------------------------------
    # 4) AGREGAÇÃO NAS CONTAS TOTALIZADORAS (por prefixo de código)
    # ---------------------------------------------------
    def agrega_por_prefixo(planos_lista, base_por_id):
        resultado = []
    ids_analiticas = list(base_por_id.keys())

    for plano in planos_lista:
        prefixo = plano.cod_estrutural or ""
        soma = 0.0

        for id_ana in ids_analiticas:
            cod_ana = cod_por_id[id_ana]
            if cod_ana == prefixo or cod_ana.startswith(prefixo + "."):
                soma += base_por_id[id_ana]

        if abs(soma) > 0.0001:
            resultado.append(
                {
                    "id_plano": plano.id_plano,       # 👈 novo
                    "cod": plano.cod_estrutural,
                    "nome": plano.nome_conta,
                    "tipo": plano.tipo,
                    "valor": soma,
                }
            )

    return resultado
