# PLA-1359 - Layout da consulta de titulos a pagar

## Projeto

PSFINANCE.

## Demanda atendida

Melhorar o layout da consulta de Titulos a Pagar do PSFINANCE, vinculada a
`PLA-1179`.

## Regra aplicada

A alteracao ficou restrita a camada de apresentacao. Foram preservados:

- filtro por mes e ano de vencimento;
- calculo de valor original, baixado e saldo em aberto;
- acoes existentes de baixar, consultar baixas, editar, copiar e excluir;
- rotas Flask existentes;
- backend, models, banco de dados e variaveis de ambiente.

## Arquitetura

Skills consultadas:

- `plansmart-governanca-desenvolvimento`;
- `plansmart-projeto-psfinance`;
- `plansmart-projeto-vps-sistemas`.

Arquivos por camada:

- Apresentacao: `templates/titulos_list.html`;
- Documentacao: `docs/decisoes.md` e este arquivo;
- Evidencia visual: `docs/mockups/evidencias/PLA-1359-titulos-desktop-com-dados.png`
  e `docs/mockups/evidencias/PLA-1359-titulos-mobile-com-dados.png`.

Nao houve alteracao em controllers, services, repositories, models, migrations
ou scripts de banco.

## O que foi alterado

- Cabeçalho da rotina passou a identificar `Contas a pagar` e
  `Consulta de titulos`.
- Filtro de vencimento passou para uma faixa propria com labels claras.
- Resumo financeiro passou a mostrar quantidade de titulos, valor original,
  valor baixado e saldo em aberto antes da tabela.
- Tabela passou a agrupar dados correlatos para reduzir largura operacional:
  documento e numero, credor e plano, empresa e centro, valores, status e acoes.
- Status visual `Aberto`/`Baixado` foi adicionado com base no saldo em aberto.
- Acoes por titulo foram agrupadas em menu para reduzir ruido horizontal.
- Estado vazio passou a ter mensagem contextual ao periodo filtrado.

## Validacao local

Com a branch da tarefa antes do merge:

```text
.venv/bin/python -m compileall src financeiro database.py models.py
```

Resultado: sucesso.

Renderizacao isolada com SQLite temporario criado fora do banco operacional:

```text
/financeiro/titulos 200 True True
/staging/psfinance/financeiro/titulos?mes=8&ano=2026 200 True True
```

`git diff --check`: sem apontamentos.

## Validacao visual

Base temporaria com dados ficticios criada fora do repositorio em `/tmp`.

Evidencias:

- `docs/mockups/evidencias/PLA-1359-titulos-desktop-com-dados.png`;
- `docs/mockups/evidencias/PLA-1359-titulos-mobile-com-dados.png`.

Resultado observado:

- desktop com filtros, resumo, tabela, status e acoes visiveis;
- mobile com cabecalho, filtros e resumo empilhados sem sobreposicao;
- tabela permanece dentro de `table-responsive` para telas estreitas.

## Validacao em staging

Branch da tarefa:

```text
pla-1359-layout-consulta-titulos-pagar
```

Commit da tarefa:

```text
9f174fb
```

Deploy de staging executado na VPS Sistemas a partir da branch `staging`.

Evidencia apos deploy:

```text
APP_SERVICE=active
GATE_SERVICE=active
HEAD=fdbe81a67f17c30c3aaaa88d8e599b05db67c5dd
STATUS_LINES=0
HEALTH_HTTP_STATUS=200
GATE_HTTP_STATUS=200
TITULOS_HTTP_STATUS=200
```

Validacao publica pela porta corporativa `5001`:

```text
PUBLIC_TITULOS_HTTP_STATUS=200
```

Gate publico:

```json
{
  "app": "PSFINANCE",
  "base_path": "/staging/psfinance",
  "branch": "staging",
  "commit": "fdbe81a67f17c30c3aaaa88d8e599b05db67c5dd",
  "database_url_source": "PSFINANCE_STAGING_DATABASE_URL",
  "db_dialect": "postgresql",
  "environment": "staging-gate",
  "status": "healthy"
}
```

Logs recentes dos servicos `psfinance-staging.service` e
`psfinance-staging-gate.service` registraram restart do Gunicorn sem erro
critico de inicializacao.

## Limites

Nao houve:

- migration;
- escrita em banco de producao;
- alteracao de `main`;
- deploy em producao;
- copia de dados entre ambientes;
- exposicao de segredo.

## Recomendacao do GDSIS

Recomendo revisao executiva do CEO no staging. Nao recomendo promocao para
producao sem pacote de producao especifico e autorizacao expressa aplicavel.

## Pendencia administrativa

A tentativa de comentar e mover a issue `PLA-1359` para `in_review` pela API
(Interface de Programacao de Aplicacoes) do Paperclip falhou com
`401 Unauthorized` usando o token de heartbeat disponivel no ambiente. O
bloqueio e administrativo do Paperclip; a entrega tecnica foi concluida,
publicada em `staging` e validada na porta `5001`.
