# PLA-1220 - Levantamento e plano multiempresa/multicentro PSFINANCE

Data da analise: 2026-08-04

## Objetivo

Levantar o estado atual do PSFINANCE e definir um plano tecnico para suportar
multiempresa e multicentro, preservando dados existentes, staging, regras
financeiras atuais e governanca de producao.

## Escopo e governanca

- Projeto: `PSFINANCE`.
- Tarefa: `PLA-1220`, vinculada a `PLA-1179`.
- Skills consultadas:
  - `plansmart-governanca-desenvolvimento`;
  - `plansmart-projeto-psfinance`;
  - `plansmart-projeto-vps-sistemas`.
- Acao executada: levantamento de codigo e documentacao, sem alteracao de
  banco, sem migration e sem deploy.
- Producao: fora do escopo.

## Fatos confirmados

- O runtime real do repositorio e Flask com SQLAlchemy.
- O staging ja foi preparado para PostgreSQL via
  `PSFINANCE_STAGING_DATABASE_URL`.
- O modelo atual nao possui isolamento por empresa, centro ou tenant.
- As tabelas financeiras atuais sao:
  - `documento`;
  - `plano_de_contas`;
  - `credor`;
  - `conta`;
  - `titulo`;
  - `titulo_anexo`;
  - `baixa`;
  - `movimentacao_conta`.
- As rotas consultam dados globais filtrando apenas `deleted=false` e campos
  funcionais como data, tipo, documento, conta e plano.
- Nao ha autenticacao, usuario logado, sessao de contexto, seletor de empresa
  ou seletor de centro no codigo atual.
- Anexos de titulos sao gravados fora do Git em diretorio operacional
  configuravel por `PSFINANCE_UPLOAD_TITULOS_FOLDER`.

## Problema tecnico atual

O PSFINANCE esta funcional para uma base financeira unica. Se mais de uma
empresa ou centro usar a mesma base sem mudanca estrutural, havera mistura de:

- contas bancarias e caixas;
- credores;
- titulos;
- baixas;
- movimentacoes;
- anexos;
- saldos;
- relatorios;
- plano financeiro, caso ele varie por empresa.

Essa mistura afeta confidencialidade, calculo de saldo, conciliacao e auditoria.

## Conceitos propostos

### Empresa

Unidade juridica ou operacional que possui dados financeiros proprios.

Proposta de tabela:

```text
empresa
- id_empresa
- uuid
- nome
- cnpj
- codigo_externo
- ativa
- created_at
- updated_at
- deleted
```

### Centro

Unidade de agrupamento gerencial dentro de uma empresa. Pode representar centro
de custo, obra, filial, empreendimento ou unidade de resultado, conforme regra
funcional a ser confirmada.

Proposta de tabela:

```text
centro
- id_centro
- uuid
- id_empresa
- codigo
- nome
- tipo
- ativo
- created_at
- updated_at
- deleted
```

### Contexto operacional

O contexto ativo da operacao deve conter `id_empresa` e, quando aplicavel,
`id_centro`. Esse contexto deve ser escolhido pelo usuario ou definido por
permissao. Ate existir autenticacao, o contexto nao deve ser inferido de forma
oculta.

## Modelo recomendado

Recomendacao tecnica do GDSIS: usar banco unico por ambiente com colunas de
escopo (`id_empresa` e `id_centro`) nas tabelas de negocio.

Motivos:

- mantem a arquitetura atual Flask + SQLAlchemy;
- evita criar um banco por cliente antes de existir governanca operacional
  madura;
- facilita relatorio consolidado por empresa ou centro;
- permite indices, constraints e validacoes de vinculo;
- reduz custo operacional na VPS Sistemas;
- preserva o padrao ja planejado de banco separado por ambiente:
  `psfinance_staging` e `psfinance_prod`.

Alternativas avaliadas:

- schema por empresa: aumenta isolamento, mas eleva complexidade de migration,
  conexao, backup e deploy para o estagio atual do produto;
