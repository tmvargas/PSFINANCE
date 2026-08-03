# PLA-1031 - Corrigir estado fechado do menu no mockup

## Objetivo

Corrigir o estado fechado do menu no mockup estatico do PSFINANCE para que o
parametro `?compact=1` mostre a barra lateral recolhida sem submenu aberto
automaticamente, mantendo a entrega em `docs/mockups/` e sem alterar aplicacao
Flask, banco de dados, VPS (Servidor Virtual Privado) ou producao.

## Escopo executado

- Ajustado o estado inicial do mockup para fechar todos os submenus quando a URL
  usar `?compact=1` sem parametro `open`.
- Preservado o suporte a evidencia de submenu especifico aberto com
  `?compact=1&open=contas-pagar` e `?compact=1&open=caixas-bancos`.
- Ajustado o botao de recolhimento para fechar submenus ao compactar o menu
  pela propria interface.
- Ajustado o clique nos itens expansivos para manter apenas um submenu aberto
  por vez.
- Atualizado o titulo do mockup para identificar a revisao da `PLA-1031`.

## Regra aplicada

A `PLA-1031` foi tratada como correcao visual e comportamental do artefato de
mockup criado na cadeia `PLA-1016`/`PLA-1019`/`PLA-1022`/`PLA-1027`. A regra
aplicada foi manter a validacao em HTML estatico antes de implementar qualquer
mudanca no produto. Nao houve alteracao de regra de negocio, rota, banco,
infraestrutura ou ambiente.

## Validacao local

- Revisao estatica do HTML, CSS e JavaScript em
  `docs/mockups/PLA-1016-layout-inicial.html`.
- Verificacao de que `?compact=1` inicia com menu recolhido e sem submenu
  flutuante aberto.
- Verificacao de que `?compact=1&open=contas-pagar` e
  `?compact=1&open=caixas-bancos` continuam abrindo os submenus especificos.
- Evidencias visuais geradas:
  `docs/mockups/evidencias/PLA-1031-menu-compact-fechado.png`,
  `docs/mockups/evidencias/PLA-1031-menu-compact-contas-pagar.png` e
  `docs/mockups/evidencias/PLA-1031-menu-compact-caixas-bancos.png`.

## Checklist dos criterios obrigatorios

- [x] Menu recolhido fechado com `?compact=1`, sem submenu aberto por padrao.
- [x] Parametros `open=contas-pagar` e `open=caixas-bancos` preservados para
  evidencias de submenu aberto.
- [x] Hierarquia e icones reais da `PLA-1027` preservados.
- [x] Escopo restrito a documentacao/mockup.

## Pendencias

- A cadeia visual `PLA-1016`/`PLA-1019`/`PLA-1022`/`PLA-1027`/`PLA-1031` ainda
  precisa ser integrada em `staging`, publicada no ambiente de teste e validada
  pela porta corporativa `5001` para encerramento completo pela governanca.
