# PLA-814 - Liberacao de acesso ao staging do PSFINANCE

Data da execucao: 2026-07-30

## Escopo

Liberar acesso externo ao staging do PSFINANCE para Thiago na VPS (Servidor
Virtual Privado) Sistemas, preservando a branch `staging`, sem alterar
producao, sem criar banco de dados e sem expor segredos.

## Skills consultadas

- `plansmart-governanca-desenvolvimento`
- `plansmart-projeto-psfinance`
- `plansmart-projeto-vps-sistemas`

## Estado encontrado

- Repositorio oficial na VPS:
  `/opt/plansmart/sistemas/psfinance/staging/repo`.
- Branch publicada na VPS: `staging`.
- Commit validado: `ecf26919b9aaa8a8fd75a52a9011d509ea727259`.
- `HEAD` e `origin/staging` estavam iguais na VPS.
- Arvore de trabalho da VPS estava limpa.
- `psfinance-staging.service` estava `active`.
- `psfinance-staging-gate.service` estava `active`.
- Antes da liberacao, a porta `5001` estava ouvindo somente em `127.0.0.1`.
- A rota interna `http://127.0.0.1:5001/gate` retornava HTTP 200.
- A rota interna `http://127.0.0.1:5104/health` retornava HTTP 200.

## Alteracao operacional aplicada na VPS

- Instalado Nginx na VPS porque ainda nao estava disponivel.
- Criada a configuracao
  `/etc/nginx/sites-available/psfinance-staging-5001`.
- Habilitado o site
  `/etc/nginx/sites-enabled/psfinance-staging-5001`.
- Removido o site default do Nginx em `sites-enabled`.
- Ajustado `psfinance-staging-gate.service` para ouvir em
  `127.0.0.1:5105`.
- Mantido `psfinance-staging.service` em `127.0.0.1:5104`.
- Nginx passou a ouvir publicamente em `0.0.0.0:5001` e fazer proxy para
  `http://127.0.0.1:5105`.
- Backup do arquivo de service anterior:
  `/etc/systemd/system/psfinance-staging-gate.service.bak.pla814-20260730_175916`.

## Validacao

Comandos executados:

```bash
curl -sS -o /tmp/psfinance_gate_public_local.json -w "LOCAL_GATE_HTTP_STATUS=%{http_code}\n" \
  http://127.0.0.1:5001/gate

curl -sS -o /tmp/psfinance_health_internal.json -w "INTERNAL_HEALTH_HTTP_STATUS=%{http_code}\n" \
  http://127.0.0.1:5104/health

curl -sS -m 15 -o /tmp/pla814_psfinance_gate_external.json -w "EXTERNAL_GATE_HTTP_STATUS=%{http_code}\n" \
  http://vps69143.publiccloud.com.br:5001/gate
```

Resultado obtido:

```text
LOCAL_GATE_HTTP_STATUS=200
INTERNAL_HEALTH_HTTP_STATUS=200
EXTERNAL_GATE_HTTP_STATUS=200
APP_SERVICE=active
GATE_SERVICE=active
NGINX_SERVICE=active
BRANCH=staging
HEAD=ecf26919b9aaa8a8fd75a52a9011d509ea727259
ORIGIN_STAGING=ecf26919b9aaa8a8fd75a52a9011d509ea727259
WORKTREE_STATUS_LINES=0
```

Resposta externa validada:

```json
{
  "app": "PSFINANCE",
  "branch": "staging",
  "checks": {
    "psfinance_staging": {
      "http_status": 200,
      "ok": true,
      "url": "http://127.0.0.1:5104/health"
    }
  },
  "commit": "ecf26919b9aaa8a8fd75a52a9011d509ea727259",
  "environment": "staging-gate",
  "status": "healthy"
}
```

## URL liberada para Thiago

```text
http://vps69143.publiccloud.com.br:5001/gate
```

## Limites

- Nao houve alteracao em producao.
- Nao houve merge para `main`.
- Nao houve criacao ou alteracao de banco de dados.
- Nao foram registrados segredos, tokens, senhas ou conteudo de chaves.
- HTTPS e subdominio oficial continuam pendentes de definicao futura.
