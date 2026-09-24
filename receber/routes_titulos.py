# financeiro/routes_titulos.py
import os
import uuid as uuid_lib
import calendar
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session as flask_session,
    url_for,
)
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_

from . import bp_receber
from financeiro.regras_empresa_centro import (
    listar_empresas_centros_ativos,
    resolver_filtro_empresa_memorizado,
    validar_conta_da_empresa,
    validar_empresa_centro,
)
from database import SessionLocal
from models import (
    Recebimento,
    Conta,
    Cliente,
    Documento,
    PlanoDeContas,
    Recebivel,
    RecebivelAnexo,
    RecebivelParcela,
)

LIMITE_PARCELAS_TITULO = 999
SITUACOES_TITULO = {"todas", "baixada", "em_aberto"}
MODOS_VENCIMENTO = {"mes", "periodo"}


def get_session():
    return SessionLocal()


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_float(value: str | None):
    if value is None:
        return None

    s = str(value).strip()
    if not s:
        return None

    # limpa moeda e espaços
    s = s.replace("R$", "").replace(" ", "")

    # Casos:
    # 1) "1.234,56"  -> pt-BR (ponto milhar, vírgula decimal)
    # 2) "1234,56"   -> vírgula decimal
    # 3) "1234.56"   -> ponto decimal (padrão)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    else:
        # se tiver mais de um ponto, mantém o último como decimal
        if s.count(".") > 1:
            parts = s.split(".")
            s = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return float(s)
    except Exception:
        return None


def _parse_int(value: str | None):
    try:
        return int(value)
    except Exception:
        return None


def _normalizar_situacao_titulo(value: str | None) -> str:
    situacao = (value or "todas").strip().lower()
    return situacao if situacao in SITUACOES_TITULO else "todas"


def _normalizar_busca_titulo(value: str | None) -> str:
    return " ".join((value or "").strip().split())[:80]


def _termo_like_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _resolver_periodo_vencimento(args, hoje: date):
    modo = (args.get("modo_vencimento") or "mes").strip().lower()
    if modo not in MODOS_VENCIMENTO:
        modo = "mes"

    mes = _parse_int(args.get("mes")) or hoje.month
    ano = _parse_int(args.get("ano")) or hoje.year
    if mes < 1 or mes > 12 or ano < 1900 or ano > 9998:
        mes, ano = hoje.month, hoje.year

    if modo == "periodo":
        vencimento_inicial = _parse_date(args.get("vencimento_inicial"))
        vencimento_final = _parse_date(args.get("vencimento_final"))
        if vencimento_inicial and vencimento_final and vencimento_inicial <= vencimento_final:
            return {
                "modo": modo,
                "mes": mes,
                "ano": ano,
                "data_ini": vencimento_inicial,
                "data_fim": vencimento_final + timedelta(days=1),
                "vencimento_inicial": vencimento_inicial,
                "vencimento_final": vencimento_final,
            }
        modo = "mes"

    data_ini = date(ano, mes, 1)
    data_fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return {
        "modo": modo,
        "mes": mes,
        "ano": ano,
        "data_ini": data_ini,
        "data_fim": data_fim,
        "vencimento_inicial": None,
        "vencimento_final": None,
    }


def _aplicar_filtros_titulo(query, id_cliente=None, emissao=None, busca_titulo=""):
    if id_cliente:
        query = query.filter(Recebivel.id_cliente == id_cliente)
    if emissao:
        query = query.filter(Recebivel.emissao == emissao)
    if busca_titulo:
        termo = f"%{_termo_like_literal(busca_titulo)}%"
        condicoes = [
            Recebivel.nr_documento.ilike(termo, escape="\\"),
            Documento.tipo_doc.ilike(termo, escape="\\"),
            Documento.nome_doc.ilike(termo, escape="\\"),
        ]
        id_recebivel = _parse_int(busca_titulo)
        if id_recebivel is not None:
            condicoes.append(Recebivel.id_recebivel == id_recebivel)
        query = query.join(Documento, Documento.id_doc == Recebivel.id_doc).filter(
            Documento.deleted.is_(False),
            or_(*condicoes),
        )
    return query


def _calcular_saldo_titulo(total_ativo: float, baixado_ativo: float) -> float:
    return max(0.0, float(total_ativo or 0) - float(baixado_ativo or 0))


def _receber_titulo_atende_situacao(saldo_titulo: float, situacao: str) -> bool:
    if situacao == "baixada":
        return saldo_titulo <= 0
    if situacao == "em_aberto":
        return saldo_titulo > 0
    return True


def _filtrar_titulos_por_situacao(
    titulos: list[Recebivel],
    saldos_titulos: dict[int, float],
    situacao: str,
) -> list[Recebivel]:
    """Aplica a situação usando o saldo das parcelas exibidas no período."""
    return [
        titulo
        for titulo in titulos
        if _receber_titulo_atende_situacao(
            saldos_titulos.get(titulo.id_recebivel, float(titulo.valor or 0)),
            situacao,
        )
    ]


def _add_months(data_base: date, meses: int) -> date:
    mes_indice = data_base.month - 1 + meses
    ano = data_base.year + mes_indice // 12
    mes = mes_indice % 12 + 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(data_base.day, ultimo_dia))


def _proximo_vencimento_cartao(hoje: date, dia_vencimento: int) -> date:
    ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
    vencimento = date(hoje.year, hoje.month, min(dia_vencimento, ultimo_dia))
    if vencimento >= hoje:
        return vencimento
    return _add_months(vencimento, 1)


def _previsoes_cartao_credito(
    session,
    hoje: date,
    data_ini: date,
    data_fim: date,
    id_empresa: int | None,
    id_cliente: int | None,
    emissao: date | None,
    busca_titulo: str,
    situacao: str,
):
    if id_cliente or emissao or situacao == "baixada":
        return []

    query = session.query(Conta).filter(
        Conta.deleted.is_(False),
        Conta.tipo == "cartao_credito",
        Conta.dia_vencimento_cartao.isnot(None),
    )
    if id_empresa:
        query = query.filter(Conta.id_empresa == id_empresa)

    termo = busca_titulo.casefold()
    previsoes = []
    for conta in query.order_by(Conta.descricao).all():
        saldo = float(conta.saldo_atual or 0)
        if saldo >= -0.005:
            continue
        if termo and termo not in f"cartão cartao fatura {conta.descricao}".casefold():
            continue
        vencimento = _proximo_vencimento_cartao(hoje, conta.dia_vencimento_cartao)
        if not data_ini <= vencimento < data_fim:
            continue
        valor = abs(saldo)
        previsoes.append(
            {
                "id": f"cartao-{conta.id_conta}",
                "tipo_linha": "cartao_credito",
                "id_conta": conta.id_conta,
                "id_empresa": conta.id_empresa,
                "doc_label": "Previsão de cartão",
                "nr_documento": "Saldo flutuante",
                "credor": conta.descricao,
                "empresa": f"{conta.empresa.codigo} - {conta.empresa.nome}" if conta.empresa else "",
                "centro_custo": "",
                "plano": "Fatura prevista",
                "emissao": "",
                "vencimento": vencimento.strftime("%d/%m/%Y"),
                "vencimento_data": vencimento,
                "valor_total_titulo": valor,
                "valor_parcela_mes": valor,
                "pago_mes": 0.0,
                "nao_pago_mes": valor,
            }
        )
    return previsoes


