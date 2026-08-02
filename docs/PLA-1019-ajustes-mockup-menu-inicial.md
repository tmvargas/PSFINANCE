# PLA-1019 - Ajustes do mockup de menu inicial

## Objetivo

Ajustar o mockup estatico do menu inicial do PSFINANCE, preservando a entrega
como artefato de validacao visual em `docs/mockups/` e sem alterar a aplicacao
Flask, banco de dados, VPS (Servidor Virtual Privado) ou producao.

## Escopo executado

- Reorganizado o menu `FINANCEIRO` com dois itens principais:
  `Contas a Pagar` e `Caixas e Bancos`.
- Posicionados `Titulos` e `Baixas` dentro de
  `FINANCEIRO > CONTAS A PAGAR`.
- Posicionados `Movimentacoes` e `Extrato` dentro de
  `FINANCEIRO > CAIXAS E BANCOS`.
- Incluido comportamento de expansao para a direita ao clicar no icone dos
  itens principais `Contas a Pagar` e `Caixas e Bancos`.
- Mantidos icones/siglas em todos os menus e submenus.
- Incluido resumo visual do menu inicial e contadores por grupo para reforcar a
  estrutura de navegacao.
- Ajustado comportamento responsivo para ocultar cabecalhos, contadores e
  resumo no menu horizontal mobile, preservando o submenu como painel associado
  ao item principal.

## Regra aplicada

A PLA-1019 foi tratada como ajuste visual de mockup, seguindo a decisao da
PLA-1016 de manter a validacao em HTML estatico antes de qualquer implementacao
no produto. Nao houve alteracao de regra de negocio, rota, banco ou ambiente.

## Validacao local

- Revisao estatica do HTML e CSS do arquivo `docs/mockups/PLA-1016-layout-inicial.html`.
- Comparacao objetiva contra os quatro pontos solicitados por Thiago:
  `Titulos`/`Baixas` sob `Contas a Pagar`, `Movimentacoes`/`Extrato` sob
  `Caixas e Bancos`, expansao lateral pelo icone e icones em todos os menus.
- Screenshot desktop gerado por Playwright CLI:
  `docs/mockups/evidencias/PLA-1019-menu-desktop.png`.
- Screenshot mobile gerado por Playwright CLI:
  `docs/mockups/evidencias/PLA-1019-menu-mobile.png`.
- Verificacao de que os ajustes permanecem restritos a `docs/mockups/` e
  documentacao.

## Pendencias

- A branch desta tarefa depende da base visual criada na PLA-1016, que ainda
  nao esta integrada em `staging` neste workspace.
- Validacao visual executavel em navegador ou screenshot deve ser feita antes de
  homologacao final, caso o fluxo da PLA-1016 ainda nao tenha sido aprovado.
