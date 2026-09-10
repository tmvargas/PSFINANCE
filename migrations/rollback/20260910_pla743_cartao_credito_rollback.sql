BEGIN;

ALTER TABLE conta DROP CONSTRAINT IF EXISTS ck_conta_dia_vencimento_cartao;
ALTER TABLE conta DROP COLUMN IF EXISTS dia_vencimento_cartao;

COMMIT;
