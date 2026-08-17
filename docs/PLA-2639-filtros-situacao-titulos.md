# PLA-2639 - Correção e comprovação dos filtros de situação

## Decisão aplicada

A situação é aplicada explicitamente sobre o conjunto que a consulta já
restringiu por mês, ano e empresa. `Todas` preserva o conjunto; `Em aberto`
mantém somente saldo das parcelas exibidas no mês maior que zero; `Baixada`
mantém somente saldo dessas parcelas igual a zero. O filtro não pode
reintroduzir títulos de outro período ou de outra empresa.

Essa regra é coerente com a consulta mensal e com as colunas `Pago no mês` e
`Não pago no mês`: uma parcela quitada em agosto aparece em `Baixada` em
agosto, ainda que o título parcelado possua saldo futuro. As regras de exclusão
lógica permanecem as mesmas. Não há escrita, migration ou mudança de estrutura
de banco.

## Causa da reprovação e evidência real de staging

A implementação anterior classificava pelo saldo global do título. Em leitura
somente do PostgreSQL de staging, o subconjunto parcelado da empresa 1 em
agosto/2026 contém cinco títulos: duas parcelas mensais em aberto e três
integralmente baixadas no mês. Como os três títulos quitados naquele mês
possuem parcelas futuras, a regra global os mantinha indevidamente em
`Em aberto` e deixava `Baixada` vazia.

IDs sanitizados do cenário real: `072b030b` e `ea5d2f1c` em aberto;
`c0c7c76d`, `f457c545` e `fc490ca4` baixados no mês. Assim, `Todas` deve conter
os cinco, `Em aberto` somente os dois primeiros e `Baixada` somente os três
últimos, sem interseção.

Na jornada completa da tela, o mesmo filtro inclui ainda quatro títulos legados
sem parcelas, todos em aberto. O resultado publicado na porta `5001` é:

| Situação | Quantidade | Relação comprovada |
| --- | ---: | --- |
| Todas | 9 | união exata dos demais conjuntos |
| Em aberto | 6 | 2 parcelados e 4 legados |
| Baixada | 3 | parcelas do mês integralmente quitadas |

Os conjuntos `Em aberto` e `Baixada` são disjuntos. A troca do seletor altera
imediatamente a URL, a opção selecionada, a quantidade e os totais exibidos.

## Evidência visual da jornada na porta 5001

- `docs/evidencias/PLA-2639/todas-empresa1-agosto2026-5001.png` — filtro e
  resumo com `Todas` e 9 títulos.
- `docs/evidencias/PLA-2639/em_aberto-empresa1-agosto2026-5001.png` — filtro e
  resumo com `Em aberto` e 6 títulos.
- `docs/evidencias/PLA-2639/baixada-empresa1-agosto2026-5001.png` — filtro e
  resumo com `Baixada` e 3 títulos.

Os recortes preservam os filtros e indicadores necessários à comparação e
não expõem documentos ou identificadores operacionais.

## Matriz de comprovação focal

| Conjunto após período/empresa | Situação | Deve aparecer | Não deve aparecer |
| --- | --- | --- | --- |
| título 1 aberto; título 2 baixado | Todas | 1 e 2 | títulos externos 3 e 4 |
| título 1 aberto; título 2 baixado | Em aberto | 1 | 2, 3 e 4 |
| título 1 aberto; título 2 baixado | Baixada | 2 | 1, 3 e 4 |
| título legado de R$ 80 sem saldo agregado | Em aberto | título legado | nenhum |
| título legado de R$ 80 sem saldo agregado | Baixada | nenhum | título legado |

## Arquitetura e prevenção

- `financeiro/routes_titulos.py`: a rota obtém o conjunto mensal/empresarial,
  calcula o saldo das parcelas do período e aplica a situação antes
  da montagem das linhas e dos totais.
- `tests/test_filtro_situacao_titulos.py`: a matriz valida as três situações,
  a combinação com filtros anteriores e o fallback defensivo de título legado.
- Prevenção: a seleção por situação deixa de ficar embutida no laço de
  apresentação, permitindo comprovar separadamente que linhas e totais usam o
  mesmo conjunto filtrado.

## Escopo e risco

Alteração focal no controller, teste e documentação. Sem template, variável de
ambiente, banco, migration, `main` ou produção. Risco residual baixo, limitado
à validação posterior no staging e na porta corporativa `5001`.
