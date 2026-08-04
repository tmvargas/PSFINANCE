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

## Arquitetura

- `models.py` recebeu os modelos `Empresa` e `CentroCusto`.
- `financeiro/routes_empresa.py` concentra o CRUD de empresa.
- `financeiro/routes_centro_custo.py` concentra o CRUD de centro de custo.
- `templates/base.html` recebeu os itens `Empresa` e `Centro de Custo` no menu
  `APOIO`.
- As telas novas seguem o padrao Bootstrap ja usado nos cadastros existentes.

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
- Screenshot local com Playwright:
  - `docs/mockups/evidencias/PLA-1235-empresas.png`;
  - `docs/mockups/evidencias/PLA-1235-centros-custo.png`.

## Impacto e limites

Esta entrega cria tabelas novas quando a aplicacao inicializar em ambiente sem
essas tabelas, pelo mecanismo atual `Base.metadata.create_all`. Nao altera
tabelas operacionais existentes, nao faz backfill de dados historicos, nao
cria migration produtiva, nao altera VPS, `main` ou producao.
