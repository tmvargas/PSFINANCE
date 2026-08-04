from flask import flash, redirect, render_template, request, url_for
from . import bp_financeiro
from database import SessionLocal
from models import Empresa, TIPOS_EMPRESA

def get_session(): return SessionLocal()

@bp_financeiro.route("/empresas")
def listar_empresas():
    session = get_session(); empresas = session.query(Empresa).filter(Empresa.deleted.is_(False)).order_by(Empresa.nome).all()
    data = [{"id": e.id_empresa, "nome": e.nome, "cnpj": e.cnpj, "tipo_empresa": e.tipo_empresa, "codigo_externo": e.codigo_externo, "ativa": e.ativa} for e in empresas]
    session.close(); return render_template("empresa_list.html", empresas=data)

@bp_financeiro.route("/empresas/novo", methods=["GET", "POST"])
def nova_empresa():
    session = get_session()
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip(); cnpj = (request.form.get("cnpj") or "").strip() or None
        tipo_empresa = (request.form.get("tipo_empresa") or "").strip(); codigo_externo = (request.form.get("codigo_externo") or "").strip() or None
        ativa = request.form.get("ativa") == "on"; erros = validar_empresa(session, nome, tipo_empresa, codigo_externo)
        if erros:
            for erro in erros: flash(erro, "erro")
        else:
            session.add(Empresa(nome=nome, cnpj=cnpj, tipo_empresa=tipo_empresa, codigo_externo=codigo_externo, ativa=ativa)); session.commit(); session.close()
            flash("Empresa cadastrada com sucesso.", "sucesso"); return redirect(url_for("financeiro.listar_empresas"))
    session.close(); return render_template("empresa_form.html", empresa=None, tipos_empresa=TIPOS_EMPRESA)

@bp_financeiro.route("/empresas/<int:id_empresa>/editar", methods=["GET", "POST"])
def editar_empresa(id_empresa):
    session = get_session(); empresa = session.query(Empresa).filter(Empresa.id_empresa == id_empresa, Empresa.deleted.is_(False)).first()
    if not empresa:
        session.close(); flash("Empresa não encontrada.", "erro"); return redirect(url_for("financeiro.listar_empresas"))
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip(); cnpj = (request.form.get("cnpj") or "").strip() or None
        tipo_empresa = (request.form.get("tipo_empresa") or "").strip(); codigo_externo = (request.form.get("codigo_externo") or "").strip() or None
        ativa = request.form.get("ativa") == "on"; erros = validar_empresa(session, nome, tipo_empresa, codigo_externo, empresa.id_empresa)
        if erros:
            for erro in erros: flash(erro, "erro")
        else:
            empresa.nome = nome; empresa.cnpj = cnpj; empresa.tipo_empresa = tipo_empresa; empresa.codigo_externo = codigo_externo; empresa.ativa = ativa
            session.commit(); session.close(); flash("Empresa atualizada com sucesso.", "sucesso"); return redirect(url_for("financeiro.listar_empresas"))
    data = {"id": empresa.id_empresa, "nome": empresa.nome, "cnpj": empresa.cnpj, "tipo_empresa": empresa.tipo_empresa, "codigo_externo": empresa.codigo_externo, "ativa": empresa.ativa}
    session.close(); return render_template("empresa_form.html", empresa=data, tipos_empresa=TIPOS_EMPRESA)

@bp_financeiro.route("/empresas/<int:id_empresa>/inativar", methods=["POST"])
def inativar_empresa(id_empresa):
    session = get_session(); empresa = session.query(Empresa).filter(Empresa.id_empresa == id_empresa, Empresa.deleted.is_(False)).first()
    if empresa: empresa.ativa = False; session.commit(); flash("Empresa inativada com sucesso.", "sucesso")
    else: flash("Empresa não encontrada.", "erro")
    session.close(); return redirect(url_for("financeiro.listar_empresas"))

def validar_empresa(session, nome, tipo_empresa, codigo_externo, id_empresa_atual=None):
    erros = []
    if not nome: erros.append("Nome da empresa é obrigatório.")
    if tipo_empresa not in TIPOS_EMPRESA: erros.append("Tipo deve ser EMPRESA, SPE ou SCP.")
    if codigo_externo:
        query = session.query(Empresa).filter(Empresa.codigo_externo == codigo_externo, Empresa.deleted.is_(False))
        if id_empresa_atual: query = query.filter(Empresa.id_empresa != id_empresa_atual)
        if query.first(): erros.append("Já existe empresa ativa com esse código externo.")
    return erros
