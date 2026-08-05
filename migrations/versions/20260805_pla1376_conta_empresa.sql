-- PLA-1376 - Vincular contas a empresa no PSFINANCE

BEGIN;

ALTER TABLE conta
    ADD COLUMN IF NOT EXISTS id_empresa INTEGER REFERENCES empresa (id_empresa);

DO $$
DECLARE
    v_id_empresa INTEGER;
    v_empresas_ativas INTEGER;
    v_contas_sem_empresa INTEGER;
BEGIN
    SELECT count(*)
      INTO v_contas_sem_empresa
      FROM conta
     WHERE id_empresa IS NULL;

    IF v_contas_sem_empresa > 0 THEN
        SELECT count(*)
          INTO v_empresas_ativas
          FROM empresa
         WHERE codigo = '1'
           AND deleted IS FALSE;

        IF v_empresas_ativas <> 1 THEN
            RAISE EXCEPTION
                'Migration PLA-1376 abortada: esperado exatamente 1 empresa ativa com codigo 1 para vincular % contas sem empresa, encontrado %.',
                v_contas_sem_empresa,
                v_empresas_ativas;
        END IF;

        SELECT id_empresa
          INTO v_id_empresa
          FROM empresa
         WHERE codigo = '1'
           AND deleted IS FALSE;

        UPDATE conta
           SET id_empresa = v_id_empresa
         WHERE id_empresa IS NULL;
    END IF;
END $$;

ALTER TABLE conta
    ALTER COLUMN id_empresa SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_conta_empresa_ativo
    ON conta (id_empresa)
    WHERE deleted IS FALSE;

COMMIT;
