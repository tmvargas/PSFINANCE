# PLA-858 - Lacuna funcional do staging do PSFINANCE

## Objetivo

Analisar a lacuna funcional entre o staging tecnico publicado do PSFINANCE e um
produto financeiro utilizavel, preparando um plano seguro de evolucao sem
alterar producao, sem criar banco e sem presumir regra de negocio ainda nao
aprovada.

## Escopo e governanca

- Projeto: `PSFINANCE`.
- Issue: `PLA-858`.
- Skills consultadas:
  - `plansmart-governanca-desenvolvimento`;
  - `plansmart-projeto-psfinance`;
  - `plansmart-projeto-vps-sistemas`.
- Ambiente analisado: staging publico da VPS (Servidor Virtual Privado)
  `vps69143.publiccloud.com.br`.
- Acoes executadas: leitura de codigo, documentacao versionada, Git e rotas
  publicas de staging.
- Producao: nao houve analise com escrita, deploy, migration ou alteracao em
  ambiente produtivo.

## Fatos confirmados em 2026-07-31

### Git e staging

- Branch local inicial: `staging`.
- `origin/staging`: `fb2b9dea247ba34ea91150cb10c20680c9c49a05`.
- `origin/main`: `23821c7786e98c5c489c60c2ac60760e3cdc17c1`.
- A diferenca `origin/main..origin/staging` contem preparacao tecnica,
  documentacao, healthcheck, gate e pagina HTML de homologacao.
- Nao ha modulo funcional financeiro na diferenca entre `main` e `staging`.

### Codigo atual

- `src/app.py` implementa uma aplicacao Flask minima com:
  - pagina HTML de homologacao;
  - `/health`;
  - `/gate`;
  - rotas equivalentes sob `/staging/psfinance`.
- `requirements.txt` contem somente `Flask` e `gunicorn`.
- Nao existem controllers, services, repositories, models, migrations,
  templates funcionais, autenticacao, integracao Sienge ou camada de
  persistencia.
- `.env.example` contem variaveis operacionais de ambiente e healthcheck, sem
  URL real de banco.

### Staging publico

- `http://vps69143.publiccloud.com.br/staging/psfinance`: HTTP 200.
- Conteudo retornado: pagina de homologacao com texto
  `Ambiente de homologacao ativo`.
- Commit exposto na pagina: `fb2b9dea247ba34ea91150cb10c20680c9c49a05`.
- `http://vps69143.publiccloud.com.br:5001/staging/psfinance/gate`: HTTP 200.
- Gate retornou:
  - `app=PSFINANCE`;
  - `environment=staging-gate`;
  - `branch=staging`;
  - `commit=fb2b9dea247ba34ea91150cb10c20680c9c49a05`;
  - healthcheck interno `http://127.0.0.1:5104/health` com HTTP 200.

### Banco e base real

- A PLA-836 ja registrou que nao foi localizada base PostgreSQL real em uso
  pelo PSFINANCE na operacao atual.
- Nao ha evidencia versionada de migration, driver PostgreSQL, ORM ou
  repository de persistencia no codigo atual.
- A referencia `psfinance_staging` permanece planejada/documental, nao como
  banco operacional validado.

## Lacuna funcional

O staging atual comprova que a infraestrutura minima responde, mas nao comprova
produto financeiro funcional.

As principais lacunas sao:

- escopo funcional do MVP (Produto Minimo Viavel) ainda nao fechado;
- modelo multicliente ainda nao decidido;
- banco de staging ainda nao criado ou conectado;
- ausencia de modelo de dados financeiro;
- ausencia de autenticacao e controle de acesso;
- ausencia de telas ou API (Interface de Programacao de Aplicacoes) de negocio;
- ausencia de integracao Sienge;
- ausencia de criterios de aceite funcionais;
- ausencia de testes funcionais e regressao de negocio.

## Hipoteses nao assumidas

- Nao foi assumido que o legado `PSCONTROL` define o escopo atual do
  `PSFINANCE`.
- Nao foi assumido que o banco deve ser criado localmente na VPS.
- Nao foi assumido o modelo multicliente como `tenant_id`, schema por cliente ou
  banco por cliente.
- Nao foi assumida a existencia de uma base produtiva pronta para promocao.

## Riscos

