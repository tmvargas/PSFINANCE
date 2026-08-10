# PLA-1816 - Multi parcela em titulo

## Projeto

PSFINANCE.

## Objetivo

Permitir que o cadastro de titulo gere varias parcelas em uma unica entrada,
preservando o titulo como registro principal e controlando as parcelas em tabela
relacional propria.

## Regra aplicada

- O campo `Parcelas` fica disponivel em novo titulo e copia de titulo.
- Quantidade valida: 1 a 120 parcelas.
- Uma parcela cria o titulo e uma parcela relacional.
- Duas ou mais parcelas criam um unico titulo com parcelas relacionais.
- O vencimento mensal parte da Data do 1º Vencimento.
- O dia original e preservado quando existir no mes seguinte; se nao existir,
  usa o ultimo dia valido e volta ao dia original quando ele existir novamente.
- O valor total e dividido por centavos; eventual resto fica nas primeiras
  parcelas.
- A guia de parcelas permite editar vencimento e valor, excluir parcela e
  incluir nova parcela.
- Ao salvar a guia de parcelas, o valor total do titulo passa a refletir a soma
  das parcelas ativas.

## Arquitetura

- Controller Flask: `financeiro/routes_titulos.py`.
- Models: `models.py`.
- Templates: `templates/titulo_form.html`, `templates/titulo_parcelas_form.html`
  e `templates/titulos_list.html`.
- Banco: migration `migrations/versions/20260810_pla1816_titulo_parcela.sql`.
- Documento de decisao: `docs/decisoes.md`.

## Validacao local

Comando executado:

```bash
.venv/bin/python -m compileall src financeiro database.py models.py
```

Resultado: compilacao concluida sem erro.

Teste focal executado com banco SQLite temporario:

- POST em `/financeiro/titulos/novo`;
- documento `NF123`;
- valor total `100,00`;
- vencimento inicial `2026-01-31`;
- quantidade `3`.

Resultado esperado:

```text
titulo NF123 com valor total 100.00
parcelas: 1 = 33.34 / 2026-01-31; 2 = 33.33 / 2026-02-28; 3 = 33.33 / 2026-03-31
```

Casos obrigatorios adicionais:

- 5 parcelas com vencimento inicial `2027-01-29` devem gerar `2027-01-29`,
  `2027-02-28`, `2027-03-29`, `2027-04-29` e `2027-05-29`.
- Alterar parcelas pela guia deve recalcular o valor total do titulo.
- Incluir nova parcela pela guia deve persistir a parcela e recalcular o total.

## Matriz funcional validada

Validacao executada com banco SQLite temporario e cliente Flask, sem uso de
dados de producao.

| Caso | Entrada | Resultado esperado | Resultado obtido |
| --- | --- | --- | --- |
| Criacao obrigatoria em 5 parcelas | valor `100,00`, primeiro vencimento `2027-01-29`, parcelas `5` | Criar um titulo, parcelas 1 a 5 e vencimentos `2027-01-29`, `2027-02-28`, `2027-03-29`, `2027-04-29`, `2027-05-29` | Aprovado |
| Divisao por centavos | valor `100,00`, primeiro vencimento `2026-01-31`, parcelas `3` | Valores `33,34`, `33,33`, `33,33`; vencimentos `2026-01-31`, `2026-02-28`, `2026-03-31` | Aprovado |
| Quantidade invalida | parcelas `0` | Rejeitar validacao e nao criar titulo | Aprovado |
| Guia de parcelas | alterar valores, excluir parcela 3 e incluir parcela 4 | Persistir parcelas ativas 1, 2 e 4; recalcular valor total para `95,00`; manter vencimento do titulo na primeira parcela ativa | Aprovado |
| Healthcheck Flask | `GET /health` | HTTP 200 e `status=healthy` | Aprovado |
| Gate Flask | `GET /gate` | HTTP 200 e `status=healthy` | Aprovado |

Comando de validacao focal executado:

```bash
.venv/bin/python - <<'PY'
# Script focal com banco temporario, seed minimo e chamadas Flask test_client.
# Saidas verificadas:
# OK caso obrigatorio: 5 parcelas 29/01/2027 -> 2027-01-29, 2027-02-28, 2027-03-29, 2027-04-29, 2027-05-29
# OK distribuicao centavos: 100,00 em 3x -> [33.34, 33.33, 33.33]
# OK validacao: quantidade 0 rejeitada
# OK edicao guia: excluir/incluir/recalcular total -> 95,00
# OK health/gate Flask: healthy healthy pla-1816-multi-parcela-titulo 9b8efbc
PY
```

## Validacao na porta corporativa 5001

Validacao executada em `2026-08-10`, com processo Flask local em
`127.0.0.1:5001`, ambiente `staging`, banco SQLite isolado em
`instance/pla1816_staging_gate/financeiro.db`, branch
`pla-1816-multi-parcela-titulo` e commit `9b8efbc`.

Comando do processo:

```bash
PYTHONPATH=. PORT=5001 APP_ENV=staging GIT_BRANCH=pla-1816-multi-parcela-titulo GIT_COMMIT=9b8efbc PSFINANCE_INSTANCE_PATH="$PWD/instance/pla1816_staging_gate" DATABASE_URL="sqlite:///$PWD/instance/pla1816_staging_gate/financeiro.db" .venv/bin/python src/app.py
```

Rotas verificadas:

| Rota | Resultado |
| --- | --- |
| `GET http://127.0.0.1:5001/health` | HTTP 200, `status=healthy`, `app=PSFINANCE`, `environment=staging`, `branch=pla-1816-multi-parcela-titulo`, `commit=9b8efbc` |
| `GET http://127.0.0.1:5001/gate` | HTTP 200, `status=healthy`, `checks={}` |
| `GET http://127.0.0.1:5001/staging/psfinance/health` | HTTP 200 |
| `GET http://127.0.0.1:5001/staging/psfinance/financeiro/titulos` | HTTP 200 |

Trecho de log do servico local:

```text
127.0.0.1 - - [10/Aug/2026 06:32:38] "GET /gate HTTP/1.1" 200 -
127.0.0.1 - - [10/Aug/2026 06:32:38] "GET /health HTTP/1.1" 200 -
127.0.0.1 - - [10/Aug/2026 06:32:38] "GET /staging/psfinance/health HTTP/1.1" 200 -
127.0.0.1 - - [10/Aug/2026 06:32:38] "GET /staging/psfinance/financeiro/titulos HTTP/1.1" 200 -
```

## Evidencia visual local

- `docs/evidencias/PLA-1816/cadastro-titulo-multi-parcela.png` - Formulario de
  novo titulo com `Valor total`, `Data do 1º Vencimento` e `Parcelas`.
- `docs/evidencias/PLA-1816/guia-parcelas-editavel.png` - Guia de parcelas com
  edicao de numero, vencimento, valor, exclusao e inclusao de nova parcela.

## Pendencias

- A validacao da porta corporativa `5001` foi executada em processo local de
  staging neste heartbeat.
- Ha migration preparada para staging. Nao houve escrita em banco de producao,
  variavel de ambiente, VPS ou producao.
