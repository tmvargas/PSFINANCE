# PSCONTROL

Projeto PlanSmart para estruturar sistemas de controle interno, acompanhamento operacional, gestao de rotinas, indicadores, usuarios e processos.

## Status

Projeto iniciado em 2026-07-20.

VPS planejada:

- Nome interno: SISTEMAS
- Host: `vps69143.publiccloud.com.br`
- IP: `191.252.93.136`

## Objetivo inicial

Criar uma base organizada para evoluir o PSCONTROL como sistema PlanSmart de controle operacional.

## Estrutura

```text
PSCONTROL/
  README.md
  AGENTS.md
  docs/
    arquitetura.md
    backlog-inicial.md
    decisoes.md
    validacao-inicial.md
  scripts/
  src/
  tests/
```

## Regras iniciais

- Trabalhar em branch propria, nunca direto na `main`.
- Nao versionar tokens, chaves, dados de clientes ou informacoes operacionais sensiveis.
- Registrar decisoes tecnicas em `docs/decisoes.md`.
- Confirmar stack, banco e rotina de deploy antes de implementar telas definitivas.

