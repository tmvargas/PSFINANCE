# PLA-1036 - Menu encolhido com icones e flyout lateral

## Objetivo

Ajustar o mockup estatico do menu inicial do PSFINANCE para que o menu
encolhido apresente icones reais de navegacao e abra submenus em flyout lateral.

## Escopo executado

- Restaurada a lista de navegacao no estado `?compact=1`, mantendo rotulos e
  grupos ocultos.
- Ajustado o menu encolhido para uma coluna estreita com icones reais.
- Incluido flyout lateral para `Contas a Pagar`, `Caixas e Bancos`,
  `Gerencial Financeiro` e `APOIO` no desktop quando o menu esta encolhido.
- Preservado comportamento horizontal no mobile, com flyout abaixo do item.
- Permitida evidencia por URL com `?compact=1&open=contas-pagar` e
  `?compact=1&open=caixas-bancos`.

## Validacao executada

- Abrir `docs/mockups/PLA-1016-layout-inicial.html?compact=1`.
- Confirmar que aparecem apenas icones reais do menu principal.
- Abrir `docs/mockups/PLA-1016-layout-inicial.html?compact=1&open=contas-pagar`.
- Confirmar que o submenu `Título` e `Baixa` aparece em flyout lateral.
- Abrir `docs/mockups/PLA-1016-layout-inicial.html?compact=1&open=caixas-bancos`.
- Confirmar que o submenu `Movimentações` e `Extrato` aparece em flyout lateral.
- Abrir `docs/mockups/PLA-1016-layout-inicial.html?compact=1&open=gerencial`.
- Confirmar que o submenu `Gerencial Financeiro` aparece em flyout lateral.
- Abrir `docs/mockups/PLA-1016-layout-inicial.html?compact=1&open=apoio`.
- Confirmar que o submenu `Credor` e `Plano Financeiro` aparece em flyout
  lateral.
- Geradas evidencias visuais em:
  - `docs/mockups/evidencias/PLA-1036-menu-aberto-desktop.png`;
  - `docs/mockups/evidencias/PLA-1036-menu-compacto-icones.png`;
  - `docs/mockups/evidencias/PLA-1036-menu-compacto-flyout-contas-pagar.png`;
  - `docs/mockups/evidencias/PLA-1036-menu-compacto-flyout-caixas-bancos.png`;
  - `docs/mockups/evidencias/PLA-1036-menu-compacto-flyout-gerencial.png`;
  - `docs/mockups/evidencias/PLA-1036-menu-compacto-flyout-apoio.png`;
  - `docs/mockups/evidencias/PLA-1036-menu-compacto-flyout-mobile.png`.

## Checklist dos criterios

- [x] Estado aberto mantem os nomes `Home`, `FINANCEIRO`, `Contas a Pagar`,
  `Título`, `Baixa`, `Caixas e Bancos`, `Movimentações`, `Extrato`,
  `GERENCIAL`, `Gerencial Financeiro`, `APOIO`, `Credor` e `Plano Financeiro`.
- [x] Estado encolhido mostra somente icones reais, sem rotulos/textos de menu.
- [x] Estado encolhido nao mostra grupos ou submenus abertos por padrao.
- [x] Icone de `Contas a Pagar` abre flyout lateral com `Título` e `Baixa`.
- [x] Icone de `Caixas e Bancos` abre flyout lateral com `Movimentações` e
  `Extrato`.
- [x] Icone de `Gerencial Financeiro` abre flyout lateral com
  `Gerencial Financeiro`.
- [x] Icone de `APOIO` abre flyout lateral com `Credor` e `Plano Financeiro`.
- [x] Todos os icones usados sao pictograficos reais em SVG, nao siglas/badges.
- [x] Nomes rejeitados `Credores`, `ANALISE` e `CADASTROS` nao foram usados.

## Impacto

A alteracao e documental/visual e nao altera templates da aplicacao Flask,
rotas, banco de dados, variaveis de ambiente, VPS, `main` ou producao.
