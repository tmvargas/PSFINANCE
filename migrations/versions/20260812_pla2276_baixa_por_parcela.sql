-- PLA-2276 - Vincular baixas de titulos a parcelas
-- Script preparado para staging. Nao executar em producao sem autorizacao
-- expressa de Thiago e pacote de producao aprovado.

BEGIN;

ALTER TABLE baixa
    ADD COLUMN IF NOT EXISTS id_parcela INTEGER REFERENCES titulo_parcela (id_parcela);

CREATE INDEX IF NOT EXISTS ix_baixa_parcela_ativo
    ON baixa (id_parcela)
    WHERE deleted = FALSE;

UPDATE baixa b
   SET id_parcela = p.id_parcela,
       updated_at = NOW()
  FROM (
        SELECT id_titulo, MIN(id_parcela) AS id_parcela
          FROM titulo_parcela
         WHERE deleted = FALSE
         GROUP BY id_titulo
        HAVING COUNT(*) = 1
       ) p
 WHERE b.id_titulo = p.id_titulo
   AND b.id_parcela IS NULL
   AND b.deleted = FALSE;

COMMIT;
