# PLA-1480 - Ajustar menu Apoio e estado inicial fechado

## Objetivo

Ajustar o menu lateral do PSFINANCE para que o grupo `APOIO` funcione como
menu expansivel e para que os submenus iniciem fechados no carregamento normal
das telas.

## Escopo executado

- Convertido o grupo `APOIO` em item expansivel unico, com submenu contendo
  `Empresa`, `Centro de Custo`, `Contas`, `Credor` e `Plano Financeiro`.
- Removida a lista direta de itens de apoio no menu aberto.
- Removida a abertura automatica inicial dos submenus por endpoint ativo.
- Definido o menu lateral como compacto no carregamento padrao quando nao ha
  preferencia salva pelo usuario.
- Preservado o destaque do item principal quando a rota atual pertence ao seu
  grupo.
- Preservado o parametro `?open=` para evidencia controlada de flyout no menu
  compacto.

## Validacao prevista

- Abrir uma rota padrao, como `/financeiro`, e confirmar que nenhum submenu
  inicia aberto.
- Abrir uma rota de apoio, como `/financeiro/empresas`, e confirmar que
  `APOIO` fica destacado, mas seu submenu inicia fechado.
- Clicar em `APOIO` e confirmar que o submenu exibe `Empresa`,
  `Centro de Custo`, `Contas`, `Credor` e `Plano Financeiro`.
- Acionar o estado compacto e confirmar que o icone de `APOIO` abre o mesmo
  submenu em flyout lateral.

## Validacao executada em 2026-08-06

- `python3 -m compileall src financeiro models.py database.py`: sem erro.
- `git diff --check`: sem erro.
- Porta `5001` local em modo `staging`: `/gate` retornou `status=healthy`,
  `branch=staging` e `commit=9502730`.
- Playwright com `localStorage` limpo confirmou que `/financeiro/` inicia com
  `sidebar-compact=true`, nenhum `.menu-node.submenu-open` e `APOIO` com
  `aria-expanded=false`.
- Playwright confirmou que o clique no icone de `APOIO` abre o flyout com
  `Empresa`, `Centro de Custo`, `Contas`, `Credor` e `Plano Financeiro`.
- Playwright confirmou que `/financeiro/contas` responde com a tela `Contas`,
  mantem `APOIO` e `Contas` destacados, mas inicia sem submenu aberto e com
  `aria-expanded=false`.

## Evidencias visuais

- `docs/mockups/evidencias/PLA-1480-menu-inicial-compacto.png`
- `docs/mockups/evidencias/PLA-1480-menu-apoio-contas.png`
- `docs/mockups/evidencias/PLA-1480-rota-contas-fechada.png`

## Impacto

A alteracao e restrita ao template base e ao comportamento visual do menu.
Nao altera controllers, services, models, banco de dados, migrations,
variaveis de ambiente, VPS, `main` ou producao.
