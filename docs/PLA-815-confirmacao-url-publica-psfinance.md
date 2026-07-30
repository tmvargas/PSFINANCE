# PLA-815 - Confirmacao da URL publica de homologacao do PSFINANCE

Data da execucao: 2026-07-30

## Escopo

Confirmar qual URL publica esta disponivel para Thiago acessar o staging do
PSFINANCE na VPS (Servidor Virtual Privado) Sistemas, sem alterar producao, sem
merge na `main`, sem criacao de banco de dados e sem exposicao de segredos.

## Skills consultadas

- `plansmart-governanca-desenvolvimento`
- `plansmart-projeto-psfinance`
- `plansmart-projeto-vps-sistemas`

## URL publica confirmada

```text
http://vps69143.publiccloud.com.br:5001/gate
```

URL auxiliar de healthcheck publico:

```text
http://vps69143.publiccloud.com.br:5001/health
```

## Validacao realizada

### DNS do subdominio planejado

O subdominio planejado ainda nao esta publicado em DNS:

```text
staging-psfinance.plansmart.com.br
```

Resultado obtido:

```text
curl: (6) Could not resolve host: staging-psfinance.plansmart.com.br
DOMAIN_GATE_HTTP_STATUS=000
```

### URL publica vigente

Comando externo executado a partir do workspace:

```bash
curl -sS -o /tmp/pla815-final-public-gate.json \
  -w 'PUBLIC_GATE_HTTP_STATUS=%{http_code}\nEFFECTIVE_URL=%{url_effective}\nREMOTE_IP=%{remote_ip}\n' \
  --connect-timeout 10 --max-time 20 \
  http://vps69143.publiccloud.com.br:5001/gate
```

Resultado:

```text
PUBLIC_GATE_HTTP_STATUS=200
EFFECTIVE_URL=http://vps69143.publiccloud.com.br:5001/gate
REMOTE_IP=191.252.93.136
```

Resposta validada:

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
  "commit": "b01f8048b3083beba1ff4e782d05ce9649ebc3aa",
  "environment": "staging-gate",
  "status": "healthy"
}
```

## Estado da VPS de teste

Diretorio validado:

```text
/opt/plansmart/sistemas/psfinance/staging/repo
```

Resultado:

```text
LOCAL_HEALTH_HTTP_STATUS=200
LOCAL_GATE_HTTP_STATUS=200
APP_SERVICE=active
GATE_SERVICE=active
NGINX_SERVICE=active
BRANCH=staging
HEAD=b01f8048b3083beba1ff4e782d05ce9649ebc3aa
ORIGIN_STAGING=b01f8048b3083beba1ff4e782d05ce9649ebc3aa
WORKTREE_STATUS_LINES=0
```

## Conclusao tecnica

A URL publica de homologacao atualmente confirmada para PSFINANCE e:

```text
http://vps69143.publiccloud.com.br:5001/gate
```

Ela usa HTTP (Protocolo de Transferencia de Hipertexto) na porta publica
corporativa `5001`, via Nginx, apontando para o gate interno do PSFINANCE. O
subdominio `staging-psfinance.plansmart.com.br` e HTTPS ainda ficam como
pendencia futura de infraestrutura/DNS.

## Limites

- Nao houve alteracao em producao.
- Nao houve merge para `main`.
- Nao houve criacao, alteracao ou escrita em banco de dados.
- Nao foram registrados segredos, tokens, senhas ou conteudo de chaves.