def _gerar_parcelas(valor_total: float, vencimento_inicial: date, quantidade: int):
    total_centavos = round(float(valor_total or 0) * 100)
    base_centavos = total_centavos // quantidade
    resto = total_centavos % quantidade

    parcelas = []
    for indice in range(quantidade):
        valor_centavos = base_centavos + (1 if indice < resto else 0)
        parcelas.append(
            {
                "numero": indice + 1,
                "valor": valor_centavos / 100,
                "vencimento": _add_months(vencimento_inicial, indice),
            }
        )
    return parcelas


def _sincronizar_parcelas_iniciais(
    session,
    titulo: Recebivel,
    valor_total: float,
    vencimento_inicial: date,
    quantidade: int,
):
    parcelas_existentes = [
        p for p in getattr(titulo, "parcelas", []) if not getattr(p, "deleted", False)
    ]
    for parcela in parcelas_existentes:
        parcela.deleted = True

    for parcela in _gerar_parcelas(valor_total, vencimento_inicial, quantidade):
        session.add(
            RecebivelParcela(
                id_recebivel=titulo.id_recebivel,
                numero_parcela=parcela["numero"],
                vencimento=parcela["vencimento"],
                valor=parcela["valor"],
            )
        )


def _garantir_parcela_unica(session, titulo: Recebivel):
    tem_parcela = (
        session.query(RecebivelParcela.id_parcela)
        .filter(
            RecebivelParcela.deleted.is_(False),
            RecebivelParcela.id_recebivel == titulo.id_recebivel,
        )
        .first()
        is not None
    )
    if not tem_parcela:
        session.add(
            RecebivelParcela(
                id_recebivel=titulo.id_recebivel,
                numero_parcela=1,
                vencimento=titulo.vencimento,
                valor=float(titulo.valor or 0),
            )
        )
        return True
    return False


def _sincronizar_parcela_unica_com_titulo(session, titulo: Recebivel):
    _garantir_parcela_unica(session, titulo)
    session.flush()

    parcelas_ativas = (
        session.query(RecebivelParcela)
        .filter(
            RecebivelParcela.deleted.is_(False),
            RecebivelParcela.id_recebivel == titulo.id_recebivel,
        )
        .order_by(RecebivelParcela.numero_parcela.asc(), RecebivelParcela.id_parcela.asc())
        .all()
    )
    if len(parcelas_ativas) == 1:
        parcela = parcelas_ativas[0]
        parcela.numero_parcela = 1
        parcela.vencimento = titulo.vencimento
        parcela.valor = float(titulo.valor or 0)


def _quantidade_parcelas_ativas(session, id_recebivel: int | None) -> int:
    if id_recebivel is None:
        return 1

    quantidade = (
        session.query(func.count(RecebivelParcela.id_parcela))
        .filter(
            RecebivelParcela.deleted.is_(False),
            RecebivelParcela.id_recebivel == id_recebivel,
        )
        .scalar()
    )
    return max(1, int(quantidade or 0))


def _titulos_periodo_por_parcela(
    session, data_ini: date, data_fim: date, id_empresa: int | None,
    id_cliente=None, emissao=None, busca_titulo="",
):
    query = (
        session.query(
            RecebivelParcela.id_recebivel,
            func.min(RecebivelParcela.vencimento).label("vencimento_periodo"),
            func.coalesce(func.sum(RecebivelParcela.valor), 0).label("valor_periodo"),
        )
        .join(Recebivel, Recebivel.id_recebivel == RecebivelParcela.id_recebivel)
        .filter(
            Recebivel.deleted.is_(False),
            RecebivelParcela.deleted.is_(False),
            RecebivelParcela.vencimento >= data_ini,
            RecebivelParcela.vencimento < data_fim,
        )
    )

    if id_empresa:
        query = query.filter(Recebivel.id_empresa == id_empresa)

    query = _aplicar_filtros_titulo(query, id_cliente, emissao, busca_titulo)

    return {
        id_recebivel: {
            "vencimento": vencimento_periodo,
            "valor": float(valor_periodo or 0),
        }
        for id_recebivel, vencimento_periodo, valor_periodo in query.group_by(RecebivelParcela.id_recebivel).all()
    }


def _titulos_legados_periodo_sem_parcela(
    session, data_ini: date, data_fim: date, id_empresa: int | None,
    id_cliente=None, emissao=None, busca_titulo="",
):
    titulos_com_parcela_ativa = (
        session.query(RecebivelParcela.id_recebivel)
        .filter(RecebivelParcela.deleted.is_(False))
        .distinct()
    )
    query = session.query(Recebivel.id_recebivel, Recebivel.vencimento, Recebivel.valor).filter(
        Recebivel.deleted.is_(False),
        Recebivel.vencimento >= data_ini,
        Recebivel.vencimento < data_fim,
        ~Recebivel.id_recebivel.in_(titulos_com_parcela_ativa),
    )

    if id_empresa:
        query = query.filter(Recebivel.id_empresa == id_empresa)

    query = _aplicar_filtros_titulo(query, id_cliente, emissao, busca_titulo)

    return {
        id_recebivel: {
            "vencimento": vencimento,
            "valor": float(valor or 0),
        }
        for id_recebivel, vencimento, valor in query.all()
    }


def _baixas_periodo_por_parcela(session, data_ini: date, data_fim: date, ids_titulos: list[int]):
    if not ids_titulos:
        return {}

    baixas_por_parcela = dict(
        session.query(
            Recebimento.id_recebivel,
            func.coalesce(func.sum(Recebimento.valor_recebido), 0).label("soma"),
        )
        .join(RecebivelParcela, RecebivelParcela.id_parcela == Recebimento.id_parcela)
        .filter(
            Recebimento.deleted.is_(False),
            Recebimento.id_recebivel.in_(ids_titulos),
            RecebivelParcela.deleted.is_(False),
            RecebivelParcela.vencimento >= data_ini,
            RecebivelParcela.vencimento < data_fim,
        )
        .group_by(Recebimento.id_recebivel)
        .all()
    )

    baixas_legadas = dict(
        session.query(
            Recebimento.id_recebivel,
            func.coalesce(func.sum(Recebimento.valor_recebido), 0).label("soma"),
        )
        .filter(
            Recebimento.deleted.is_(False),
            Recebimento.id_recebivel.in_(ids_titulos),
            Recebimento.id_parcela.is_(None),
            Recebimento.data >= data_ini,
            Recebimento.data < data_fim,
        )
        .group_by(Recebimento.id_recebivel)
        .all()
    )

    return {
        id_recebivel: float(baixas_por_parcela.get(id_recebivel, 0) or 0)
        + float(baixas_legadas.get(id_recebivel, 0) or 0)
        for id_recebivel in ids_titulos
    }


