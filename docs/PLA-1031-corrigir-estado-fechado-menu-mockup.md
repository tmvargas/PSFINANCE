# PLA-1031 - Corrigir estado fechado do menu no mockup

## Objetivo

Corrigir o estado fechado do menu no mockup estatico do PSFINANCE para que o
parametro `?compact=1` mostre a barra lateral recolhida sem lista de menus,
icones de itens, rotulos ou grupos visiveis, mantendo apenas um controle minimo
para reabrir o menu. A entrega permanece em `docs/mockups/` e nao altera
aplicacao Flask, banco de dados, VPS (Servidor Virtual Privado) ou producao.

## Escopo executado

- Ajustado o estado fechado do mockup para ocultar marca, grupos, itens de menu,
  icones de navegacao e submenus.
- Mantido apenas o botao minimo para reabrir o menu lateral no estado fechado.
- Ajustado o parametro `open` para funcionar somente com o menu aberto,
  impedindo submenu visivel no estado fechado.
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
- Verificacao de que `?compact=1` inicia com menu recolhido limpo, sem grupos,
  itens, icones de navegacao ou submenus visiveis.
- Verificacao de que `?compact=1&open=contas-pagar` continua fechado, sem
  exibir submenu no estado recolhido.
- Verificacao de que `?open=contas-pagar` e `?open=caixas-bancos` continuam
  abrindo os submenus especificos no estado aberto.
- Evidencias visuais geradas:
  `docs/mockups/evidencias/PLA-1031-menu-fechado-limpo.png`,
  `docs/mockups/evidencias/PLA-1031-menu-fechado-limpo-mobile.png`,
  `docs/mockups/evidencias/PLA-1031-menu-fechado-ignora-open.png`,
  `docs/mockups/evidencias/PLA-1031-menu-aberto-contas-pagar.png` e
  `docs/mockups/evidencias/PLA-1031-menu-aberto-caixas-bancos.png`.

## Checklist dos criterios obrigatorios

- [x] Menu recolhido fechado com `?compact=1`, sem itens de menu, icones de
  navegacao, rotulos, grupos ou submenu visiveis.
- [x] Controle minimo de reabertura preservado sem parecer item de menu.
- [x] Parametros `open=contas-pagar` e `open=caixas-bancos` preservados para
  evidencias de submenu aberto somente no estado aberto.
- [x] Hierarquia e icones reais da `PLA-1027` preservados.
- [x] Escopo restrito a documentacao/mockup.

## Integracao e staging

- A cadeia visual `PLA-1016`/`PLA-1019`/`PLA-1022`/`PLA-1027`/`PLA-1031` foi
  integrada em `staging`.
- A VPS (Servidor Virtual Privado) de teste foi atualizada por fast-forward no
  diretorio `/opt/plansmart/sistemas/psfinance/staging/repo`.
- Os servicos `psfinance-staging.service` e `psfinance-staging-gate.service`
  foram reiniciados e permaneceram `active`.
- O metadado nao sensivel `GIT_COMMIT` do staging foi atualizado no arquivo de
  ambiente da VPS para refletir o commit vigente da branch `staging`; foi criado
  backup operacional do arquivo antes da alteracao.
- A porta corporativa `5001` foi validada em
  `http://vps69143.publiccloud.com.br:5001/gate` com HTTP 200, branch
  `staging`, ambiente `staging-gate` e status `healthy`.

## Estado de GitHub

- Branch da tarefa: `fix/PLA-1031-menu-fechado`.
- Commit da tarefa: `698e1ff20264fedea10d0b2070fc2790027dafef`.
- PR (Pull Request, solicitacao de revisao): `https://github.com/tmvargas/PSFINANCE/pull/17`.
- Base do PR: `staging`.
- PR complementar de documentacao: `https://github.com/tmvargas/PSFINANCE/pull/18`.

## Pendencias

- Revisao visual executiva do CEO sobre as evidencias geradas, antes de decidir
  se o mockup deve virar implementacao na aplicacao Flask.
