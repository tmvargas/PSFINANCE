# PLA-1655 - Cadastro Geral dentro de Apoio

## Escopo

Corrigir a interpretacao da PLA-1655 para manter `APOIO` como unico menu
principal da area e posicionar `CADASTRO GERAL` como submenu expansivo dentro
dele.

## Checklist do esclarecimento de Thiago

- `APOIO` mantido como menu principal unico da area.
- `CADASTRO GERAL` removido como grupo principal separado.
- `CADASTRO GERAL` criado como submenu expansivo dentro de `APOIO`.
- Itens dentro de `CADASTRO GERAL`: `Credor`, `Plano Financeiro`, `Empresa`,
  `Centro de Custo` e `Conta`.
- Rotas existentes preservadas.
- Banco de dados, migrations, permissoes, `main` e producao nao alterados.

## Evidencias visuais

- `docs/evidencias/PLA-1655/correcao-desktop-apoio-cadastro-geral.png` -
  desktop com `APOIO` aberto e `CADASTRO GERAL` expandido.
- `docs/evidencias/PLA-1655/correcao-mobile-responsivo-apoio-cadastro-geral.png`
  - viewport responsivo com a hierarquia visivel.
- `docs/evidencias/PLA-1655/correcao-mobile-estreito-estrutura-apoio-cadastro-geral.png`
  - viewport estreito com validacao de DOM da estrutura.
- `docs/evidencias/PLA-1655/correcao-compacto-flyout-apoio-cadastro-geral.png`
  - menu compacto/flyout com `APOIO` e `CADASTRO GERAL` aninhado.
- `docs/evidencias/PLA-1655/correcao-vps-5001-apoio-cadastro-geral.png` -
  validacao visual publicada na VPS de teste pela porta `5001`.

## Validacao local

- `.venv/bin/python -m compileall src financeiro templates`
- `git diff --check`
- Playwright Python: validou que existe apenas um `group-title` `APOIO`, que
  nao existe `group-title` `CADASTRO GERAL`, e que os cinco itens esperados
  estao dentro de `CADASTRO GERAL`.
- `curl http://127.0.0.1:5001/health`: HTTP 200, `status=healthy`.
- `curl http://127.0.0.1:5001/financeiro/credores?open=cadastro-geral`: HTTP
  200.

## Validacao na VPS de teste

- VPS: `vps69143.publiccloud.com.br` (`191.252.93.136`).
- Diretorio: `/opt/plansmart/sistemas/psfinance/staging/repo`.
- Branch remota publicada: `staging`.
- Commit local da VPS: `9481df3e3f21dd7f434a271086249bc78fc33797`.
- Commit `origin/staging`: `9481df3e3f21dd7f434a271086249bc78fc33797`.
- `git status --short`: limpo.
- Servicos: `psfinance-staging` e `psfinance-staging-gate` ativos.
- Porta `5001`: `http://191.252.93.136:5001/health` retornou HTTP 200,
  `status=healthy`, `branch=staging` e commit
  `9481df3e3f21dd7f434a271086249bc78fc33797`.
- Rota visual validada:
  `http://191.252.93.136:5001/staging/psfinance/financeiro/credores?open=cadastro-geral`.
- Logs recentes do Gunicorn registraram reinicio normal e workers iniciados,
  sem erro critico de inicializacao.

## Observacao de banco local

Durante teste focal com `app.test_client()`, as rotas `/financeiro/` e
`/financeiro/contas` retornaram erro no SQLite local por ausencia da coluna
`conta.id_empresa`. Esse erro e preexistente no banco local usado como fallback
e nao decorre da alteracao de menu. As rotas de cadastro usadas para validar o
menu responderam HTTP 200.

## Risco

Risco baixo. A alteracao ficou restrita ao template base, ao comportamento de
submenu aninhado no JavaScript do menu e a documentacao de decisao/evidencia.
Nao houve alteracao de controller, model, banco, migration, permissao,
integracao ou regra de negocio.
