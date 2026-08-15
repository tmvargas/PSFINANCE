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
