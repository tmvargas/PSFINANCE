# PLA-2171 - Filtro por empresa na consulta de titulos

## Objetivo

Adicionar filtro por empresa na consulta de titulos do PSFINANCE, preservando o
filtro existente de mes e ano de vencimento e memorizando a ultima empresa
selecionada pelo usuario.

## Implementacao

- A rota `/financeiro/titulos` passou a carregar empresas ativas e aplicar
  `Titulo.id_empresa` quando uma empresa e selecionada.
- A preferencia fica salva na sessao assinada do Flask pela chave
  `titulos_filtro_id_empresa`.
- Ao acessar novamente a consulta sem `id_empresa` na URL, a empresa
  memorizada e reaplicada se ainda estiver ativa.
- Selecionar `Todas` ou informar empresa invalida/inativa remove a preferencia
  da sessao.
- Nao houve migration, alteracao de banco ou escrita em producao.

## Branches e commits

- Branch da tarefa: `pla-2171-filtro-empresa-titulos`.
- PR (Pull Request, solicitacao de revisao): `https://github.com/tmvargas/PSFINANCE/pull/58`.
- Commit funcional da tarefa: `d40b03d873af721836d3c1377048daef99ee3fe9`.
- Branch `staging` publicada inicialmente no commit
  `d40b03d873af721836d3c1377048daef99ee3fe9`.

## Validacao local

- `python3 -m compileall financeiro models.py database.py src/app.py`: sucesso.
- `git diff --check`: sucesso.
- Teste funcional com Flask test client e SQLite temporario:
  - filtro por empresa restringiu listagem e totais;
  - retorno a tela sem `id_empresa` reaplicou a empresa memorizada;
  - selecao de `Todas` limpou a preferencia.

## Validacao na VPS de staging

Executada na porta publica corporativa `5001` da VPS (Servidor Virtual Privado)
Sistemas.

| Caso | Resultado |
| --- | --- |
| `GET /health` | HTTP 200, `status=healthy`, `branch=staging`, `commit=d40b03d873af721836d3c1377048daef99ee3fe9`, `db_dialect=postgresql`, `database_url_source=PSFINANCE_STAGING_DATABASE_URL` |
| `GET /gate` | HTTP 200, `status=healthy`, check interno `psfinance_staging` com HTTP 200 |
| `GET /staging/psfinance/financeiro/titulos?mes=8&ano=2026` | HTTP 200 e campo `Empresa` presente |
| Selecao de empresa com cookie de sessao | HTTP 200 e empresa permaneceu `selected` no retorno sem `id_empresa` |
| Selecao de `Todas` | HTTP 200 e preferencia anterior removida |

## Evidencia visual

- `docs/evidencias/PLA-2171/filtro-empresa-titulos-staging-5001.png` -
  Screenshot da consulta de titulos no staging real com filtro de empresa
  visivel e empresa `1 - THIAGO` selecionada.

## Riscos e limites

- Nao houve alteracao em `main`.
- Nao houve deploy em producao.
- Nao houve escrita no banco de producao.
- Nao houve migration.
- A memorizacao e por sessao do navegador; nao cria preferencia global ou
  compartilhada entre usuarios.
