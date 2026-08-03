# PLA-1062 - Reentrega do pacote de producao PSFINANCE

Data da reentrega: 2026-08-03

## Objetivo

Reentregar o Pacote de Producao do PSFINANCE em subtarefa com fluxo nativo de
revisao executiva do CEO, corrigindo a falha administrativa da `PLA-1010`.

A `PLA-1010` possui pacote tecnico valido, mas foi criada sem
`executionPolicy` com stage de `review` para o CEO. A `PLA-1062` substitui esse
fluxo administrativo para permitir decisao executiva nativa antes de qualquer
pedido de autorizacao a Thiago.

## Skills consultadas

- `plansmart-governanca-desenvolvimento`
- `plansmart-projeto-psfinance`
- `plansmart-projeto-vps-sistemas`

## Limite operacional

Esta reentrega nao autoriza:

- merge da `staging` na `main`;
- push na `main`;
- deploy em producao;
- criacao, alteracao ou escrita no banco produtivo;
- migration produtiva;
- reinicio de servico produtivo;
- copia de dados de `staging` para producao.

## Fluxo administrativo validado

- Issue valida para revisao executiva: `PLA-1062`.
- `executionPolicy`: presente na `PLA-1062`.
- Stage nativo: `review`.
- Revisor configurado: CEO, agente `46cfee48-443f-409f-bd1d-60c1c0c73771`.
- Aprovacoes exigidas: 1.
- Issue anterior com pacote tecnico reaproveitado: `PLA-1010`.
- Motivo da substituicao: a `PLA-1010` nao possui `executionPolicy` nativa e o
  Paperclip recusou `in_review` com `invalid_issue_disposition`.

## GitHub e branches

- Repositorio oficial: `https://github.com/tmvargas/PSFINANCE.git`.
- Branch de producao analisada: `origin/main`.
- Commit atual da `main`: `23821c7786e98c5c489c60c2ac60760e3cdc17c1`.
- Branch de teste analisada: `origin/staging`.
- Commit atual da `staging`: `e0c434bbfb8573daba3ff9d0fdfc730afb65a971`.
- Branch do pacote anterior: `docs/PLA-1010-plano-producao`.
- Commit do pacote anterior: `5cd69d60153e213aa81414507307f0c303c969d1`.
- PR do pacote anterior: `https://github.com/tmvargas/PSFINANCE/pull/12`.
- Estado do PR #12 em 2026-08-03: aberto, base `staging`, head
  `docs/PLA-1010-plano-producao`, ainda nao mergeado.

Observacao de governanca: o commit `5cd69d60153e213aa81414507307f0c303c969d1`
nao esta contido em `origin/staging`. Por isso, a reentrega da `PLA-1062`
atualiza o pacote documental para o commit atual da `staging`, sem considerar o
PR #12 como ja publicado em staging.

## Staging e porta 5001

Validacoes executadas em 2026-08-03:

- `http://vps69143.publiccloud.com.br:5001/staging/psfinance/health`: HTTP 200.
- `http://vps69143.publiccloud.com.br:5001/gate`: HTTP 200.
- `http://vps69143.publiccloud.com.br:5001/staging/psfinance`: HTTP 200.
- `http://vps69143.publiccloud.com.br:5001/staging/psfinance/financeiro/`:
  HTTP 200.

Resposta tecnica confirmada na porta `5001`:

- `app=PSFINANCE`;
- `branch=staging`;
- `commit=e0c434bbfb8573daba3ff9d0fdfc730afb65a971`;
- `db_dialect=postgresql`;
- `database_url_source=PSFINANCE_STAGING_DATABASE_URL`;
- `environment=staging-gate`;
- `status=healthy`.

## Diferenca atual entre main e staging

Comando executado:

```bash
git diff --shortstat origin/main..origin/staging
```

Resultado:

```text
75 files changed, 9719 insertions(+), 3 deletions(-)
```

O escopo atual da `staging` inclui, alem do pacote funcional de staging e
PostgreSQL ja analisado na `PLA-1010`, entregas documentais e visuais
posteriores das tarefas `PLA-1019`, `PLA-1022`, `PLA-1027`, `PLA-1031`,
`PLA-1036` e `PLA-1043`.

Se Thiago autorizar producao, o escopo exato deve ser congelado novamente no
commit aprovado da `staging`. Qualquer novo commit em `staging` apos esta
reentrega invalida a autorizacao anterior e exige nova analise.

