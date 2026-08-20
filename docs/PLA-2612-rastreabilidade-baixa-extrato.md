# PLA-2612 - Rastreabilidade e exclusao de baixa por parcela

## Diagnostico somente leitura em staging

Consulta executada em 2026-08-16 com transacao PostgreSQL explicitamente
configurada como somente leitura, usando data `13/08/2026`, valor `R$ 1,00` e
documento reportados na tarefa.

- Titulo identificado: `id_titulo=60`, documento `AV - Aviso de lancamento - teste`.
- Baixa ativa identificada: `id_baixa=41`, nao conciliada.
- Parcela vinculada: `id_parcela=20`, numero `1`, excluida logicamente.
- Baixas historicas `40` (parcela `20`) e `42` (parcela `21`) ja estao
  excluidas logicamente.
- O titulo `60` permanece ativo.

A causa da dificuldade de localizacao e a dependencia da consulta mensal de
titulos: o Extrato exibia a baixa, mas nao oferecia caminho para o titulo nem
identificava o vinculo; adicionalmente, a baixa ativa aponta para uma parcela
ja excluida logicamente.

## Regra aplicada

- O Extrato oferece acesso direto a baixa sem depender de mes, ano ou estado
  atual da parcela.
- Baixa vinculada identifica `id_titulo`, numero e `id_parcela`.
- Baixa legada identifica explicitamente a ausencia de parcela.
- O endpoint de exclusao exige a combinacao correta de `id_titulo` e
  `id_baixa`, rejeitando requisicao manipulada.
- Baixa conciliada continua protegida no frontend e no backend.
- A exclusao logica existente permanece responsavel por retirar a baixa dos
  calculos de saldo da parcela, titulo, consulta mensal, Extrato e Analise.

## Gate de arquitetura

- Skills consultadas: `plansmart-governanca-desenvolvimento`,
  `plansmart-projeto-psfinance` e `plansmart-projeto-vps-sistemas`.
- Controller de Extrato: `financeiro/routes_contas.py`.
- Controller de titulos e baixas: `financeiro/routes_titulos.py`.
- Templates: `templates/extrato_conta.html` e
  `templates/titulo_baixas_list.html`.
- Testes focais: `tests/test_parcela_exclusao_baixa.py`.
- Sem model, migration ou mudanca estrutural de banco.

## Matriz de validacao preparada

| Caso | Resultado esperado |
| --- | --- |
| Baixa ativa vinculada a parcela ativa | Extrato identifica e abre a baixa; exclusao recalcula os saldos |
| Baixa ativa vinculada a parcela excluida | Extrato continua identificando e abrindo a baixa |
| Baixa legada sem parcela | Extrato identifica `Baixa legada sem parcela` e abre a baixa |
| Titulo manipulado no POST | Backend rejeita sem excluir a baixa |
| Baixa conciliada | Botao desabilitado e backend rejeita a exclusao com motivo |
| Baixa nao conciliada | Backend permite a exclusao logica |

## Validacoes e pendencias

- Compilacao Python: concluida sem erro.
- `git diff --check`: concluido sem erro.
- PR funcional: `https://github.com/tmvargas/PSFINANCE/pull/93`, base
  `staging`, head `086f3e6280a8417324ca7afb3d69c9ea5965fec8`.
- Integracao em `staging`: `b960aa5cbb2c0d2678e135b3b1ee2d2582c0b4d0`.
- VPS de teste: branch `staging`, `HEAD` igual a `origin/staging`, diretorio
  sem alteracoes locais e servicos `psfinance-staging` e
  `psfinance-staging-gate` ativos.
- Porta `5001`: `/health`, `/gate`, `/financeiro/extrato`,
  `/financeiro/titulos/60/baixas` e `/financeiro/analise` retornaram HTTP 200.
- `/health` e `/gate` confirmaram `db_dialect=postgresql`, branch `staging` e
  commit `b960aa5cbb2c0d2678e135b3b1ee2d2582c0b4d0`.
