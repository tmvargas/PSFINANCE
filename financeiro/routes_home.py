# financeiro/routes_home.py
from flask import render_template
from . import bp_financeiro
from database import SessionLocal
from models import Conta


def get_session():
    return SessionLocal()


@bp_financeiro.route("/")
def dashboard_financeiro():
    """Tela inicial: visão geral de saldos de contas."""
    session = get_session()

    contas = (
        session.query(Conta)
        .filter(Conta.deleted.is_(False))
        .order_by(Conta.descricao)
        .all()
    )

    contas_view = []
    total_saldo = 0.0

    for c in contas:
        saldo_atual = c.saldo_atual
        total_saldo += saldo_atual

        contas_view.append({
            "id": c.id_conta,
            "descricao": c.descricao,
            "tipo": c.tipo,
            "saldo_atual": saldo_atual,
        })

    session.close()

    return render_template(
        "dashboard_financeiro.html",
        contas=contas_view,
        total_saldo=total_saldo,
    )
