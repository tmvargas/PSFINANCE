\set ON_ERROR_STOP on

-- PLA-2612 — pre-validacao somente leitura do PostgreSQL isolado/efemero.
-- Este script nao cria fixtures, nao altera schema e nao executa DML/DDL.
-- Uso proposto, somente apos informar explicitamente o banco isolado:
--   psql --dbname "$PLA2612_DATABASE_URL" \
--     --set=expected_database=psfinance_pla2612_isolado \
--     --file scripts/sql/PLA-2612_prevalidacao_postgresql_isolado.sql

BEGIN TRANSACTION READ ONLY;
SET LOCAL statement_timeout = '5s';
SET LOCAL lock_timeout = '1s';
SET LOCAL idle_in_transaction_session_timeout = '10s';
SET LOCAL pla2612.expected_database = :'expected_database';

SELECT current_database() AS banco_atual,
       current_user AS usuario_atual,
       current_setting('transaction_read_only') AS transacao_somente_leitura,
       clock_timestamp() AS iniciado_em_utc;

-- Falha fechada: o nome deve ser fornecido e deve corresponder ao banco atual.
DO $pla2612$
DECLARE
  banco_esperado text := current_setting('pla2612.expected_database', true);
BEGIN
  IF banco_esperado IS NULL OR banco_esperado = '' THEN
    RAISE EXCEPTION 'expected_database nao informado';
  END IF;
  IF current_database() <> banco_esperado THEN
    RAISE EXCEPTION 'banco atual (%) difere do esperado (%)',
      current_database(), banco_esperado;
  END IF;
  IF current_database() IN ('psfinance_staging', 'psfinance_prod') THEN
    RAISE EXCEPTION 'banco operacional/produtivo proibido para a matriz PLA-2612: %',
      current_database();
  END IF;
END
$pla2612$;

SELECT 'BANCO_ISOLADO_OK' AS gate_banco_isolado;

-- Schema e nulabilidade exigidos pelo fluxo de titulo, parcela e baixa.
WITH esperado(tabela, coluna, tipo, nullable) AS (
  VALUES
    ('titulo', 'id_titulo', 'integer', 'NO'),
    ('titulo', 'deleted', 'boolean', 'NO'),
    ('titulo_parcela', 'id_parcela', 'integer', 'NO'),
    ('titulo_parcela', 'id_titulo', 'integer', 'NO'),
    ('titulo_parcela', 'numero_parcela', 'integer', 'NO'),
    ('titulo_parcela', 'valor', 'numeric', 'NO'),
    ('titulo_parcela', 'deleted', 'boolean', 'NO'),
    ('baixa', 'id_baixa', 'integer', 'NO'),
    ('baixa', 'id_titulo', 'integer', 'NO'),
    ('baixa', 'id_parcela', 'integer', 'YES'),
    ('baixa', 'valor_baixa', 'numeric', 'NO'),
    ('baixa', 'conciliado', 'boolean', 'NO'),
    ('baixa', 'deleted', 'boolean', 'NO')
), encontrado AS (
  SELECT table_name AS tabela,
         column_name AS coluna,
         data_type AS tipo,
         is_nullable AS nullable
    FROM information_schema.columns
   WHERE table_schema = 'public'
     AND table_name IN ('titulo', 'titulo_parcela', 'baixa')
)
SELECT e.tabela,
       e.coluna,
       e.tipo AS tipo_esperado,
       f.tipo AS tipo_encontrado,
       e.nullable AS nulabilidade_esperada,
       f.nullable AS nulabilidade_encontrada,
       (f.coluna IS NOT NULL
        AND f.tipo = e.tipo
        AND f.nullable = e.nullable) AS conforme
  FROM esperado e
  LEFT JOIN encontrado f USING (tabela, coluna)
 ORDER BY e.tabela, e.coluna;

-- Volume atual do banco isolado. A matriz autorizavel adicionara menos de
-- 20 registros sinteticos no total e sera descartada integralmente ao final.
SELECT 'titulo' AS tabela, count(*) AS registros FROM titulo
UNION ALL
SELECT 'titulo_parcela', count(*) FROM titulo_parcela
UNION ALL
SELECT 'baixa', count(*) FROM baixa;

-- Evidencia de locks/esperas no banco alvo sem expor texto de consultas.
SELECT a.pid,
       a.state,
       a.wait_event_type,
       a.wait_event,
       age(clock_timestamp(), a.xact_start) AS duracao_transacao,
       l.locktype,
       l.mode,
       l.granted
  FROM pg_stat_activity a
  LEFT JOIN pg_locks l ON l.pid = a.pid
 WHERE a.datname = current_database()
   AND a.pid <> pg_backend_pid()
 ORDER BY a.pid, l.granted, l.locktype, l.mode;

SELECT clock_timestamp() AS concluido_em_utc,
       'PREVALIDACAO_READ_ONLY_CONCLUIDA' AS resultado;

ROLLBACK;
