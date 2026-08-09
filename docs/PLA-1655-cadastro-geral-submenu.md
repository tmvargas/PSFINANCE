# PLA-1655 - Cadastro Geral dentro de Apoio

## Escopo

Corrigir a interpretacao da PLA-1655 para manter `APOIO` como unico menu
principal da area e posicionar `Cadastro Geral` como submenu expansivo dentro
dele.

## Checklist do esclarecimento de Thiago

- `APOIO` mantido como menu principal unico da area.
- `Cadastro Geral` removido como grupo principal separado.
- `Cadastro Geral` criado como submenu expansivo dentro de `APOIO`.
- Itens dentro de `Cadastro Geral`: `Credor`, `Plano Financeiro`, `Empresa`,
  `Centro de Custo` e `Conta`.
- Correcao recorrente em 2026-08-08: removido o segundo `APOIO` visivel que
  permanecia como item/titulo de submenu; `APOIO` agora aparece uma unica vez
  por estado visual.
- Ajuste pos-revisao em 2026-08-08: menu aberto preservado e menu compacto
  corrigido para exibir o acionador de `Cadastro Geral`, usando o mesmo icone
  do submenu aberto, sem expor `APOIO` como item acionavel no estado compacto.
- Ajuste pos-rejeicao em 2026-08-09: removido o titulo textual adicional
  `Cadastro Geral` do flyout compacto, alinhando o comportamento visual ao
  padrao real de `FINANCEIRO > Contas a Pagar`, que mostra somente o acionador
  compacto e os itens do submenu.
- Ajuste pos-revisao CEO em 2026-08-09: removidos os titulos internos
  redundantes do submenu aberto de `Cadastro Geral`, incluindo o segundo
  `APOIO` que ainda existia no HTML como `.submenu-title`, e substituidas as
  evidencias principais por screenshots que mostram a hierarquia aberta e o
  flyout compacto com os itens.
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
- `docs/evidencias/PLA-1655/recorrencia-desktop-apoio-unico-cadastro-geral.png`
  - desktop com `APOIO` unico e `Cadastro Geral` expandido.
- `docs/evidencias/PLA-1655/recorrencia-compacto-flyout-apoio-unico-cadastro-geral.png`
  - menu compacto/flyout com `APOIO` unico, `Cadastro Geral` e os cinco itens.
- `docs/evidencias/PLA-1655/recorrencia-mobile-apoio-unico-cadastro-geral.png`
  - mobile com flyout aberto mostrando a mesma hierarquia.
- `docs/evidencias/PLA-1655/ajuste-compacto-menu-aberto-preservado.png` -
  menu aberto com `APOIO > Cadastro Geral` preservado.
- `docs/evidencias/PLA-1655/ajuste-compacto-flyout-apoio.png` - menu compacto
  com o icone de `APOIO` acionando o flyout.
- `docs/evidencias/PLA-1655/ajuste-compacto-flyout-comparativo-gerencial.png`
  - comparacao com outro flyout compacto equivalente.
- `docs/evidencias/PLA-1655/corrige-icone-compacto-comparativo.png` -
  comparacao do menu compacto entre `Gerencial Financeiro` e `Cadastro Geral`,
  demonstrando o mesmo padrao de acionador por submenu.
- `docs/evidencias/PLA-1655/corrige-icone-compacto-flyout-cadastro-geral.png`
  - flyout aberto pelo acionador compacto de `Cadastro Geral`.
- `docs/evidencias/PLA-1655/corrige-icone-menu-aberto-preservado.png` - menu
  aberto preservando `APOIO > Cadastro Geral`.
- `docs/evidencias/PLA-1655/compacto-contas-pagar-referencia.png` - referencia
  real do compacto/flyout de `FINANCEIRO > Contas a Pagar`.
- `docs/evidencias/PLA-1655/compacto-cadastro-geral-corrigido.png` -
  compacto/flyout corrigido de `Cadastro Geral`, sem titulo textual adicional.
- `docs/evidencias/PLA-1655/menu-aberto-hierarquia-preservada.png` - menu
  aberto com `APOIO > Cadastro Geral` preservado.
- `docs/evidencias/PLA-1655/revisao-ceo-menu-aberto-apoio-cadastro-geral.png`
  - menu aberto com `APOIO` uma unica vez, `Cadastro Geral` expandido e itens
  `Credor`, `Plano Financeiro`, `Empresa`, `Centro de Custo` e `Conta`.
- `docs/evidencias/PLA-1655/revisao-ceo-compacto-flyout-cadastro-geral-itens.png`
  - menu compacto com o acionador de `Cadastro Geral` abrindo flyout lateral
  com os cinco itens, sem titulo textual adicional e sem segundo `APOIO`.
