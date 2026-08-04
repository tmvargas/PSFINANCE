# PLA-1290 - Backfill empresa 1 centro 1001 nos lancamentos PSFINANCE

## Objetivo

Preparar o backfill dos lancamentos historicos do PSFINANCE para vincular
`empresa` codigo `1` e `centro de custo` codigo `1001` aos registros ativos de
`titulo` e `movimentacao_conta` que ainda estejam sem empresa ou centro de
custo.

## Regra aplicada

- A empresa deve existir como registro ativo com `codigo = '1'`.
- O centro de custo deve existir como registro ativo com `codigo = '1001'` e
  pertencer a empresa encontrada.
- O script aborta se houver ausencia ou ambiguidade nesses cadastros.
- Apenas registros ativos com `id_empresa` ou `id_centro_custo` ausente sao
  atualizados.
- Registros ja vinculados integralmente a empresa e centro de custo nao sao
  alterados.
- Registros com `deleted = TRUE` nao sao alterados.

## Arquitetura

- `migrations/versions/20260804_pla1290_backfill_empresa_1_centro_1001.sql`
  concentra o script SQL versionado para PostgreSQL.
- Nao houve alteracao em controllers, services, repositories, models,
  templates ou CSS, porque a regra de obrigatoriedade para novos lancamentos ja
  esta centralizada em `financeiro/regras_empresa_centro.py` e aplicada nas
  rotas de titulos e movimentacoes pela PLA-1235.

## Validacao planejada em staging

Executar primeiro uma conferencia de escopo:

```sql
SELECT COUNT(*) AS titulos_pendentes
  FROM titulo
 WHERE deleted = FALSE
   AND (id_empresa IS NULL OR id_centro_custo IS NULL);

SELECT COUNT(*) AS movimentacoes_pendentes
  FROM movimentacao_conta
 WHERE deleted = FALSE
   AND (id_empresa IS NULL OR id_centro_custo IS NULL);
```

Depois executar o script:

```bash
psql "$PSFINANCE_STAGING_DATABASE_URL" \
  -f migrations/versions/20260804_pla1290_backfill_empresa_1_centro_1001.sql
```

Conferir o resultado:

```sql
SELECT COUNT(*) AS titulos_pendentes
  FROM titulo
 WHERE deleted = FALSE
   AND (id_empresa IS NULL OR id_centro_custo IS NULL);

SELECT COUNT(*) AS movimentacoes_pendentes
  FROM movimentacao_conta
 WHERE deleted = FALSE
   AND (id_empresa IS NULL OR id_centro_custo IS NULL);
```

Resultado esperado: `0` pendencias ativas nas duas consultas, desde que os
cadastros de empresa codigo `1` e centro codigo `1001` existam em staging.

## Validacao executada em staging

Data: 2026-08-04.

- Branch publicada na VPS de teste: `staging`.
- Commit publicado na VPS de teste: `caed622c4d0b206590a69b36597e8fdcc69e24a8`.
- Banco validado pela aplicacao: PostgreSQL via `PSFINANCE_STAGING_DATABASE_URL`
  no servico de staging, com valor omitido.
- Empresa ativa `codigo = '1'`: 1 registro, `id_empresa = 1`.
- Centro de custo ativo `codigo = '1001'` para a empresa `1`: 1 registro,
  `id_centro_custo = 1`.
- Colunas confirmadas em `titulo`: `id_empresa` e `id_centro_custo`.
- Colunas confirmadas em `movimentacao_conta`: `id_empresa` e
  `id_centro_custo`.

Contagens do backfill:

| Verificacao | Titulos | Movimentacoes |
| --- | ---: | ---: |
| Registros ativos pendentes antes | 54 | 90 |
| Registros ativos pendentes depois | 0 | 0 |
| Registros ativos com empresa e centro depois | 54 | 90 |
| Registros inativos fora do escopo com nulos | 4 | 4 |

Execucao do script:

```text
BACKFILL_SEGUNDOS=0.049
```

Validacao das rotas e listagens pela porta corporativa `5001`:

| Rota | Resultado |
| --- | --- |
| `/staging/psfinance` | HTTP 200 |
| `/staging/psfinance/financeiro/` | HTTP 200 |
| `/staging/psfinance/financeiro/titulos` | HTTP 200, colunas Empresa e Centro de Custo presentes, registros exibindo centro `1001` |
| `/staging/psfinance/financeiro/movimentacoes` | HTTP 200, colunas Empresa e Centro de Custo presentes, 90 ocorrencias de `1001` na listagem |
| `/staging/psfinance/financeiro/empresas` | HTTP 200 |
| `/staging/psfinance/financeiro/centros-custo` | HTTP 200 |
| `/staging/psfinance/health` | HTTP 200 |
| `/staging/psfinance/gate` | HTTP 200, `status=healthy`, `branch=staging`, `commit=caed622c4d0b206590a69b36597e8fdcc69e24a8`, `db_dialect=postgresql` |

Logs recentes dos servicos `psfinance-staging` e `psfinance-staging-gate`
foram verificados apos o restart e registraram inicializacao do Gunicorn sem
erro critico de aplicacao ou banco.

## Impacto e limites

Este pacote apenas prepara o backfill para staging. Nao executa escrita em
producao, nao altera `main`, nao copia dados entre ambientes e nao transforma
as colunas em obrigatorias no banco.
