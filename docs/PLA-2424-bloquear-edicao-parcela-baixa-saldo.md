# PLA-2424 - Bloquear edição de parcela com baixa e mostrar saldo

## Objetivo e regra de negócio

- Parcela com ao menos uma baixa ativa vinculada por `baixa.id_parcela` não
  permite alteração de número, vencimento ou valor.
- O backend rejeita a alteração mesmo em requisição POST manipulada.
- A guia de parcelas mantém os campos protegidos como somente leitura e mostra
  o saldo individual de todas as parcelas.
- Saldo da parcela = valor da parcela menos a soma de suas baixas ativas, com
  limite visual mínimo de zero.
- Parcela sem baixa continua editável e a exclusão de uma baixa não conciliada
  libera novamente a edição e a exclusão da parcela.

## Gate de arquitetura

- Skills consultadas: `plansmart-governanca-desenvolvimento`,
  `plansmart-projeto-psfinance` e `plansmart-projeto-vps-sistemas`.
- Controller: `financeiro/routes_titulos.py` valida imutabilidade no POST e
  agrega baixas ativas para calcular o saldo enviado à tela.
- Template: `templates/titulo_parcelas_form.html` preserva a grade existente,
  torna os campos protegidos somente leitura e inclui a coluna `Saldo`.
- Testes: `tests/test_parcela_exclusao_baixa.py` amplia a regressão do vínculo
  parcela/baixa sem criar uma regra paralela.
- Banco: nenhuma migration ou alteração estrutural.

## Matriz de validação funcional

| Caso | Resultado esperado | Resultado local |
| --- | --- | --- |
| Parcela de R$ 100,00 com baixa ativa de R$ 50,00 | Campos somente leitura e saldo R$ 50,00 | Aprovado |
| POST altera vencimento e valor da parcela com baixa | Rejeição; valores persistidos permanecem iguais | Aprovado |
| Parcela de R$ 100,00 sem baixa | Campos editáveis e saldo R$ 100,00 | Aprovado |
| POST altera parcela sem baixa para R$ 120,00 | Alteração persistida e título recalculado | Aprovado |
| Exclusão de parcela com baixa | Continua rejeitada no backend e na interface | Aprovado |
| Baixa não conciliada excluída | Edição e exclusão da parcela voltam a ser permitidas | Aprovado |
| Baixa conciliada | Baixa e parcela continuam protegidas | Aprovado |

## Validação local

```bash
.venv/bin/python -m py_compile financeiro/routes_titulos.py tests/test_parcela_exclusao_baixa.py
.venv/bin/python -m unittest -v tests/test_parcela_exclusao_baixa.py
git diff --check
```

Resultado: oito testes focais aprovados, compilação aprovada e nenhuma
inconsistência de whitespace.

## Gate visual

| Item solicitado | Referência | Implementação |
| --- | --- | --- |
| Bloquear edição com baixa | Grade real de parcelas publicada pela PLA-2407 | Mesmos campos e posições, agora somente leitura quando há baixa |
| Mostrar saldo | Regra de baixa por parcela da PLA-2276 | Nova coluna `Saldo`, ao lado de `Valor`, sem novos cards ou seções |
| Orientar o usuário | Mensagem existente da PLA-2407 | Texto passa a informar liberação de edição ou exclusão após excluir a baixa |

O screenshot da porta `5001` será anexado após integração e deploy da branch
`staging`, pois evidência local não substitui o gate visual do ambiente oficial.

## Riscos e pendências

- Risco residual baixo: baixas legadas sem `id_parcela` não identificam uma
  parcela específica e, portanto, não bloqueiam individualmente sua edição.
- A validação de staging, logs e porta `5001` depende da integração pelo fluxo
  oficial e permanece obrigatória antes da revisão executiva.
- Produção não faz parte desta entrega.