- `docs/evidencias/PLA-1655/revisao-ceo-compacto-flyout-contas-pagar-referencia.png`
  - referencia visual equivalente de `FINANCEIRO > Contas a Pagar` no estado
  compacto, usada para comparar o padrao de flyout.
- `docs/evidencias/PLA-1655/revisao-ceo-mobile-flyout-cadastro-geral-itens.png`
  - viewport mobile com o mesmo flyout de `Cadastro Geral` e os cinco itens.

## Validacao local

- `.venv/bin/python -m compileall src financeiro templates`
- `git diff --check`
- Playwright Python: validou que existe apenas um `group-title` `APOIO`, que
  nao existe `group-title` `CADASTRO GERAL`, e que os cinco itens esperados
  estao dentro de `CADASTRO GERAL`.
- Playwright Python da correcao recorrente: validou em desktop, compacto/flyout
  e mobile que ha exatamente um `APOIO` visivel, nenhum item de menu/submenu
  paralelo chamado `APOIO`, `Cadastro Geral` aninhado no grupo `APOIO`,
  `aria-expanded=true`, e os itens exatamente na ordem `Credor`, `Plano
  Financeiro`, `Empresa`, `Centro de Custo`, `Conta`.
- Playwright Python do ajuste compacto: validou que o estado aberto preserva
  `APOIO > Cadastro Geral`; no estado compacto, a lista aberta fica oculta, o
  acionador visivel e `APOIO`, o clique abre o flyout com `Cadastro Geral` e os
  cinco itens, com comportamento equivalente ao flyout de `Gerencial
  Financeiro`.
- Playwright Python da correcao do icone compacto: validou que, em
  `.sidebar-compact`, o acionador visivel possui
  `data-menu-node="cadastro-geral-compacto"`, `aria-label="Expandir Cadastro
  Geral"`, icone `#icon-landmark` e rotulo acessivel `Cadastro Geral`, sem
  `APOIO` como acionador compacto.
- Playwright Python da correcao pos-rejeicao: comparou `Contas a Pagar` e
  `Cadastro Geral` no estado compacto/flyout e validou que ambos exibem somente
  itens do submenu, sem `.submenu-title` visivel ou texto adicional de titulo no
  flyout compacto.
- Playwright Python da revisao CEO: validou que o menu aberto nao inicia
  compacto, possui exatamente um `.group-title` `APOIO`, nao possui
  `.submenu-title` `APOIO`, abre `[data-menu-node="cadastro-geral"]` com
  `aria-expanded=true` e exibe exatamente os itens `Credor`,
  `Plano Financeiro`, `Empresa`, `Centro de Custo`, `Conta`.
- Playwright Python da revisao CEO no compacto/mobile: validou
  `[data-menu-node="cadastro-geral-compacto"]`, `aria-expanded=true`,
  ausencia de `.submenu-title`, ausencia de acionador compacto
  `data-menu-node="apoio"` e os cinco itens esperados no flyout.
- `curl http://127.0.0.1:5001/health`: HTTP 200, `status=healthy`.
- `curl http://127.0.0.1:5001/financeiro/credores?open=cadastro-geral`: HTTP
  200.

## Matriz objetiva da correcao recorrente

| Estrutura exigida | Evidencia |
| --- | --- |
| `APOIO` como unico grupo/menu principal da area | Um unico `.group-title` `APOIO`; nenhum `.nav-label` de menu chamado `APOIO`. |
| Sem segundo `APOIO` como header, grupo, item, flyout ou submenu paralelo | Um unico `APOIO` visivel por estado: grupo no desktop; titulo do flyout no compacto/mobile. |
| `Cadastro Geral` dentro de `APOIO` | `[data-menu-node="cadastro-geral"]` localizado dentro do `.menu-group` de `APOIO`. |
| Itens dentro de `Cadastro Geral` | DOM retornou exatamente `Credor`, `Plano Financeiro`, `Empresa`, `Centro de Custo`, `Conta`. |
| Rotas preservadas | Links mantidos para as rotas existentes de credores, plano, empresas, centros de custo e contas. |

## Matriz objetiva do ajuste compacto

| Estrutura exigida | Evidencia |
| --- | --- |
| Menu aberto preservado | `.menu-list.open-only` contem `[data-menu-node="cadastro-geral"]` com os cinco itens na ordem validada. |
| Compacto acionado por `Cadastro Geral` | Em `.sidebar-compact`, o no visivel e `[data-menu-node="cadastro-geral-compacto"]`, com `aria-label="Expandir Cadastro Geral"` e icone `#icon-landmark`. |
| Flyout compacto abre como os demais menus | Clique no botao de `Cadastro Geral` define `aria-expanded=true` e exibe `.submenu`, igual ao teste aplicado em `Gerencial Financeiro`. |
| `APOIO` nao aparece como acionador compacto | O DOM visivel do estado compacto nao possui botao, rotulo ou `data-menu-node` de acionador `APOIO`. |
| `Cadastro Geral` acessivel no flyout compacto | Flyout de `Cadastro Geral` exibe os itens `Credor`, `Plano Financeiro`, `Empresa`, `Centro de Custo`, `Conta`, sem titulo textual adicional. |
| Escopo restrito | Sem alteracao de rotas, banco de dados, migrations, permissoes, `main` ou producao. |

