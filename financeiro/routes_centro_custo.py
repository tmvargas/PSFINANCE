from flask import flash, redirect, render_template, request, url_for
from . import bp_financeiro
from database import SessionLocal
from models import CentroCusto, Empresa

def get_session(): return SessionLocal()
def parse_int(value):
    try: return int(value)
    except (TypeError, ValueError): return None

def listar_empresas_ativas(session):
    empresas = session.query(Empresa).filter(Empresa.deleted.is_(False), Empresa.ativa.is_(True)).order_by(Empresa.nome).all()
    return [{"id": e.id_empresa, "nome": e.nome, "tipo_empresa": e.tipo_empresa} for e in empresas]

@bp_financeiro.route("/centros-custo")
def listar_centros_custo():
    session = get_session(); centros = session.query(CentroCusto).join(Empresa).filter(CentroCusto.deleted.is_(False), Empresa.deleted.is_(False)).order_by(Empresa.nome, CentroCusto.codigo).all()
    data = [{"id": c.id_centro_custo, "empresa": c.empresa.nome, "codigo": c.codigo, "nome": c.nome, "codigo_externo": c.codigo_externo, "ativo": c.ativo} for c in centros]
    session.close(); return render_template("centro_custo_list.html", centros_custo=data)

@bp_financeiro.route("/centros-custo/novo", methods=["GET", "POST"])
def novo_centro_custo():
    session = get_session(); empresas = listar_empresas_ativas(session)
    if request.method == "POST":
        id_empresa = parse_int(request.form.get("id_empresa")); codigo = (request.form.get("codigo") or "").strip(); nome = (request.form.get("nome") or "").strip()
        codigo_externo = (request.form.get("codigo_externo") or "").strip() or None; ativo = request.form.get("ativo") == "on"
        erros = validar_centro_custo(session, id_empresa, codigo, nome)
        if erros:
            for erro in erros: flash(erro, "erro")
        else:
            session.add(CentroCusto(id_empresa=id_empresa, codigo=codigo, nome=nome, codigo_externo=codigo_externo, ativo=ativo)); session.commit(); session.close()
            flash("Centro de custo cadastrado com sucesso.", "sucesso"); return redirect(url_for("financeiro.listar_centros_custo"))
    session.close(); return render_template("centro_custo_form.html", centro_custo=None, empresas=empresas)

@bp_financeiro.route("/centros-custo/<int:id_centro_custo>/editar", methods=["GET", "POST"])
def editar_centro_custo(id_centro_custo):
    session = get_session(); centro = session.query(CentroCusto).filter(CentroCusto.id_centro_custo == id_centro_custo, CentroCusto.deleted.is_(False)).first()
    if not centro:
        session.close(); flash("Centro de custo não encontrado.", "erro"); return redirect(url_for("financeiro.listar_centros_custo"))
    empresas = listar_empresas_ativas(session)
    if request.method == "POST":
        id_empresa = parse_int(request.form.get("id_empresa")); codigo = (request.form.get("codigo") or "").strip(); nome = (request.form.get("nome") or "").strip()
        codigo_externo = (request.form.get("codigo_externo") or "").strip() or None; ativo = request.form.get("ativo") == "on"; erros = validar_centro_custo(session, id_empresa, codigo, nome, centro.id_centro_custo)
        if erros:
            for erro in erros: flash(erro, "erro")
        else:
            centro.id_empresa = id_empresa; centro.codigo = codigo; centro.nome = nome; centro.codigo_externo = codigo_externo; centro.ativo = ativo
            session.commit(); session.close(); flash("Centro de custo atualizado com sucesso.", "sucesso"); return redirect(url_for("financeiro.listar_centros_custo"))
    data = {"id": centro.id_centro_custo, "id_empresa": centro.id_empresa, "codigo": centro.codigo, "nome": centro.nome, "codigo_externo": centro.codigo_externo, "ativo": centro.ativo}
    session.close(); return render_template("centro_custo_form.html", centro_custo=data, empresas=empresas)

@bp_financeiro.route("/centros-custo/<int:id_centro_custo>/inativar", methods=["POST"])
def inativar_centro_custo(id_centro_custo):
    session = get_session(); centro = session.query(CentroCusto).filter(CentroCusto.id_centro_custo == id_centro_custo, CentroCusto.deleted.is_(False)).first()
    if centro: centro.ativo = False; session.commit(); flash("Centro de custo inativado com sucesso.", "sucesso")
    else: flash("Centro de custo não encontrado.", "erro")
    session.close(); return redirect(url_for("financeiro.listar_centros_custo"))

def validar_centro_custo(session, id_empresa, codigo, nome, id_centro_custo_atual=None):
    erros = []
    if not id_empresa: erros.append("Empresa é obrigatória.")
    elif not session.query(Empresa).filter(Empresa.id_empresa == id_empresa, Empresa.deleted.is_(False), Empresa.ativa.is_(True)).first(): erros.append("Empresa ativa não encontrada.")
    if not codigo: erros.append("Código do centro de custo é obrigatório.")
    if not nome: erros.append("Nome do centro de custo é obrigatório.")
    if id_empresa and codigo:
        query = session.query(CentroCusto).filter(CentroCusto.id_empresa == id_empresa, CentroCusto.codigo == codigo, CentroCusto.deleted.is_(False))
        if id_centro_custo_atual: query = query.filter(CentroCusto.id_centro_custo != id_centro_custo_atual)
        if query.first(): erros.append("Já existe centro de custo ativo com esse código nessa empresa.")
    return erros
