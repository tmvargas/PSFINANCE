# PLA-1618 - Padronizar layout das consultas conforme titulos

## Projeto

PSFINANCE.

## Demanda atendida

Padronizar o layout das consultas do PSFINANCE conforme o padrao ja aplicado
na consulta de titulos.

## Regra aplicada

A alteracao ficou restrita a camada de apresentacao. Foram preservados:

- rotas Flask existentes;
- nomes de campos renderizados nas consultas;
- acoes de criar, editar, desativar, reativar e excluir;
- totais de contas;
- backend, models, banco de dados e variaveis de ambiente.

## Arquitetura

Skills consultadas:

- `plansmart-governanca-desenvolvimento`;
- `plansmart-projeto-psfinance`;
- `plansmart-projeto-vps-sistemas`.

Arquivos por camada:

- Apresentacao: `templates/base.html`;
- Apresentacao: `templates/contas_list.html`;
- Apresentacao: `templates/contas_inativas.html`;
- Apresentacao: `templates/movimentacoes_list.html`;
- Apresentacao: `templates/empresa_list.html`;
- Apresentacao: `templates/centro_custo_list.html`;
- Apresentacao: `templates/credores_list.html`;
- Apresentacao: `templates/plano_list.html`;
- Documentacao: `docs/decisoes.md` e este arquivo;
- Evidencias visuais: arquivos `docs/mockups/evidencias/PLA-1618-*.png`.

Nao houve alteracao em controllers, services, repositories, models, migrations
ou scripts de banco.

## O que foi alterado

- Consultas passaram a usar cabeçalho com contexto da rotina, titulo em formato
  `Consulta de ...` e subtitulo operacional.
- Tabelas passaram a usar shell visual, cabecalho verde escuro e estado vazio
  padronizado.
- Acoes por linha foram convertidas em botoes compactos com icones, `title` e
  `aria-label`.
- Botoes principais do cabecalho passaram a usar icone e texto.
- A consulta de movimentacoes foi agrupada em colunas operacionais para reduzir
  largura visual sem remover dados.
- A consulta de contas passou a usar o `total_saldo` calculado no backend no
  rodape da tabela.

## Validacao local

```text
.venv/bin/python -m compileall src financeiro database.py models.py
```

Resultado: sucesso.

```text
git diff --check
```

Resultado: sem apontamentos.

Renderizacao isolada com SQLite temporario criado fora do repositorio:

```text
/financeiro/contas 200 True False False
/financeiro/contas/inativas 200 True False False
/financeiro/movimentacoes 200 True False False
/financeiro/empresas 200 True False False
/financeiro/centros-custo 200 True False False
/financeiro/credores 200 True False False
/financeiro/plano 200 True False False
```

Os campos finais indicam, respectivamente:

- presenca de `consultation-page`;
- ausencia de `table-dark`;
- ausencia de `table-striped`.

## Validacao visual

Base temporaria com dados ficticios criada fora do repositorio em
`/tmp/psfinance-pla1618-instance`.

Evidencias:

- `docs/mockups/evidencias/PLA-1618-referencia-titulos-desktop.png`;
- `docs/mockups/evidencias/PLA-1618-referencia-titulos-mobile.png`;
- `docs/mockups/evidencias/PLA-1618-contas-desktop.png`;
- `docs/mockups/evidencias/PLA-1618-movimentacoes-desktop.png`;
- `docs/mockups/evidencias/PLA-1618-movimentacoes-mobile.png`;
- `docs/mockups/evidencias/PLA-1618-empresas-desktop.png`;
- `docs/mockups/evidencias/PLA-1618-centros-custo-desktop.png`;
- `docs/mockups/evidencias/PLA-1618-credores-desktop.png`;
- `docs/mockups/evidencias/PLA-1618-plano-desktop.png`.

Resultado observado:

- desktop com cabecalho, acoes, tabela e rodape de total sem sobreposicao;
- mobile com cabecalho e acoes empilhados e tabela dentro de area responsiva;
- acoes por linha renderizadas com icones compactos.

## Comparacao objetiva com consulta de titulos

Referencia usada no sistema real: `/financeiro/titulos`, template
`templates/titulos_list.html`, conforme entrega visual da PLA-1359/PLA-1370.

| Criterio visual da consulta de titulos | Rotinas ajustadas | Evidencia |
| --- | --- | --- |
| Pagina com classe `consultation-page` e cabecalho operacional. | Contas, contas inativas, movimentacoes, empresas, centros de custo, credores e plano financeiro usam a mesma estrutura. | Renderizacao local retornou `consultation-page=True` em todas as rotas. |
| Titulo em formato `Consulta de ...` com subtitulo de contexto. | Todas as rotinas ajustadas passaram a usar titulo e subtitulo equivalentes ao padrao de titulos. | Screenshots desktop das sete rotinas e mobile de movimentacoes. |
| Acoes principais no cabecalho com botao compacto, icone e texto. | Botoes de novo cadastro, movimentacao, contas inativas e voltar seguem `btn-icon-label`. | Screenshots desktop das rotinas ajustadas. |
| Tabela dentro de shell visual padronizado, sem `table-dark` ou `table-striped`. | Todas as consultas ajustadas usam `consultation-table-shell` e cabecalho proprio. | Renderizacao local confirmou ausencia de `table-dark` e `table-striped`. |
| Acoes por linha com icones compactos, `title` e `aria-label`. | Editar, desativar, reativar e excluir foram convertidos para botoes compactos por icone. | Screenshots desktop e inspecao dos templates alterados. |
| Estado vazio sem tabela quebrada. | Todas as rotinas ajustadas possuem `consultation-empty` quando nao ha registros. | Inspecao dos templates e renderizacao local. |
| Responsividade com area rolavel quando a tabela e larga. | As rotinas usam `table-responsive` e a consulta de movimentacoes foi evidenciada tambem em mobile. | `PLA-1618-movimentacoes-mobile.png` e referencia mobile de titulos. |

Conclusao da comparacao: as rotinas ajustadas reproduzem a logica visual da
consulta de titulos sem copiar regra de negocio e sem alterar backend, banco,
rotas ou permissoes.

## Validacao de staging na VPS

Validacao inicial executada em 2026-08-06 antes da publicacao desta correcao:

```text
GET http://vps69143.publiccloud.com.br:5001/health -> HTTP 200
GET http://vps69143.publiccloud.com.br:5001/gate -> HTTP 200
branch retornada: staging
commit retornado: 9502730df2c760e0e596033295fd4b3aa1e73a04
status retornado: healthy
```

Conclusao inicial: o gate corporativo esta saudavel, mas ainda apontava para o
commit anterior da `staging`. A validacao final deve ser registrada apos merge
da branch de tarefa na `staging` e publicacao na VPS de teste.

## Limites

Nao houve:

- migration;
- escrita em banco de producao;
- alteracao de `main`;
- deploy em producao;
- copia de dados entre ambientes;
- exposicao de segredo.

## Recomendacao do GDSIS

Recomendo revisao executiva do CEO apos integracao e validacao em staging.
Nao recomendo promocao para producao sem Pacote de Producao especifico e
autorizacao expressa aplicavel.
