from models import CentroCusto, Empresa


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
