# PLA-2276 - Baixas por parcela

## Demanda

Alterar o fluxo de baixas do PSFINANCE para que a baixa seja vinculada a uma
parcela do titulo.

## Regra aplicada

- Cada nova baixa exige selecao de uma parcela ativa do titulo.
- O valor da baixa e limitado ao saldo da parcela selecionada.
- O saldo total do titulo continua considerando todas as baixas ativas.
- Baixas historicas sem `id_parcela` permanecem legiveis como registros
  legados.
- Na consulta mensal, baixas vinculadas passam a compor o `Pago no mes` pela
  parcela vencida no periodo. Baixas legadas sem parcela mantem fallback por
  data da baixa.

## Arquitetura

- Modelo: `Baixa` recebe relacionamento opcional com `TituloParcela`.
- Controller: `financeiro/routes_titulos.py` centraliza selecao, validacao e
  calculo de saldo por parcela.
- Templates: telas de baixa e consulta de baixas exibem parcela, saldos e
  registros legados.
- Banco: script SQL preparado para adicionar `baixa.id_parcela` e indice.

## Validacao local

Ambiente: `.venv` com SQLite temporario.

Comandos executados:

```bash
.venv/bin/python -m py_compile models.py financeiro/routes_titulos.py src/app.py
.venv/bin/python - <<'PY'
# teste funcional com Flask test_client e banco temporario
PY
```

Resultado:

```text
OK PLA-2276: baixa vinculada a parcela, limite por saldo da parcela e consulta mensal validada
```

Casos validados:

| Caso | Resultado |
| --- | --- |
| Abrir baixa de titulo com duas parcelas | Tela exibiu `Parcela 1` e `Parcela 2` com saldos |
| Baixar `150,00` em parcela com saldo `100,00` | Bloqueado com mensagem de saldo da parcela |
| Baixar `60,00` na parcela 1 | Baixa gravada com `id_parcela` da parcela 1 |
| Consultar baixas do titulo | Linha exibiu `1 - 10/09/2026` |
| Consultar setembro/2026 | Exibiu `Pago no mes` `60,00` e `Nao pago no mes` `40,00` |

## Pendencias para staging

- Aplicar `migrations/versions/20260812_pla2276_baixa_por_parcela.sql` no banco
  de staging antes de subir a branch integrada.
- Validar rota `/financeiro/titulos/<id>/baixar` e consulta mensal na porta
  corporativa `5001`.
- Produção exige Pacote de Produção e autorização expressa de Thiago.
