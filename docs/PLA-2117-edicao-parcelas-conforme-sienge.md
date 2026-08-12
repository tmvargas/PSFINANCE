# PLA-2117 - Edicao de parcelas do titulo conforme Sienge

## Projeto

PSFINANCE.

## Demanda

Corrigir a edicao de parcelas do titulo conforme o comportamento do Sienge.

## Regra aplicada

- A aba `Parcelas` permanece como local de inclusao, exclusao e ajuste da
  distribuicao de parcelas do titulo.
- A inclusao manual permanece uma parcela por vez, aderente ao fluxo publicado
  no suporte Sienge para titulo a pagar.
- Ao salvar a aba `Parcelas`, o valor total do titulo continua refletindo a
  soma das parcelas ativas.
- Quando o titulo possui exatamente uma parcela ativa, a edicao do valor total
  ou da data do primeiro vencimento na tela principal tambem sincroniza essa
  parcela unica.
- Quando o titulo possui duas ou mais parcelas ativas, a tela principal nao
  redistribui parcelas automaticamente; os ajustes permanecem na aba
  `Parcelas`, preservando a regra ja validada nas PLAs 1816, 2073 e 2106.

## Fonte funcional usada

- Artigo publico Sienge `Como incluir parcelas em um titulo a pagar?`,
  consultado em 2026-08-12, informa que a inclusao ocorre pela aba `Parcelas`,
  com botao de adicionar, uma parcela por vez, e confirmacao de alteracao do
  valor do titulo ao salvar.

## Arquitetura

- Controller: `financeiro/routes_titulos.py`.
- Nao houve alteracao em model, migration, banco de dados, template, CSS,
  JavaScript, VPS ou producao.

## Validacao executada

```bash
.venv/bin/python -m compileall src financeiro database.py models.py
```

Resultado: compilacao concluida sem erro.

Teste focal com banco SQLite temporario e `Flask test_client`:

```text
OK PLA-2117: parcela unica sincronizada; multiplas parcelas preservadas para edicao pela aba Parcelas
```

Matriz funcional:

| Caso | Entrada | Resultado esperado |
| --- | --- | --- |
| Titulo com uma parcela ativa | Editar valor para `150,50` e vencimento para `2026-11-15` na tela principal | Titulo salvo; parcela unica ativa fica como parcela `1`, valor `150.50` e vencimento `2026-11-15` |
| Titulo com duas parcelas ativas | Editar valor e vencimento na tela principal | Titulo salvo; parcelas existentes continuam com valores e vencimentos originais para ajuste pela aba `Parcelas` |

## Gate de arquitetura

- Skill consultada: `plansmart-projeto-psfinance`, junto com
  `plansmart-governanca-desenvolvimento` e `plansmart-projeto-vps-sistemas`.
- Arquitetura preservada: regra aplicada no controller de titulos, sem criar
  camada paralela ou duplicar modelo de parcelas.
- Excecao: nenhuma.

## Gate de recorrencia

- Erro anterior: a edicao de titulo de parcela unica podia alterar o titulo sem
  atualizar a parcela relacional, criando divergencia entre a tela principal e a
  aba `Parcelas`.
- Causa: a rotina de edicao garantia a existencia da parcela unica, mas nao
  sincronizava valor e vencimento quando ela ja existia.
- Correcao: criada sincronizacao focal para atualizar somente a parcela unica.
- Evidencia de nao recorrencia: teste focal confirmou a sincronizacao da
  parcela unica e a preservacao das multiplas parcelas.
- Risco residual: validacao executada localmente com SQLite temporario; a
  publicacao em staging e validacao da porta `5001` ainda dependem do fluxo de
  merge/deploy da `staging`.

## Limites

- Nao houve escrita em banco de producao.
- Nao houve migration.
- Nao houve alteracao de variavel de ambiente.
- Nao houve deploy em VPS nem producao neste heartbeat.
