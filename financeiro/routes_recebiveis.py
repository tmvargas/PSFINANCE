import calendar
from datetime import date, datetime

from flask import flash, redirect, render_template, request, url_for
from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import (Cliente, Conta, Documento, Empresa, PlanoDeContas,
                    Recebimento, Recebivel, RecebivelParcela)
from . import bp_financeiro


def _mes(data, meses):
    indice = data.month - 1 + meses
    ano, mes = data.year + indice // 12, indice % 12 + 1
    return date(ano, mes, min(data.day, calendar.monthrange(ano, mes)[1]))


def _listas(session):
    return dict(
        clientes=session.query(Cliente).filter_by(deleted=False).order_by(Cliente.nome).all(),
        empresas=session.query(Empresa).filter_by(deleted=False).order_by(Empresa.codigo).all(),
        documentos=session.query(Documento).filter_by(deleted=False).order_by(Documento.tipo_doc).all(),
        planos=session.query(PlanoDeContas).filter(PlanoDeContas.deleted.is_(False), PlanoDeContas.tipo == "analitica", PlanoDeContas.cod_estrutural.like("1.%")).order_by(PlanoDeContas.cod_estrutural).all(),
    )


@bp_financeiro.get("/recebiveis")
def listar_recebiveis():
    session = SessionLocal(); query = session.query(Recebivel).options(joinedload(Recebivel.cliente), joinedload(Recebivel.empresa)).filter_by(deleted=False)
    if request.args.get("id_cliente", type=int): query = query.filter_by(id_cliente=request.args.get("id_cliente", type=int))
    itens = query.order_by(Recebivel.vencimento, Recebivel.id_recebivel).all()
    clientes = session.query(Cliente).filter_by(deleted=False).order_by(Cliente.nome).all()
    result = [{"obj": r, "saldo": r.saldo_aberto} for r in itens]; session.close()
    return render_template("recebiveis_list.html", recebiveis=result, clientes=clientes)


def _form_recebivel(id_recebivel=None, copia=None):
    session = SessionLocal(); base = session.get(Recebivel, id_recebivel or copia) if (id_recebivel or copia) else None
    if (id_recebivel or copia) and (not base or base.deleted): session.close(); flash("Recebível não encontrado.", "erro"); return redirect(url_for("financeiro.listar_recebiveis"))
    if request.method == "POST":
        obj = base if id_recebivel else Recebivel()
        try:
            obj.nr_documento=(request.form.get("nr_documento") or "").strip(); obj.id_cliente=request.form.get("id_cliente",type=int); obj.id_empresa=request.form.get("id_empresa",type=int); obj.id_doc=request.form.get("id_doc",type=int); obj.id_plano=request.form.get("id_plano",type=int); obj.valor=float((request.form.get("valor") or "0").replace(",",".")); obj.emissao=datetime.strptime(request.form.get("emissao"),"%Y-%m-%d").date(); obj.vencimento=datetime.strptime(request.form.get("vencimento"),"%Y-%m-%d").date(); obj.observacao=(request.form.get("observacao") or "").strip() or None; parcelas=request.form.get("parcelas",type=int) or 1
        except (TypeError, ValueError):
            flash("Preencha os dados obrigatórios com valores válidos.", "erro")
        else:
            plano=session.query(PlanoDeContas).filter_by(id_plano=obj.id_plano,deleted=False,tipo="analitica").first()
            erros=[]
            if not obj.nr_documento: erros.append("Número do documento é obrigatório.")
            if not session.query(Cliente).filter_by(id_cliente=obj.id_cliente,deleted=False).first(): erros.append("Cliente inválido.")
            if not plano or not plano.cod_estrutural.startswith("1."): erros.append("Selecione uma conta analítica de entrada do Plano Financeiro.")
            if obj.valor <= 0: erros.append("Valor deve ser maior que zero.")
            if not 1 <= parcelas <= 999: erros.append("Quantidade de parcelas deve estar entre 1 e 999.")
            if not erros:
                if not id_recebivel: session.add(obj)
                session.flush()
                if not id_recebivel:
                    centavos=round(obj.valor*100); base_centavos=centavos//parcelas; resto=centavos%parcelas
                    for n in range(parcelas): session.add(RecebivelParcela(recebivel=obj,numero_parcela=n+1,vencimento=_mes(obj.vencimento,n),valor=(base_centavos+(1 if n<resto else 0))/100))
                session.commit(); rid=obj.id_recebivel; session.close(); flash("Recebível salvo com sucesso!", "sucesso"); return redirect(url_for("financeiro.listar_recebiveis"))
            for erro in erros: flash(erro,"erro")
    listas=_listas(session); session.close(); return render_template("recebivel_form.html", recebivel=base, copia=bool(copia), **listas)


@bp_financeiro.route("/recebiveis/novo", methods=["GET","POST"])
def novo_recebivel(): return _form_recebivel()
@bp_financeiro.route("/recebiveis/<int:id_recebivel>/editar", methods=["GET","POST"])
def editar_recebivel(id_recebivel): return _form_recebivel(id_recebivel=id_recebivel)
@bp_financeiro.route("/recebiveis/<int:id_recebivel>/copiar", methods=["GET","POST"])
def copiar_recebivel(id_recebivel): return _form_recebivel(copia=id_recebivel)


@bp_financeiro.post("/recebiveis/<int:id_recebivel>/excluir")
def excluir_recebivel(id_recebivel):
    session=SessionLocal(); obj=session.get(Recebivel,id_recebivel)
    if not obj or obj.deleted: flash("Recebível não encontrado.","erro")
    elif any(not r.deleted for r in obj.recebimentos): flash("Não é possível excluir recebível com recebimento.","erro")
    else: obj.deleted=True; session.commit(); flash("Recebível excluído com sucesso!","sucesso")
    session.close(); return redirect(url_for("financeiro.listar_recebiveis"))


@bp_financeiro.route("/recebiveis/<int:id_recebivel>/receber", methods=["GET","POST"])
def receber_recebivel(id_recebivel):
    session=SessionLocal(); obj=session.query(Recebivel).options(joinedload(Recebivel.cliente),joinedload(Recebivel.recebimentos)).filter_by(id_recebivel=id_recebivel,deleted=False).first()
    if not obj: session.close(); flash("Recebível não encontrado.","erro"); return redirect(url_for("financeiro.listar_recebiveis"))
    if request.method=="POST":
        valor=request.form.get("valor",type=float); conta=session.query(Conta).filter_by(id_conta=request.form.get("id_conta",type=int),deleted=False).first()
        if not conta or not valor or valor<=0 or valor>obj.saldo_aberto+0.005: flash("Conta ou valor de recebimento inválido.","erro")
        else: session.add(Recebimento(data=date.today(),conta=conta,recebivel=obj,valor_recebido=valor)); session.commit(); session.close(); flash("Recebimento registrado com sucesso!","sucesso"); return redirect(url_for("financeiro.listar_recebiveis"))
    contas=session.query(Conta).filter_by(deleted=False,id_empresa=obj.id_empresa).order_by(Conta.descricao).all(); saldo=obj.saldo_aberto; session.close(); return render_template("recebivel_receber.html",recebivel=obj,contas=contas,saldo=saldo)
