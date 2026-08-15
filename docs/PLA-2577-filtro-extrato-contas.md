# PLA-2577 - Correção de contas cruzadas no filtro do Extrato

## Causa e correção

- O backend já restringia as contas pela empresa e rejeitava combinações
  incompatíveis recebidas pela URL.
- Na interface, trocar a empresa não atualizava o seletor de contas antes do
  envio manual; por isso, contas de outras empresas permaneciam visíveis e uma
  seleção anterior podia acompanhar o novo filtro.
- A troca de empresa agora limpa a conta selecionada e reenvia imediatamente o
  filtro. A resposta renderiza apenas as contas vinculadas à empresa escolhida.

## Matriz funcional

| Caso | Ação | Resultado esperado |
| --- | --- | --- |
| Padrão | Abrir sem empresa | Exibe todas as contas, preservando a visão consolidada |
| Empresa preenchida | Selecionar Empresa Alfa | Recarrega e exibe somente contas da Empresa Alfa |
| Troca combinada | Conta Alfa selecionada e troca para Empresa Beta | Limpa Conta Alfa antes de recarregar |
| URL manipulada | Empresa Alfa com conta da Empresa Beta | Backend rejeita a conta incompatível |

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

## Gate de staging

- Branch da VPS: `staging`.
- Commit funcional publicado: `50aaed2302c0f71c284dad5b96957a3186683af6`.
- `HEAD` da VPS e `origin/staging`: iguais ao commit funcional.
- Serviços `psfinance-staging` e `psfinance-staging-gate`: ativos.
- `/health`, `/gate` e `/financeiro/extrato` na porta `5001`: HTTP 200.
- `/health` e `/gate`: `status=healthy`, branch `staging`, commit funcional e
  banco PostgreSQL.
- O metadado `GIT_COMMIT` do arquivo operacional de staging foi atualizado após
  o deploy; um backup recuperável foi preservado. Nenhum segredo foi exposto.
- Logs após o restart: inicialização normal do Gunicorn; mensagens SIGTERM
  correspondem ao encerramento controlado dos processos anteriores.
