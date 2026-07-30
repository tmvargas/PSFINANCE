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

## Limites

- Nao houve alteracao em producao.
- Nao houve merge para `main`.
- Nao houve criacao ou alteracao de banco de dados.
- Nao foram registrados segredos, tokens, senhas ou conteudo de chaves.