def _saldos_titulos_ativos(session, titulos: list[Recebivel]) -> dict[int, float]:
    ids_titulos = [titulo.id_recebivel for titulo in titulos]
    if not ids_titulos:
        return {}

    ids_titulos_com_parcelas = {
        id_recebivel
        for (id_recebivel,) in (
            session.query(RecebivelParcela.id_recebivel)
            .filter(RecebivelParcela.id_recebivel.in_(ids_titulos))
            .distinct()
            .all()
        )
    }
    totais_parcelas = dict(
        session.query(
            RecebivelParcela.id_recebivel,
            func.coalesce(func.sum(RecebivelParcela.valor), 0),
        )
        .filter(
            RecebivelParcela.deleted.is_(False),
            RecebivelParcela.id_recebivel.in_(ids_titulos),
        )
        .group_by(RecebivelParcela.id_recebivel)
        .all()
    )
    baixas_parcelas = dict(
        session.query(
            Recebimento.id_recebivel,
            func.coalesce(func.sum(Recebimento.valor_recebido), 0),
        )
        .join(RecebivelParcela, RecebivelParcela.id_parcela == Recebimento.id_parcela)
        .filter(
            Recebimento.deleted.is_(False),
            Recebimento.id_recebivel.in_(ids_titulos),
            RecebivelParcela.deleted.is_(False),
        )
        .group_by(Recebimento.id_recebivel)
        .all()
    )
    baixas_legadas = dict(
        session.query(
            Recebimento.id_recebivel,
            func.coalesce(func.sum(Recebimento.valor_recebido), 0),
        )
        .filter(
            Recebimento.deleted.is_(False),
            Recebimento.id_recebivel.in_(ids_titulos),
            Recebimento.id_parcela.is_(None),
        )
        .group_by(Recebimento.id_recebivel)
        .all()
    )

    return {
        titulo.id_recebivel: _calcular_saldo_titulo(
            (
                totais_parcelas.get(titulo.id_recebivel, 0)
                if titulo.id_recebivel in ids_titulos_com_parcelas
                else titulo.valor
            ),
            float(baixas_parcelas.get(titulo.id_recebivel, 0) or 0)
            + float(baixas_legadas.get(titulo.id_recebivel, 0) or 0),
        )
        for titulo in titulos
    }



def _uploads_dir() -> Path:
    # guarda dentro da pasta do app (não versionada)
    base = current_app.instance_path if current_app else "instance"
    p = Path(base) / "uploads" / "titulos"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _receber_titulo_saldo_aberto(session, id_recebivel: int) -> float:
    titulo = (
        session.query(Recebivel)
        .filter(Recebivel.id_recebivel == id_recebivel, Recebivel.deleted.is_(False))
        .first()
    )
    if not titulo:
        return 0.0

    baixado = (
        session.query(func.coalesce(func.sum(Recebimento.valor_recebido), 0))
        .filter(
            Recebimento.deleted.is_(False),
            Recebimento.id_recebivel == id_recebivel,
        )
        .scalar()
    )
    total = float(titulo.valor or 0)
    baixado = float(baixado or 0)
    return max(0.0, total - baixado)


def _parcelas_baixa_view(session, id_recebivel: int):
    parcelas = (
        session.query(RecebivelParcela)
        .filter(
            RecebivelParcela.deleted.is_(False),
            RecebivelParcela.id_recebivel == id_recebivel,
        )
        .order_by(RecebivelParcela.numero_parcela.asc(), RecebivelParcela.id_parcela.asc())
        .all()
    )

    baixas_por_parcela = dict(
        session.query(
            Recebimento.id_parcela,
            func.coalesce(func.sum(Recebimento.valor_recebido), 0).label("soma"),
        )
        .filter(
            Recebimento.deleted.is_(False),
            Recebimento.id_recebivel == id_recebivel,
            Recebimento.id_parcela.isnot(None),
        )
        .group_by(Recebimento.id_parcela)
        .all()
    )

    parcelas_view = []
    for parcela in parcelas:
        valor = float(parcela.valor or 0)
        baixado = float(baixas_por_parcela.get(parcela.id_parcela, 0) or 0)
        saldo = max(0.0, valor - baixado)
        parcelas_view.append(
            {
                "id": parcela.id_parcela,
                "numero": parcela.numero_parcela,
                "vencimento": parcela.vencimento.strftime("%d/%m/%Y") if parcela.vencimento else "",
                "valor": valor,
                "baixado": baixado,
                "saldo": saldo,
            }
        )

    return parcelas_view


def _buscar_parcela_baixa(session, id_recebivel: int, id_parcela: int | None):
    if id_parcela is None:
        return None

    return (
        session.query(RecebivelParcela)
        .filter(
            RecebivelParcela.deleted.is_(False),
            RecebivelParcela.id_recebivel == id_recebivel,
            RecebivelParcela.id_parcela == id_parcela,
        )
        .first()
    )


def _saldo_parcela(session, id_recebivel: int, id_parcela: int) -> float:
    parcela = _buscar_parcela_baixa(session, id_recebivel, id_parcela)
    if not parcela:
        return 0.0

    baixado = (
        session.query(func.coalesce(func.sum(Recebimento.valor_recebido), 0))
        .filter(
            Recebimento.deleted.is_(False),
            Recebimento.id_recebivel == id_recebivel,
            Recebimento.id_parcela == id_parcela,
        )
        .scalar()
    )
    return max(0.0, float(parcela.valor or 0) - float(baixado or 0))


def _ids_parcelas_com_baixa(session, id_recebivel: int) -> set[int]:
    return {
        id_parcela
        for (id_parcela,) in (
            session.query(Recebimento.id_parcela)
            .filter(
                Recebimento.deleted.is_(False),
                Recebimento.id_recebivel == id_recebivel,
                Recebimento.id_parcela.isnot(None),
            )
            .distinct()
            .all()
        )
    }


