# PLA-2264 - Consulta de titulos parcelados por mes

## Projeto

PSFINANCE.

## Objetivo

Corrigir a consulta de titulos para que o filtro de mes e ano considere os
vencimentos das parcelas ativas quando o titulo possui parcelamento.

## Regra aplicada

- Titulos com parcelas ativas entram na consulta mensal pelo vencimento de
  `titulo_parcela`.
- Titulos sem parcelas ativas continuam entrando pelo vencimento principal de
  `titulo`.
- Quando houver parcela ativa no periodo selecionado, a coluna `Vencimento`
  exibe o vencimento da parcela do periodo, nao apenas o primeiro vencimento do
  titulo.
- O filtro por empresa permanece aplicado ao titulo e tambem restringe os
  titulos parcelados.
- A linha da consulta continua representando o titulo; valores, baixas e saldo
  permanecem no nivel do titulo, porque as baixas ainda nao sao vinculadas a
  uma parcela especifica.

## Arquitetura

- Controller Flask: `financeiro/routes_titulos.py`.
- Template preservado: `templates/titulos_list.html`.
- Banco preservado: sem migration.

## Validacao local

Comandos executados:

```bash
.venv/bin/python -m compileall src financeiro database.py models.py
git diff --check
```

Resultado: sem erro.

Teste funcional focal com banco SQLite temporario e `Flask test_client`:

- titulo parcelado com vencimento principal em agosto e parcela ativa em
  setembro aparece em `/financeiro/titulos?mes=9&ano=2026`;
- a coluna `Vencimento` exibe `15/09/2026`, correspondente a parcela do
  periodo, e nao `15/08/2026`;
- titulo legado sem parcelas ativas continua aparecendo pelo vencimento do
  proprio titulo em setembro;
- titulo parcelado de outra empresa aparece sem filtro e deixa de aparecer ao
  aplicar `id_empresa` da Empresa A.

Saida validada:

```text
OK PLA-2264: consulta mensal usa parcelas ativas, preserva legado sem parcelas e respeita filtro por empresa
```

## Riscos e limites

- Nao houve alteracao em `main`.
- Nao houve deploy em producao.
- Nao houve escrita em banco de producao.
- Nao houve migration.
- A consulta ainda trata baixas no nivel do titulo, pois o modelo atual
  `baixa` nao possui vinculo com `titulo_parcela`.
