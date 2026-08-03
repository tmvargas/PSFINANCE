# PLA-1036 - Menu encolhido com icones e flyout lateral

## Objetivo

Ajustar o mockup estatico do menu inicial do PSFINANCE para que o menu
encolhido apresente icones reais de navegacao e abra submenus em flyout lateral.

## Escopo executado

- Restaurada a lista de navegacao no estado `?compact=1`, mantendo rotulos e
  grupos ocultos.
- Ajustado o menu encolhido para uma coluna estreita com icones reais.
- Incluido flyout lateral para submenus no desktop quando o menu esta
  encolhido.
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
- Geradas evidencias visuais em:
  - `docs/mockups/evidencias/PLA-1036-menu-compacto-icones.png`;
  - `docs/mockups/evidencias/PLA-1036-menu-compacto-flyout-contas-pagar.png`;
  - `docs/mockups/evidencias/PLA-1036-menu-compacto-flyout-caixas-bancos.png`;
  - `docs/mockups/evidencias/PLA-1036-menu-compacto-flyout-mobile.png`.

## Impacto

A alteracao e documental/visual e nao altera templates da aplicacao Flask,
rotas, banco de dados, variaveis de ambiente, VPS, `main` ou producao.