# ----------------------------------------------------------------------
# LISTAR TÍTULOS (filtro por mês/ano do VENCIMENTO)
# ----------------------------------------------------------------------
@bp_receber.route("/titulos")
def listar_titulos():
    session = get_session()

    hoje = date.today()
    periodo = _resolver_periodo_vencimento(request.args, hoje)
    mes = periodo["mes"]
    ano = periodo["ano"]
    situacao = _normalizar_situacao_titulo(request.args.get("situacao"))
    emissao = _parse_date(request.args.get("emissao"))
    busca_titulo = _normalizar_busca_titulo(request.args.get("titulo"))
    data_ini = periodo["data_ini"]
    data_fim = periodo["data_fim"]
    empresas_view, _centros_custo_view = listar_empresas_centros_ativos(session)
    id_empresa = resolver_filtro_empresa_memorizado(empresas_view, request.args, flask_session)

    credores_query = (
        session.query(Cliente)
        .join(Recebivel, Recebivel.id_cliente == Cliente.id_cliente)
        .filter(Cliente.deleted.is_(False), Recebivel.deleted.is_(False))
    )
    if id_empresa:
        credores_query = credores_query.filter(Recebivel.id_empresa == id_empresa)
    credores = credores_query.order_by(Cliente.nome).distinct().all()
    credores_view = [{"id": credor.id_cliente, "nome": credor.nome} for credor in credores]
    ids_credores_validos = {credor["id"] for credor in credores_view}
    id_cliente = _parse_int(request.args.get("id_cliente"))
    if id_cliente not in ids_credores_validos:
        id_cliente = None

    titulos_periodo = _titulos_periodo_por_parcela(
        session, data_ini, data_fim, id_empresa, id_cliente, emissao, busca_titulo
    )
    titulos_periodo.update(
        _titulos_legados_periodo_sem_parcela(
            session, data_ini, data_fim, id_empresa, id_cliente, emissao, busca_titulo
        )
    )
    ids_titulos = list(titulos_periodo)

    titulos_por_id = {}
    if ids_titulos:
        titulos = (
            session.query(Recebivel)
            .options(
                joinedload(Recebivel.credor),
                joinedload(Recebivel.empresa),
                joinedload(Recebivel.centro_custo),
                joinedload(Recebivel.plano),
                joinedload(Recebivel.documento),  # requer relationship via id_doc
            )
            .filter(Recebivel.id_recebivel.in_(ids_titulos))
            .all()
        )
        titulos_por_id = {t.id_recebivel: t for t in titulos}

    titulos = [
        titulos_por_id[id_recebivel]
        for id_recebivel in sorted(
            ids_titulos,
            key=lambda item: (titulos_periodo[item]["vencimento"], -item),
        )
        if id_recebivel in titulos_por_id
    ]

    baixas_soma = _baixas_periodo_por_parcela(
        session,
        data_ini,
        data_fim,
        [t.id_recebivel for t in titulos],
    )
    saldos_periodo = {
        t.id_recebivel: _calcular_saldo_titulo(
            titulos_periodo[t.id_recebivel]["valor"],
            baixas_soma.get(t.id_recebivel, 0),
        )
        for t in titulos
    }
    titulos = _filtrar_titulos_por_situacao(titulos, saldos_periodo, situacao)

    rows = []
    total_valor_titulo = 0.0
    total_valor_parcela_mes = 0.0
    total_pago_mes = 0.0
    total_nao_pago_mes = 0.0

    for t in titulos:
        valor_total_titulo = float(t.valor or 0)
        valor_parcela_mes = float(titulos_periodo[t.id_recebivel]["valor"] or 0)
        pago_mes = float(baixas_soma.get(t.id_recebivel, 0) or 0)
        nao_pago_mes = max(0.0, valor_parcela_mes - pago_mes)

        total_valor_titulo += valor_total_titulo
        total_valor_parcela_mes += valor_parcela_mes
        total_pago_mes += pago_mes
        total_nao_pago_mes += nao_pago_mes

        doc_label = ""
        if getattr(t, "documento", None) is not None:
            doc_label = f"{t.documento.tipo_doc} - {t.documento.nome_doc}"
        else:
            # fallback se ainda existir campo string antigo
            doc_label = getattr(t, "documento", "") or ""

        vencimento_periodo = titulos_periodo[t.id_recebivel]["vencimento"] or t.vencimento

        rows.append(
            {
                "id": t.id_recebivel,
                "doc_label": doc_label,
                "nr_documento": t.nr_documento,
                "credor": t.credor.nome if t.credor else "",
                "empresa": f"{t.empresa.codigo} - {t.empresa.nome}" if t.empresa else "",
                "centro_custo": f"{t.centro_custo.codigo} - {t.centro_custo.nome}" if t.centro_custo else "",
                "plano": f"{t.plano.cod_estrutural} - {t.plano.nome_conta}" if t.plano else "",
                "emissao": t.emissao.strftime("%d/%m/%Y") if t.emissao else "",
                "vencimento": vencimento_periodo.strftime("%d/%m/%Y") if vencimento_periodo else "",
                "vencimento_data": vencimento_periodo,
                "tipo_linha": "titulo",
                "valor_total_titulo": valor_total_titulo,
                "valor_parcela_mes": valor_parcela_mes,
                "pago_mes": pago_mes,
                "nao_pago_mes": nao_pago_mes,
            }
        )

    previsoes_cartao = _previsoes_cartao_credito(
        session, hoje, data_ini, data_fim, id_empresa, id_cliente,
        emissao, busca_titulo, situacao,
    )
    for previsao in previsoes_cartao:
        rows.append(previsao)
        total_valor_titulo += previsao["valor_total_titulo"]
        total_valor_parcela_mes += previsao["valor_parcela_mes"]
        total_nao_pago_mes += previsao["nao_pago_mes"]
    rows.sort(key=lambda row: (row.get("vencimento_data") or date.max, str(row["id"])))

    meses = [
        (1, "Jan"), (2, "Fev"), (3, "Mar"), (4, "Abr"),
        (5, "Mai"), (6, "Jun"), (7, "Jul"), (8, "Ago"),
        (9, "Set"), (10, "Out"), (11, "Nov"), (12, "Dez"),
    ]
    anos = list(range(hoje.year - 3, hoje.year + 2))

    session.close()
    return render_template(
        "receber_titulos_list.html",
        titulos=rows,
        mes=mes,
        ano=ano,
        meses=meses,
        anos=anos,
        modo_vencimento=periodo["modo"],
        vencimento_inicial=periodo["vencimento_inicial"],
        vencimento_final=periodo["vencimento_final"],
        empresas=empresas_view,
        id_empresa=id_empresa,
        credores=credores_view,
        id_cliente=id_cliente,
        emissao=emissao,
        busca_titulo=busca_titulo,
        situacao=situacao,
        total_valor_titulo=total_valor_titulo,
        total_valor_parcela_mes=total_valor_parcela_mes,
        total_pago_mes=total_pago_mes,
        total_nao_pago_mes=total_nao_pago_mes,
    )


# ----------------------------------------------------------------------
# NOVO / EDITAR TÍTULO
# ----------------------------------------------------------------------
@bp_receber.route("/titulos/novo", methods=["GET", "POST"])
def novo_titulo():
    return _upsert_titulo(None)


@bp_receber.route("/titulos/<int:id_recebivel>/editar", methods=["GET", "POST"])
def editar_titulo(id_recebivel: int):
    return _upsert_titulo(id_recebivel)


@bp_receber.route("/titulos/<int:id_recebivel>/copiar", methods=["GET", "POST"])
def copiar_titulo(id_recebivel: int):
    return _upsert_titulo(None, id_recebivel_copia=id_recebivel)


