# financeiro/routes_credor.py
from flask import flash, jsonify, redirect, render_template, request, url_for

from . import bp_financeiro
from database import SessionLocal
from models import Credor


def get_session():
    return SessionLocal()


# ----------------------------------------------------------------------
# LISTAR CREDORES
# ----------------------------------------------------------------------
@bp_financeiro.route("/credores")
def listar_credores():
    session = get_session()

    credores = (
        session.query(Credor)
        .filter(Credor.deleted.is_(False))
        .order_by(Credor.nome)
        .all()
    )

    credores_view = [
        {
            "id": c.id_credor,
            "nome": c.nome,
        }
        for c in credores
    ]

    session.close()
    return render_template("credores_list.html", credores=credores_view)


@bp_financeiro.get("/credores/busca")
def buscar_credores():
    termo = (request.args.get("q") or "").strip()[:100]
    session = get_session()
    query = session.query(Credor).filter(Credor.deleted.is_(False))
    if termo:
        query = query.filter(Credor.nome.ilike(f"%{termo}%"))
    credores = query.order_by(Credor.nome).limit(100).all()
    resultado = [{"id": credor.id_credor, "nome": credor.nome} for credor in credores]
    session.close()
    return jsonify({"credores": resultado})


# ----------------------------------------------------------------------
# NOVO CREDOR
# ----------------------------------------------------------------------
@bp_financeiro.route("/credores/novo", methods=["GET", "POST"])
def novo_credor():
    session = get_session()
    origem = request.values.get("origem") if request.values.get("origem") == "titulo" else None

    id_credor_criado = request.args.get("criado", type=int)
    if request.method == "GET" and origem and id_credor_criado:
        credor_criado = (
            session.query(Credor)
            .filter(Credor.id_credor == id_credor_criado, Credor.deleted.is_(False))
            .first()
        )
        if credor_criado:
            credor_view = {"id": credor_criado.id_credor, "nome": credor_criado.nome}
            session.close()
            return render_template(
                "credor_form.html", credor=None, origem=origem, credor_criado=credor_view
            )

    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()

        erros = []
        if not nome:
            erros.append("Nome do credor é obrigatório.")

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            credor = Credor(nome=nome)
            session.add(credor)
            session.commit()
            id_credor = credor.id_credor
            session.close()

            if origem:
                return redirect(
                    url_for("financeiro.novo_credor", origem=origem, criado=id_credor)
                )
            flash("Credor cadastrado com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_credores"))

    session.close()
    return render_template(
        "credor_form.html", credor=None, origem=origem, credor_criado=None
    )


# ----------------------------------------------------------------------
# EDITAR CREDOR
# ----------------------------------------------------------------------
@bp_financeiro.route("/credores/<int:id_credor>/editar", methods=["GET", "POST"])
def editar_credor(id_credor):
    session = get_session()

    credor = (
        session.query(Credor)
        .filter(Credor.id_credor == id_credor, Credor.deleted.is_(False))
        .first()
    )

    if not credor:
        session.close()
        flash("Credor não encontrado.", "erro")
        return redirect(url_for("financeiro.listar_credores"))

    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()

        erros = []
        if not nome:
            erros.append("Nome do credor é obrigatório.")

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            credor.nome = nome
            session.commit()
            session.close()

            flash("Credor atualizado com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_credores"))

    credor_view = {
        "id": credor.id_credor,
        "nome": credor.nome,
    }

    session.close()
    return render_template("credor_form.html", credor=credor_view)
