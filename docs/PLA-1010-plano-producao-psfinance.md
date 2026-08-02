# PLA-1010 - Analise e plano de producao do PSFINANCE

Data da analise: 2026-08-02

## Objetivo

Retomar a `PLA-1004` apos a validacao da `PLA-1005`, atualizar o pacote de
analise de producao com o commit atual da `staging` e preparar recomendacao
tecnica para revisao executiva do CEO, sem executar producao.

## Skills consultadas

- `plansmart-governanca-desenvolvimento`
- `plansmart-projeto-psfinance`
- `plansmart-projeto-vps-sistemas`

## Limite operacional

Esta analise nao autoriza:

- merge da `staging` na `main`;
- push na `main`;
- deploy em producao;
- criacao, alteracao ou escrita no banco produtivo;
- migration produtiva;
- reinicio de servico produtivo;
- copia de dados de `staging` para producao.

## Fatos confirmados

- Projeto: `PSFINANCE`.
- Repositorio oficial: `https://github.com/tmvargas/PSFINANCE.git`.
- Branch de teste analisada: `origin/staging`.
- Branch de producao analisada: `origin/main`.
- Commit atual da `staging`: `2976a64ea07e09b53a97dfcb8d6879edae4fe042`.
- Commit atual da `main`: `23821c7786e98c5c489c60c2ac60760e3cdc17c1`.
- A `PLA-1005` corrigiu a divergencia da `PLA-1004`: a verificacao manual
  anterior nao carregava o `EnvironmentFile` do systemd, enquanto o servico real
  de staging usa PostgreSQL.
- A porta corporativa `5001` respondeu HTTP 200 em
  `/staging/psfinance/health` e `/gate`.
- As respostas tecnicas da porta `5001` confirmaram:
  - `branch=staging`;
  - `commit=2976a64ea07e09b53a97dfcb8d6879edae4fe042`;
  - `db_dialect=postgresql`;
  - `database_url_source=PSFINANCE_STAGING_DATABASE_URL`;
  - `status=healthy`.
- A URL funcional de staging na porta `5001` respondeu HTTP 200 em
  `/staging/psfinance` e `/staging/psfinance/financeiro/`.

## Historico entre main e staging

Comando executado:

```bash
git log --oneline --left-right --cherry-pick origin/main...origin/staging
```

Resultado:

```text
> 2976a64 merge: PLA-1005 evidenciar PostgreSQL staging
> 6d4f244 fix: evidenciar postgresql staging PLA-1005
> a346e3f merge: PLA-988 migrar staging PSFINANCE para PostgreSQL
> 5861b43 infra: preparar migracao staging para postgresql
> 500f2f9 merge: PLA-981 URL base funcional em staging
> ed931d2 fix: retornar dashboard na base do staging PSFINANCE
> 5c73b13 merge: PLA-985 retomar PSFINANCE funcional do ZIP
> 5e34516 feat: retomar PSFINANCE funcional do ZIP
> f67b1e1 docs: registrar bloqueio de artefatos da PLA-981
> fb2b9de merge: PLA-836 localizar base real do PSFINANCE
> 334e347 docs: registrar base real do PSFINANCE
> e7c1b1e merge: PLA-831 corrigir URL de homologacao
> 66f9320 fix: ajustar homologacao HTML do PSFINANCE
> 3d9e86a docs: registrar URL sem porta do staging PSFINANCE
> 7c029d2 docs: registrar validacao da URL de staging PSFINANCE
> c2982b9 PLA-825 configura URL de staging do PSFINANCE
> ca3ddce merge: PLA-815 confirmar URL publica de homologacao
> 26c58f5 docs: confirmar URL publica do staging PSFINANCE
> b01f804 merge: PLA-814 registrar evidencia final
> 960e560 docs: registrar validacao final do gate PSFINANCE
> 3ef9a1b merge: PLA-814 liberar acesso ao staging
> 1f11b46 docs: registrar liberacao do staging PSFINANCE
> ecf2691 merge: PLA-747 registrar evidencia do staging
> b619fdb docs: registrar evidencia do staging PSFINANCE
> 6a3eb0c merge: PLA-747 preparar staging do PSFINANCE
> 0e0f3ed infra: preparar staging do PSFINANCE
```

## Diferenca de arquivos entre main e staging

Comando executado:

```bash
git diff --stat origin/main..origin/staging
```

Resultado consolidado:

```text
44 files changed, 7455 insertions(+), 3 deletions(-)
```

Comando executado:

```bash
git diff --name-status origin/main..origin/staging
```

Arquivos no escopo da promocao:

- `.env.example` - Incluidas variaveis esperadas para staging e PostgreSQL sem valores reais.
- `.gitignore` - Ajustadas regras para impedir versionamento de artefatos operacionais.
- `database.py` - Incluida configuracao SQLAlchemy com prioridade para variaveis PostgreSQL e fallback SQLite local.
- `docs/PLA-1005-corrigir-divergencia-postgresql-staging.md` - Registrada a correcao da divergencia PostgreSQL.
- `docs/PLA-747-preparacao-staging-psfinance.md` - Registrada a preparacao inicial do staging.
- `docs/PLA-814-liberacao-acesso-staging-psfinance.md` - Registrada a liberacao externa do gate.
- `docs/PLA-815-confirmacao-url-publica-psfinance.md` - Confirmada URL publica auxiliar de homologacao.
- `docs/PLA-825-configurar-url-staging-psfinance.md` - Documentada URL `/staging/psfinance`.
- `docs/PLA-831-corrigir-url-homologacao-psfinance.md` - Documentada correcao da pagina de homologacao.
- `docs/PLA-836-localizacao-base-real-psfinance.md` - Registrado levantamento da base real anterior.
- `docs/PLA-981-bloqueio-artefatos-funcionais.md` - Registrado bloqueio inicial dos artefatos funcionais.
- `docs/PLA-985-retomada-zip-funcional.md` - Registrada retomada do ZIP funcional.
- `docs/PLA-988-migracao-staging-postgresql.md` - Documentado procedimento de migracao controlada para PostgreSQL.
- `docs/decisoes.md` - Registradas decisoes tecnicas do PSFINANCE.
- `financeiro/__init__.py` - Criado blueprint financeiro.
- `financeiro/routes_contas.py` - Incluidas rotas de contas, saldos, extrato e movimentacoes.
- `financeiro/routes_credor.py` - Incluidas rotas de credores.
- `financeiro/routes_home.py` - Incluida rota do dashboard financeiro.
- `financeiro/routes_plano.py` - Incluidas rotas de plano de contas.
- `financeiro/routes_titulos.py` - Incluidas rotas de titulos, baixas e anexos.
- `models.py` - Criado modelo SQLAlchemy das tabelas financeiras.
- `requirements.txt` - Incluidas dependencias Flask, Gunicorn, SQLAlchemy e driver PostgreSQL.
- `scripts/migrate_sqlite_to_postgres.py` - Criado script transacional de migracao SQLite para PostgreSQL.
- `src/app.py` - Incluida aplicacao Flask, healthcheck, gate e rotas com prefixo de staging.
- `templates/analise_conta_detalhe.html` - Incluida tela de detalhe da analise por conta.
- `templates/analise_resultados.html` - Incluida tela de analise de resultados.
- `templates/analise_resultados_detalhe.html` - Incluida tela de detalhe de resultados.
- `templates/base.html` - Criado template base da interface financeira.
- `templates/conta_form.html` - Incluido formulario de conta.
- `templates/contas_inativas.html` - Incluida tela de contas inativas.
- `templates/contas_list.html` - Incluida listagem de contas.
- `templates/credor_form.html` - Incluido formulario de credor.
- `templates/credores_list.html` - Incluida listagem de credores.
- `templates/dashboard_financeiro.html` - Incluido dashboard financeiro.
- `templates/extrato_conta.html` - Incluida tela de extrato de conta.
- `templates/movimentacao_edit_form.html` - Incluido formulario de edicao de movimentacao.
- `templates/movimentacao_form.html` - Incluido formulario de movimentacao.
- `templates/movimentacoes_list.html` - Incluida listagem de movimentacoes.
- `templates/plano_form.html` - Incluido formulario de plano de contas.
- `templates/plano_list.html` - Incluida listagem de plano de contas.
- `templates/titulo_baixa_form.html` - Incluido formulario de baixa de titulo.
- `templates/titulo_baixas_list.html` - Incluida listagem de baixas.
- `templates/titulo_form.html` - Incluido formulario de titulo.
- `templates/titulos_list.html` - Incluida listagem de titulos.

## Banco de dados

Estrutura esperada em PostgreSQL:

- `documento`;
- `plano_de_contas`;
- `credor`;
- `conta`;
- `titulo`;
- `titulo_anexo`;
- `baixa`;
- `movimentacao_conta`.

O script versionado `scripts/migrate_sqlite_to_postgres.py` cria as tabelas a
partir dos modelos SQLAlchemy e copia dados de uma origem SQLite para um destino
PostgreSQL vazio. O script interrompe quando o destino ja possui dados, salvo
uso explicito de `--truncate-target`, que so pode ocorrer apos backup validado e
autorizacao especifica.

Dados validados no PostgreSQL de staging pela `PLA-1005`:

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

Separacao obrigatoria para producao:

- Estrutura de banco: tabelas, chaves, colunas e sequences previstas nos modelos.
- Dados obrigatorios de configuracao: `documento` e `plano_de_contas` podem ser
  necessarios para operacao inicial, mas devem ser validados por Thiago antes de
  qualquer carga produtiva.
- Dados operacionais: contas, credores, titulos, anexos, baixas e movimentacoes
  devem ser preservados em producao por padrao.

Pergunta obrigatoria para Thiago em caso de aprovacao produtiva com banco:

```text
Migrar dados de staging para producao ou preservar os dados operacionais existentes em producao?
```

Recomendacao tecnica padrao: preservar dados operacionais de producao. Qualquer
copia de dados de `staging` para producao exige autorizacao separada, com origem,
destino, volume, motivo, impacto, backup e rollback.

## Plano de backup antes de producao

1. Confirmar diretorio real de producao do PSFINANCE na VPS Sistemas.
2. Confirmar banco produtivo real ou planejado, preferencialmente
   `psfinance_prod`, sem expor URL ou senha.
3. Executar backup do banco produtivo antes de qualquer alteracao, quando o
   banco existir.
4. Preservar arquivos operacionais de upload, especialmente anexos de titulos,
   fora do Git.
5. Registrar commit atual da `main`, commit anterior do servico produtivo e
   horario de inicio.
6. Validar que o backup pode ser localizado e restaurado antes de seguir.

## Plano de deploy produtivo proposto

Executar somente apos autorizacao expressa de Thiago, com escopo e commits
congelados:

1. Revalidar que `origin/staging` esta no commit autorizado
   `2976a64ea07e09b53a97dfcb8d6879edae4fe042`.
2. Revalidar que `origin/main` esta no commit analisado
   `23821c7786e98c5c489c60c2ac60760e3cdc17c1`, ou refazer esta analise se
   houver mudanca.
3. Abrir PR (Pull Request, solicitacao de revisao) de `staging` para `main` ou
   executar o merge somente pelo fluxo autorizado por Thiago.
4. Publicar a `main` no diretorio produtivo planejado do PSFINANCE.
5. Configurar variaveis produtivas sem registrar valores:
   - `PSFINANCE_PROD_DATABASE_URL` ou `DATABASE_URL` isolada de producao;
   - `PSFINANCE_SECRET_KEY`;
   - `PSFINANCE_INSTANCE_PATH`;
   - `PSFINANCE_UPLOAD_TITULOS_FOLDER`;
   - `APP_ENV=production`;
   - `GIT_BRANCH=main`;
   - `GIT_COMMIT=<commit autorizado>`.
6. Subir Gunicorn por servico produtivo isolado, atras do Nginx.
7. Validar healthcheck produtivo, rotas financeiras criticas e logs.
8. Registrar commit, horario, servicos, banco, validacoes e incidentes.

## Plano de validacao pos-deploy

1. Confirmar branch produtiva `main`.
2. Confirmar commit produtivo igual ao commit autorizado.
3. Confirmar servico ativo.
4. Confirmar Nginx apontando para a porta interna produtiva planejada.
5. Validar `/health` ou rota equivalente sem expor segredo.
6. Validar dashboard financeiro.
7. Validar listagens de contas, credores, plano de contas e titulos.
8. Validar uma consulta de extrato sem executar escrita destrutiva.
9. Confirmar logs sem erro de conexao PostgreSQL ou SQLAlchemy.
10. Confirmar que anexos operacionais continuam acessiveis, quando existirem.

## Plano de rollback

1. Interromper alteracoes se qualquer validacao critica falhar.
2. Reverter o servico produtivo para o commit anterior registrado.
3. Restaurar variaveis produtivas anteriores, se alteradas.
4. Restaurar backup do banco produtivo somente se houver alteracao de banco
   executada e se a restauracao estiver dentro do escopo autorizado.
5. Restaurar arquivos operacionais somente a partir de backup validado, quando
   aplicavel.
6. Reiniciar servico produtivo.
7. Validar healthcheck, rotas criticas e logs.
8. Registrar horario, causa, commit revertido, backup usado e resultado.

## Riscos

- A producao ainda exige confirmacao operacional de diretorio real, servico,
  Nginx, variaveis e banco produtivo.
- O modelo multicliente do PSFINANCE ainda precisa de decisao antes de uso
  produtivo amplo.
- Copiar dados de `staging` para producao pode sobrescrever ou misturar dados
  reais; a recomendacao padrao e preservar producao.
- O script de migracao aceita `--truncate-target`, mas esse modo exige
  autorizacao explicita e backup validado.
- Anexos fisicos nao estao no Git; precisam de plano operacional proprio se
  forem necessarios em producao.
- A promocao inclui uma diferenca grande entre `main` e `staging`, com 44
  arquivos e criacao do modulo funcional financeiro.

## Recomendacao do GDSIS

Recomenda com ressalvas.

A parte de staging esta tecnicamente validada, incluindo porta `5001`,
healthcheck, gate e PostgreSQL. A promocao para producao so deve ser solicitada
apos o CEO validar este pacote e Thiago autorizar explicitamente:

- merge da `staging` na `main`;
- deploy produtivo;
- estrategia de banco produtivo;
- decisao sobre preservar dados produtivos ou migrar dados de `staging`;
- plano operacional para anexos, se aplicavel.

Sem essas autorizacoes, a acao correta e manter a `PLA-1004` em revisao
executiva/preparacao, nao executar producao.