def _upsert_titulo(id_recebivel: int | None, id_recebivel_copia: int | None = None):
    session = get_session()

    receber_titulo_obj = None
    receber_titulo_base = None
    anexos = []
    modo_copia = id_recebivel is None and id_recebivel_copia is not None

    if id_recebivel is not None or id_recebivel_copia is not None:
        id_busca = id_recebivel if id_recebivel is not None else id_recebivel_copia
        receber_titulo_base = (
            session.query(Recebivel)
            .options(
                joinedload(Recebivel.anexos),
                joinedload(Recebivel.credor),
                joinedload(Recebivel.empresa),
                joinedload(Recebivel.centro_custo),
                joinedload(Recebivel.plano),
                joinedload(Recebivel.documento),
            )
            .filter(Recebivel.id_recebivel == id_busca, Recebivel.deleted.is_(False))
            .first()
        )
        if not receber_titulo_base:
            session.close()
            flash("Título não encontrado.", "erro")
            return redirect(url_for("receber.listar_titulos"))

        if modo_copia:
            receber_titulo_obj = None
            anexos = []
        else:
            receber_titulo_obj = receber_titulo_base
            anexos = [a for a in (receber_titulo_obj.anexos or []) if not getattr(a, "deleted", False)]

    credores = (
        session.query(Cliente)
        .filter(Cliente.deleted.is_(False))
        .order_by(Cliente.nome)
        .all()
    )
    planos = (
        session.query(PlanoDeContas)
        .filter(
            PlanoDeContas.deleted.is_(False),
            PlanoDeContas.cod_estrutural.like("2.%"),  # ✅ só grupo 2
        )
        .order_by(PlanoDeContas.cod_estrutural)
        .all()
    )

    documentos = (
        session.query(Documento)
        .filter(Documento.deleted.is_(False))
        .order_by(Documento.tipo_doc)
        .all()
    )
    empresas_view, centros_custo_view = listar_empresas_centros_ativos(session)

    if request.method == "POST":
        id_doc = request.form.get("id_doc", type=int)
        nr_documento = (request.form.get("nr_documento") or "").strip()
        id_cliente = request.form.get("id_cliente", type=int)
        id_empresa = request.form.get("id_empresa", type=int)
        id_centro_custo = request.form.get("id_centro_custo", type=int)
        id_plano = request.form.get("id_plano", type=int)
        valor = _parse_float(request.form.get("valor"))
        emissao = _parse_date(request.form.get("emissao"))
        vencimento = _parse_date(request.form.get("vencimento"))
        observacao = (request.form.get("observacao") or "").strip()
        quantidade_parcelas_raw = request.form.get("quantidade_parcelas") or "1"
        quantidade_parcelas = _parse_int(quantidade_parcelas_raw)
        permitir_multi_parcela = receber_titulo_obj is None
        files = request.files.getlist("arquivos")
        files = [f for f in files if f and f.filename]


        erros = []
        if not id_doc:
            erros.append("Documento é obrigatório.")
        if not nr_documento:
            erros.append("Número do documento é obrigatório.")
        if not id_cliente:
            erros.append("Cliente é obrigatório.")
        erros_empresa_centro, _empresa, _centro = validar_empresa_centro(session, id_empresa, id_centro_custo)
        erros.extend(erros_empresa_centro)
        if not id_plano:
            erros.append("Plano financeiro é obrigatório.")
        if valor is None or valor <= 0:
            erros.append("Valor inválido.")
        if not emissao:
            erros.append("Data de emissão inválida.")
        if not vencimento:
            erros.append("Data de vencimento inválida.")
        if (
            quantidade_parcelas is None
            or quantidade_parcelas < 1
            or quantidade_parcelas > LIMITE_PARCELAS_TITULO
        ):
            erros.append(
                f"Quantidade de parcelas deve estar entre 1 e {LIMITE_PARCELAS_TITULO}."
            )
        if quantidade_parcelas is None:
            quantidade_parcelas = 1
        if not permitir_multi_parcela and quantidade_parcelas != 1:
            erros.append("Parcelamento só pode ser informado ao criar ou copiar um título.")

        if id_doc:
            doc = (
                session.query(Documento)
                .filter(Documento.id_doc == id_doc, Documento.deleted.is_(False))
                .first()
            )
            if not doc:
                erros.append("Documento selecionado não existe.")

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            receber_titulo_criado = receber_titulo_obj is None
            if receber_titulo_obj is None:
                receber_titulo_obj = Recebivel(
                    id_doc=id_doc,
                    nr_documento=nr_documento,
                    id_cliente=id_cliente,
                    id_empresa=id_empresa,
                    id_centro_custo=id_centro_custo,
                    id_plano=id_plano,
                    valor=valor,
                    emissao=emissao,
                    vencimento=vencimento,
                    observacao=observacao or None,

                )
                session.add(receber_titulo_obj)
                session.flush()
                _sincronizar_parcelas_iniciais(
                    session,
                    receber_titulo_obj,
                    valor,
                    vencimento,
                    quantidade_parcelas,
                )
            else:
                baixado = (
                    session.query(func.coalesce(func.sum(Recebimento.valor_recebido), 0))
                    .filter(Recebimento.deleted.is_(False), Recebimento.id_recebivel == receber_titulo_obj.id_recebivel)
                    .scalar()
                )
                baixado = float(baixado or 0)
                if valor < baixado - 0.0001:
                    flash(f"Não é possível definir valor menor que o já baixado (R$ {baixado:.2f}).", "erro")
                    session.close()
                    return redirect(url_for("receber.editar_titulo", id_recebivel=receber_titulo_obj.id_recebivel))

                receber_titulo_obj.id_doc = id_doc
                receber_titulo_obj.nr_documento = nr_documento
                receber_titulo_obj.id_cliente = id_cliente
                receber_titulo_obj.id_empresa = id_empresa
                receber_titulo_obj.id_centro_custo = id_centro_custo
                receber_titulo_obj.id_plano = id_plano
                receber_titulo_obj.valor = valor
                receber_titulo_obj.emissao = emissao
                receber_titulo_obj.vencimento = vencimento
                receber_titulo_obj.observacao = observacao
                _sincronizar_parcela_unica_com_titulo(session, receber_titulo_obj)
      
            if files:
                existentes = (
                    session.query(RecebivelAnexo)
                    .filter(
                        RecebivelAnexo.deleted.is_(False),
                        RecebivelAnexo.id_recebivel == receber_titulo_obj.id_recebivel,
                    )
                    .count()
                )
                if existentes + len(files) > 5:
                    flash("Limite de 5 anexos por título.", "erro")
                else:
                    updir = _uploads_dir()
                    for f in files:
                        ext = os.path.splitext(f.filename)[1]
                        safe_name = f"{uuid_lib.uuid4().hex}{ext}"
                        path = updir / safe_name
                        f.save(path)

                        an = RecebivelAnexo(
                            id_recebivel=receber_titulo_obj.id_recebivel,
                            nome_arquivo=f.filename,
                            caminho_arquivo=str(path),
                        )
                        session.add(an)

            session.commit()
            id_recebivel_salvo = receber_titulo_obj.id_recebivel
            session.close()
            if quantidade_parcelas > 1:
                flash(f"{quantidade_parcelas} parcelas salvas com sucesso!", "sucesso")
                return redirect(url_for("receber.editar_parcelas_titulo", id_recebivel=id_recebivel_salvo))
            if modo_copia:
                flash("Cópia do título salva com sucesso!", "sucesso")
                return redirect(url_for("receber.listar_titulos"))
            if receber_titulo_criado:
                flash("Título salvo com sucesso com parcela única.", "sucesso")
                return redirect(url_for("receber.listar_titulos"))
            flash("Título salvo com sucesso!", "sucesso")
            return redirect(url_for("receber.listar_titulos"))

    hoje_str = date.today().isoformat()

    receber_titulo_view = None
    receber_titulo_ref = receber_titulo_obj or receber_titulo_base
    if receber_titulo_ref is not None:
        receber_titulo_view = {
            "id_recebivel": None if modo_copia else receber_titulo_ref.id_recebivel,
            "id_doc": getattr(receber_titulo_ref, "id_doc", None),
            "nr_documento": receber_titulo_ref.nr_documento,
            "id_cliente": receber_titulo_ref.id_cliente,
            "id_empresa": getattr(receber_titulo_ref, "id_empresa", None),
            "id_centro_custo": getattr(receber_titulo_ref, "id_centro_custo", None),
            "id_plano": receber_titulo_ref.id_plano,
            "valor": float(receber_titulo_ref.valor or 0),
            "emissao": receber_titulo_ref.emissao,        # date (tem isoformat)
            "vencimento": receber_titulo_ref.vencimento,  # date (tem isoformat)
            "observacao": getattr(receber_titulo_ref, "observacao", "") or "",
            "quantidade_parcelas": _quantidade_parcelas_ativas(session, receber_titulo_ref.id_recebivel),

        }

    anexos_view = [{"id_anexo": a.id_anexo, "nome_arquivo": a.nome_arquivo} for a in anexos]
    credores_view = [{"id_cliente": c.id_cliente, "nome": c.nome} for c in credores]
    
    planos_view = [{
    "id_plano": p.id_plano,
    "cod_estrutural": p.cod_estrutural,
    "nome_conta": p.nome_conta,
    "tipo": p.tipo,  # ✅ necessário para desabilitar no template
} for p in planos]


    documentos_view = [{"id_doc": d.id_doc, "tipo_doc": d.tipo_doc, "nome_doc": d.nome_doc} for d in documentos]

    session.close()
    return render_template(
        "receber_titulo_form.html",
        titulo=receber_titulo_view,
        anexos=anexos_view,
        credores=credores_view,
        empresas=empresas_view,
        centros_custo=centros_custo_view,
        planos=planos_view,
        documentos=documentos_view,
        hoje=hoje_str,
        modo_copia=modo_copia,
        receber_titulo_original=receber_titulo_base.id_recebivel if receber_titulo_base else None,
        limite_parcelas_titulo=LIMITE_PARCELAS_TITULO,
    )