- Consulta PostgreSQL repetida em transacao `READ ONLY`: baixa `41`, titulo
  `60`, parcela `20`, conta `1`, data `13/08/2026`, valor `R$ 1,00`, baixa
  ativa e nao conciliada, parcela numero `1` excluida logicamente.
- Jornada somente leitura: o Extrato exibiu `Titulo #60 - Parcela 1 (ID #20)`;
  o destino abriu a baixa `41` destacada, com botao `Excluir` disponivel.
- Logs apos estabilizacao dos servicos: sem `error`, `traceback` ou `failed`.
- Evidencias visuais reais:
  `docs/evidencias/PLA-2612/extrato-baixa-41-staging-5001.png` e
  `docs/evidencias/PLA-2612/baixa-41-destacada-staging-5001.png`.
- Testes focais persistentes: preparados, nao executados porque criam e
  alteram dados. A execucao solicitada em PostgreSQL exige autorizacao expressa
  e especifica de Thiago para escrita em banco de teste isolado.
- Exclusao real da baixa `41`: nao executada; depende de autorizacao expressa
  e especifica de Thiago e nao e recomendada como teste automatizado, pois e
  dado operacional de staging. A recomendacao e preservar a baixa `41` ate a
  decisao de Thiago e executar a matriz persistente em banco PostgreSQL isolado,
  com transacao/rollback ou descarte integral do banco de teste autorizado.

## Complemento apos revisao executiva de 20/08/2026

A revisao solicitou prova adicional de protecao contra requisicao manipulada e
dos reflexos da exclusao. Foi adicionado o teste sem banco
`tests/test_pla2612_protecao_endpoint_sem_banco.py`, executado com sucesso em
cinco casos:

| Evidencia executavel | Resultado |
| --- | --- |
| Filtros de `id_baixa`, `id_titulo` e `deleted=False` | Aprovado |
| Titulo manipulado retorna antes de qualquer `commit` | Aprovado |
| Baixa conciliada retorna antes de `bx.deleted=True` | Aprovado |
| Baixa permitida usa exclusao logica e um unico `commit` | Aprovado |
| Saldo da parcela, saldo do titulo, consulta mensal, Extrato e Analise filtram baixas excluidas | Aprovado |

Comando:

```bash
python3 -m unittest tests.test_pla2612_protecao_endpoint_sem_banco -v
```

Esse complemento nao abriu conexao e nao escreveu em SQLite ou PostgreSQL. A
matriz funcional persistente em PostgreSQL isolado, incluindo prova de estado
anterior/posterior e descarte ou rollback, continua dependente da autorizacao
expressa e especifica de Thiago na interacao canonica da tarefa mae `PLA-743`.
Sem essa autorizacao, a governanca proibe criar fixtures, excluir a baixa `41`
ou executar qualquer teste que persista dados, inclusive em banco isolado.

## Pacote de Pre-Validacao de Banco

Pacote preparado em 20/08/2026 sem conexao nem escrita em banco. O alvo futuro
deve ser um PostgreSQL isolado/efemero, diferente de `psfinance_staging` e
`psfinance_prod`.

### Script e integridade

- Script: `scripts/sql/PLA-2612_prevalidacao_postgresql_isolado.sql`.
- Efeito: somente `BEGIN TRANSACTION READ ONLY`, consultas de metadados,
  contagens e locks, seguido de `ROLLBACK`.
- Checksum SHA-256:
  `99db40db1d7f813769da0a72c4fa3672509f920e8edd4a7d16d33e424da52a49`.
- O script exige `expected_database`, compara o nome ao banco atual e falha
  fechado se o alvo for `psfinance_staging` ou `psfinance_prod`.
- O script exige `synthetic_records` e aborta se o valor nao for inteiro entre
  `1` e `19`; esse parametro representa o total da futura fixture autorizada.

