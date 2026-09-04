from flask import flash, jsonify, redirect, render_template, request, url_for

from database import SessionLocal
from models import Cidade, Credor

from . import bp_financeiro


def get_session():
    return SessionLocal()


@bp_financeiro.get("/cidades")
def listar_cidades():
    session = get_session()
    cidades = session.query(Cidade).filter(Cidade.deleted.is_(False)).order_by(Cidade.nome).all()
    result = [{"id": item.id_cidade, "nome": item.nome} for item in cidades]
    session.close()
    return render_template("cidades_list.html", cidades=result)


@bp_financeiro.get("/cidades/busca")
def buscar_cidades():
    termo = (request.args.get("q") or "").strip()[:100]
    session = get_session()
    query = session.query(Cidade).filter(Cidade.deleted.is_(False))
    if termo:
        if termo.isdigit():
            query = query.filter((Cidade.id_cidade == int(termo)) | Cidade.nome.ilike(f"%{termo}%"))
        else:
            query = query.filter(Cidade.nome.ilike(f"%{termo}%"))
    cidades = query.order_by(Cidade.nome).limit(100).all()
    result = [{"id": item.id_cidade, "nome": item.nome} for item in cidades]
    session.close()
    return jsonify({"cidades": result})


@bp_financeiro.route("/cidades/nova", methods=["GET", "POST"])
def nova_cidade():
    session = get_session()
    origem = "credor" if request.values.get("origem") == "credor" else None
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        if not nome:
            flash("Nome da cidade é obrigatório.", "erro")
        elif session.query(Cidade).filter(Cidade.deleted.is_(False), Cidade.nome.ilike(nome)).first():
            flash("Já existe uma cidade ativa com esse nome.", "erro")
        else:
            cidade = Cidade(nome=nome)
            session.add(cidade)
            session.commit()
            result = {"id": cidade.id_cidade, "nome": cidade.nome}
            session.close()
            if origem:
                return render_template("cidade_form.html", cidade=None, origem=origem, cidade_criada=result)
            flash("Cidade cadastrada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_cidades"))
    session.close()
    return render_template("cidade_form.html", cidade=None, origem=origem, cidade_criada=None)


@bp_financeiro.route("/cidades/<int:id_cidade>/editar", methods=["GET", "POST"])
def editar_cidade(id_cidade):
    session = get_session()
    cidade = session.query(Cidade).filter(Cidade.id_cidade == id_cidade, Cidade.deleted.is_(False)).first()
    if not cidade:
        session.close()
        flash("Cidade não encontrada.", "erro")
        return redirect(url_for("financeiro.listar_cidades"))
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        if not nome:
            flash("Nome da cidade é obrigatório.", "erro")
        else:
            cidade.nome = nome
            session.commit()
            session.close()
            flash("Cidade atualizada com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_cidades"))
    result = {"id": cidade.id_cidade, "nome": cidade.nome}
    session.close()
    return render_template("cidade_form.html", cidade=result, origem=None, cidade_criada=None)


@bp_financeiro.post("/cidades/<int:id_cidade>/excluir")
def excluir_cidade(id_cidade):
    session = get_session()
    cidade = session.query(Cidade).filter(Cidade.id_cidade == id_cidade, Cidade.deleted.is_(False)).first()
    if not cidade:
        flash("Cidade não encontrada.", "erro")
    elif session.query(Credor.id_credor).filter(Credor.deleted.is_(False), Credor.id_cidade == id_cidade).first():
        flash("Não é possível excluir uma cidade vinculada a credor.", "erro")
    else:
        cidade.deleted = True
        session.commit()
        flash("Cidade excluída com sucesso!", "sucesso")
    session.close()
    return redirect(url_for("financeiro.listar_cidades"))
