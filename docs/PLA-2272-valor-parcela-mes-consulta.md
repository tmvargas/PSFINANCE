# PLA-2272 - Exibir valor da parcela no mes na consulta

## Projeto

PSFINANCE.

## Objetivo

Ajustar a consulta de titulos para que, ao filtrar por mes e ano, a tela mostre
explicitamente a leitura de caixa mensal sem ocultar o valor total do titulo.

## Regra aplicada

- Titulos com parcelas ativas continuam entrando na consulta mensal pelo
  vencimento de `titulo_parcela`.
- Titulos sem parcelas ativas continuam entrando pelo vencimento principal de
  `titulo`.
- Cada linha passa a exibir `Valor total do titulo`.
- Cada linha passa a exibir `Valor da parcela no mes`, calculado pela soma das
  parcelas ativas que vencem no periodo selecionado.
- Quando o titulo nao possuir parcelas ativas, `Valor da parcela no mes`
  preserva o valor do titulo legado filtrado pelo vencimento principal.
- Cada linha passa a exibir `Pago no mes`, considerando somente baixas com data
  dentro do mes filtrado.
- Cada linha passa a exibir `Nao pago no mes`, calculado por
  `valor da parcela no mes - pago no mes`.
- Os totais da consulta passam a separar `Valor total dos titulos`,
  `Valor da parcela no mes`, `Pago no mes` e `Nao pago no mes`.
- A linha da consulta continua representando o titulo.

## Arquitetura

- Controller Flask: `financeiro/routes_titulos.py`.
- Template preservado: `templates/titulos_list.html`.
- Banco preservado: sem migration.

## Matriz de validacao focal

| Caso | Resultado esperado |
| --- | --- |
| Titulo parcelado com valor total de `300,00` e parcela de setembro de `100,00` | Consulta de setembro exibe `Valor total do titulo 300,00` e `Valor da parcela no mes 100,00` |
| Baixa de setembro de `30,00` no titulo parcelado | Consulta de setembro exibe `Pago no mes 30,00` e `Nao pago no mes 70,00` |
| Titulo legado sem parcelas em setembro no valor de `50,00` | Consulta de setembro exibe `Valor total do titulo 50,00` e `Valor da parcela no mes 50,00` |
| Total do periodo com os dois registros acima | Totais exibem `Valor total dos titulos 350,00`, `Valor da parcela no mes 150,00`, `Pago no mes 30,00` e `Nao pago no mes 120,00` |

## Ajuste apos revisao executiva

Em 2026-08-12, a revisao executiva reprovou a entrega anterior porque a tela
ainda usava os rotulos ambiguos `Valor`, `Baixado` e `Saldo`, nao deixando
claro o valor total do titulo e a composicao financeira do mes.

Correcao aplicada:

- o backend passou a enviar campos explicitos para a tela:
  `valor_total_titulo`, `valor_parcela_mes`, `pago_mes` e `nao_pago_mes`;
- o resumo superior e o rodape da tabela passaram a exibir totais separados
  para os mesmos conceitos;
- o template deixou de apresentar `Valor`, `Baixado` e `Saldo` como leitura
  principal da consulta mensal;
- o status visual deixou de usar `Baixado` e passou a indicar `Pago no mes` ou
  `Nao pago no mes`, coerente com a leitura de caixa do filtro.

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
- validado que a consulta exibe `Valor total do titulo`, `Valor da parcela no
  mes`, `Pago no mes` e `Nao pago no mes`;
- validado que o titulo parcelado exibe `300,00` como valor total do titulo e
  `100,00` como valor da parcela no mes;
- validado que a consulta exibe `Pago no mes 30,00` e `Nao pago no mes 70,00`
  para o titulo parcelado;
- validado que o titulo legado exibe `50,00` como valor total do titulo e
  `50,00` como valor da parcela no mes;
- validado que os totais exibem `Valor total dos titulos 350,00`,
  `Valor da parcela no mes 150,00`, `Pago no mes 30,00` e
  `Nao pago no mes 120,00`;
- validado que os rotulos antigos `Valor`, `Baixado` e `Saldo` nao permanecem
  como leitura principal do bloco financeiro.

Saida validada:

```text
OK PLA-2272: consulta exibe total do titulo, parcela no mes, pago no mes e nao pago no mes
```

## Validacao na VPS de staging

Executada em 2026-08-12 na porta publica corporativa `5001`.

| Caso | Resultado |
| --- | --- |
| Branch da VPS | `staging` |
| Commit da VPS | `c30d9856fed132a63528b4d3afd5e63c55d2d6e1` |
| `origin/staging` na VPS | `c30d9856fed132a63528b4d3afd5e63c55d2d6e1` |
| `git status` na VPS | limpo |
| `psfinance-staging` | `active` |
| `psfinance-staging-gate` | `active` |
| `GET http://127.0.0.1:5104/health` | HTTP 200 |
| `GET http://127.0.0.1:5001/health` | HTTP 200 |
| `GET http://127.0.0.1:5001/financeiro/titulos?mes=6&ano=2026` | HTTP 200 |

Validacao funcional publicada:

- consulta em Jun/2026 na porta `5001`;
- titulo `59` exibido com vencimento `11/06/2026`;
- coluna `Valor` exibindo `R$ 30.01`, correspondente ao valor da parcela do
  periodo;
- total `Valor` exibindo `R$ 30.01`;
- valor total anterior do titulo, `R$ 40.01`, nao aparece na consulta mensal.

Evidencia visual:

- `docs/evidencias/PLA-2272/consulta-titulos-valor-parcela-junho-5001.png` -
  Screenshot da consulta publicada na porta `5001`, filtrada por Jun/2026,
  comprovando a exibicao do valor da parcela no mes.

## Riscos e limites

- Nao houve migration.
- Nao houve alteracao em producao.
- Nao houve escrita em banco de producao.
- A alteracao nao cria vinculo direto entre baixa e parcela; baixas permanecem
  vinculadas ao titulo e filtradas por data dentro do mes.
