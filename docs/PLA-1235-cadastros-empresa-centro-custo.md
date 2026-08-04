# PLA-1235 - Cadastros Empresa e Centro de Custo PSFINANCE

## Objetivo

Implementar no PSFINANCE os cadastros funcionais `APOIO > Empresa` e
`APOIO > Centro de Custo`, vinculados a `PLA-1179`, usando a decisao
arquitetural consolidada na `PLA-1221`.

## Regra aplicada

- `Empresa` aceita somente `EMPRESA`, `SPE` e `SCP`.
- `Empresa` exige codigo e nome.
- `Centro de Custo` exige empresa ativa, codigo e nome.
- O codigo de empresa ativa nao pode ser duplicado.
- O codigo de centro de custo ativo nao pode ser duplicado dentro da mesma
  empresa.
- Empresa com centro de custo ativo nao pode ser desativada.
- Centro de custo e empresa usam desativacao logica pelo campo `deleted`.
- Novos titulos e movimentacoes financeiras exigem empresa ativa e centro de
  custo ativo pertencente a empresa selecionada.

## Arquitetura

- `models.py` recebeu os modelos `Empresa` e `CentroCusto`.
- `financeiro/routes_empresa.py` concentra o CRUD de empresa.
- `financeiro/routes_centro_custo.py` concentra o CRUD de centro de custo.
- `financeiro/regras_empresa_centro.py` centraliza a listagem e validacao do
  par empresa/centro de custo usado por titulos e movimentacoes.
- `templates/base.html` recebeu os itens `Empresa` e `Centro de Custo` no menu
  `APOIO`.
- `templates/titulo_form.html`, `templates/movimentacao_form.html` e
  `templates/movimentacao_edit_form.html` receberam selecao obrigatoria de
  empresa e centro de custo.
- `templates/titulos_list.html` e `templates/movimentacoes_list.html` exibem
  empresa e centro de custo para conferencia operacional.
- As telas novas seguem o padrao Bootstrap ja usado nos cadastros existentes.
- `migrations/versions/20260804_pla1235_empresa_centro_custo.sql` prepara o
  SQL versionado para criacao das tabelas e inclusao dos vinculos em titulos e
  movimentacoes em staging, sem execucao em producao.

## Validacao executada

- `python3 -m compileall src financeiro models.py database.py`
- `.venv/bin/python` com `app.test_client()` e banco SQLite temporario:
  - `GET /financeiro/empresas` retornou HTTP 200;
  - `POST /financeiro/empresas/nova` criou empresa valida;
  - tipo de empresa fora de `EMPRESA`, `SPE` e `SCP` foi bloqueado;
  - duplicidade de empresa ativa foi bloqueada;
  - `GET /financeiro/centros-custo` retornou HTTP 200;
  - `POST /financeiro/centros-custo/novo` criou centro de custo valido;
  - duplicidade de centro de custo ativo por empresa foi bloqueada;
  - edicao de centro de custo retornou sucesso;
  - desativacao de empresa com centro de custo ativo foi bloqueada.
- `.venv/bin/python` com `app.test_client()` e banco SQLite temporario:
  - criacao de titulo sem empresa/centro foi bloqueada;
  - criacao de titulo com centro de custo de outra empresa foi bloqueada;
  - criacao de titulo com empresa/centro validos foi persistida;
  - criacao de movimentacao sem empresa/centro foi bloqueada;
  - criacao de movimentacao com empresa/centro validos foi persistida.
- Screenshot local com Playwright:
  - `docs/mockups/evidencias/PLA-1235-empresas.png`;
  - `docs/mockups/evidencias/PLA-1235-centros-custo.png`.

## Impacto e limites

Esta entrega cria tabelas novas quando a aplicacao inicializar em ambiente sem
essas tabelas, pelo mecanismo atual `Base.metadata.create_all`. Em bancos ja
existentes, a migration preparada adiciona colunas opcionais em `titulo` e
`movimentacao_conta`; a obrigatoriedade e aplicada no backend para novos
registros e edicoes. Nao faz backfill de dados historicos, nao executa
migration produtiva, nao altera `main` ou producao.