- banco por empresa: maior isolamento, porem aumenta manutencao, custos
  operacionais e risco de divergencia entre bases;
- somente filtro visual sem coluna de escopo: rejeitado por nao isolar dados no
  backend.

## Escopo minimo por tabela

### Tabelas mestres

- `empresa`: nova tabela obrigatoria.
- `centro`: nova tabela vinculada a `empresa`.
- `documento`: pode continuar global inicialmente, salvo decisao de variacao por
  empresa.
- `plano_de_contas`: recomendado vincular a `empresa`; `id_centro` nao deve ser
  obrigatorio no plano, porque o plano e estrutura contabil/financeira.
- `credor`: recomendado vincular a `empresa`; credor global so deve existir se
  houver regra explicita de compartilhamento.
- `conta`: deve vincular a `empresa` e, opcionalmente, a `centro`.

### Tabelas transacionais

- `titulo`: deve vincular a `empresa` e, opcionalmente, a `centro`.
- `baixa`: deve herdar coerencia de empresa e centro pelo titulo e pela conta.
- `movimentacao_conta`: deve vincular a `empresa`; `id_centro` deve ser
  obrigatorio para entrada/saida se o centro for criterio de apropriacao, e
  opcional ou derivado para transferencia conforme decisao funcional.
- `titulo_anexo`: deve permanecer vinculado ao titulo; o caminho fisico deve
  considerar particionamento operacional por empresa/titulo para reduzir risco
  de mistura de anexos.

## Regras de integridade necessarias

- Uma conta usada em baixa deve pertencer a mesma empresa do titulo.
- Um titulo deve usar credor e plano da mesma empresa.
- Uma movimentacao deve usar conta e plano da mesma empresa.
- Uma transferencia deve ocorrer entre contas da mesma empresa, salvo regra
  explicita de transferencia interempresa.
- O centro escolhido deve pertencer a empresa selecionada.
- Consultas de listagem e dashboard devem sempre filtrar pelo contexto ativo.
- Operacoes sem contexto valido devem falhar de forma explicita, nao cair em
  base global.

## Impacto por camada

### Backend

Arquivos provaveis:

- `models.py` - Incluir modelos `Empresa` e `Centro` e colunas de escopo nas
  entidades financeiras.
- `database.py` - Preservar selecao de banco por ambiente, sem expor URL.
- `financeiro/routes_home.py` - Filtrar dashboard por empresa/centro ativo.
- `financeiro/routes_contas.py` - Filtrar e validar contas, movimentacoes e
  transferencias por contexto.
- `financeiro/routes_titulos.py` - Filtrar e validar titulos, baixas, credores,
  planos, documentos e anexos por contexto.
- `financeiro/routes_plano.py` - Filtrar e validar plano por empresa.
- `financeiro/routes_credor.py` - Filtrar e validar credores por empresa.

### Frontend

Arquivos provaveis:

- `templates/base.html` - Incluir seletor de empresa/centro quando a regra de
  autenticacao/contexto for aprovada.
- `templates/dashboard_financeiro.html` - Exibir saldos filtrados pelo contexto.
- `templates/contas_list.html` e `templates/conta_form.html` - Associar contas
  ao contexto.
- `templates/titulos_list.html` e `templates/titulo_form.html` - Associar
  titulos ao contexto.
- `templates/movimentacao_form.html` - Exigir centro quando aplicavel.
- `templates/extrato_conta.html` e telas de analise - Garantir que filtros e
  totais respeitem empresa/centro.

### Banco

Alteracoes futuras exigirao migration ou script transacional, com backup de
staging antes da execucao. Producao exigira Pacote de Producao e autorizacao
expressa.

## Plano de execucao recomendado

### Fase 1 - Decisao funcional e modelo

1. Confirmar se "centro" significa centro de custo, obra, filial,
   empreendimento ou outra unidade.
2. Confirmar se um usuario podera acessar uma ou varias empresas.
3. Confirmar se o plano financeiro e por empresa ou compartilhado.
4. Confirmar se credores podem ser compartilhados entre empresas.
5. Confirmar se transferencia interempresa sera permitida ou bloqueada.

