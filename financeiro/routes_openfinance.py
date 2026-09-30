from flask import flash, redirect, render_template, request, url_for
from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import OpenFinanceConexao, OpenFinanceConta, OpenFinanceTransacao, PlanoDeContas
from . import bp_financeiro
from .openfinance_service import OpenFinanceProcessamentoErro, processar_transacao


@bp_financeiro.get("/open-finance/configuracao")
def openfinance_configuracao():
    session = SessionLocal()
    try:
        conexoes = session.query(OpenFinanceConexao).filter(
            OpenFinanceConexao.deleted.is_(False)
        ).order_by(OpenFinanceConexao.nome).all()
        contas = session.query(OpenFinanceConta).options(
            joinedload(OpenFinanceConta.conta), joinedload(OpenFinanceConta.centro_custo)
        ).filter(OpenFinanceConta.deleted.is_(False)).order_by(OpenFinanceConta.nome).all()
        return render_template("openfinance_configuracao.html", conexoes=conexoes, contas=contas)
    finally:
        session.close()


@bp_financeiro.get("/open-finance/transacoes")
def openfinance_transacoes():
    session = SessionLocal()
    try:
        transacoes = session.query(OpenFinanceTransacao).options(
            joinedload(OpenFinanceTransacao.openfinance_conta)
        ).filter(
            OpenFinanceTransacao.deleted.is_(False),
            OpenFinanceTransacao.status == "pendente",
        ).order_by(OpenFinanceTransacao.data.desc(), OpenFinanceTransacao.id_transacao.desc()).all()
        planos_entrada = session.query(PlanoDeContas).filter(
            PlanoDeContas.deleted.is_(False), PlanoDeContas.tipo.ilike("analitica"),
            PlanoDeContas.cod_estrutural.like("1.%"),
        ).order_by(PlanoDeContas.cod_estrutural).all()
        planos_saida = session.query(PlanoDeContas).filter(
            PlanoDeContas.deleted.is_(False), PlanoDeContas.tipo.ilike("analitica"),
            PlanoDeContas.cod_estrutural.like("2.%"),
        ).order_by(PlanoDeContas.cod_estrutural).all()
        return render_template(
            "openfinance_transacoes.html", transacoes=transacoes,
            planos_entrada=planos_entrada, planos_saida=planos_saida,
        )
    finally:
        session.close()


@bp_financeiro.post("/open-finance/transacoes/<int:id_transacao>/processar")
def openfinance_processar(id_transacao):
    session = SessionLocal()
    try:
        transacao = session.query(OpenFinanceTransacao).options(
            joinedload(OpenFinanceTransacao.openfinance_conta).joinedload(OpenFinanceConta.conta),
            joinedload(OpenFinanceTransacao.openfinance_conta).joinedload(OpenFinanceConta.centro_custo),
        ).filter_by(id_transacao=id_transacao).first()
        if not transacao:
            flash("Transação não encontrada.", "erro")
        else:
            processar_transacao(session, transacao, request.form.get("id_plano"))
            session.commit()
            flash("Transação processada e enviada para Movimentações.", "sucesso")
    except (OpenFinanceProcessamentoErro, TypeError, ValueError) as exc:
        session.rollback()
        flash(str(exc), "erro")
    finally:
        session.close()
    return redirect(url_for("financeiro.openfinance_transacoes"))
