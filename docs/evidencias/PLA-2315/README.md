# [PLA-2315](/PLA/issues/PLA-2315) - Evidencia tecnica

## Staging

- VPS: `vps69143.publiccloud.com.br`
- Porta: `5001`
- Branch publicada: `staging`
- Commit publicado: `f7e605d119ae67505405d96c7d2eb0b98a9d69b8`
- Banco: `postgresql` via `PSFINANCE_STAGING_DATABASE_URL`

## Validacao

| Caso | Resultado |
| --- | --- |
| `GET /health` | HTTP 200, `status=healthy`, `commit=f7e605d119ae67505405d96c7d2eb0b98a9d69b8` |
| `GET /gate` | HTTP 200, `status=healthy`, `commit=f7e605d119ae67505405d96c7d2eb0b98a9d69b8` |
| `GET /financeiro/titulos/1/baixar` | HTTP 200, HTML contem `id_parcela`, `data-saldo`, `valor_baixa`, `js-money`, `sugerirSaldoParcela` e `Intl.NumberFormat('pt-BR')` |
| `GET /financeiro/titulos/58/baixar` | HTTP 200, tela com parcela unica selecionada e `Valor da baixa` sugerido como `1.200,00` |

## Regra validada

- Ao selecionar uma parcela, o formulario possui o saldo da parcela em `data-saldo` para sugerir o valor da baixa.
- O campo `Valor da baixa` possui mascara pt-BR em reais e continua editavel para baixa parcial.
- A validacao backend existente continua impedindo valor maior que o saldo da parcela.

## Artefatos

- `docs/evidencias/PLA-2315/baixa-parcela-5001.html` - HTML capturado da rota real publicada na porta `5001`.
- `docs/evidencias/PLA-2315/baixa-parcela-5001.png` - Screenshot da rota de baixa com parcela ja quitada, comprovando preservacao visual da tela.
- `docs/evidencias/PLA-2315/baixa-parcela-saldo-aberto-5001.html` - HTML capturado da rota real com parcela em aberto.
- `docs/evidencias/PLA-2315/baixa-parcela-saldo-aberto-5001.png` - Screenshot da rota real com parcela selecionada automaticamente e valor sugerido pela mascara pt-BR.
