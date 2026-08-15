# PLA-2577 - Correção de contas cruzadas no filtro do Extrato

## Causa e correção

- O backend já restringia as contas pela empresa e rejeitava combinações
  incompatíveis recebidas pela URL.
- Na interface, trocar a empresa não atualizava o seletor de contas antes do
  envio manual; por isso, contas de outras empresas permaneciam visíveis e uma
  seleção anterior podia acompanhar o novo filtro.
- A troca de empresa agora limpa a conta selecionada e reenvia imediatamente o
  filtro. A resposta renderiza apenas as contas vinculadas à empresa escolhida.

## Matriz funcional e contas esperadas × retornadas

| Caso | Ação | Resultado esperado |
| --- | --- | --- |
| Padrão | Abrir sem empresa | Exibe todas as contas, preservando a visão consolidada |
| Empresa preenchida | Selecionar Empresa Alfa | Recarrega e exibe somente contas da Empresa Alfa |
| Troca combinada | Conta Alfa selecionada e troca para Empresa Beta | Limpa Conta Alfa antes de recarregar |
| URL manipulada | Empresa Alfa com conta da Empresa Beta | Backend rejeita a conta incompatível |

A matriz abaixo foi obtida em `staging` por duas fontes independentes e
somente de leitura: vínculos ativos no PostgreSQL e opções renderizadas por
`GET /financeiro/extrato` na porta corporativa `5001`.

| Empresa | Contas esperadas no PostgreSQL | Contas retornadas no seletor da porta `5001` | Contas indevidas | Resultado |
| --- | --- | --- | --- | --- |
| `1 - THIAGO` | `5 BB THIAGO`; `1 C6`; `2 CAIXA THIAGO`; `3 CRÉDITO C6`; `4 CRÉDITO RICO`; `14 NUBANK - THIAGO`; `9 PS-APLICAÇÃO`; `8 PS-C6-CORRENTE`; `7 PS-INTER-CORRENTE`; `6 PS-INTER-CRÉDITO` | As mesmas 10 contas | Nenhuma | Aprovado |
| `2 - PLANSMART` | Nenhuma conta ativa vinculada | Nenhuma conta, além da opção neutra `Selecione...` | Nenhuma | Aprovado |
| `3 - OBRA VIOLETA` | `11 VIOLETA - RAQUEL`; `10 VIOLETA - THIAGO` | As mesmas 2 contas | Nenhuma | Aprovado |
| `4 - OBRA VIDA NOVA` | `12 VIDA NOVA - RAQUEL`; `13 VIDA NOVA - THIAGO` | As mesmas 2 contas | Nenhuma | Aprovado |
| `Todas as empresas` | União das 14 contas ativas permitidas | As mesmas 14 contas | Nenhuma | Aprovado |

## Escopo

- Skills consultadas: `plansmart-governanca-desenvolvimento`,
  `plansmart-projeto-psfinance` e `plansmart-projeto-vps-sistemas`.
- Sem alteração de banco, migration, variável de ambiente, `main` ou produção.

## Validação automatizada e em staging

- Sete testes focais de `tests/test_filtro_empresa_analise_extrato.py`:
  aprovados.
- Compilação de `financeiro` e do teste focal: aprovada.
- Empresa técnica `1`: `10` contas retornadas no seletor.
- Empresa técnica `3`: `2` contas retornadas no seletor.
- A troca entre as empresas limpou a conta anterior antes da navegação; os
  conjuntos foram renderizados novamente pelo backend e sem conta cruzada.
- A combinação manipulada entre a empresa A e a conta da empresa B continuou
  sem selecionar a conta e sem renderizar saldos ou resultados.
- `Todas as empresas` continuou restaurando a visão consolidada e limpando a
  preferência compartilhada, conforme teste de regressão existente.

Evidências visuais reais da porta `5001`:

- `docs/evidencias/PLA-2577/extrato-empresa-1-staging-5001.png` - Extrato com a
  empresa técnica `1` selecionada e conta anterior limpa.
- `docs/evidencias/PLA-2577/extrato-empresa-2-staging-5001.png` - Extrato com a
  empresa técnica `3` selecionada e conta anterior limpa.
- `docs/evidencias/PLA-2577/seletor-contas-thiago-staging-5001.png` - Seletor
  aberto para `1 - THIAGO`, exibindo nominalmente somente as 10 contas
  esperadas.
- `docs/evidencias/PLA-2577/seletor-contas-obra-violeta-staging-5001.png` -
  Seletor aberto para `3 - OBRA VIOLETA`, exibindo nominalmente somente as 2
  contas esperadas.

## Gate de staging e rastreabilidade do commit

- Branch da VPS: `staging`.
- Commit funcional integrado: `50aaed2302c0f71c284dad5b96957a3186683af6`.
- Commit da primeira coleta visual: `43192c9bdaeabf17c86bcc0b8ba850281d0220da`.
- O commit final de `staging`, que inclui esta matriz e os screenshots com o
  seletor aberto, deve ser registrado na issue após o merge e o redeploy. Esse
  registro pós-merge é a referência autoritativa, pois inserir o próprio hash
  neste documento criaria uma referência circular e mudaria novamente o hash.
- Serviços `psfinance-staging` e `psfinance-staging-gate`: ativos.
- `/health`, `/gate` e `/financeiro/extrato` na porta `5001`: HTTP 200.
- `/health` e `/gate`: `status=healthy`, branch `staging`, commit funcional e
  banco PostgreSQL.
- O metadado `GIT_COMMIT` do arquivo operacional de staging foi atualizado após
  o deploy; um backup recuperável foi preservado. Nenhum segredo foi exposto.
- Logs após o restart: inicialização normal do Gunicorn; mensagens SIGTERM
  correspondem ao encerramento controlado dos processos anteriores.

## Gate de recorrência

- Erro anterior: a revisão não conseguia ver as opções do seletor, não possuía
  a comparação esperadas × retornadas e recebeu hashes de `staging`
  inconsistentes entre documentação e entrega.
- Causa: os screenshots mostravam o seletor fechado; a matriz registrava apenas
  quantidades; e o documento tratava o commit funcional como se fosse o commit
  final da branch após a integração das próprias evidências.
- Correção: seletor aberto em duas empresas com conjuntos distintos, matriz
  nominal para todas as empresas e separação explícita entre commit funcional,
  commit de coleta e commit final pós-merge.
- Não recorrência: o gate final será repetido depois da integração destas
  evidências, exigindo igualdade entre `HEAD` da VPS, `origin/staging`,
  `/health` e `/gate` na porta `5001`.
- Risco residual: baixo, restrito à homologação visual; não houve alteração
  adicional de regra, banco, `main` ou produção.
