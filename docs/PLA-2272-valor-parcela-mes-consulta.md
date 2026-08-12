# PLA-2272 - Exibir valor da parcela no mes na consulta

## Projeto

PSFINANCE.

## Objetivo

Ajustar a consulta de titulos para que, ao filtrar por mes e ano, a coluna
`Valor` exiba o valor da parcela vencida no periodo consultado, e nao o valor
total do titulo parcelado.

## Regra aplicada

- Titulos com parcelas ativas continuam entrando na consulta mensal pelo
  vencimento de `titulo_parcela`.
- Titulos sem parcelas ativas continuam entrando pelo vencimento principal de
  `titulo`.
- Quando houver parcela ativa no periodo selecionado, a coluna `Valor` exibe a
  soma das parcelas ativas que vencem no mes consultado.
- Quando o titulo nao possuir parcelas ativas, a coluna `Valor` preserva o
  valor do titulo legado.
- O total `Valor` da consulta passa a somar os valores do periodo exibidos nas
  linhas.
- A coluna `Baixado` permanece considerando somente baixas com data dentro do
  mes filtrado.
- A coluna `Saldo` permanece calculada por `valor do periodo - baixado no mes`.
- A linha da consulta continua representando o titulo.

## Arquitetura

- Controller Flask: `financeiro/routes_titulos.py`.
- Template preservado: `templates/titulos_list.html`.
- Banco preservado: sem migration.

## Matriz de validacao focal

| Caso | Resultado esperado |
| --- | --- |
| Titulo parcelado com valor total de `300,00` e parcela de setembro de `100,00` | Consulta de setembro exibe `Valor 100,00`, e nao `300,00` |
| Baixa de setembro de `30,00` no titulo parcelado | Consulta de setembro exibe `Baixado 30,00` e `Saldo 70,00` |
| Titulo legado sem parcelas em setembro no valor de `50,00` | Consulta de setembro exibe `Valor 50,00` |
| Total do periodo com os dois registros acima | Total `Valor 150,00`, `Baixado 30,00` e `Saldo 120,00` |

## Validacao local

Comandos executados:

```bash
.venv/bin/python -m compileall src financeiro database.py models.py
git diff --check
```

Resultado: sem erro.

Teste funcional focal com banco SQLite temporario e `Flask test_client`:

- titulo parcelado com valor total de `300,00`, parcela ativa de setembro de
  `100,00` e baixa de setembro de `30,00`;
- titulo legado sem parcelas ativas em setembro no valor de `50,00`;
- consulta em `/financeiro/titulos?mes=9&ano=2026`;
- validado que o titulo parcelado aparece com vencimento `15/09/2026`;
- validado que o valor total do titulo parcelado `300,00` nao aparece na
  consulta mensal;
- validado que a consulta exibe `Valor 100,00` para o titulo parcelado,
  `Valor 50,00` para o titulo legado, total `Valor 150,00`, total `Baixado
  30,00` e total `Saldo 120,00`.

Saida validada:

```text
OK PLA-2272: consulta mensal exibe valor da parcela, totais do periodo e saldo mensal corretos
```

## Riscos e limites

- Nao houve migration.
- Nao houve alteracao em producao.
- Nao houve escrita em banco de producao.
- A alteracao nao cria vinculo direto entre baixa e parcela; baixas permanecem
  vinculadas ao titulo e filtradas por data dentro do mes.
