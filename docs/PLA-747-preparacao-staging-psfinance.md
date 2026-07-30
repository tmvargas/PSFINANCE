# PLA-747 - Preparacao do staging do PSFINANCE na VPS Sistemas

Data da execucao: 2026-07-30

## Escopo

Preparar uma base minima e versionada para o staging do PSFINANCE na VPS
(Servidor Virtual Privado) Sistemas, respeitando `staging` como branch de teste,
sem alterar producao, sem criar banco de dados e sem registrar segredos.

## Skills consultadas

- `plansmart-governanca-desenvolvimento`
- `plansmart-projeto-psfinance`
- `plansmart-projeto-vps-sistemas`

## Fatos confirmados

- Repositorio oficial: `https://github.com/tmvargas/PSFINANCE.git`.
- `origin/main` e `origin/staging` existem e apontavam para
  `23821c7786e98c5c489c60c2ac60760e3cdc17c1` no inicio da execucao.
- A VPS alvo responde por SSH (Secure Shell, acesso remoto seguro) com o usuario
  `root` e a chave operacional `/paperclip/.ssh/plansmart_sistemas_vps69143`.
- A VPS executa Ubuntu 24.04.4 LTS.
- `git`, `python3` e `systemctl` existem na VPS.
- Nao foram encontrados Docker nem Nginx disponiveis no `PATH` durante o
  inventario inicial.
- Antes da preparacao, `/opt/plansmart/sistemas/psfinance` nao existia.
- O pacote `python3.12-venv` foi instalado na VPS porque a criacao do ambiente
  virtual falhou inicialmente por ausencia do `ensurepip`.
- Apos a preparacao, a VPS ficou com a branch `staging` publicada em
  `/opt/plansmart/sistemas/psfinance/staging/repo`.
- Commit validado na VPS: `6a3eb0c82c7168d45a01f51d8aa5700abd2abc66`.
- `HEAD` e `origin/staging` estavam iguais na VPS apos o deploy.
- `git status --short` estava limpo na copia da VPS apos o deploy.

## Decisao aplicada

Usar uma aplicacao Flask minima com Gunicorn para fornecer:

- `/health` como healthcheck do PSFINANCE;
- `/gate` como rota de gate corporativo na porta `5001`, com verificacao do
  healthcheck interno quando `PSFINANCE_STAGING_HEALTH_URL` estiver definido.

Esta decisao e operacional e provisoria para validar staging. A evolucao do
produto deve preservar `PSFINANCE` como nome oficial e manter `PSCONTROL`
somente como referencia legada.

## Portas de staging

- `127.0.0.1:5104`: aplicacao PSFINANCE staging.
- `127.0.0.1:5001`: gate corporativo de staging.

## Servicos criados na VPS

- `psfinance-staging.service`: Gunicorn servindo `src.app:app` em
  `127.0.0.1:5104`.
- `psfinance-staging-gate.service`: Gunicorn servindo `src.app:app` em
  `127.0.0.1:5001` e validando `http://127.0.0.1:5104/health`.

Os dois servicos foram habilitados com `systemd` e estavam `active` na
validacao.

## Banco de dados

Nenhum banco, usuario, tabela, migration ou escrita em banco foi criado nesta
fase. A variavel planejada para uso futuro permanece
`PSFINANCE_STAGING_DATABASE_URL`, sem valor versionado.

## Validacao esperada

Na VPS, apos deploy da branch `staging`:

```bash
curl -sS -o /tmp/psfinance_health.json -w 'HTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:5104/health

curl -sS -o /tmp/psfinance_gate.json -w 'HTTP_STATUS=%{http_code}\n' \
  http://127.0.0.1:5001/gate
```

Resultado esperado: `HTTP_STATUS=200` nas duas rotas.

## Evidencia obtida

```text
HEALTH_HTTP_STATUS=200
GATE_HTTP_STATUS=200
SERVICE_APP=active
SERVICE_GATE=active
BRANCH=staging
HEAD=6a3eb0c82c7168d45a01f51d8aa5700abd2abc66
ORIGIN_STAGING=6a3eb0c82c7168d45a01f51d8aa5700abd2abc66
```

As portas `5001` e `5104` estavam ouvindo somente em `127.0.0.1`.

## Pendencias

- Nginx e HTTPS publico ainda nao foram configurados porque Nginx nao estava
  instalado no inventario inicial e a skill exige confirmacao dos subdominios
  oficiais antes da exposicao publica.
- Nenhum banco foi criado; a criacao de banco, usuario ou migration depende de
  autorizacao futura.
- A VPS indicou kernel mais novo disponivel apos instalacao de pacote, mas nao
  foi realizado reboot por nao fazer parte do escopo autorizado.