## Banco de dados

Fatos reaproveitados da `PLA-1010` e `PLA-1005`:

- Staging usa PostgreSQL.
- Fonte da URL do banco em staging: `PSFINANCE_STAGING_DATABASE_URL`.
- Estrutura esperada:
  - `documento`;
  - `plano_de_contas`;
  - `credor`;
  - `conta`;
  - `titulo`;
  - `titulo_anexo`;
  - `baixa`;
  - `movimentacao_conta`.
- Script versionado de migracao: `scripts/migrate_sqlite_to_postgres.py`.

Separacao obrigatoria para producao:

- Estrutura de banco: tabelas, chaves, colunas e sequences previstas nos
  modelos.
- Dados obrigatorios de configuracao: `documento` e `plano_de_contas` podem ser
  necessarios para operacao inicial, mas precisam de validacao explicita antes
  de carga produtiva.
- Dados operacionais: contas, credores, titulos, anexos, baixas e movimentacoes
  devem ser preservados em producao por padrao.

Pergunta obrigatoria para Thiago antes de qualquer acao produtiva com banco:

```text
Migrar dados de staging para producao ou preservar os dados operacionais existentes em producao?
```

Recomendacao tecnica padrao do GDSIS: preservar os dados operacionais de
producao. Qualquer copia de `staging` para producao exige autorizacao separada,
com origem, destino, volume, motivo, impacto, backup e rollback.

## Validacao tecnica

- `python3 -m py_compile src/app.py database.py models.py scripts/migrate_sqlite_to_postgres.py`:
  OK.
- `git diff --check origin/main..origin/staging`: encontrou trailing whitespace
  preexistente em arquivos do escopo atual da `staging`; nao foi corrigido
  nesta reentrega para nao misturar refatoracao/formatação com pacote de
  producao.
- Rotas criticas de staging na porta `5001`: OK conforme secao de staging.

## Plano de deploy produtivo proposto

Executar somente apos autorizacao expressa de Thiago, com escopo e commits
congelados:

1. Revalidar que `origin/staging` esta no commit autorizado.
2. Revalidar que `origin/main` esta no commit analisado ou refazer o pacote se
   a `main` mudou.
3. Abrir ou aprovar PR de `staging` para `main`, conforme autorizacao de
   Thiago.
4. Preparar backup do banco produtivo real, quando existir.
5. Publicar a `main` no diretorio produtivo planejado do PSFINANCE.
6. Configurar variaveis produtivas somente por nomes de segredo, sem registrar
   valores.
7. Subir Gunicorn por servico produtivo isolado, atras do Nginx.
8. Validar healthcheck produtivo, rotas financeiras criticas e logs.
9. Registrar commit anterior, novo commit, horario, backup, scripts, servicos,
   banco, validacoes e incidentes.

## Rollback proposto

1. Interromper o servico produtivo do PSFINANCE se houver incidente critico.
2. Restaurar o commit produtivo anterior da `main` ou reverter o merge
   autorizado.
3. Restaurar backup do banco somente se houve alteracao produtiva autorizada no
   banco.
4. Revalidar healthcheck, rotas criticas e logs.
5. Registrar incidente, causa, rollback executado e pendencias.

## Riscos e pendencias

- Producao segue bloqueada ate autorizacao expressa de Thiago.
- O PR #12 esta aberto e nao mergeado; a revisao executiva deve usar a
  `PLA-1062` como caminho administrativo valido.
- A `staging` avancou depois da `PLA-1010`; o pacote produtivo precisa ser
  congelado no commit exato aprovado antes de qualquer execucao.
- Existem trailing whitespaces preexistentes no diff `main..staging`; isso e
  risco baixo para execucao, mas deve ser considerado em revisao de qualidade
  antes de producao.

## Recomendacao do GDSIS

Recomenda com ressalvas.

O ambiente de staging do PSFINANCE esta saudavel na porta `5001`, usando
PostgreSQL e branch `staging`, mas a promocao para producao deve aguardar:

- revisao executiva nativa do CEO nesta `PLA-1062`;
- decisao do CEO sobre encaminhar ou nao o pedido a Thiago;
- autorizacao expressa de Thiago para `main`, producao e qualquer acao em banco
  produtivo;
- congelamento do commit exato da `staging` a ser promovido.
