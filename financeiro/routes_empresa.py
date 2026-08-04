from flask import flash, redirect, render_template, request, url_for

from . import bp_financeiro
from database import SessionLocal
from models import CentroCusto, Empresa


TIPOS_EMPRESA = ("EMPRESA", "SPE", "SCP")


def get_session():
    return SessionLocal()


def empresa_to_view(empresa):
    return {
        "id": empresa.id_empresa,
        "codigo": empresa.codigo,
        "nome": empresa.nome,
        "tipo_empresa": empresa.tipo_empresa,
        "codigo_externo": empresa.codigo_externo or "",
        "observacao": empresa.observacao or "",
    }


def validar_empresa(session, codigo, nome, tipo_empresa, id_empresa=None):
    erros = []

    if not codigo:
        erros.append("Código da empresa é obrigatório.")
    if not nome:
        erros.append("Nome da empresa é obrigatório.")
    if tipo_empresa not in TIPOS_EMPRESA:
        erros.append("Tipo da empresa deve ser EMPRESA, SPE ou SCP.")

    if codigo:
        query = session.query(Empresa).filter(
            Empresa.codigo == codigo,
            Empresa.deleted.is_(False),
        )
        if id_empresa:
            query = query.filter(Empresa.id_empresa != id_empresa)
        if query.first():
            erros.append("Já existe uma empresa ativa com esse código.")

    return erros


@bp_financeiro.route("/empresas")
def listar_empresas():
    session = get_session()

    empresas = (
        session.query(Empresa)
        .filter(Empresa.deleted.is_(False))
        .order_by(Empresa.codigo, Empresa.nome)
        .all()
    )
    empresas_view = [empresa_to_view(empresa) for empresa in empresas]

    session.close()
    return render_template("empresa_list.html", empresas=empresas_view)


@bp_financeiro.route("/empresas/nova", methods=["GET", "POST"])
def nova_empresa():
    session = get_session()
    empresa_view = None

    if request.method == "POST":
        codigo = (request.form.get("codigo") or "").strip().upper()
        nome = (request.form.get("nome") or "").strip()
        tipo_empresa = (request.form.get("tipo_empresa") or "").strip().upper()
        codigo_externo = (request.form.get("codigo_externo") or "").strip()
        observacao = (request.form.get("observacao") or "").strip()

        empresa_view = {
            "codigo": codigo,
            "nome": nome,
            "tipo_empresa": tipo_empresa,
            "codigo_externo": codigo_externo,
            "observacao": observacao,
        }

        erros = validar_empresa(session, codigo, nome, tipo_empresa)
        if erros:
            for erro in erros:
                flash(erro, "erro")
        else:
            empresa = Empresa(
                codigo=codigo,
                nome=nome,
                tipo_empresa=tipo_empresa,
                codigo_externo=codigo_externo or None,
                observacao=observacao or None,
            )
            session.add(empresa)
            session.commit()
            session.close()

            flash("Empresa cadastrada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_empresas"))

    session.close()
    return render_template(
        "empresa_form.html",
        empresa=empresa_view,
        tipos_empresa=TIPOS_EMPRESA,
    )


@bp_financeiro.route("/empresas/<int:id_empresa>/editar", methods=["GET", "POST"])
def editar_empresa(id_empresa):
    session = get_session()

    empresa = (
        session.query(Empresa)
        .filter(Empresa.id_empresa == id_empresa, Empresa.deleted.is_(False))
        .first()
    )

    if not empresa:
        session.close()
        flash("Empresa não encontrada.", "erro")
        return redirect(url_for("financeiro.listar_empresas"))

    if request.method == "POST":
        codigo = (request.form.get("codigo") or "").strip().upper()
        nome = (request.form.get("nome") or "").strip()
        tipo_empresa = (request.form.get("tipo_empresa") or "").strip().upper()
        codigo_externo = (request.form.get("codigo_externo") or "").strip()
        observacao = (request.form.get("observacao") or "").strip()

        erros = validar_empresa(session, codigo, nome, tipo_empresa, empresa.id_empresa)
        if erros:
            for erro in erros:
                flash(erro, "erro")
            empresa_view = {
                "id": empresa.id_empresa,
                "codigo": codigo,
                "nome": nome,
                "tipo_empresa": tipo_empresa,
                "codigo_externo": codigo_externo,
                "observacao": observacao,
            }
        else:
            empresa.codigo = codigo
            empresa.nome = nome
            empresa.tipo_empresa = tipo_empresa
            empresa.codigo_externo = codigo_externo or None
            empresa.observacao = observacao or None
            session.commit()
            session.close()

            flash("Empresa atualizada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_empresas"))
    else:
        empresa_view = empresa_to_view(empresa)

    session.close()
    return render_template(
        "empresa_form.html",
        empresa=empresa_view,
        tipos_empresa=TIPOS_EMPRESA,
    )


@bp_financeiro.route("/empresas/<int:id_empresa>/desativar", methods=["POST"])
def desativar_empresa(id_empresa):
    session = get_session()

    empresa = (
        session.query(Empresa)
        .filter(Empresa.id_empresa == id_empresa, Empresa.deleted.is_(False))
        .first()
    )

    if not empresa:
        session.close()
        flash("Empresa não encontrada.", "erro")
        return redirect(url_for("financeiro.listar_empresas"))

    centro_ativo = (
        session.query(CentroCusto)
        .filter(
            CentroCusto.id_empresa == empresa.id_empresa,
            CentroCusto.deleted.is_(False),
        )
        .first()
    )
    if centro_ativo:
        session.close()
        flash("Empresa possui centro de custo ativo e não pode ser desativada.", "erro")
        return redirect(url_for("financeiro.listar_empresas"))

    empresa.deleted = True
    session.commit()
    session.close()

    flash("Empresa desativada com sucesso.", "sucesso")
    return redirect(url_for("financeiro.listar_empresas"))
