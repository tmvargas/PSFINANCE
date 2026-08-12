# PLA-2111 - UX do cadastro de novo titulo

## Projeto

PSFINANCE.

## Contexto

Revisao CEO sobre `/staging/psfinance/financeiro/titulos/novo` apontou riscos de
experiencia no cadastro de novo titulo: mascara de valor contraintuitiva,
linguagem tecnica no plano financeiro, centro de custo selecionavel antes da
empresa, falta de orientacao para cadastros auxiliares, fluxo de parcela unica
burocratico, botoes com emojis e anexos com peso visual excessivo.

## Decisao aplicada

- Valor total passa a aceitar entrada em reais: `200` e formatado como
  `200,00`.
- `Plano Financeiro (Grupo 2)` passa a ser exibido como `Categoria financeira`.
- Centro de Custo fica indisponivel ate a escolha da Empresa e mostra apenas
  centros compativeis.
- Formulario apresenta orientacao e atalhos quando faltam cadastros auxiliares
  de credor, empresa, centro de custo ou categoria financeira.
- Criacao/copia com uma parcela retorna para a lista de titulos; duas ou mais
  parcelas continuam abrindo a revisao de parcelas.
- Anexos ficam em secao secundaria expansivel.
- Botoes principais removem emojis e usam texto direto.

## Evidencias

- Antes: `docs/evidencias/PLA-2111/novo-titulo-antes-staging.png`.
- Depois: `docs/evidencias/PLA-2111/novo-titulo-ux-ajustada.png`.

Na evidencia antes, a entrada `200` no campo Valor total era formatada como
`2,00`. Na evidencia depois, a mesma entrada e formatada como `200,00` e a
tela exibe a previa de `3 parcelas`.

## Validacao executada

- `python3 -m compileall financeiro src database.py models.py`.
- `git diff --check`.
- Renderizacao local com SQLite temporario:
  - `GET /financeiro/titulos/novo` retornou HTTP 200;
  - textos `Categoria financeira`, `Digite o valor em reais`,
    `Selecione uma empresa primeiro`, `Previa das parcelas` e
    `Anexos do titulo` renderizados;
  - `POST /financeiro/titulos/novo` com valor `200` e uma parcela retornou
    HTTP 302 para `/financeiro/titulos`;
  - titulo salvo no SQLite temporario com valor `200.0`;
  - uma parcela criada.
- Playwright local com Chromium temporario:
  - versao anterior: `200` formatou como `2,00`;
  - versao ajustada: `200` formatou como `200,00`;
  - previa dinamica exibiu `3 parcelas`.

## Limites

- Sem alteracao de banco.
- Sem migration.
- Sem alteracao em `main`.
- Sem producao.
- Validacao em VPS/staging real e porta corporativa `5001` ainda depende de
  publicacao da branch na `staging`.
