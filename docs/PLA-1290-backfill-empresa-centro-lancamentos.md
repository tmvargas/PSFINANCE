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

## Impacto e limites

Este pacote apenas prepara o backfill para staging. Nao executa escrita em
producao, nao altera `main`, nao copia dados entre ambientes e nao transforma
as colunas em obrigatorias no banco.
