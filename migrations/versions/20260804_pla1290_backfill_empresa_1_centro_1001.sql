-- PLA-1290 - Backfill empresa 1 e centro 1001 nos lancamentos PSFINANCE
-- Script preparado para staging. Nao executar em producao sem autorizacao
-- expressa de Thiago e pacote de producao aprovado.

BEGIN;

DO $$
DECLARE
    v_id_empresa INTEGER;
    v_id_centro_custo INTEGER;
    v_empresas_ativas INTEGER;
    v_centros_ativos INTEGER;
    v_titulos_atualizados INTEGER;
    v_movimentacoes_atualizadas INTEGER;
BEGIN
    SELECT COUNT(*)
      INTO v_empresas_ativas
      FROM empresa
     WHERE codigo = '1'
       AND deleted = FALSE;

    IF v_empresas_ativas <> 1 THEN
        RAISE EXCEPTION
            'Backfill abortado: esperado exatamente 1 empresa ativa com codigo 1, encontrado %.',
            v_empresas_ativas;
    END IF;

    SELECT id_empresa
      INTO v_id_empresa
      FROM empresa
     WHERE codigo = '1'
       AND deleted = FALSE;

    SELECT COUNT(*)
      INTO v_centros_ativos
      FROM centro_custo
     WHERE id_empresa = v_id_empresa
       AND codigo = '1001'
       AND deleted = FALSE;

    IF v_centros_ativos <> 1 THEN
        RAISE EXCEPTION
            'Backfill abortado: esperado exatamente 1 centro de custo ativo codigo 1001 para a empresa %, encontrado %.',
            v_id_empresa,
            v_centros_ativos;
    END IF;

    SELECT id_centro_custo
      INTO v_id_centro_custo
      FROM centro_custo
     WHERE id_empresa = v_id_empresa
       AND codigo = '1001'
       AND deleted = FALSE;

    UPDATE titulo
       SET id_empresa = v_id_empresa,
           id_centro_custo = v_id_centro_custo,
           updated_at = NOW()
     WHERE deleted = FALSE
       AND (id_empresa IS NULL OR id_centro_custo IS NULL);

    GET DIAGNOSTICS v_titulos_atualizados = ROW_COUNT;

    UPDATE movimentacao_conta
       SET id_empresa = v_id_empresa,
           id_centro_custo = v_id_centro_custo,
           updated_at = NOW()
     WHERE deleted = FALSE
       AND (id_empresa IS NULL OR id_centro_custo IS NULL);

    GET DIAGNOSTICS v_movimentacoes_atualizadas = ROW_COUNT;

    RAISE NOTICE
        'Backfill PLA-1290 concluido: empresa %, centro %, titulos %, movimentacoes %.',
        v_id_empresa,
        v_id_centro_custo,
        v_titulos_atualizados,
        v_movimentacoes_atualizadas;
END $$;

COMMIT;
