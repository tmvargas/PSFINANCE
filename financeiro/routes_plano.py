# financeiro/routes_plano.py
from flask import render_template, request, redirect, url_for, flash

from . import bp_financeiro
from database import SessionLocal
from models import PlanoDeContas


def get_session():
    return SessionLocal()


# ----------------------------------------------------------------------
# LISTAR PLANO DE CONTAS
# ----------------------------------------------------------------------
@bp_financeiro.route("/plano")
def listar_plano():
    session = get_session()

    planos = (
        session.query(PlanoDeContas)
        .filter(PlanoDeContas.deleted.is_(False))
        .order_by(PlanoDeContas.cod_estrutural)
        .all()
    )

    planos_view = [
        {
            "id": p.id_plano,
            "cod": p.cod_estrutural,
            "nome": p.nome_conta,
            "tipo": p.tipo,  # totalizadora / analitica
        }
        for p in planos
    ]

    session.close()
    return render_template("plano_list.html", planos=planos_view)


# ----------------------------------------------------------------------
# NOVA CONTA DO PLANO FINANCEIRO
# ----------------------------------------------------------------------
@bp_financeiro.route("/plano/novo", methods=["GET", "POST"])
def novo_plano():
    session = get_session()

    if request.method == "POST":
        cod = (request.form.get("cod_estrutural") or "").strip()
        nome = (request.form.get("nome_conta") or "").strip()
        tipo = (request.form.get("tipo") or "").strip()  # totalizadora / analitica

        erros = []

        if not cod:
            erros.append("Código estrutural é obrigatório.")
        if not nome:
            erros.append("Nome da conta é obrigatório.")
        if tipo not in ("totalizadora", "analitica"):
            erros.append("Tipo deve ser 'totalizadora' ou 'analitica'.")

        # Opcional: evitar duplicidade de código estrutural ativo
        existente = (
            session.query(PlanoDeContas)
            .filter(
                PlanoDeContas.cod_estrutural == cod,
                PlanoDeContas.deleted.is_(False),
            )
            .first()
        )
        if existente:
            erros.append("Já existe uma conta ativa com esse código estrutural.")

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            plano = PlanoDeContas(
                cod_estrutural=cod,
                nome_conta=nome,
                tipo=tipo,
            )
            session.add(plano)
            session.commit()
            session.close()

            flash("Conta do plano financeiro cadastrada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_plano"))

    # GET ou POST com erro → volta pro form
    session.close()
    return render_template("plano_form.html", plano=None)


# ----------------------------------------------------------------------
# EDITAR CONTA DO PLANO FINANCEIRO
# ----------------------------------------------------------------------
@bp_financeiro.route("/plano/<int:id_plano>/editar", methods=["GET", "POST"])
def editar_plano(id_plano):
    session = get_session()

    plano = (
        session.query(PlanoDeContas)
        .filter(PlanoDeContas.id_plano == id_plano, PlanoDeContas.deleted.is_(False))
        .first()
    )

    if not plano:
        session.close()
        flash("Conta do plano financeiro não encontrada.", "erro")
        return redirect(url_for("financeiro.listar_plano"))

    if request.method == "POST":
        cod = (request.form.get("cod_estrutural") or "").strip()
        nome = (request.form.get("nome_conta") or "").strip()
        tipo = (request.form.get("tipo") or "").strip()

        erros = []

        if not cod:
            erros.append("Código estrutural é obrigatório.")
        if not nome:
            erros.append("Nome da conta é obrigatório.")
        if tipo not in ("totalizadora", "analitica"):
            erros.append("Tipo deve ser 'totalizadora' ou 'analitica'.")

        # verificar se existe outro plano com o mesmo código
        existente = (
            session.query(PlanoDeContas)
            .filter(
                PlanoDeContas.id_plano != plano.id_plano,
                PlanoDeContas.cod_estrutural == cod,
                PlanoDeContas.deleted.is_(False),
            )
            .first()
        )
        if existente:
            erros.append("Já existe outra conta ativa com esse código estrutural.")

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            plano.cod_estrutural = cod
            plano.nome_conta = nome
            plano.tipo = tipo

            session.commit()
            session.close()

            flash("Conta do plano financeiro atualizada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_plano"))

    # GET → montar objeto para o formulário
    plano_view = {
        "id": plano.id_plano,
        "cod_estrutural": plano.cod_estrutural,
        "nome_conta": plano.nome_conta,
        "tipo": plano.tipo,
    }

    session.close()
    return render_template("plano_form.html", plano=plano_view)
