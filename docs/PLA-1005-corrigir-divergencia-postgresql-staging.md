# PLA-1005 - Correcao da divergencia PostgreSQL no staging do PSFINANCE

Data da analise: 2026-08-02

## Objetivo

Corrigir a divergencia identificada na PLA-1004 sobre o banco do staging do
PSFINANCE e deixar evidencia oficial, sem expor segredos, de qual backend de
banco a aplicacao em execucao esta usando.

## Skills consultadas

- `plansmart-governanca-desenvolvimento`
- `plansmart-projeto-psfinance`
- `plansmart-projeto-vps-sistemas`

## Fatos confirmados

- A VPS Sistemas respondeu por SSH usando a chave dedicada
  `/paperclip/.ssh/plansmart_sistemas_vps69143`.
- O repositorio de staging na VPS esta na branch `staging`, limpo e alinhado ao
  `origin/staging`.
- Os servicos `psfinance-staging.service` e `psfinance-staging-gate.service`
  estavam ativos.
- O processo Gunicorn ativo possui as variaveis
  `PSFINANCE_STAGING_DATABASE_URL` e `PSFINANCE_DATABASE_URL` definidas, sem
  valores registrados neste documento.
- O PostgreSQL local esta ativo e existem o banco `psfinance_staging` e o
  usuario `psfinance_staging_app`.

## Causa da divergencia

A leitura da PLA-1004 executou uma verificacao manual sem carregar o
`EnvironmentFile` do systemd. Nessa condicao, `database.py` cai corretamente no
fallback SQLite local. Quando o mesmo arquivo de ambiente do servico e
carregado, a aplicacao usa PostgreSQL.

Para impedir nova evidencia ambigua, a aplicacao passa a expor em `/health` e
`/gate` apenas metadados nao sensiveis do banco:

- `db_dialect`;
- `database_url_source`.

Nenhuma URL, senha, token ou conteudo de `.env` e retornado.

## Contagens validadas com PostgreSQL

Com o `EnvironmentFile` de staging carregado, a aplicacao retornou:

| Tabela | Registros |
| --- | ---: |
| `documento` | 5 |
| `plano_de_contas` | 41 |
| `credor` | 12 |
| `conta` | 9 |
| `titulo` | 47 |
| `titulo_anexo` | 28 |
| `baixa` | 37 |
| `movimentacao_conta` | 94 |

## Validacao esperada apos deploy da staging

```bash
curl -sS http://127.0.0.1:5001/staging/psfinance/health
curl -sS http://127.0.0.1:5001/gate
```

Resultado esperado nos JSONs:

```text
db_dialect=postgresql
database_url_source=PSFINANCE_STAGING_DATABASE_URL
```

## Limites

- Esta tarefa nao autoriza producao.
- Nenhuma escrita foi executada no banco produtivo.
- Nenhum valor secreto foi documentado.