### Schema e nulabilidade esperados

| Tabela | Colunas verificadas | Nulabilidade relevante |
| --- | --- | --- |
| `titulo` | `id_titulo`, `deleted` | ambas `NOT NULL` |
| `titulo_parcela` | `id_parcela`, `id_titulo`, `numero_parcela`, `valor`, `deleted` | todas `NOT NULL` |
| `baixa` | `id_baixa`, `id_titulo`, `id_parcela`, `valor_baixa`, `conciliado`, `deleted` | `id_parcela` aceita `NULL` para legado; demais `NOT NULL` |

Qualquer coluna ausente ou divergencia de tipo/nulabilidade executa
`RAISE EXCEPTION` e interrompe o script por `ON_ERROR_STOP`. Nenhuma correcao
automatica de schema esta prevista ou autorizada.

### Volume, lock e duracao

- Volume sintetico maximo: de 1 a 19 registros somando todas as tabelas da
  fixture. Valor ausente, nao inteiro, zero ou maior/igual a 20 aborta o script.
- O script registra contagens iniciais de `titulo`, `titulo_parcela` e `baixa`.
- `lock_timeout`: 1 segundo; `statement_timeout`: 5 segundos;
  `idle_in_transaction_session_timeout`: 10 segundos.
- O script aborta via `RAISE EXCEPTION` ao detectar outra sessao com transacao
  aberta, espera ativa ou lock nao concedido no banco isolado; depois do gate,
  lista somente metadados sanitizados, sem texto SQL.
- Duracao estimada da pre-validacao: menos de 10 segundos. Matriz funcional e
  descarte: ate 10 minutos, condicionados ao aceite e medidos na execucao.

### Backup e restauracao

Antes da matriz autorizada, o GDSIS deve registrar uma das opcoes:

1. banco efemero recem-criado a partir de schema versionado, sem dados
   operacionais, cuja estrategia de rollback e o descarte integral; ou
2. backup logico do banco isolado com `pg_dump --format=custom`, checksum
   SHA-256, tamanho, horario UTC e teste de leitura do catalogo com
   `pg_restore --list`.

Restauracao proposta para a opcao 2: criar outro banco isolado vazio e usar
`pg_restore --clean --if-exists --no-owner --no-privileges`; nunca restaurar
sobre `psfinance_staging` ou `psfinance_prod`.

### Matriz apos autorizacao

O responsavel sera o GDSIS. A execucao usara exclusivamente dados sinteticos e
validara:

1. baixa ativa vinculada a parcela ativa;
2. baixa ativa vinculada a parcela excluida;
3. baixa legada com `id_parcela IS NULL`;
4. baixa conciliada protegida;
5. titulo manipulado rejeitado;
6. reflexos apos exclusao permitida em parcela, titulo, Consulta Mensal,
   Extrato e Analise.

A baixa operacional `41` nao sera copiada, alterada ou excluida. A validacao
registrara IDs sinteticos, estado anterior/posterior, HTTP, screenshots e
contagens, sem expor dados privados.

### Rollback e criterios de parada

- Rollback padrao: descarte integral do banco efemero ou restauracao validada em
  novo banco isolado.
- Abortar sem escrita se banco, schema, nulabilidade, checksum, volume, backup,
  locks, commit de `staging` ou escopo divergirem do pacote aprovado.
- Erro durante a matriz interrompe novos casos, preserva logs sanitizados e
  aciona o rollback antes de qualquer nova tentativa.
- Nenhuma etapa deste pacote autoriza `main`, producao, migration, deploy
  produtivo, banco produtivo ou alteracao da baixa `41`.

### Testes estaticos dos gates

`python3 -m unittest tests.test_pla2612_prevalidacao_sql -v` comprova que o
artefato permanece `READ ONLY`, usa `ON_ERROR_STOP` e contem gates fail-closed
para schema/nulabilidade, locks/concorrencia e limite sintetico de 1 a 19.
