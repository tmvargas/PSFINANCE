# PLA-1480 - Ajustar menu Apoio e estado inicial fechado

## Objetivo

Ajustar o menu lateral do PSFINANCE para que o grupo `APOIO` funcione como
menu expansivel e para que os submenus iniciem fechados no carregamento normal
das telas.

## Escopo executado

- Convertido o grupo `APOIO` em item expansivel unico, com submenu contendo
  `Empresa`, `Centro de Custo`, `Credor` e `Plano Financeiro`.
- Removida a lista direta de itens de apoio no menu aberto.
- Removida a abertura automatica inicial dos submenus por endpoint ativo.
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
  `Centro de Custo`, `Credor` e `Plano Financeiro`.
- Acionar o estado compacto e confirmar que o icone de `APOIO` abre o mesmo
  submenu em flyout lateral.

## Impacto

A alteracao e restrita ao template base e ao comportamento visual do menu.
Nao altera controllers, services, models, banco de dados, migrations,
variaveis de ambiente, VPS, `main` ou producao.
