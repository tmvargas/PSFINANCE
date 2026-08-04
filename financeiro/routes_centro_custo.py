from flask import flash, redirect, render_template, request, url_for

from . import bp_financeiro
from database import SessionLocal
from models import CentroCusto, Empresa


def get_session():
    return SessionLocal()


def listar_empresas_ativas(session):
    return (
        session.query(Empresa)
        .filter(Empresa.deleted.is_(False))
        .order_by(Empresa.codigo, Empresa.nome)
        .all()
    )


def centro_custo_to_view(centro):
    return {
        "id": centro.id_centro_custo,
        "id_empresa": centro.id_empresa,
        "empresa": centro.empresa.nome if centro.empresa else "",
        "empresa_codigo": centro.empresa.codigo if centro.empresa else "",
        "codigo": centro.codigo,
        "nome": centro.nome,
        "codigo_externo": centro.codigo_externo or "",
        "observacao": centro.observacao or "",
    }


def validar_centro_custo(session, id_empresa, codigo, nome, id_centro_custo=None):
    erros = []

    empresa = None
    if not id_empresa:
        erros.append("Empresa é obrigatória.")
    else:
        empresa = (
            session.query(Empresa)
            .filter(Empresa.id_empresa == id_empresa, Empresa.deleted.is_(False))
            .first()
        )
        if not empresa:
            erros.append("Empresa ativa não encontrada.")

    if not codigo:
        erros.append("Código do centro de custo é obrigatório.")
    if not nome:
        erros.append("Nome do centro de custo é obrigatório.")

    if empresa and codigo:
        query = session.query(CentroCusto).filter(
            CentroCusto.id_empresa == id_empresa,
            CentroCusto.codigo == codigo,
            CentroCusto.deleted.is_(False),
        )
        if id_centro_custo:
            query = query.filter(CentroCusto.id_centro_custo != id_centro_custo)
        if query.first():
            erros.append("Já existe um centro de custo ativo com esse código para a empresa.")

    return erros


@bp_financeiro.route("/centros-custo")
def listar_centros_custo():
    session = get_session()

    centros = (
        session.query(CentroCusto)
        .join(Empresa)
        .filter(CentroCusto.deleted.is_(False), Empresa.deleted.is_(False))
        .order_by(Empresa.codigo, CentroCusto.codigo, CentroCusto.nome)
        .all()
    )
    centros_view = [centro_custo_to_view(centro) for centro in centros]

    session.close()
    return render_template("centro_custo_list.html", centros=centros_view)


@bp_financeiro.route("/centros-custo/novo", methods=["GET", "POST"])
def novo_centro_custo():
    session = get_session()
    empresas = listar_empresas_ativas(session)
    centro_view = None

    if request.method == "POST":
        id_empresa_raw = (request.form.get("id_empresa") or "").strip()
        id_empresa = int(id_empresa_raw) if id_empresa_raw.isdigit() else None
        codigo = (request.form.get("codigo") or "").strip().upper()
        nome = (request.form.get("nome") or "").strip()
        codigo_externo = (request.form.get("codigo_externo") or "").strip()
        observacao = (request.form.get("observacao") or "").strip()

        centro_view = {
            "id_empresa": id_empresa,
            "codigo": codigo,
            "nome": nome,
            "codigo_externo": codigo_externo,
            "observacao": observacao,
        }

        erros = validar_centro_custo(session, id_empresa, codigo, nome)
        if erros:
            for erro in erros:
                flash(erro, "erro")
        else:
            centro = CentroCusto(
                id_empresa=id_empresa,
                codigo=codigo,
                nome=nome,
                codigo_externo=codigo_externo or None,
                observacao=observacao or None,
            )
            session.add(centro)
            session.commit()
            session.close()

            flash("Centro de custo cadastrado com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_centros_custo"))

    empresas_view = [empresa_to_option(empresa) for empresa in empresas]
    session.close()
    return render_template(
        "centro_custo_form.html",
        centro=centro_view,
        empresas=empresas_view,
    )


@bp_financeiro.route("/centros-custo/<int:id_centro_custo>/editar", methods=["GET", "POST"])
def editar_centro_custo(id_centro_custo):
    session = get_session()

    centro = (
        session.query(CentroCusto)
        .filter(
            CentroCusto.id_centro_custo == id_centro_custo,
            CentroCusto.deleted.is_(False),
        )
        .first()
    )

    if not centro:
        session.close()
        flash("Centro de custo não encontrado.", "erro")
        return redirect(url_for("financeiro.listar_centros_custo"))

    empresas = listar_empresas_ativas(session)

    if request.method == "POST":
        id_empresa_raw = (request.form.get("id_empresa") or "").strip()
        id_empresa = int(id_empresa_raw) if id_empresa_raw.isdigit() else None
        codigo = (request.form.get("codigo") or "").strip().upper()
        nome = (request.form.get("nome") or "").strip()
        codigo_externo = (request.form.get("codigo_externo") or "").strip()
        observacao = (request.form.get("observacao") or "").strip()

        erros = validar_centro_custo(
            session,
            id_empresa,
            codigo,
            nome,
            centro.id_centro_custo,
        )
        if erros:
            for erro in erros:
                flash(erro, "erro")
            centro_view = {
                "id": centro.id_centro_custo,
                "id_empresa": id_empresa,
                "codigo": codigo,
                "nome": nome,
                "codigo_externo": codigo_externo,
                "observacao": observacao,
            }
        else:
            centro.id_empresa = id_empresa
            centro.codigo = codigo
            centro.nome = nome
            centro.codigo_externo = codigo_externo or None
            centro.observacao = observacao or None
            session.commit()
            session.close()

            flash("Centro de custo atualizado com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_centros_custo"))
    else:
        centro_view = centro_custo_to_view(centro)

    empresas_view = [empresa_to_option(empresa) for empresa in empresas]
    session.close()
    return render_template(
        "centro_custo_form.html",
        centro=centro_view,
        empresas=empresas_view,
    )


@bp_financeiro.route("/centros-custo/<int:id_centro_custo>/desativar", methods=["POST"])
def desativar_centro_custo(id_centro_custo):
    session = get_session()

    centro = (
        session.query(CentroCusto)
        .filter(
            CentroCusto.id_centro_custo == id_centro_custo,
            CentroCusto.deleted.is_(False),
        )
        .first()
    )

    if not centro:
        session.close()
        flash("Centro de custo não encontrado.", "erro")
        return redirect(url_for("financeiro.listar_centros_custo"))

    centro.deleted = True
    session.commit()
    session.close()

    flash("Centro de custo desativado com sucesso.", "sucesso")
    return redirect(url_for("financeiro.listar_centros_custo"))


def empresa_to_option(empresa):
    return {
        "id": empresa.id_empresa,
        "label": f"{empresa.codigo} - {empresa.nome}",
    }
