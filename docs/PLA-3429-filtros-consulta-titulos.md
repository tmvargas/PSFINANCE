# PLA-3429 - Filtros ampliados da Consulta de Títulos

## Escopo entregue

- vencimento com modos exclusivos `Mês` e `Período`;
- intervalo de vencimento com limites inclusivos;
- credor limitado aos vínculos ativos da empresa selecionada;
- data de emissão exata;
- busca por número do documento, código/nome documental e ID exato;
- combinação com empresa memorizada e situação;
- limpeza explícita dos filtros;
- totais e quantidades calculados após todos os filtros.

## Matriz de validação

| Caso | Entrada | Resultado na porta 5001 |
| --- | --- | --- |
| Padrão mensal | agosto/2026, todas as situações | 9 títulos; totais preservados |
| Credor + situação | credor ativo + `Em aberto` | conjunto vazio, sem registros indevidos e totais zerados |
| Período + ID | 01/08/2026 a 31/08/2026 + ID 66 | 1 título; R$ 1.148,52 da parcela e pago |
| Período + emissão + situação | agosto/2026 + emissão 01/08/2026 + `Baixada` | conjunto vazio e totais zerados |
| Período mobile | 01/08/2026 a 31/08/2026 | 9 títulos; somente campos do modo `Período` visíveis |
| Parâmetro inválido | modo, mês, ano ou datas inválidas | normalização segura para o mês atual |
| Limite inclusivo | final 31/08/2026 | backend usa limite técnico exclusivo em 01/09/2026 |
| Busca com curinga | `%`, `_` e `\\` | tratados como texto literal na consulta SQL |

Os casos mensal e de período percorrem tanto títulos simples legados quanto
títulos parcelados pela consulta agregada existente. A situação continua sendo
calculada sobre o valor e as baixas das parcelas contidas no período exibido.

## Evidências

- `docs/evidencias/PLA-3429/consulta-titulos-filtros-desktop-5001.png`;
- `docs/evidencias/PLA-3429/consulta-titulos-filtros-mobile-5001.png`;
- `docs/evidencias/PLA-3429/matriz-jornada-5001.json`.

## Testes sem persistência

- `python3 -m py_compile financeiro/routes_titulos.py`;
- 5 testes focais da PLA-3429;
- compilação Jinja de `templates/titulos_list.html`;
- `git diff --check`;
- healthcheck HTTP 200 e rota real HTTP 200 na porta `5001`;
- serviços `psfinance-staging` e `psfinance-staging-gate` ativos;
- logs sem erro de aplicação após o restart.

Uma rodada inicial de regressão executou um teste preexistente com SQLite em
memória. Embora não tenha alterado arquivo nem ambiente compartilhado, isso é
escrita temporária segundo a governança e não possuía autorização expressa.
Ela não foi repetida; as validações finais ficaram restritas a operações sem
persistência.

## Impactos

- banco: nenhum;
- migration: nenhuma;
- variável de ambiente: nenhuma nova;
- VPS: atualização da `staging` e metadado de commit dos serviços;
- produção e `main`: não alteradas.
