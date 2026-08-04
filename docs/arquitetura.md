# Arquitetura inicial - PSFINANCE

## Identificacao

PSFINANCE e o nome oficial do sistema financeiro da PlanSmart. `PSCONTROL`
permanece somente como referencia legada em documentos antigos.

## Principio

O PSFINANCE deve funcionar como sistema financeiro operacional da PlanSmart,
priorizando clareza, auditoria, isolamento de dados e manutencao simples.

Fluxo conceitual inicial:

```text
Entrada financeira
  -> Escopo por empresa e centro quando o modelo multiempresa for aprovado
  -> Titulos, baixas, contas, movimentacoes, plano financeiro e credores
  -> Indicadores, saldos, extratos, analises e evidencias operacionais
```

## Modelo multiempresa/multicentro

A arquitetura recomendada para evolucao multiempresa/multicentro esta
documentada em `docs/PLA-1221-multiempresa-multicentro-psfinance.md`.

Diretriz tecnica:

- manter uma base por ambiente nesta fase;
- isolar registros operacionais por `id_empresa` e `id_centro_custo`;
- aplicar filtro de escopo em todas as consultas operacionais;
- validar compatibilidade de escopo antes de baixas, movimentacoes,
  transferencias, anexos e relatorios;
- bloquear transferencias interempresa ate haver regra funcional explicita;
- preservar dados existentes com migration versionada e backfill controlado
  somente apos aprovacao.

## Decisoes ainda abertas

- Modelo final de isolamento multiempresa/multicentro.
- Se `Documento`, `PlanoDeContas` e `Credor` serao compartilhados entre
  empresas ou segregados por empresa/centro.
- Necessidade futura ou nao de `tenant_id` acima de empresa/centro.
- Modelo de usuarios e permissoes por escopo.
- API (Interface de Programacao de Aplicacoes) versionada para app iPhone.
- Dominio, HTTPS e configuracao final de staging/producao na VPS Sistemas.

## Regras de seguranca

- Separar ambiente local, homologacao e producao.
- Nunca versionar credenciais.
- Registrar origem e data de informacoes importantes.
