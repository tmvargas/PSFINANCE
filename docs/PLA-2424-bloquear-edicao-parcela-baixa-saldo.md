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

## GitHub e staging

- Branch da tarefa: `fix/PLA-2424-bloquear-edicao-parcela-baixa-saldo`.
- Commit da tarefa: `11802bb85f142c544a42270455d56c93d4f812de`.
- PR: `https://github.com/tmvargas/PSFINANCE/pull/75`, base `staging`.
- Commit publicado inicialmente em `staging`:
  `e4ee88b38d5a1fa2985d54d18cc909c0f42c83f3`.
- VPS: `/opt/plansmart/sistemas/psfinance/staging/repo`, branch `staging`,
  HEAD igual ao `origin/staging` e diretório sem alterações locais.
- Serviços `psfinance-staging` e `psfinance-staging-gate`: ativos.
- Oito testes focais aprovados também no runtime Python 3.12 da VPS.

## Validação na porta 5001

| Verificação | Resultado |
| --- | --- |
| `GET /health` | HTTP 200, PostgreSQL, branch `staging`, commit `e4ee88b` |
| `GET /gate` | HTTP 200, aplicação interna em `127.0.0.1:5104` saudável |
| `GET /financeiro/titulos/1/parcelas` | HTTP 200, uma coluna `Saldo`, quatro atributos `readonly` e orientação de bloqueio |
| Logs após deploy | Sem exceção da aplicação; dois `SIGTERM` esperados durante o restart dos workers |

Evidência visual:

- `docs/evidencias/PLA-2424/parcela-com-baixa-bloqueada-saldo-5001.png` - Tela
  real publicada na porta `5001`, com coluna `Saldo`, valor `R$ 0,00`, campos de
  vencimento e valor protegidos, lixeira desabilitada e orientação para excluir
  a baixa antes de editar ou excluir a parcela.

Comparação objetiva: menu lateral, topo, card, botões existentes, ordem das
parcelas e bloco `Nova parcela` foram preservados; a única coluna acrescentada
foi `Saldo`, solicitada na demanda, posicionada ao lado de `Valor`.

## Riscos e pendências

- Risco residual baixo: baixas legadas sem `id_parcela` não identificam uma
  parcela específica e, portanto, não bloqueiam individualmente sua edição.
- Risco visual baixo: a orientação ocupa mais altura na célula `Excluir`, sem
  alterar a estrutura ou ocultar ações existentes.
- Produção não faz parte desta entrega.
