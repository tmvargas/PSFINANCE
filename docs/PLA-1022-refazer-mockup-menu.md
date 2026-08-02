# PLA-1022 - Refazer mockup do menu conforme rejeicao de Thiago

## Objetivo

Refazer o mockup estatico do menu inicial do PSFINANCE apos rejeicao da versao
anterior, mantendo a entrega como validacao visual em `docs/mockups/` e sem
alterar aplicacao Flask, banco de dados, VPS (Servidor Virtual Privado) ou
producao.

## Escopo executado

- Removido o bloco de resumo do menu lateral para reduzir ruido visual.
- Removidos contadores dos grupos do menu lateral.
- Substituido o submenu flutuante do desktop por submenu embutido na propria
  coluna lateral, evitando sobreposicao sobre o conteudo principal.
- Mantida a hierarquia solicitada para `FINANCEIRO`:
  `Contas a Pagar > Título/Baixa` e
  `Caixas e Bancos > Movimentações/Extrato`.
- Corrigidos os grupos para `FINANCEIRO`, `GERENCIAL` e `APOIO`.
- Corrigidos os nomes para `Título`, `Baixa` e `Credor`.
- Mantidos icones/siglas nos grupos, itens principais e subitens.
- Incluido suporte a parametros de URL para evidenciar menu recolhido:
  `?compact=1&open=contas-pagar` e `?compact=1&open=caixas-bancos`.
- Atualizado o titulo do mockup para identificar a revisao da `PLA-1022`.

## Regra aplicada

A `PLA-1022` foi tratada como refacao visual do mockup rejeitado, preservando a
decisao anterior de validar a navegacao em HTML estatico antes de implementar no
produto. Nao houve alteracao de regra de negocio, rota, banco, infraestrutura
ou ambiente.

## Validacao local

- Revisao estatica do HTML e CSS em
  `docs/mockups/PLA-1016-layout-inicial.html`.
- Verificacao de que a alteracao permanece restrita a documentacao/mockup.
- Evidencias visuais geradas:
  `docs/mockups/evidencias/PLA-1022-menu-desktop.png`,
  `docs/mockups/evidencias/PLA-1022-menu-compact-contas-pagar.png`,
  `docs/mockups/evidencias/PLA-1022-menu-compact-caixas-bancos.png` e
  `docs/mockups/evidencias/PLA-1022-menu-mobile.png`.

## Checklist dos criterios obrigatorios

- [x] Grupos mantidos exatamente como `FINANCEIRO`, `GERENCIAL` e `APOIO`.
- [x] Nomes do menu mantidos como `Home`, `Contas a Pagar`, `Título`,
  `Baixa`, `Caixas e Bancos`, `Movimentações`, `Extrato`,
  `Gerencial Financeiro`, `Credor` e `Plano Financeiro`.
- [x] Estrutura `FINANCEIRO > Contas a Pagar > Título, Baixa`.
- [x] Estrutura `FINANCEIRO > Caixas e Bancos > Movimentações, Extrato`.
- [x] Icone visivel para `FINANCEIRO`, `GERENCIAL`, `APOIO` e para todos os
  menus/submenus.
- [x] Menu recolhido com `Contas a Pagar` expandindo submenu para a direita.
- [x] Menu recolhido com `Caixas e Bancos` expandindo submenu para a direita.
- [x] Evidencias geradas para desktop normal, dois estados recolhidos e mobile.

## Pendencias

- A base do mockup ainda nao esta integrada em `staging`; a `PLA-1022` foi
  criada a partir da branch visual da `PLA-1019` para preservar a continuidade
  da revisao rejeitada.
- Para encerramento completo pela governanca, a cadeia `PLA-1016`/`PLA-1019`/
  `PLA-1022` precisa ser integrada em `staging`, publicada no ambiente de teste
  e validada pela porta corporativa `5001`.
