BEGIN;

ALTER TABLE conta ADD COLUMN IF NOT EXISTS dia_vencimento_cartao INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_conta_dia_vencimento_cartao') THEN
        ALTER TABLE conta ADD CONSTRAINT ck_conta_dia_vencimento_cartao
            CHECK (dia_vencimento_cartao IS NULL OR dia_vencimento_cartao BETWEEN 1 AND 31);
    END IF;
END $$;

COMMIT;
