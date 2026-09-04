from flask import flash, jsonify, redirect, render_template, request, url_for

from database import SessionLocal
from models import Cidade, Credor, Titulo

from . import bp_financeiro


def get_session():
    return SessionLocal()


def _dados_formulario(credor):
    credor.nome = (request.form.get("nome") or "").strip()
    credor.cnpj = (request.form.get("cnpj") or "").strip() or None
    credor.endereco = (request.form.get("endereco") or "").strip() or None
    credor.bairro = (request.form.get("bairro") or "").strip() or None
    credor.cep = (request.form.get("cep") or "").strip() or None
    credor.id_cidade = request.form.get("id_cidade", type=int)
    credor.whats = (request.form.get("whats") or "").strip() or None
    credor.fone = (request.form.get("fone") or "").strip() or None
    credor.email = (request.form.get("email") or "").strip() or None


def _view(credor):
    return {
        "id": credor.id_credor, "nome": credor.nome, "cnpj": credor.cnpj or "",
        "endereco": credor.endereco or "", "bairro": credor.bairro or "", "cep": credor.cep or "",
        "id_cidade": credor.id_cidade, "cidade": credor.cidade.nome if credor.cidade else "",
        "whats": credor.whats or "", "fone": credor.fone or "", "email": credor.email or "",
    }


def _erros(session, credor):
    erros = []
    if not credor.nome:
        erros.append("Nome do credor é obrigatório.")
    if credor.id_cidade and not session.query(Cidade).filter(Cidade.id_cidade == credor.id_cidade, Cidade.deleted.is_(False)).first():
        erros.append("Cidade selecionada não existe.")
    return erros


@bp_financeiro.get("/credores")
def listar_credores():
    session = get_session()
    credores = session.query(Credor).filter(Credor.deleted.is_(False)).order_by(Credor.nome).all()
    result = [_view(item) for item in credores]
    session.close()
    return render_template("credores_list.html", credores=result)


@bp_financeiro.get("/credores/busca")
def buscar_credores():
    termo = (request.args.get("q") or "").strip()[:100]
    session = get_session()
    query = session.query(Credor).filter(Credor.deleted.is_(False))
    if termo:
        query = query.filter(Credor.nome.ilike(f"%{termo}%"))
    result = [{"id": item.id_credor, "nome": item.nome} for item in query.order_by(Credor.nome).limit(100)]
    session.close()
    return jsonify({"credores": result})


@bp_financeiro.route("/credores/novo", methods=["GET", "POST"])
def novo_credor():
    session = get_session()
    origem = "titulo" if request.values.get("origem") == "titulo" else None
    id_credor_criado = request.args.get("criado", type=int)
    if request.method == "GET" and origem and id_credor_criado:
        criado = session.query(Credor).filter(Credor.id_credor == id_credor_criado, Credor.deleted.is_(False)).first()
        if criado:
            result = {"id": criado.id_credor, "nome": criado.nome}
            session.close()
            return render_template("credor_form.html", credor=None, origem=origem, credor_criado=result)
    if request.method == "POST":
        credor = Credor()
        _dados_formulario(credor)
        erros = _erros(session, credor)
        if erros:
            for erro in erros:
                flash(erro, "erro")
        else:
            session.add(credor)
            session.commit()
            id_credor = credor.id_credor
            result = {"id": credor.id_credor, "nome": credor.nome}
            session.close()
            if origem:
                return redirect(url_for("financeiro.novo_credor", origem=origem, criado=id_credor))
            flash("Credor cadastrado com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_credores"))
    session.close()
    return render_template("credor_form.html", credor=None, origem=origem, credor_criado=None)


@bp_financeiro.route("/credores/<int:id_credor>/editar", methods=["GET", "POST"])
def editar_credor(id_credor):
    session = get_session()
    credor = session.query(Credor).filter(Credor.id_credor == id_credor, Credor.deleted.is_(False)).first()
    if not credor:
        session.close()
        flash("Credor não encontrado.", "erro")
        return redirect(url_for("financeiro.listar_credores"))
    if request.method == "POST":
        _dados_formulario(credor)
        erros = _erros(session, credor)
        if erros:
            for erro in erros:
                flash(erro, "erro")
        else:
            session.commit()
            session.close()
            flash("Credor atualizado com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_credores"))
    result = _view(credor)
    session.close()
    return render_template("credor_form.html", credor=result, origem=None, credor_criado=None)


@bp_financeiro.post("/credores/<int:id_credor>/excluir")
def excluir_credor(id_credor):
    session = get_session()
    credor = session.query(Credor).filter(Credor.id_credor == id_credor, Credor.deleted.is_(False)).first()
    if not credor:
        flash("Credor não encontrado.", "erro")
    elif session.query(Titulo.id_titulo).filter(Titulo.deleted.is_(False), Titulo.id_credor == id_credor).first():
        flash("Não é possível excluir um credor que possui título cadastrado.", "erro")
    else:
        credor.deleted = True
        session.commit()
        flash("Credor excluído com sucesso!", "sucesso")
    session.close()
    return redirect(url_for("financeiro.listar_credores"))
