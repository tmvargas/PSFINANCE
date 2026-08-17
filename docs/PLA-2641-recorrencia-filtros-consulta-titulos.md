# PLA-2641 - Correção da recorrência dos filtros da Consulta de Títulos

## Decisão aplicada

A situação é aplicada explicitamente sobre o conjunto que a consulta já
restringiu por mês, ano e empresa. `Todas` preserva o conjunto; `Em aberto`
mantém somente saldo global ativo maior que zero; `Baixada` mantém somente
saldo global ativo igual a zero. O filtro não pode reintroduzir títulos de
outro período ou de outra empresa.

O cálculo de saldo ativo e as regras de exclusão lógica permanecem os mesmos
validados na PLA-2629. Não há escrita, migration ou mudança de estrutura de
banco.

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
  calcula os saldos globais e aplica a situação em uma etapa explícita antes
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
