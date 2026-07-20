# Arquitetura inicial - PSCONTROL

## Principio

O PSCONTROL deve funcionar como sistema de controle operacional da PlanSmart, priorizando clareza, auditoria e manutencao simples.

Fluxo conceitual inicial:

```text
Entrada de dados / rotinas
  -> Organizacao por cliente, projeto e status
  -> Indicadores e acompanhamento
  -> Alertas, relatorios ou proximas acoes
```

## Decisoes ainda abertas

- Stack principal: Flask, FastAPI, Node, outro.
- Banco de dados: PostgreSQL, outro.
- Modelo de usuarios e permissoes.
- Integracoes com Paperclip, Notion ou GitHub.
- Deploy na VPS SISTEMAS.

## Regras de seguranca

- Separar ambiente local, homologacao e producao.
- Nunca versionar credenciais.
- Registrar origem e data de informacoes importantes.