# ----------------------------------------------------------------------
# PARCELAS DO TÍTULO
# ----------------------------------------------------------------------
@bp_receber.route("/titulos/<int:id_recebivel>/parcelas", methods=["GET", "POST"])
def editar_parcelas_titulo(id_recebivel: int):
    session = get_session()

    titulo = (
        session.query(Recebivel)
        .options(
            joinedload(Recebivel.credor),
            joinedload(Recebivel.documento),
            joinedload(Recebivel.parcelas),
        )
        .filter(Recebivel.id_recebivel == id_recebivel, Recebivel.deleted.is_(False))
        .first()
    )
    if not titulo:
        session.close()
        flash("Título não encontrado.", "erro")
        return redirect(url_for("receber.listar_titulos"))

    _garantir_parcela_unica(session, titulo)
    session.flush()

    if request.method == "POST":
        parcela_ids = request.form.getlist("parcela_id")
        numeros = request.form.getlist("numero_parcela")
        vencimentos = request.form.getlist("vencimento_parcela")
        valores = request.form.getlist("valor_parcela")
        excluir_ids = set(request.form.getlist("excluir_parcela"))

        parcelas_por_id = {
            str(p.id_parcela): p
            for p in titulo.parcelas
            if not getattr(p, "deleted", False)
        }
        erros = []
        numeros_usados = set()
        parcelas_com_baixa = _ids_parcelas_com_baixa(session, titulo.id_recebivel)

        for indice, id_parcela in enumerate(parcela_ids):
            parcela = parcelas_por_id.get(id_parcela)
            if not parcela:
                continue

            if id_parcela in excluir_ids:
                if parcela.id_parcela in parcelas_com_baixa:
                    erros.append(
                        f"Não é possível excluir a parcela {parcela.numero_parcela} "
                        "porque ela possui baixa."
                    )
                    continue
                parcela.deleted = True
                continue

            numero = _parse_int(numeros[indice] if indice < len(numeros) else None)
            vencimento = _parse_date(vencimentos[indice] if indice < len(vencimentos) else None)
            valor = _parse_float(valores[indice] if indice < len(valores) else None)

            if parcela.id_parcela in parcelas_com_baixa and (
                numero != parcela.numero_parcela
                or vencimento != parcela.vencimento
                or valor is None
                or abs(valor - float(parcela.valor or 0)) > 0.0001
            ):
                erros.append(
                    f"Não é possível editar a parcela {parcela.numero_parcela} "
                    "porque ela possui baixa."
                )
                continue

            if numero is None or numero < 1:
                erros.append("Número de parcela inválido.")
                continue
            if numero in numeros_usados:
                erros.append("Número de parcela duplicado.")
                continue
            if not vencimento:
                erros.append(f"Vencimento inválido na parcela {numero}.")
                continue
            if valor is None or valor <= 0:
                erros.append(f"Valor inválido na parcela {numero}.")
                continue

            numeros_usados.add(numero)
            parcela.numero_parcela = numero
            parcela.vencimento = vencimento
            parcela.valor = valor

        novo_numero = _parse_int(request.form.get("novo_numero_parcela"))
        novo_vencimento = _parse_date(request.form.get("novo_vencimento_parcela"))
        novo_valor = _parse_float(request.form.get("novo_valor_parcela"))

        if novo_vencimento or novo_valor is not None:
            if novo_numero is None or novo_numero < 1:
                erros.append("Número da nova parcela inválido.")
            elif novo_numero in numeros_usados:
                erros.append("Número da nova parcela duplicado.")
            elif not novo_vencimento:
                erros.append("Vencimento da nova parcela inválido.")
            elif novo_valor is None or novo_valor <= 0:
                erros.append("Valor da nova parcela inválido.")
            else:
                numeros_usados.add(novo_numero)
                session.add(
                    RecebivelParcela(
                        id_recebivel=titulo.id_recebivel,
                        numero_parcela=novo_numero,
                        vencimento=novo_vencimento,
                        valor=novo_valor,
                    )
                )

        if erros:
            session.rollback()
            for erro in erros:
                flash(erro, "erro")
        else:
            session.flush()
            parcelas_ativas = (
                session.query(RecebivelParcela)
                .filter(
                    RecebivelParcela.deleted.is_(False),
                    RecebivelParcela.id_recebivel == titulo.id_recebivel,
                )
                .order_by(RecebivelParcela.numero_parcela.asc())
                .all()
            )
            if not parcelas_ativas:
                flash("Título deve possuir ao menos uma parcela ativa.", "erro")
                session.rollback()
            else:
                titulo.valor = sum(float(p.valor or 0) for p in parcelas_ativas)
                primeira_parcela = parcelas_ativas[0]
                titulo.vencimento = primeira_parcela.vencimento
                session.commit()
                session.close()
                flash("Parcelas salvas e valor total do título atualizado.", "sucesso")
                return redirect(url_for("receber.editar_parcelas_titulo", id_recebivel=id_recebivel))

    parcelas_view = []
    parcelas = (
        session.query(RecebivelParcela)
        .filter(
            RecebivelParcela.deleted.is_(False),
            RecebivelParcela.id_recebivel == titulo.id_recebivel,
        )
        .order_by(RecebivelParcela.numero_parcela.asc(), RecebivelParcela.id_parcela.asc())
        .all()
    )
    total_parcelas = 0.0
    parcelas_com_baixa = _ids_parcelas_com_baixa(session, titulo.id_recebivel)
    baixas_por_parcela = dict(
        session.query(
            Recebimento.id_parcela,
            func.coalesce(func.sum(Recebimento.valor_recebido), 0),
        )
        .filter(
            Recebimento.deleted.is_(False),
            Recebimento.id_recebivel == titulo.id_recebivel,
            Recebimento.id_parcela.isnot(None),
        )
        .group_by(Recebimento.id_parcela)
        .all()
    )
    for parcela in parcelas:
        valor = float(parcela.valor or 0)
        valor_recebidodo = float(baixas_por_parcela.get(parcela.id_parcela, 0) or 0)
        total_parcelas += valor
        parcelas_view.append(
            {
                "id_parcela": parcela.id_parcela,
                "numero_parcela": parcela.numero_parcela,
                "vencimento": parcela.vencimento.isoformat() if parcela.vencimento else "",
                "valor": valor,
                "saldo": max(0.0, valor - valor_recebidodo),
                "tem_baixa": parcela.id_parcela in parcelas_com_baixa,
            }
        )

    receber_titulo_view = {
        "id": titulo.id_recebivel,
        "documento": titulo.documento.tipo_doc if titulo.documento else "",
        "nr_documento": titulo.nr_documento,
        "credor": titulo.credor.nome if titulo.credor else "",
        "valor": float(titulo.valor or 0),
    }
    proximo_numero = (max([p["numero_parcela"] for p in parcelas_view] or [0]) + 1)

    session.close()
    return render_template(
        "receber_titulo_parcelas_form.html",
        titulo=receber_titulo_view,
        parcelas=parcelas_view,
        total_parcelas=total_parcelas,
        proximo_numero=proximo_numero,
        hoje=date.today().isoformat(),
    )


