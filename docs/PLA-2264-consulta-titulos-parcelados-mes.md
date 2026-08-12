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
- A coluna `Valor` continua exibindo o valor total do titulo.
- A coluna `Baixado` e o total de baixado passam a considerar somente baixas
  com data dentro do mes filtrado.
- A coluna `Saldo` e o total em aberto passam a considerar o valor vencido no
  periodo, descontando o que foi baixado no mesmo mes.
- O filtro por empresa permanece aplicado ao titulo e tambem restringe os
  titulos parcelados.
- A linha da consulta continua representando o titulo; valores, baixas e saldo
  de periodo sao calculados no backend da consulta.

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
- valor total exibido do titulo parcelado permanece `300,00`;
- baixa de agosto nao entra no total de setembro;
- baixa de setembro entra no total pago do periodo;
- saldo em aberto do periodo usa `valor da parcela de setembro - baixa de
  setembro`.

Saida validada:

```text
OK PLA-2264: parcela do mes, valor total do titulo, pago no mes, nao pago no mes e filtro por empresa validados
```

Matriz focal validada:

| Caso | Resultado |
| --- | --- |
| Sem filtro de empresa em setembro | `PARC-001`, `LEG-001` e `OUTRA-001` retornam; totais: valor `440,00`, baixado `30,00`, aberto `210,00` |
| Com filtro da Empresa A em setembro | Apenas `PARC-001` e `LEG-001` retornam; totais: valor `350,00`, baixado `30,00`, aberto `120,00` |
| Titulo parcelado em setembro | `PARC-001` exibe vencimento `15/09/2026`, valor total `300,00`, baixado no mes `30,00` e aberto do periodo `70,00` |

## Validacao na VPS de staging

Executada em 2026-08-12 na porta publica corporativa `5001`.

| Caso | Resultado |
| --- | --- |
| `GET /health` | HTTP 200, `status=healthy`, `branch=staging`, `commit=02d6f336af943d8859fda55068f5824b7e5a21be`, `db_dialect=postgresql` |
| `GET /gate` | HTTP 200, `status=healthy`, check interno `psfinance_staging` com HTTP 200 |
| `GET /staging/psfinance/financeiro/titulos?mes=6&ano=2026` | HTTP 200 |
| Consulta publicada em Jun/2026 | Titulo `59` aparece com vencimento `11/06/2026`, valor total `40,01`, baixado no mes `0,00` e saldo do periodo `30,01` |

Evidencia visual:

- `docs/evidencias/PLA-2264/consulta-titulos-parcelados-junho-5001.png` -
  Screenshot da consulta publicada na porta `5001`, filtrada por Jun/2026,
  comprovando o titulo parcelado exibido pelo vencimento da parcela do periodo
  e os totais do mes.

## Riscos e limites

- Nao houve alteracao em `main`.
- Nao houve deploy em producao.
- Nao houve escrita em banco de producao.
- Nao houve migration.
- As baixas sao filtradas por `Baixa.data` no mes selecionado e vinculadas ao
  titulo, pois o modelo atual `baixa` nao possui vinculo direto com
  `titulo_parcela`.
