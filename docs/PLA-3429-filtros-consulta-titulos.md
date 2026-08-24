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

### Complemento solicitado na revisão executiva

| Caso positivo | Combinação | Deve aparecer | Não deve aparecer | Resultado na porta 5001 |
| --- | --- | --- | --- | --- |
| Credor por empresa | empresa `2`, Amico Celular, agosto, `Em aberto` | título `69` | título `49`, do mesmo credor em outra empresa | 1 registro; R$ 31,80 não pago |
| Emissão exata | empresa `1`, emissão `10/08/2026`, agosto, `Baixada` | títulos `49`, `50` e `53` | títulos `54`, `55` e `69` | 3 registros; R$ 2.883,35 pagos |
| Título simples | empresa `1`, agosto, ID `54`, `Em aberto` | título simples `54`, sem parcelas | título parcelado `66` | 1 registro; R$ 128,00 não pago |
| Título parcelado | empresa `4`, período de agosto, descrição `TERRENO VIDA NOVA`, `Baixada` | título parcelado `66`, com 180 parcelas ativas | título simples `54` | 1 registro; R$ 1.148,52 pago no período |
| Combinação completa | período de agosto, empresa `2`, Amico Celular, emissão `01/08/2026`, `EMAILGO`, `Em aberto` | título `69` | títulos `49`, `50` e `66` | 1 registro; totais iguais à linha retornada |
| Segundo credor distinto | empresa `1`, Estácio, agosto, todas as situações | títulos `54` e `65` | títulos `49`, `66` e `69` | 2 registros, ambos do credor Estácio |
| Emissão adjacente | empresa `1`, emissão `09/08/2026`, agosto, `Baixada` | nenhum título | títulos `49`, `50` e `53`, emitidos em `10/08/2026` | conjunto vazio e totais zerados |
| Limites inclusivos | empresa `1`, período `10/08/2026` a `21/08/2026`, todas as situações | títulos `49` e `50` no limite inicial; título `56` no limite final | títulos `66` e `69`, de outras empresas | 8 registros; os dois limites aparecem na jornada real |

A classificação simples/parcelado foi confirmada por consulta somente leitura
no PostgreSQL de staging: o título `54` não possui parcela ativa e o título
`66` possui 180. Nenhum dado foi criado ou alterado para esta validação.

Os casos mensal e de período percorrem tanto títulos simples legados quanto
títulos parcelados pela consulta agregada existente. A situação continua sendo
calculada sobre o valor e as baixas das parcelas contidas no período exibido.

## Evidências

- `docs/evidencias/PLA-3429/consulta-titulos-filtros-desktop-5001.png`;
- `docs/evidencias/PLA-3429/consulta-titulos-filtros-mobile-5001.png`;
- `docs/evidencias/PLA-3429/matriz-jornada-5001.json`;
- `docs/evidencias/PLA-3429/consulta-titulos-filtro-positivo-5001.png`;
- `docs/evidencias/PLA-3429/matriz-complemento-revisao-5001.json`;
- `docs/evidencias/PLA-3429/consulta-titulos-segundo-credor-5001.png`;
- `docs/evidencias/PLA-3429/consulta-titulos-emissao-adjacente-vazia-5001.png`;
- `docs/evidencias/PLA-3429/consulta-titulos-limites-inclusivos-5001.png`;
- `scripts/pla3429_capture_complemento_revisao.js` — captura reproduzível
  com asserções de presença, ausência, quantidade, filtros selecionados e totais.

## Testes sem persistência

- `python3 -m py_compile financeiro/routes_titulos.py`;
- 5 testes focais da PLA-3429;
- compilação Jinja de `templates/titulos_list.html`;
- `git diff --check`;
- healthcheck HTTP 200 e rota real HTTP 200 na porta `5001`;
- serviços `psfinance-staging` e `psfinance-staging-gate` ativos;
- logs sem erro de aplicação após o restart.
- 8 jornadas complementares executadas pela interface real na porta `5001`,
  incluindo dois credores distintos, emissão exata e adjacente vazia, títulos
  simples e parcelados, combinação completa e limites inicial/final inclusivos.

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
