# PLA-2612 - Rastreabilidade e exclusao de baixa por parcela

## Diagnostico somente leitura em staging

Consulta executada em 2026-08-16 com transacao PostgreSQL explicitamente
configurada como somente leitura, usando data `13/08/2026`, valor `R$ 1,00` e
documento reportados na tarefa.

- Titulo identificado: `id_titulo=60`, documento `AV - Aviso de lancamento - teste`.
- Baixa ativa identificada: `id_baixa=41`, nao conciliada.
- Parcela vinculada: `id_parcela=20`, numero `1`, excluida logicamente.
- Baixas historicas `40` (parcela `20`) e `42` (parcela `21`) ja estao
  excluidas logicamente.
- O titulo `60` permanece ativo.

A causa da dificuldade de localizacao e a dependencia da consulta mensal de
titulos: o Extrato exibia a baixa, mas nao oferecia caminho para o titulo nem
identificava o vinculo; adicionalmente, a baixa ativa aponta para uma parcela
ja excluida logicamente.

## Regra aplicada

- O Extrato oferece acesso direto a baixa sem depender de mes, ano ou estado
  atual da parcela.
- Baixa vinculada identifica `id_titulo`, numero e `id_parcela`.
- Baixa legada identifica explicitamente a ausencia de parcela.
- O endpoint de exclusao exige a combinacao correta de `id_titulo` e
  `id_baixa`, rejeitando requisicao manipulada.
- Baixa conciliada continua protegida no frontend e no backend.
- A exclusao logica existente permanece responsavel por retirar a baixa dos
  calculos de saldo da parcela, titulo, consulta mensal, Extrato e Analise.

## Gate de arquitetura

- Skills consultadas: `plansmart-governanca-desenvolvimento`,
  `plansmart-projeto-psfinance` e `plansmart-projeto-vps-sistemas`.
- Controller de Extrato: `financeiro/routes_contas.py`.
- Controller de titulos e baixas: `financeiro/routes_titulos.py`.
- Templates: `templates/extrato_conta.html` e
  `templates/titulo_baixas_list.html`.
- Testes focais: `tests/test_parcela_exclusao_baixa.py`.
- Sem model, migration ou mudanca estrutural de banco.

## Matriz de validacao preparada

| Caso | Resultado esperado |
| --- | --- |
| Baixa ativa vinculada a parcela ativa | Extrato identifica e abre a baixa; exclusao recalcula os saldos |
| Baixa ativa vinculada a parcela excluida | Extrato continua identificando e abrindo a baixa |
| Baixa legada sem parcela | Extrato identifica `Baixa legada sem parcela` e abre a baixa |
| Titulo manipulado no POST | Backend rejeita sem excluir a baixa |
| Baixa conciliada | Botao desabilitado e backend rejeita a exclusao com motivo |
| Baixa nao conciliada | Backend permite a exclusao logica |

## Validacoes e pendencias

- Compilacao Python: concluida sem erro.
- `git diff --check`: concluido sem erro.
- Templates: validacao sintatica pelo runtime da VPS pendente de registro.
- Testes focais persistentes: preparados, nao executados porque criam e
  alteram banco SQLite local; a governanca exige autorizacao expressa de
  Thiago para qualquer escrita em banco.
- Exclusao real da baixa `41`: nao executada; depende de autorizacao expressa
  e especifica de Thiago.
- Deploy de staging, screenshot e porta `5001`: dependem de branch revisada e
  merge em `staging`; ainda nao executados nesta etapa.
