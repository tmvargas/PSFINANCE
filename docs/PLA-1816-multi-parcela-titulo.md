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

## Evidencia visual local

- `docs/evidencias/PLA-1816/cadastro-titulo-multi-parcela.png` - Formulario de
  novo titulo com `Valor total`, `Data do 1º Vencimento` e `Parcelas`.
- `docs/evidencias/PLA-1816/guia-parcelas-editavel.png` - Guia de parcelas com
  edicao de numero, vencimento, valor, exclusao e inclusao de nova parcela.

## Pendencias

- Nao foi executado deploy em staging nem validacao na porta corporativa `5001`
  neste heartbeat.
- Ha migration preparada para staging. Nao houve escrita em banco de producao,
  variavel de ambiente, VPS ou producao.
