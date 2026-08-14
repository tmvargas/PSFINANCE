from models import CentroCusto, Conta, Empresa


FILTRO_EMPRESA_SESSION_KEY = "titulos_filtro_id_empresa"


def resolver_filtro_empresa_memorizado(empresas_view, request_args, session_storage):
    empresas_ativas = {empresa["id"] for empresa in empresas_view}

    if "id_empresa" in request_args:
        id_empresa_raw = (request_args.get("id_empresa") or "").strip()
        if not id_empresa_raw:
            session_storage.pop(FILTRO_EMPRESA_SESSION_KEY, None)
            return None

        try:
            id_empresa = int(id_empresa_raw)
        except (TypeError, ValueError):
            id_empresa = None

        if id_empresa in empresas_ativas:
            session_storage[FILTRO_EMPRESA_SESSION_KEY] = id_empresa
            return id_empresa

        session_storage.pop(FILTRO_EMPRESA_SESSION_KEY, None)
        return None

    id_empresa_memorizada = session_storage.get(FILTRO_EMPRESA_SESSION_KEY)
    try:
        id_empresa_memorizada = int(id_empresa_memorizada)
    except (TypeError, ValueError):
        session_storage.pop(FILTRO_EMPRESA_SESSION_KEY, None)
        return None

    if id_empresa_memorizada in empresas_ativas:
        return id_empresa_memorizada

    session_storage.pop(FILTRO_EMPRESA_SESSION_KEY, None)
    return None


def listar_empresas_centros_ativos(session):
    empresas = (
        session.query(Empresa)
        .filter(Empresa.deleted.is_(False))
        .order_by(Empresa.codigo, Empresa.nome)
        .all()
    )
    centros = (
        session.query(CentroCusto)
        .join(Empresa)
        .filter(CentroCusto.deleted.is_(False), Empresa.deleted.is_(False))
        .order_by(Empresa.codigo, CentroCusto.codigo, CentroCusto.nome)
        .all()
    )

    empresas_view = [
        {"id": empresa.id_empresa, "label": f"{empresa.codigo} - {empresa.nome}"}
        for empresa in empresas
    ]
    centros_view = [
        {
            "id": centro.id_centro_custo,
            "id_empresa": centro.id_empresa,
            "label": f"{centro.empresa.codigo} - {centro.codigo} - {centro.nome}",
        }
        for centro in centros
    ]
    return empresas_view, centros_view


def validar_empresa_centro(session, id_empresa, id_centro_custo):
    erros = []
    empresa = None
    centro = None

    if not id_empresa:
        erros.append("Empresa é obrigatória.")
    else:
        empresa = (
            session.query(Empresa)
            .filter(Empresa.id_empresa == id_empresa, Empresa.deleted.is_(False))
            .first()
        )
        if not empresa:
            erros.append("Empresa ativa não encontrada.")

    if not id_centro_custo:
        erros.append("Centro de custo é obrigatório.")
    else:
        centro = (
            session.query(CentroCusto)
            .filter(
                CentroCusto.id_centro_custo == id_centro_custo,
                CentroCusto.deleted.is_(False),
            )
            .first()
        )
        if not centro:
            erros.append("Centro de custo ativo não encontrado.")

    if empresa and centro and centro.id_empresa != empresa.id_empresa:
        erros.append("Centro de custo não pertence à empresa selecionada.")

    return erros, empresa, centro


def validar_empresa_ativa(session, id_empresa, mensagem_obrigatoria="Empresa é obrigatória."):
    erros = []
    empresa = None

    if not id_empresa:
        erros.append(mensagem_obrigatoria)
    else:
        empresa = (
            session.query(Empresa)
            .filter(Empresa.id_empresa == id_empresa, Empresa.deleted.is_(False))
            .first()
        )
        if not empresa:
            erros.append("Empresa ativa não encontrada.")

    return erros, empresa


def validar_conta_da_empresa(session, id_conta, id_empresa, mensagem_obrigatoria="Conta é obrigatória."):
    erros = []
    conta = None

    if not id_conta:
        erros.append(mensagem_obrigatoria)
        return erros, conta

    conta = (
        session.query(Conta)
        .filter(Conta.id_conta == id_conta, Conta.deleted.is_(False))
        .first()
    )
    if not conta:
        erros.append("Conta ativa não encontrada.")
        return erros, conta

    if id_empresa and conta.id_empresa != id_empresa:
        erros.append("Conta não pertence à empresa selecionada.")

    return erros, conta
