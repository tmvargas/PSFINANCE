# PLA-1221 - Arquitetura e execucao multiempresa/multicentro PSFINANCE

Data: 2026-08-04

## Objetivo

Consolidar a arquitetura tecnica segura e a ordem de execucao para evoluir o
PSFINANCE de uma base financeira global para operacao multiempresa e
multicentro, preservando os dados existentes e evitando mistura entre empresas,
centros, titulos, contas e anexos.

## Skills consultadas

- `plansmart-governanca-desenvolvimento`
- `plansmart-projeto-psfinance`
- `plansmart-projeto-vps-sistemas`

## Fatos confirmados

- O sistema oficial e `PSFINANCE`; `PSCONTROL` permanece somente como referencia
  legada.
- O repositorio oficial e `https://github.com/tmvargas/PSFINANCE.git`.
- `origin/staging` existe e aponta para o commit
  `e0c434bbfb8573daba3ff9d0fdfc730afb65a971` neste levantamento.
- O runtime real do repositorio e Flask com SQLAlchemy.
- A aplicacao usa `PSFINANCE_STAGING_DATABASE_URL`, `PSFINANCE_DATABASE_URL`,
  `DATABASE_URL` ou fallback SQLite em `instance/financeiro.db`.
- A skill do PSFINANCE exige decisao de modelo multicliente antes de uso
  produtivo.
- A `PLA-1220` ja recomendou banco unico por ambiente com colunas `id_empresa`
  e `id_centro` como implementacao minima.
- A skill de VPS Sistemas registra bancos separados por sistema e por ambiente,
  nao por empresa ou centro.
- A governanca proibe criar banco, tabela, usuario ou migration nesta fase sem
  autorizacao.

## Estado atual do modelo

As tabelas atuais representam uma unica visao global:

- `documento`
- `plano_de_contas`
- `credor`
- `conta`
- `titulo`
- `titulo_anexo`
- `baixa`
- `movimentacao_conta`

Nao existem colunas ou tabelas para:

- empresa;
- centro;
- centro de custo;
- unidade operacional;
- cliente;
- `tenant_id`.

As rotas consultam registros com filtros globais por `deleted`, data, conta,
titulo ou plano. Exemplos confirmados:

- dashboard lista todas as contas ativas.
- plano financeiro impede duplicidade global de `cod_estrutural`.
- credores sao listados globalmente por nome.
- titulos sao listados globalmente por periodo de vencimento.
- extrato e movimentacoes filtram por conta global.

## Risco tecnico

Implementar multiempresa apenas com filtros de tela, sem isolamento no banco,
nao atende a governanca. Isso permitiria:

- visualizar dados de outra empresa ou centro por URL direta;
- baixar titulo em conta de outra empresa;
- conciliar movimentacao em contexto incorreto;
- reutilizar credor ou plano indevidamente entre empresas;
- misturar anexos de titulos;
- gerar saldos e analises consolidadas sem escopo claro.

## Decisao tecnica recomendada

Adotar uma unica base por ambiente, confirmando a linha da `PLA-1220`, com
isolamento minimo por colunas obrigatorias de escopo:

- `id_empresa` para a empresa operacional;
- `id_centro` para centro, obra, filial, unidade ou centro financeiro.

`tenant_id` deve ser tratado como camada futura ou opcional de organizacao
controladora, somente se Thiago confirmar que o PSFINANCE tera mais de um
cliente/tenant na mesma base. Nao deve entrar como obrigatorio na primeira
implementacao se a necessidade atual for apenas multiempresa/multicentro dentro
da PlanSmart.

Motivo:

- preserva o padrao atual da VPS Sistemas: `psfinance_staging` e
  `psfinance_prod`;
- evita multiplicar bancos por empresa nesta fase;
- permite filtros obrigatorios em todas as rotas;
- reduz risco de deploy e rollback;
- facilita evolucao futura para permissao por usuario, `tenant_id` e API
  versionada.

Modelo descartado nesta fase:

- banco por cliente ou por empresa, porque aumentaria custo operacional,
  exigiria provisionamento por cliente e ainda nao existe decisao produtiva para
  esse grau de isolamento.
- schema PostgreSQL por cliente, porque complicaria migrations e operacao sem
  necessidade confirmada neste momento.

## Modelo conceitual proposto

Tabelas novas:

- `empresa`: empresa juridica ou operacional.
- `centro`: centro operacional vinculado a uma `empresa`.

Campos de escopo recomendados:

- `documento`: `id_empresa` opcional, `id_centro` opcional,
  conforme decisao funcional sobre documentos compartilhados.
- `plano_de_contas`: `id_empresa` opcional, `id_centro` opcional,
  conforme decisao funcional sobre plano padrao ou plano por empresa.
- `credor`: `id_empresa` opcional, conforme decisao funcional
  sobre cadastro compartilhado de fornecedores.
- `conta`: `id_empresa`, `id_centro` opcional.
- `titulo`: `id_empresa`, `id_centro`.
- `titulo_anexo`: herda o escopo do `titulo`; pode manter somente `id_titulo`
  se houver validacao obrigatoria pelo titulo.
