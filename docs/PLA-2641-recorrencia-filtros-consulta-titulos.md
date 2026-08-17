# PLA-2641 - Recorrência dos filtros da Consulta de Títulos

## Diagnóstico

O `staging` atual já contém a correção funcional da PLA-2639: o filtro de
situação é aplicado sobre o conjunto previamente limitado por mês, ano e
empresa, antes da montagem das linhas e dos totais. A recorrência foi tratada
pela revalidação dessa integração e pela manutenção do teste que impede
registros eliminados por filtros anteriores de serem reintroduzidos.

## Matriz focal revalidada

| Situação | Deve aparecer | Não deve aparecer |
| --- | --- | --- |
| Todas | títulos aberto e baixado do período/empresa | títulos externos ao período/empresa |
| Em aberto | somente título com saldo global ativo | baixado e títulos externos |
| Baixada | somente título com saldo global zerado | aberto e títulos externos |

O caso defensivo de título legado sem saldo agregado também foi revalidado:
ele usa o valor do título como fallback e não interrompe a consulta.

## Evidência técnica

- `financeiro/routes_titulos.py`: `_filtrar_titulos_por_situacao()` concentra a
  seleção antes da criação das linhas e dos totais.
- `tests/test_filtro_situacao_titulos.py`: cobre as três situações, combinação
  com filtros anteriores, saldos ativos, exclusões lógicas e fallback legado.
- Validação local: 16 testes focais aprovados; compilação e `git diff --check`
  aprovados.

Não há alteração de banco, migration, variável de ambiente, `main` ou
produção. A validação final de staging exige alinhamento da VPS e porta
corporativa `5001`.
