# PLA-1019 - Ajustes do mockup de menu inicial

## Objetivo

Ajustar o mockup estatico do menu inicial do PSFINANCE, preservando a entrega
como artefato de validacao visual em `docs/mockups/` e sem alterar a aplicacao
Flask, banco de dados, VPS (Servidor Virtual Privado) ou producao.

## Escopo executado

- Reorganizado o menu lateral por grupos mais claros: `HOME`, `OPERACIONAL`,
  `GERENCIAL` e `CADASTROS`.
- Ajustados rotulos para plural e consistencia com as rotinas financeiras:
  `Titulos`, `Baixas`, `Credores`, `Caixas e Bancos`, `Extrato` e
  `Plano Financeiro`.
- Substituidos icones improvisados por siglas curtas e consistentes para o
  mockup, melhorando legibilidade em menu expandido e recolhido.
- Incluido resumo visual do menu inicial e contadores por grupo para reforcar a
  estrutura de navegacao.
- Ajustado comportamento responsivo para ocultar cabecalhos, contadores e
  resumo no menu horizontal mobile.

## Regra aplicada

A PLA-1019 foi tratada como ajuste visual de mockup, seguindo a decisao da
PLA-1016 de manter a validacao em HTML estatico antes de qualquer implementacao
no produto. Nao houve alteracao de regra de negocio, rota, banco ou ambiente.

## Validacao local

- Revisao estatica do HTML e CSS do arquivo `docs/mockups/PLA-1016-layout-inicial.html`.
- Verificacao de que os ajustes permanecem restritos a `docs/mockups/` e
  documentacao.

## Pendencias

- A branch desta tarefa depende da base visual criada na PLA-1016, que ainda
  nao esta integrada em `staging` neste workspace.
- Validacao visual executavel em navegador ou screenshot deve ser feita antes de
  homologacao final, caso o fluxo da PLA-1016 ainda nao tenha sido aprovado.