Resultado esperado: decisao funcional registrada antes de migration.

### Fase 2 - Preparacao tecnica segura

1. Criar migration de staging para tabelas `empresa` e `centro`.
2. Inserir uma empresa inicial de configuracao para enquadrar os dados atuais.
3. Popular `id_empresa` nos dados existentes de staging.
4. Definir regras para `id_centro` nos dados historicos:
   - nulo permitido ate classificacao manual; ou
   - centro padrao de implantacao, se Thiago aprovar.
5. Criar indices e constraints de integridade.

Resultado esperado: staging com dados atuais preservados e escopados por uma
empresa inicial.

### Fase 3 - Contexto e filtros obrigatorios

1. Criar utilitario de contexto ativo.
2. Aplicar filtro de empresa em todas as consultas.
3. Aplicar filtro de centro nas rotas em que a regra exigir.
4. Bloquear gravacoes sem contexto.
5. Validar coerencia de FKs (chaves estrangeiras) no backend.

Resultado esperado: nenhuma tela financeira lista ou grava dados fora do
contexto ativo.

### Fase 4 - Interface operacional

1. Incluir seletor de empresa/centro no shell da aplicacao.
2. Criar telas minimas de cadastro/gestao de empresa e centro.
3. Ajustar formularios de contas, titulos e movimentacoes.
4. Exibir contexto ativo em telas financeiras criticas.

Resultado esperado: usuario opera conscientemente dentro de empresa/centro.

### Fase 5 - QA e staging

1. Testar dashboard por empresa.
2. Testar contas e saldos por empresa/centro.
3. Testar titulos, baixas e saldo aberto sem cruzamento entre empresas.
4. Testar movimentacao de entrada, saida e transferencia.
5. Testar anexos de titulos.
6. Validar `/health`, `/gate` e porta corporativa `5001`.

Resultado esperado: evidencia objetiva de isolamento e preservacao dos dados.

## Criterios de aceite

- Empresa e centro possuem modelo aprovado.
- Dados existentes de staging sao preservados.
- Listagens e dashboards nao mostram dados de outra empresa.
- Formularios nao permitem vincular conta, titulo, credor, plano ou centro de
  empresa diferente.
- Transferencia entre empresas fica bloqueada, salvo aprovacao funcional
  explicita.
- Rotas criticas continuam respondendo em staging.
- Porta `5001` retorna `healthy`, branch `staging` e commit correto.
- Nenhum segredo, dump, banco SQLite ou anexo operacional e versionado.

## Riscos

- Ausencia de autenticacao/contexto pode levar a isolamento apenas parcial se
  for implementado diretamente sem decisao funcional.
- Dados historicos sem centro exigem decisao de classificacao.
- Credores e plano financeiro podem ser compartilhaveis ou especificos por
  empresa; aplicar uma regra errada gera retrabalho e risco de duplicidade.
- Constraints compostas exigem cuidado com chaves existentes e PostgreSQL.
- Producao nao deve receber migration sem comparacao entre staging e producao,
  backup, plano de deploy e rollback.

## Bloqueios para implementacao

Nao ha bloqueio para o planejamento.

Ha bloqueio funcional para iniciar implementacao/migration: Thiago ou CEO deve
confirmar as decisoes da Fase 1, principalmente o significado de centro, regras
de compartilhamento e tratamento dos dados historicos sem centro.

## Recomendacao do GDSIS

Avancar com o modelo de banco unico por ambiente e escopo por colunas
`id_empresa` e `id_centro`, comecando em staging por uma empresa inicial que
preserve os dados existentes. Nao executar migration em producao nem copiar
dados de staging para producao sem Pacote de Producao e autorizacao expressa de
Thiago.

## Proxima acao

Encaminhar este plano para revisao executiva do CEO/Thiago. Apos aprovacao das
decisoes funcionais da Fase 1, criar tarefa de implementacao com
`executionPolicy` nativa de revisao do CEO, conforme governanca Paperclip.
