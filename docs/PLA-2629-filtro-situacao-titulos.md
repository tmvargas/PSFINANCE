# PLA-2629 - Revisao do filtro de situacao de titulos

## Regra confirmada

- `Todas` e o padrao inicial e nao restringe registros.
- `Em aberto` exige saldo global ativo maior que zero.
- `Baixada` exige saldo global ativo igual a zero.
- O periodo continua selecionando titulos pelas parcelas ativas com vencimento
  no mes e ano; empresa e situacao sao combinadas sem substituir um ao outro.
- Baixas excluidas e parcelas excluidas nao compoem os agregados ativos.
- Titulo com parcelas, mas sem nenhuma parcela ativa, tem total ativo zero.
- Apenas titulo simples, sem qualquer parcela cadastrada, usa `titulo.valor`.

## Matriz focal

| Cenario | Total ativo | Baixas ativas | Situacao esperada |
| --- | ---: | ---: | --- |
| Simples sem baixa | 100,00 | 0,00 | Em aberto |
| Baixa parcial | 100,00 | 40,00 | Em aberto |
| Multiplas baixas | 100,00 | 100,00 | Baixada |
| Parcelado parcialmente baixado | 300,00 | 200,00 | Em aberto |
| Integralmente quitado | 300,00 | 300,00 | Baixada |
| Baixa excluida de 60,00 e ativa de 40,00 | 100,00 | 40,00 | Em aberto |
| Uma parcela ativa e outra excluida | somente a ativa | baixas da ativa | Conforme saldo ativo |
| Todas as parcelas excluidas | 0,00 | 0,00 | Baixada |

## Correcao de recorrencia

- Erro anterior: todas as parcelas excluidas faziam o agregado ficar ausente e
  o codigo usava indevidamente o valor original do titulo.
- Causa: o mesmo fallback representava dois estados diferentes: titulo simples
  e titulo com parcelas sem parcela ativa.
- Prevencao: consulta separada identifica a existencia de qualquer parcela;
  testes da funcao agregadora cobrem os dois estados e as baixas ativas.
- Risco residual: a prova com dados reais de PostgreSQL depende de dados ja
  existentes ou de autorizacao expressa de Thiago para preparar massa.

## Evidencia real em staging

Commit publicado: `7bafc313ef9e5b82d85ff2290b7a50732ccb1511`.

As consultas abaixo foram somente leitura, na porta corporativa `5001`, usando
agosto de 2026 e empresa `1 - THIAGO`:

| Situacao | HTTP | Titulos | Selecao preservada |
| --- | ---: | ---: | --- |
| Todas | 200 | 9 | mes `8`, ano `2026`, empresa `1`, situacao `todas` |
| Em aberto | 200 | 9 | mes `8`, ano `2026`, empresa `1`, situacao `em_aberto` |
| Baixada | 200 | 0 | mes `8`, ano `2026`, empresa `1`, situacao `baixada` |

Evidencias visuais do mesmo conjunto de filtros:

- `docs/evidencias/PLA-2629/titulos-todas-empresa-mes-ano-5001.png`;
- `docs/evidencias/PLA-2629/titulos-em-aberto-empresa-mes-ano-5001.png`;
- `docs/evidencias/PLA-2629/titulos-baixada-empresa-mes-ano-5001.png`.

Os tres screenshots preservam o layout existente e mostram separadamente as
tres opcoes selecionadas no seletor compacto, sem texto explicativo adicional.