- `baixa`: herda o escopo do `titulo` e da `conta`; deve validar que ambos
  pertencem a empresas compativeis.
- `movimentacao_conta`: `id_empresa`, `id_centro` opcional, com
  validacao entre contas de origem e destino.

## Regras de negocio minimas

- Toda consulta operacional deve aplicar escopo ativo antes de retornar dados.
- Toda escrita deve receber ou derivar `id_empresa` e, quando aplicavel,
  `id_centro`.
- Uma baixa nao pode vincular titulo e conta de empresas incompativeis.
- Uma transferencia entre contas de empresas diferentes deve ser bloqueada ate
  existir regra funcional explicita para transferencia interempresa.
- Saldos de contas devem ser calculados dentro do escopo da conta.
- Analises e extratos devem informar o escopo usado.
- Anexos devem ser baixados somente se o titulo vinculado estiver no escopo
  autorizado.
- Cadastros compartilhados devem ser decisao explicita, nao comportamento
  acidental.

## Ordem de execucao recomendada

1. Aprovar a decisao funcional de isolamento: `id_empresa` + `id_centro` em
   base unica por ambiente.
2. Definir se `Documento`, `PlanoDeContas` e `Credor` sao compartilhados entre
   empresas ou especificos por empresa/centro.
3. Preparar migration versionada e reversivel para staging, com backfill
   controlado dos registros existentes para uma empresa/centro padrao de
   homologacao.
4. Criar helper de contexto de escopo no backend antes de alterar todas as
   rotas.
5. Aplicar filtros obrigatorios nas consultas de dashboard, contas, titulos,
   baixas, movimentacoes, analises, extrato, credores e plano financeiro.
6. Ajustar formularios para selecionar empresa e centro quando aplicavel.
7. Validar dados existentes em staging e rotas criticas na porta `5001`.
8. Somente depois preparar Pacote de Producao, com pergunta explicita a Thiago
   sobre preservar dados operacionais de producao ou migrar dados de staging.

## Arquivos e camadas impactadas na implementacao futura

- `models.py`: criacao de modelos de empresa e centro; inclusao de
  chaves estrangeiras e constraints de escopo.
- `database.py`: sem mudanca obrigatoria prevista para conexao; migrations
  devem ser versionadas fora do `create_all`.
- `financeiro/routes_home.py`: filtro de dashboard por escopo.
- `financeiro/routes_contas.py`: filtro e validacao de contas, movimentacoes,
  extrato e analises por escopo.
- `financeiro/routes_titulos.py`: filtro e validacao de titulos, baixas e
  anexos por escopo.
- `financeiro/routes_credor.py`: regra de compartilhamento de credores entre
  empresas ou por empresa.
- `financeiro/routes_plano.py`: regra de compartilhamento do plano financeiro.
- `templates/*.html`: seletores e exibicao do escopo quando aplicavel.
- `scripts/migrate_sqlite_to_postgres.py`: revisar se houver backfill de dados
  existentes para PostgreSQL.

## Validacao executada neste heartbeat

- `git fetch origin`
- `git ls-remote --heads origin staging main`
- `git status --short --branch`
- `python3 -m compileall src financeiro models.py database.py`

Resultado:

- Sintaxe Python validada com `python3`.
- A tentativa com `python` falhou porque o binario nao existe no ambiente local;
  a validacao equivalente foi executada com `python3`.
- Nenhuma rota, tabela, migration, banco, VPS, `main` ou producao foi alterado.
- A API do Paperclip retornou `Unauthorized` ao tentar consultar/comentar a
  issue com as variaveis de execucao disponiveis; isso foi tratado como falha
  administrativa, sem interromper o trabalho tecnico seguro.

## Bloqueios e decisoes pendentes

Bloqueio funcional:

- falta aprovacao explicita do modelo de isolamento multiempresa/multicentro.

Responsavel pelo desbloqueio:

- CEO/Thiago devem validar a decisao de modelo antes da implementacao com
  migration.

Perguntas objetivas para aprovar a execucao:

- O PSFINANCE deve usar base unica por ambiente com `id_empresa` e `id_centro`,
  conforme recomendado na `PLA-1220`?
- `PlanoDeContas`, `Documento` e `Credor` serao compartilhados entre empresas
  ou segregados por empresa/centro?
- Havera necessidade de `tenant_id` ja nesta fase, ou a segregacao atual e
  apenas por empresas e centros dentro da PlanSmart?
- Transferencias entre contas de empresas diferentes devem ser proibidas nesta
  fase?

## Recomendacao do GDSIS

Recomendo aprovar a arquitetura de base unica por ambiente com escopo
obrigatorio por `id_empresa` e `id_centro`, bloquear transferencia interempresa
nesta fase e executar a implementacao em subtarefa tecnica propria com revisao
nativa do CEO por `executionPolicy`.

Nao recomendo criar migration ou alterar codigo operacional nesta PLA-1221 antes
da decisao funcional, porque o risco de mistura ou classificacao incorreta de
dados financeiros e alto.
