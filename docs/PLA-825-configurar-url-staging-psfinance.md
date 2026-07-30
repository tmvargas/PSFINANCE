# PLA-825 - Configurar URL /staging/psfinance do PSFINANCE

Data da execucao: 2026-07-30

## Escopo

Configurar o staging publico do PSFINANCE para responder tambem pelo caminho
`/staging/psfinance` na porta corporativa `5001`, preservando as rotas tecnicas
ja existentes e sem alterar producao, banco de dados ou segredos.

## Skills consultadas

- `plansmart-governanca-desenvolvimento`
- `plansmart-projeto-psfinance`
- `plansmart-projeto-vps-sistemas`

## Regra aplicada

- Trabalhar em branch propria criada a partir da `staging`.
- Preservar compatibilidade com `/`, `/health` e `/gate`.
- Manter validacao obrigatoria pela porta `5001`.
- Nao executar merge na `main`.
- Nao criar banco, tabela, usuario, migration ou escrita em banco.
- Nao registrar valores de tokens, senhas, chaves privadas ou `.env`.

## Alteracao tecnica

A aplicacao Flask passou a expor os mesmos retornos sob o prefixo:

```text
/staging/psfinance
/staging/psfinance/health
/staging/psfinance/gate
```

As rotas antigas permanecem ativas:

```text
/
/health
/gate
```

## URL publica esperada

```text
http://vps69143.publiccloud.com.br:5001/staging/psfinance
```

Healthcheck publico:

```text
http://vps69143.publiccloud.com.br:5001/staging/psfinance/health
```

Gate publico:

```text
http://vps69143.publiccloud.com.br:5001/staging/psfinance/gate
```

## Validacao local esperada

```bash
python -m flask --app src.app routes

python - <<'PY'
from src.app import app

client = app.test_client()
for path in [
    "/",
    "/health",
    "/gate",
    "/staging/psfinance",
    "/staging/psfinance/health",
    "/staging/psfinance/gate",
]:
    response = client.get(path)
    print(path, response.status_code, response.json["status"])
PY
```

Resultado esperado: HTTP (Protocolo de Transferencia de Hipertexto) 200 nas
rotas antigas e novas.

## Evidencia local obtida

```text
/ 200 ok PSFINANCE /staging/psfinance
/health 200 healthy PSFINANCE /staging/psfinance
/gate 200 healthy PSFINANCE /staging/psfinance
/staging/psfinance 200 ok PSFINANCE /staging/psfinance
/staging/psfinance/ 200 ok PSFINANCE /staging/psfinance
/staging/psfinance/health 200 healthy PSFINANCE /staging/psfinance
/staging/psfinance/gate 200 healthy PSFINANCE /staging/psfinance
```

## Validacao em staging esperada

Apos merge na `staging`, deploy da branch `staging` na VPS (Servidor Virtual
Privado) Sistemas e restart dos servicos:

```bash
curl -sS -o /tmp/pla825_index.json -w "INDEX_HTTP_STATUS=%{http_code}\n" \
  http://vps69143.publiccloud.com.br:5001/staging/psfinance

curl -sS -o /tmp/pla825_health.json -w "HEALTH_HTTP_STATUS=%{http_code}\n" \
  http://vps69143.publiccloud.com.br:5001/staging/psfinance/health

curl -sS -o /tmp/pla825_gate.json -w "GATE_HTTP_STATUS=%{http_code}\n" \
  http://vps69143.publiccloud.com.br:5001/staging/psfinance/gate
```

Resultado esperado: `INDEX_HTTP_STATUS=200`, `HEALTH_HTTP_STATUS=200` e
`GATE_HTTP_STATUS=200`.

## Evidencia de staging obtida

Branch publicada na VPS:

```text
staging
```

Commit validado inicialmente apos o deploy de codigo:

```text
c2982b916d58503c34c552cf3ecb8e2ed49941ce
```

Validacao publica:

```text
PUBLIC_INDEX_HTTP_STATUS=200
EFFECTIVE_URL=http://vps69143.publiccloud.com.br:5001/staging/psfinance
REMOTE_IP=191.252.93.136
PUBLIC_HEALTH_HTTP_STATUS=200
PUBLIC_GATE_HTTP_STATUS=200
```

Validacao interna na VPS:

```text
LOCAL_INDEX_HTTP_STATUS=200
LOCAL_HEALTH_HTTP_STATUS=200
LOCAL_GATE_HTTP_STATUS=200
LEGACY_GATE_HTTP_STATUS=200
APP_SERVICE=active
GATE_SERVICE=active
NGINX_SERVICE=active
HEAD=c2982b916d58503c34c552cf3ecb8e2ed49941ce
ORIGIN_STAGING=c2982b916d58503c34c552cf3ecb8e2ed49941ce
WORKTREE_STATUS_LINES=0
```

Resposta publica validada em
`http://vps69143.publiccloud.com.br:5001/staging/psfinance/gate`:

```json
{
  "app": "PSFINANCE",
  "base_path": "/staging/psfinance",
  "branch": "staging",
  "checks": {
    "psfinance_staging": {
      "http_status": 200,
      "ok": true,
      "url": "http://127.0.0.1:5104/health"
    }
  },
  "commit": "c2982b916d58503c34c552cf3ecb8e2ed49941ce",
  "environment": "staging-gate",
  "status": "healthy"
}
```

Os metadados `GIT_COMMIT` dos servicos `psfinance-staging.service` e
`psfinance-staging-gate.service` foram atualizados para o commit publicado.
Backups operacionais foram preservados em `/etc/systemd/system/` com prefixo
`*.bak.pla825-*`.

## Limites

- Nao houve alteracao em producao.
- Nao houve merge para `main`.
- Nao houve criacao ou alteracao de banco de dados.
- Nao foram registrados segredos, tokens, senhas ou conteudo de chaves.
