# PLA-743 — matriz obrigatória de paridade

Contas a Receber deve repetir a linguagem, navegação e comportamento de Contas
a Pagar. As únicas trocas funcionais são Credor por Cliente, plano de saída por
plano de entrada e pagamento por recebimento.

| Contas a Pagar | Contas a Receber | Aceite obrigatório |
| --- | --- | --- |
| Contas a Pagar > Título | Contas a Receber > Título | Mesma consulta, resumo, filtros, colunas e ações |
| Credor | Cliente | Mesma busca código/nome, lupa e cadastro em popup |
| Plano financeiro de saída | Plano financeiro de entrada | Somente analíticas `1.*` |
| Novo/editar/copiar título | Novo/editar/copiar título | Mesmos campos, validações e anexos |
| Controle de parcelas | Controle de parcelas | Até 999, edição individual, soma exata e bloqueio com baixa |
| Baixa | Baixa | Parcial/total, seleção de parcela, conta da empresa e histórico |
| Exclusão de baixa | Estorno da baixa | Mesma proteção de conciliação e recomposição do saldo |
| Exclusão de título/parcela | Exclusão de título/parcela | Bloqueada quando existir baixa ativa |

Não entregar por etapas visíveis. A publicação só ocorre quando todas as linhas
forem comprovadas por testes de sucesso e erro e por comparação desktop/móvel
com as telas reais de Contas a Pagar.
