# PLA-1816 - Multi parcela em titulo

## Projeto

PSFINANCE.

## Objetivo

Permitir que o cadastro de titulo gere varias parcelas em uma unica entrada,
preservando a estrutura atual de titulos, baixas e anexos.

## Regra aplicada

- O campo `Parcelas` fica disponivel em novo titulo e copia de titulo.
- Quantidade valida: 1 a 120 parcelas.
- Uma parcela mantem o comportamento anterior.
- Duas ou mais parcelas geram titulos separados, com vencimento mensal a partir
  da data de vencimento informada.
- O valor total e dividido por centavos; eventual resto fica nas primeiras
  parcelas.
- O numero do documento recebe sufixo `NN/TT`, por exemplo `NF123-01/03`.
- Edicao de titulo existente permanece como titulo unico.
- Anexos em parcelamento devem ser incluidos posteriormente em cada titulo
  gerado.

## Arquitetura

- Controller Flask: `financeiro/routes_titulos.py`.
- Template: `templates/titulo_form.html`.
- Banco: sem alteracao de schema e sem migration.
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

Resultado confirmado:

```text
[('NF123-01/03', 33.34, '2026-01-31'), ('NF123-02/03', 33.33, '2026-02-28'), ('NF123-03/03', 33.33, '2026-03-31')]
```

## Pendencias

- Nao foi executado deploy em staging nem validacao na porta corporativa `5001`
  neste heartbeat.
- Nao houve alteracao de banco, variavel de ambiente, VPS ou producao.
