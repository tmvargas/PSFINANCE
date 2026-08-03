# PLA-1027 - Corrigir mockup com icones reais no menu

## Objetivo

Corrigir o mockup estatico do menu inicial do PSFINANCE para substituir as
siglas visuais dos itens de navegacao por icones reais, mantendo a entrega em
`docs/mockups/` e sem alterar aplicacao Flask, banco de dados, VPS (Servidor
Virtual Privado) ou producao.

## Escopo executado

- Substituidas as siglas dos grupos `HOME`, `FINANCEIRO`, `GERENCIAL` e
  `APOIO` por icones SVG embutidos.
- Substituidas as siglas dos menus `Home`, `Contas a Pagar`,
  `Caixas e Bancos`, `Gerencial Financeiro`, `Credor` e `Plano Financeiro` por
  icones SVG.
- Substituidas as siglas dos submenus `Título`, `Baixa`, `Movimentações` e
  `Extrato` por icones SVG.
- Substituidas as siglas dos atalhos rapidos por icones SVG.
- Atualizado o titulo do mockup para identificar a revisao da `PLA-1027`.

## Regra aplicada

A `PLA-1027` foi tratada como correcao visual do artefato de mockup criado na
cadeia `PLA-1016`/`PLA-1019`/`PLA-1022`. A regra aplicada foi manter a
validacao em HTML estatico antes de implementar qualquer mudanca no produto.
Nao houve alteracao de regra de negocio, rota, banco, infraestrutura ou
ambiente.

## Validacao local

- Revisao estatica do HTML e CSS em
  `docs/mockups/PLA-1016-layout-inicial.html`.
- Verificacao de que nao restaram siglas como conteudo dos elementos de icone
  do menu e dos atalhos rapidos.
- Evidencias visuais geradas:
  `docs/mockups/evidencias/PLA-1027-menu-desktop.png`,
  `docs/mockups/evidencias/PLA-1027-menu-compact-contas-pagar.png`,
  `docs/mockups/evidencias/PLA-1027-menu-compact-caixas-bancos.png` e
  `docs/mockups/evidencias/PLA-1027-menu-mobile.png`.

## Checklist dos criterios obrigatorios

- [x] `FINANCEIRO`, `GERENCIAL` e `APOIO` mantidos como grupos do menu.
- [x] Hierarquia `FINANCEIRO > Contas a Pagar > Título, Baixa` preservada.
- [x] Hierarquia `FINANCEIRO > Caixas e Bancos > Movimentações, Extrato`
  preservada.
- [x] Icones reais visiveis nos grupos, menus, submenus e atalhos rapidos.
- [x] Escopo restrito a documentacao/mockup.

## Pendencias

- A cadeia visual `PLA-1016`/`PLA-1019`/`PLA-1022`/`PLA-1027` ainda precisa ser
  integrada em `staging`, publicada no ambiente de teste e validada pela porta
  corporativa `5001` para encerramento completo pela governanca.