# ----------------------------------------------------------------------
# EXCLUIR TÍTULO (somente se NÃO tiver baixa)
# ----------------------------------------------------------------------
@bp_receber.route("/titulos/<int:id_recebivel>/excluir", methods=["POST"])
def excluir_titulo(id_recebivel: int):
    session = get_session()

    titulo = (
        session.query(Recebivel)
        .filter(Recebivel.id_recebivel == id_recebivel, Recebivel.deleted.is_(False))
        .first()
    )
    if not titulo:
        session.close()
        flash("Título não encontrado.", "erro")
        return redirect(url_for("receber.listar_titulos"))

    tem_baixa = (
        session.query(Recebimento.id_baixa)
        .filter(Recebimento.deleted.is_(False), Recebimento.id_recebivel == id_recebivel)
        .first()
        is not None
    )
    if tem_baixa:
        session.close()
        flash("Não é possível excluir um título que possui baixa (mesmo parcial).", "erro")
        return redirect(url_for("receber.listar_titulos"))

    titulo.deleted = True
    session.commit()
    session.close()

    flash("Título excluído com sucesso.", "sucesso")
    return redirect(url_for("receber.listar_titulos"))


# ----------------------------------------------------------------------
# BAIXAR TÍTULO
# ----------------------------------------------------------------------
@bp_receber.route("/titulos/<int:id_recebivel>/baixar", methods=["GET", "POST"])
def baixar_titulo(id_recebivel: int):
    session = get_session()

    titulo = (
        session.query(Recebivel)
        .options(
            joinedload(Recebivel.credor),
            joinedload(Recebivel.empresa),
            joinedload(Recebivel.plano),
            joinedload(Recebivel.documento),
        )
        .filter(Recebivel.id_recebivel == id_recebivel, Recebivel.deleted.is_(False))
        .first()
    )
    if not titulo:
        session.close()
        flash("Título não encontrado.", "erro")
        return redirect(url_for("receber.listar_titulos"))

    parcela_criada = _garantir_parcela_unica(session, titulo)
    session.flush()
    if parcela_criada:
        session.commit()
    saldo_aberto = _receber_titulo_saldo_aberto(session, id_recebivel)
    parcelas_view = _parcelas_baixa_view(session, id_recebivel)

    contas = (
        session.query(Conta)
        .filter(
            Conta.deleted.is_(False),
            Conta.id_empresa == titulo.id_empresa,
        )
        .order_by(Conta.descricao)
        .all()
    )
    contas_view = [{"id": c.id_conta, "descricao": c.descricao, "id_empresa": c.id_empresa} for c in contas]

    if request.method == "POST":
        data_baixa = _parse_date(request.form.get("data"))
        id_conta = request.form.get("id_conta", type=int)
        id_parcela = request.form.get("id_parcela", type=int)
        valor_recebido = _parse_float(request.form.get("valor_recebido"))
        parcela = _buscar_parcela_baixa(session, id_recebivel, id_parcela)
        saldo_parcela = _saldo_parcela(session, id_recebivel, id_parcela) if parcela else 0.0

        erros = []
        if not titulo.id_empresa:
            erros.append("Título sem empresa vinculada não pode ser baixado.")
        if not data_baixa:
            erros.append("Data da baixa inválida.")
        if not parcela:
            erros.append("Parcela da baixa inválida.")
        if valor_recebido is None or valor_recebido <= 0:
            erros.append("Valor da baixa inválido.")
        if valor_recebido is not None and valor_recebido > saldo_parcela + 0.0001:
            erros.append(f"Valor da baixa não pode ser maior que o saldo da parcela (R$ {saldo_parcela:.2f}).")

        erros_conta, conta = validar_conta_da_empresa(session, id_conta, titulo.id_empresa)
        erros.extend(erros_conta)

        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            bx = Recebimento(
                data=data_baixa,
                id_conta=conta.id_conta,
                id_recebivel=id_recebivel,
                id_parcela=parcela.id_parcela,
                valor_recebido=valor_recebido,
            )
            session.add(bx)
            session.commit()
            session.close()
            flash("Recebimento registrada com sucesso!", "sucesso")
            return redirect(url_for("receber.listar_baixas_titulo", id_recebivel=id_recebivel))

    receber_titulo_view = {
        "id": titulo.id_recebivel,
        "nr_documento": titulo.nr_documento,
        "credor": titulo.credor.nome if titulo.credor else "",
        "empresa": f"{titulo.empresa.codigo} - {titulo.empresa.nome}" if titulo.empresa else "",
        "plano": f"{titulo.plano.cod_estrutural} - {titulo.plano.nome_conta}" if titulo.plano else "",
        "valor": float(titulo.valor or 0),
        "saldo_aberto": float(saldo_aberto or 0),
    }
    session.close()
    return render_template(
        "receber_titulo_baixa_form.html",
        titulo=receber_titulo_view,
        contas=contas_view,
        parcelas=parcelas_view,
        hoje=date.today().isoformat(),
    )