## Matriz objetiva da correcao pos-rejeicao

| Estrutura exigida | Evidencia |
| --- | --- |
| Padrao comparavel de `Contas a Pagar` | Flyout compacto de `Contas a Pagar` nao possui `.submenu-title` e exibe apenas `Titulo` e `Baixa`. |
| `Cadastro Geral` sem titulo textual adicional no compacto | Flyout compacto de `Cadastro Geral` nao possui `.submenu-title` visivel e exibe apenas `Credor`, `Plano Financeiro`, `Empresa`, `Centro de Custo`, `Conta`. |
| Hierarquia aberta preservada | Menu aberto continua com `APOIO > Cadastro Geral > Credor / Plano Financeiro / Empresa / Centro de Custo / Conta`. |
| Escopo restrito | Sem alteracao de rotas, banco de dados, migrations, permissoes, `main` ou producao. |

## Matriz objetiva da revisao CEO

| Ponto devolvido pelo CEO | Evidencia atualizada |
| --- | --- |
| Screenshots anteriores nao comprovavam a hierarquia aberta | `revisao-ceo-menu-aberto-apoio-cadastro-geral.png` mostra `APOIO` como grupo unico, `Cadastro Geral` expandido e os cinco itens diretamente abaixo. |
| Screenshots anteriores nao comprovavam o flyout compacto | `revisao-ceo-compacto-flyout-cadastro-geral-itens.png` mostra o flyout lateral aberto pelo acionador compacto de `Cadastro Geral` com os cinco itens. |
| Faltava comparacao com menu equivalente | `revisao-ceo-compacto-flyout-contas-pagar-referencia.png` registra a referencia compacta de `Contas a Pagar`, sem titulo textual adicional, para comparar o mesmo padrao visual. |
| Risco de segundo `APOIO` ainda visivel | Playwright validou ausencia de `.submenu-title` `APOIO` e ausencia de acionador compacto `data-menu-node="apoio"`; o template removeu o segundo `APOIO` interno. |
| Responsividade do flyout | `revisao-ceo-mobile-flyout-cadastro-geral-itens.png` mostra o flyout em viewport mobile com os mesmos itens. |

## Validacao na VPS de teste

- VPS: `vps69143.publiccloud.com.br` (`191.252.93.136`).
- Diretorio: `/opt/plansmart/sistemas/psfinance/staging/repo`.
- Branch remota publicada: `staging`.
- Commit da correcao do icone compacto integrado por PR #46:
  `8078f3630154d0e1ef1f1f24d85a68f7b4361c35`.
- Commit local da VPS validado em 2026-08-08:
  `8078f3630154d0e1ef1f1f24d85a68f7b4361c35`.
- `git status --short`: limpo.
- Servicos: `psfinance-staging` e `psfinance-staging-gate` ativos.
- Porta `5001`: `http://191.252.93.136:5001/health` retornou HTTP 200,
  `status=healthy`, `branch=staging` e commit
  `8078f3630154d0e1ef1f1f24d85a68f7b4361c35`.
- Rota visual validada:
  `http://191.252.93.136:5001/staging/psfinance/financeiro/credores?compact=1`.
- Playwright publico na porta `5001`: validou que o estado compacto publicado
  possui `[data-menu-node="cadastro-geral-compacto"]`,
  `aria-label="Expandir Cadastro Geral"`, icone `#icon-landmark`,
  `aria-expanded=true` apos clique e itens `Credor`, `Plano Financeiro`,
  `Empresa`, `Centro de Custo`, `Conta`, sem acionador compacto `APOIO`.
- Logs recentes do Gunicorn registraram reinicio normal e workers iniciados,
  sem erro critico de inicializacao.

## Registro de revisao GitHub

- Branch da correcao recorrente:
  `fix/PLA-1655-cadastro-geral-apoio-unico`.
- Commit head da branch da correcao recorrente:
  `450545f928442e51112f31934fbbc7173b399992`.
- A branch da correcao recorrente ja estava integrada em `origin/staging` pelo
  merge `df0110c` quando a revisao executiva solicitou a correcao documental.
- Como a branch original passou a ser ancestral de `origin/staging`, nao ha
  diff restante para abertura de PR retrospectivo daquela branch.
- A lacuna de revisao foi corrigida em branch propria
  `docs/PLA-1655-alinha-evidencias-revisao`, aberta contra `staging`, para
  registrar a evidencia GitHub e alinhar o commit validado da VPS.

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