- Alto: iniciar desenvolvimento funcional sem decisao de multicliente pode
  causar mistura de dados entre clientes.
- Alto: criar banco ou migration antes da aprovacao pode contrariar a
  governanca atual da skill do PSFINANCE.
- Medio: evoluir telas sem modelo de dados aprovado pode gerar retrabalho e
  regras duplicadas.
- Medio: tratar a URL de homologacao como produto pronto pode induzir
  homologacao incorreta pelo CEO ou Thiago.
- Baixo: manter o staging tecnico atual sem evolucao funcional preserva a
  governanca, mas nao entrega valor operacional.

## Plano seguro proposto

### Etapa 1 - Fechamento funcional

- Responsavel: GDSIS com decisao do CEO/Thiago.
- Objetivo: definir o primeiro fluxo financeiro do PSFINANCE.
- Entregaveis:
  - escopo do MVP;
  - criterios de aceite;
  - papeis de usuario;
  - regras de negocio iniciais;
  - rotas ou telas esperadas.
- Saida esperada: aprovacao explicita do escopo antes de implementar regra de
  negocio.

### Etapa 2 - Decisao de arquitetura de dados

- Responsavel: GDSIS.
- Objetivo: decidir modelo multicliente e banco de staging.
- Entregaveis:
  - escolha entre `tenant_id`, schema por cliente ou banco por cliente;
  - definicao do banco `psfinance_staging` ou origem externa;
  - variaveis de ambiente necessarias, sem valores sensiveis;
  - estrategia de migrations;
  - plano de rollback de banco.
- Saida esperada: autorizacao antes de criar banco, usuario ou migration.

### Etapa 3 - Base tecnica funcional minima

- Responsavel: GDSIS.
- Objetivo: implementar a primeira base funcional preservando o gate atual.
- Entregaveis:
  - estrutura de controllers, services, repositories e models;
  - configuracao segura de banco;
  - migration versionada;
  - healthcheck com checagem de banco quando aprovado;
  - testes focais de backend.
- Saida esperada: branch propria, pull request contra `staging`, merge em
  `staging` e validacao na porta `5001`.

### Etapa 4 - Interface e validacao funcional

- Responsavel: GDSIS.
- Objetivo: disponibilizar a primeira tela ou API funcional para homologacao.
- Entregaveis:
  - fluxo navegavel ou endpoint funcional;
  - validacoes de entrada;
  - tratamento de erro;
  - evidencias de navegador ou `curl`;
  - regressao de `/health`, `/gate` e `/staging/psfinance`.
- Saida esperada: staging homologavel como funcional, nao apenas tecnico.

### Etapa 5 - Preparacao futura de producao

- Responsavel: GDSIS, somente apos homologacao.
- Objetivo: preparar relatorio de promocao sem executar producao.
- Entregaveis:
  - comparacao `staging` contra `main`;
  - analise de banco de producao somente leitura;
  - scripts aprovados;
  - plano de deploy;
  - plano de validacao;
  - plano de rollback;
  - recomendacao tecnica.
- Saida esperada: pedido de autorizacao formal para Thiago, se o CEO desejar
  promover.

## Recomendacao do GDSIS

Nao promover o PSFINANCE para producao neste momento.

Recomendo manter o staging tecnico ativo e iniciar a Etapa 1 com decisao
explicita do primeiro fluxo funcional e do modelo multicliente. Depois disso, a
evolucao deve ocorrer em subtarefas pequenas, cada uma em branch propria criada
da `staging`, com pull request contra `staging`, deploy de staging e validacao
obrigatoria na porta `5001`.

## Proximas acoes

1. Submeter este plano para revisao do CEO/Thiago.
2. Apos aprovacao, criar subtarefa de definicao do MVP funcional.
3. Em seguida, criar subtarefa tecnica de decisao de banco e multicliente.
4. Somente depois iniciar implementacao funcional.

## Arquivos relacionados

- `src/app.py` - Aplicacao Flask atual de homologacao, healthcheck e gate.
- `requirements.txt` - Dependencias atuais sem driver de banco ou ORM.
- `.env.example` - Variaveis de exemplo sem URL real de banco.
- `docs/PLA-836-localizacao-base-real-psfinance.md` - Evidencia de ausencia de
  base real em operacao.
- `docs/decisoes.md` - Registro das decisoes tecnicas permanentes do projeto.