# ----------------------------------------------------------------------
# LISTAR BAIXAS DO TÍTULO
# ----------------------------------------------------------------------
@bp_receber.route("/titulos/<int:id_recebivel>/baixas")
def listar_baixas_titulo(id_recebivel: int):
    session = get_session()
    id_baixa_destacada = request.args.get("baixa", type=int)

    titulo = (
        session.query(Recebivel)
        .options(joinedload(Recebivel.credor), joinedload(Recebivel.documento))
        .filter(Recebivel.id_recebivel == id_recebivel, Recebivel.deleted.is_(False))
        .first()
    )
    if not titulo:
        session.close()
        flash("Título não encontrado.", "erro")
        return redirect(url_for("receber.listar_titulos"))

    baixas = (
        session.query(Recebimento)
        .options(joinedload(Recebimento.conta), joinedload(Recebimento.parcela))
        .filter(Recebimento.deleted.is_(False), Recebimento.id_recebivel == id_recebivel)
        .order_by(Recebimento.data.desc(), Recebimento.id_baixa.desc())
        .all()
    )

    baixas_view = []
    total = 0.0
    for b in baixas:
        v = float(b.valor_recebido or 0)
        total += v
        baixas_view.append(
            {
                "id_baixa": b.id_baixa,
                "data": b.data.strftime("%d/%m/%Y") if b.data else "",
                "conta": b.conta.descricao if b.conta else "",
                "parcela": (
                    f"{b.parcela.numero_parcela} - {b.parcela.vencimento.strftime('%d/%m/%Y')}"
                    if getattr(b, "parcela", None) and b.parcela.vencimento
                    else "Legada sem parcela"
                ),
                "valor": v,
                "conciliado": bool(getattr(b, "conciliado", False)),
            }
        )

    saldo_aberto = _receber_titulo_saldo_aberto(session, id_recebivel)
    session.close()
    return render_template(
        "receber_titulo_baixas_list.html",
        titulo={
            "id": titulo.id_recebivel,
            "nr_documento": titulo.nr_documento,
            "credor": titulo.credor.nome if titulo.credor else "",
            "valor": float(titulo.valor or 0),
        },
        baixas=baixas_view,
        total_baixas=total,
        saldo_aberto=saldo_aberto,
        id_baixa_destacada=id_baixa_destacada,
    )


# ----------------------------------------------------------------------
# EXCLUIR BAIXA (somente se NÃO conciliada)
# ----------------------------------------------------------------------
@bp_receber.route(
    "/titulos/<int:id_recebivel>/baixas/<int:id_baixa>/excluir",
    methods=["POST"],
)
def excluir_baixa(id_recebivel: int, id_baixa: int):
    session = get_session()

    bx = (
        session.query(Recebimento)
        .filter(
            Recebimento.id_baixa == id_baixa,
            Recebimento.id_recebivel == id_recebivel,
            Recebimento.deleted.is_(False),
        )
        .first()
    )
    if not bx:
        session.close()
        flash("Recebimento não encontrada para o título informado.", "erro")
        return redirect(url_for("receber.listar_baixas_titulo", id_recebivel=id_recebivel))

    if bool(getattr(bx, "conciliado", False)):
        session.close()
        flash("Não é possível excluir uma baixa conciliada.", "erro")
        return redirect(url_for("receber.listar_baixas_titulo", id_recebivel=id_recebivel))

    bx.deleted = True
    session.commit()
    session.close()

    flash("Recebimento excluída com sucesso.", "sucesso")
    return redirect(url_for("receber.listar_baixas_titulo", id_recebivel=id_recebivel))


# ----------------------------------------------------------------------
# DOWNLOAD / EXCLUIR ANEXO
# (mantive nomes '..._titulo' para bater com seu template)
# ----------------------------------------------------------------------
@bp_receber.route("/titulos/anexos/<int:id_anexo>/download")
def download_anexo_titulo(id_anexo: int):
    return download_anexo(id_anexo)


@bp_receber.route("/titulos/anexos/<int:id_anexo>/excluir", methods=["POST", "GET"])
def excluir_anexo_titulo(id_anexo: int):
    # teu template usa <a href>, então aceitamos GET também
    return excluir_anexo(id_anexo)


@bp_receber.route("/anexos/<int:id_anexo>/download")
def download_anexo(id_anexo: int):
    session = get_session()
    an = (
        session.query(RecebivelAnexo)
        .filter(RecebivelAnexo.id_anexo == id_anexo, RecebivelAnexo.deleted.is_(False))
        .first()
    )
    if not an:
        session.close()
        flash("Anexo não encontrado.", "erro")
        return redirect(url_for("receber.listar_titulos"))

    path = getattr(an, "caminho_arquivo", None) or ""
    nome = an.nome_arquivo or "anexo"
    session.close()

    if not path or not os.path.exists(path):
        flash("Arquivo físico do anexo não foi encontrado.", "erro")
        return redirect(url_for("receber.listar_titulos"))

    return send_file(path, as_attachment=True, download_name=nome)


@bp_receber.route("/anexos/<int:id_anexo>/excluir", methods=["POST", "GET"])
def excluir_anexo(id_anexo: int):
    session = get_session()
    an = (
        session.query(RecebivelAnexo)
        .filter(RecebivelAnexo.id_anexo == id_anexo, RecebivelAnexo.deleted.is_(False))
        .first()
    )
    if not an:
        session.close()
        flash("Anexo não encontrado.", "erro")
        return redirect(url_for("receber.listar_titulos"))

    id_recebivel = an.id_recebivel
    an.deleted = True
    session.commit()
    session.close()

    flash("Anexo excluído com sucesso.", "sucesso")
    return redirect(url_for("receber.editar_titulo", id_recebivel=id_recebivel))
