"""Regras de importação e processamento do Open Finance.

O conector bancário somente alimenta ``OpenFinanceTransacao``. A transformação
em movimentação é deliberadamente separada para manter revisão humana,
idempotência e as mesmas regras contábeis das movimentações manuais.
"""
from datetime import datetime
from decimal import Decimal
import hashlib
import json

from models import Documento, MovimentacaoConta, OpenFinanceTransacao, PlanoDeContas


class OpenFinanceProcessamentoErro(ValueError):
    pass


def registrar_transacoes(session, conta_openfinance, itens):
    """Inclui apenas transações ainda não importadas e devolve as novas linhas."""
    criadas = []
    for item in itens:
        external_id = str(item["external_id"]).strip()
        existente = session.query(OpenFinanceTransacao).filter_by(
            id_openfinance_conta=conta_openfinance.id_openfinance_conta,
            external_id=external_id,
        ).first()
        if existente:
            continue
        payload = json.dumps(item, sort_keys=True, default=str, ensure_ascii=False)
        transacao = OpenFinanceTransacao(
            openfinance_conta=conta_openfinance,
            external_id=external_id,
            data=item["data"],
            descricao=str(item.get("descricao") or "Transação Open Finance").strip(),
            valor=abs(Decimal(str(item["valor"]))),
            natureza=item["natureza"],
            payload_hash=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        )
        session.add(transacao)
        criadas.append(transacao)
    session.flush()
    return criadas


def processar_transacao(session, transacao, id_plano):
    """Converte uma pendência classificada em movimentação conciliável."""
    if transacao.status != "pendente" or transacao.id_movimentacao:
        raise OpenFinanceProcessamentoErro("A transação já foi processada.")

    conta_externa = transacao.openfinance_conta
    conta = conta_externa.conta
    if not conta or conta.deleted or not conta_externa.ativa:
        raise OpenFinanceProcessamentoErro("Vincule uma conta ativa do PSFINANCE antes de processar.")
    centro = conta_externa.centro_custo
    if not centro or centro.deleted or centro.id_empresa != conta.id_empresa:
        raise OpenFinanceProcessamentoErro("Configure um centro de custo da mesma empresa da conta.")

    natureza = transacao.natureza
    if natureza not in ("entrada", "saida"):
        raise OpenFinanceProcessamentoErro("Natureza da transação inválida.")
    grupo = "1.%" if natureza == "entrada" else "2.%"
    plano = session.query(PlanoDeContas).filter(
        PlanoDeContas.id_plano == int(id_plano),
        PlanoDeContas.deleted.is_(False),
        PlanoDeContas.tipo.ilike("analitica"),
        PlanoDeContas.cod_estrutural.like(grupo),
    ).first()
    if not plano:
        raise OpenFinanceProcessamentoErro(
            f"Selecione uma conta analítica do grupo {grupo[0]} para esta transação."
        )
    documento = session.query(Documento).filter(
        Documento.tipo_doc == "AV", Documento.deleted.is_(False)
    ).first()
    if not documento:
        raise OpenFinanceProcessamentoErro("Cadastre o documento AV antes de processar.")

    movimento = MovimentacaoConta(
        data=transacao.data,
        tipo="E" if natureza == "entrada" else "S",
        documento=documento,
        nr_documento=transacao.external_id[:30],
        descricao=transacao.descricao,
        valor=transacao.valor,
        id_conta_origem=conta.id_conta if natureza == "saida" else None,
        id_conta_destino=conta.id_conta if natureza == "entrada" else None,
        id_empresa=conta.id_empresa,
        id_centro_custo=centro.id_centro_custo,
        id_plano=plano.id_plano,
        conciliado=False,
    )
    session.add(movimento)
    session.flush()
    transacao.id_plano = plano.id_plano
    transacao.id_movimentacao = movimento.id_movimentacao
    transacao.status = "processada"
    transacao.processada_em = datetime.utcnow()
    session.flush()
    return movimento
