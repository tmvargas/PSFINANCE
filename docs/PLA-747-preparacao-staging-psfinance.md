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
