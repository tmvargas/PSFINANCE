from flask import flash, jsonify, redirect, render_template, request, url_for

from database import SessionLocal
from models import Cidade, Cliente
from . import bp_financeiro


def _dados(cliente):
    cliente.nome = (request.form.get("nome") or "").strip()
    cliente.cpf_cnpj = (request.form.get("cpf_cnpj") or "").strip() or None
    cliente.endereco = (request.form.get("endereco") or "").strip() or None
    cliente.bairro = (request.form.get("bairro") or "").strip() or None
    cliente.cep = (request.form.get("cep") or "").strip() or None
    id_cidade = request.form.get("id_cidade", type=int)
    cliente.id_cidade = id_cidade if id_cidade and id_cidade > 0 else None
    cliente.whats = (request.form.get("whats") or "").strip() or None
    cliente.fone = (request.form.get("fone") or "").strip() or None
    cliente.email = (request.form.get("email") or "").strip() or None


def _view(cliente):
    return {
        "id": cliente.id_cliente, "nome": cliente.nome,
        "cpf_cnpj": cliente.cpf_cnpj or "", "endereco": cliente.endereco or "",
        "bairro": cliente.bairro or "", "cep": cliente.cep or "",
        "id_cidade": cliente.id_cidade, "cidade": cliente.cidade.nome if cliente.cidade else "",
        "whats": cliente.whats or "", "fone": cliente.fone or "", "email": cliente.email or "",
    }


def _erros(session, cliente):
    erros = []
    if not cliente.nome:
        erros.append("Nome do cliente é obrigatório.")
    if cliente.id_cidade and not session.query(Cidade).filter(
        Cidade.id_cidade == cliente.id_cidade, Cidade.deleted.is_(False)
    ).first():
        erros.append("Cidade selecionada não existe.")
    return erros


@bp_financeiro.get("/clientes")
def listar_clientes():
    session = SessionLocal()
    itens = session.query(Cliente).filter(Cliente.deleted.is_(False)).order_by(Cliente.nome).all()
    result = [_view(item) for item in itens]
    session.close()
    return render_template("clientes_list.html", clientes=result)


@bp_financeiro.get("/clientes/busca")
def buscar_clientes():
    termo = (request.args.get("q") or "").strip()[:100]
    session = SessionLocal()
    query = session.query(Cliente).filter(Cliente.deleted.is_(False))
    if termo:
        if termo.isdigit():
            query = query.filter((Cliente.id_cliente == int(termo)) | Cliente.nome.ilike(f"%{termo}%"))
        else:
            query = query.filter(Cliente.nome.ilike(f"%{termo}%"))
    itens = [{"id": item.id_cliente, "nome": item.nome} for item in query.order_by(Cliente.nome).limit(100)]
    session.close()
    return jsonify({"clientes": itens})


@bp_financeiro.route("/clientes/novo", methods=["GET", "POST"])
def novo_cliente():
    session = SessionLocal()
    origem = "recebivel" if request.values.get("origem") == "recebivel" else None
    criado_id = request.args.get("criado", type=int)
    if request.method == "GET" and origem and criado_id:
        criado = session.query(Cliente).filter_by(id_cliente=criado_id, deleted=False).first()
        if criado:
            result = {"id": criado.id_cliente, "nome": criado.nome}
            session.close()
            return render_template("cliente_form.html", cliente=None, origem=origem, cliente_criado=result)
    cliente = Cliente()
    if request.method == "POST":
        _dados(cliente)
        erros = _erros(session, cliente)
        if not erros:
            session.add(cliente); session.commit(); criado_id = cliente.id_cliente; session.close()
            if origem:
                return redirect(url_for("financeiro.novo_cliente", origem=origem, criado=criado_id))
            flash("Cliente cadastrado com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_clientes"))
        for erro in erros: flash(erro, "erro")
    session.close()
    return render_template("cliente_form.html", cliente=None, origem=origem, cliente_criado=None)


@bp_financeiro.route("/clientes/<int:id_cliente>/editar", methods=["GET", "POST"])
def editar_cliente(id_cliente):
    session = SessionLocal()
    cliente = session.query(Cliente).filter_by(id_cliente=id_cliente, deleted=False).first()
    if not cliente:
        session.close(); flash("Cliente não encontrado.", "erro")
        return redirect(url_for("financeiro.listar_clientes"))
    if request.method == "POST":
        _dados(cliente); erros = _erros(session, cliente)
        if not erros:
            session.commit(); session.close(); flash("Cliente atualizado com sucesso!", "sucesso")
            return redirect(url_for("financeiro.listar_clientes"))
        for erro in erros: flash(erro, "erro")
    result = _view(cliente); session.close()
    return render_template("cliente_form.html", cliente=result, origem=None, cliente_criado=None)


@bp_financeiro.post("/clientes/<int:id_cliente>/excluir")
def excluir_cliente(id_cliente):
    session = SessionLocal()
    cliente = session.query(Cliente).filter_by(id_cliente=id_cliente, deleted=False).first()
    if not cliente:
        flash("Cliente não encontrado.", "erro")
    else:
        cliente.deleted = True; session.commit(); flash("Cliente excluído com sucesso!", "sucesso")
    session.close()
    return redirect(url_for("financeiro.listar_clientes"))
