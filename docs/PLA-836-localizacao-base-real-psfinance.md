# PLA-836 - Localizacao da base real do PSFINANCE em operacao

## Objetivo

Localizar a base de dados real usada pelo PSFINANCE em operacao e registrar a
evidencia tecnica sem expor segredos, credenciais ou dados operacionais.

## Escopo e governanca

- Projeto: `PSFINANCE`.
- Skills consultadas:
  - `plansmart-governanca-desenvolvimento`;
  - `plansmart-projeto-psfinance`;
  - `plansmart-projeto-vps-sistemas`.
- Ambiente analisado: VPS (Servidor Virtual Privado)
  `vps69143.publiccloud.com.br` (`191.252.93.136`).
- Acoes executadas: somente leitura em codigo, servicos, Nginx, portas e
  configuracao operacional.
- Producao: nao houve alteracao, deploy, migration ou escrita em banco.

## Evidencias confirmadas em 2026-07-31

### Repositorio em operacao na VPS

- Diretorio operacional de staging:
  `/opt/plansmart/sistemas/psfinance/staging/repo`.
- Branch ativa: `staging`.
- Commit local da VPS:
  `e7c1b1ed566dc9f715d676bc3b94d6cd632a6376`.
- Commit `origin/staging`:
  `e7c1b1ed566dc9f715d676bc3b94d6cd632a6376`.
- `git status --short`: sem alteracoes locais.

### Servicos ativos

- `psfinance-staging.service`: ativo, Gunicorn servindo `src.app:app` em
  `127.0.0.1:5104`.
- `psfinance-staging-gate.service`: ativo, Gunicorn servindo `src.app:app` em
  `127.0.0.1:5105`.
- Nginx publica:
  - porta `80` para `/staging/psfinance`;
  - porta `5001` para o gate corporativo.
- Portas observadas:
  - `127.0.0.1:5104` com Gunicorn;
  - `0.0.0.0:5001` com Nginx.

### Validacao HTTP

- `http://vps69143.publiccloud.com.br/staging/psfinance`: HTTP 200.
- `http://vps69143.publiccloud.com.br/staging/psfinance/gate`: HTTP 200.
- Gate retornou:
  - `app=PSFINANCE`;
  - `environment=staging-gate`;
  - `branch=staging`;
  - `commit=e7c1b1ed566dc9f715d676bc3b94d6cd632a6376`;
  - healthcheck interno `http://127.0.0.1:5104/health` com HTTP 200.

## Resultado da busca pela base de dados

Nao foi localizada base PostgreSQL real em uso pelo PSFINANCE na operacao atual.

Evidencias:

- Os arquivos `systemd` dos servicos `psfinance-staging.service` e
  `psfinance-staging-gate.service` nao declaram `DATABASE_URL` nem
  `PSFINANCE_STAGING_DATABASE_URL`.
- O ambiente dos processos Gunicorn do PSFINANCE nao possui variavel de banco
  configurada.
- O servico local `postgresql` na VPS esta `inactive`.
- O comando `psql` nao esta instalado no ambiente analisado.
- Nao existe listener local em `5432`.
- Nao foi localizado `Docker` na VPS.
- Nao foram encontrados arquivos `docker-compose` operacionais do PSFINANCE.
- Nao existe diretorio produtivo em:
  - `/opt/plansmart/sistemas/psfinance/production`;
  - `/opt/plansmart/sistemas/psfinance/prod`;
  - `/opt/plansmart/sistemas/pscontrol`;
  - `/opt/plansmart/sistemas/PSCONTROL`.
- O codigo atual em `src/app.py` nao usa camada de persistencia.
- `requirements.txt` contem somente `Flask` e `gunicorn`, sem driver de banco,
  ORM ou biblioteca PostgreSQL.

## Conclusao tecnica

O PSFINANCE que esta em operacao na VPS Sistemas neste momento e um staging
tecnico de homologacao, sem persistencia real conectada.

A "base real" do PSFINANCE ainda nao esta criada, configurada ou consumida pela
aplicacao em operacao. A referencia `psfinance_staging` aparece somente como
nome planejado/documental e como chave de healthcheck no gate, nao como banco
PostgreSQL existente ou conectado.

## Riscos

- Qualquer desenvolvimento funcional que dependa de persistencia ainda precisa
  de decisao formal de banco, usuario, variavel de ambiente e modelo
  multicliente.
- Nao ha base produtiva do PSFINANCE validada para promocao.
- A existencia de URL publica de homologacao nao deve ser interpretada como
  existencia de banco operacional.

## Proximas acoes recomendadas

1. Confirmar com Thiago se o PSFINANCE deve criar primeiro
   `psfinance_staging` ou se deve conectar a uma base externa ja existente.
2. Definir o modelo multicliente antes de qualquer uso produtivo:
   `tenant_id`, schema por cliente ou banco por cliente.
3. Somente apos aprovacao, preparar script/migration e variaveis de ambiente
   sem registrar valores sensiveis.
4. Manter qualquer analise de producao somente leitura ate autorizacao expressa.

## Arquivos relacionados

- `src/app.py` - Aplicacao Flask de staging sem uso de banco.
- `requirements.txt` - Dependencias atuais sem driver PostgreSQL/ORM.
- `.env.example` - Variaveis de exemplo sem URL real de banco.
- `docs/PLA-747-preparacao-staging-psfinance.md` - Historico da preparacao
  inicial do staging.
- `docs/PLA-825-configurar-url-staging-psfinance.md` - Historico da URL publica
  de staging.
