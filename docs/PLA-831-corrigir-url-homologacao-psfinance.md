# PLA-831 - Corrigir URL de homologacao do PSFINANCE

## Objetivo

Corrigir a URL publica de homologacao do PSFINANCE que abria JSON diretamente,
entregando uma pagina HTML para acesso humano e preservando as rotas tecnicas
usadas por healthcheck e gate de staging.

## Skills consultadas

- `plansmart-governanca-desenvolvimento`
- `plansmart-projeto-psfinance`
- `plansmart-projeto-vps-sistemas`

## Regra aplicada

- A URL principal de homologacao deve ser uma pagina de acesso humano.
- `/health` e `/gate` continuam como endpoints JSON tecnicos para validacao.
- A porta corporativa `5001` deve continuar validavel.
- Nao houve alteracao de banco, producao, segredos ou variaveis de ambiente.

## Arquivos alterados

- `src/app.py` - Alterada a rota de entrada para retornar HTML em vez de JSON.
- `docs/decisoes.md` - Registrada a decisao de separar pagina de homologacao e endpoints tecnicos.
- `docs/PLA-831-corrigir-url-homologacao-psfinance.md` - Documentadas a demanda, regra e validacao da entrega.

## Validacao local

Validar com o teste focal da aplicacao Flask:

```bash
.venv/bin/python - <<'PY'
from src.app import app

client = app.test_client()

for path in ["/", "/staging/psfinance", "/staging/psfinance/"]:
    response = client.get(path)
    print(path, response.status_code, response.content_type)
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
    assert b"PSFINANCE" in response.data

for path in ["/health", "/gate", "/staging/psfinance/health", "/staging/psfinance/gate"]:
    response = client.get(path)
    print(path, response.status_code, response.content_type)
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")
PY
```

## Validacao esperada em staging

Apos merge na `staging` e deploy na VPS (Servidor Virtual Privado) Sistemas:

```bash
curl -sS -I http://vps69143.publiccloud.com.br/staging/psfinance
curl -sS -o /tmp/pla831_health.json -w "HEALTH_HTTP_STATUS=%{http_code}\n" \
  http://vps69143.publiccloud.com.br/staging/psfinance/health
curl -sS -o /tmp/pla831_gate.json -w "GATE_HTTP_STATUS=%{http_code}\n" \
  http://vps69143.publiccloud.com.br:5001/staging/psfinance/gate
```

Resultado esperado:

- URL principal retorna `Content-Type: text/html` e HTTP (Protocolo de Transferencia de Hipertexto) 200.
- Healthcheck retorna JSON com `status=healthy`.
- Gate na porta `5001` retorna JSON com `status=healthy`.
