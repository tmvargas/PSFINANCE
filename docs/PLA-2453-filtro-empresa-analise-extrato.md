# PLA-2453 - Filtro por empresa em Análise de Resultado e Extrato

## Arquitetura e regra

- Skills consultadas: `plansmart-governanca-desenvolvimento`, `plansmart-projeto-psfinance` e `plansmart-projeto-vps-sistemas`.
- Regra compartilhada: `resolver_filtro_empresa_memorizado()` centraliza validação, memória de sessão e limpeza por `Todas` para Títulos, Análise e Extrato.
- Análise: movimentações usam `MovimentacaoConta.id_empresa`; baixas usam `Titulo.id_empresa`; o detalhamento preserva o mesmo filtro.
- Extrato: a empresa limita o seletor de contas e uma combinação manipulada de empresa/conta é ignorada.
- Sem empresa selecionada, as telas preservam a visão consolidada permitida pelo comportamento anterior.
- Sem alteração de banco, migration, produção ou regra de conciliação.

## Matriz funcional automatizada

| Caso | Filtros | Resultado esperado | Evidência |
| --- | --- | --- | --- |
| Análise padrão | mês + ano, empresa vazia | Soma empresas Alfa e Beta | Teste `test_analise_sem_empresa_preserva_visao_consolidada` |
| Análise por empresa | mês + ano + Alfa | Inclui somente movimentações e baixas da Alfa | Teste `test_analise_filtra_movimentacoes_e_baixas_por_empresa` |
| Extrato por empresa | Alfa | Lista Conta Alfa e exclui Conta Beta | Teste `test_extrato_lista_so_contas_da_empresa_e_rejeita_conta_cruzada` |
| Extrato combinado | Alfa + Conta Alfa + período | Exibe saldo e movimentações da conta válida | Teste `test_extrato_empresa_selecionada_mantem_conta_valida` |
| Acesso manipulado | Alfa + Conta Beta | Conta incompatível não é selecionada | Teste `test_extrato_lista_so_contas_da_empresa_e_rejeita_conta_cruzada` |
| Memória compartilhada | Seleciona Alfa na Análise e abre Extrato | Alfa permanece selecionada e limita contas | Teste `test_preferencia_e_compartilhada_e_todas_limpa_a_sessao` |
| Limpeza | Seleciona `Todas` | Preferência removida e visão consolidada restaurada | Teste `test_preferencia_e_compartilhada_e_todas_limpa_a_sessao` |
| Empresa inválida | `id_empresa=999999` | Parâmetro ignorado e preferência inválida removida | Teste `test_empresa_invalida_limpa_preferencia_memorizada` |

## Validação local

- 21 testes automatizados: aprovados.
- `python -m compileall`: aprovado no ambiente virtual temporário.
- `git diff --check`: aprovado.
- Banco dos testes: SQLite isolado e descartável; nenhuma escrita em staging ou produção.

## GitHub e staging

- Branch: `feat/PLA-2453-filtro-empresa-analise-extrato`.
- PR: `https://github.com/tmvargas/PSFINANCE/pull/76`, base `staging`.
- Commit funcional mais recente da branch: `a1f6a41`.
- Commit integrado em `staging`: `2adc116e92a709c287cc5b6ed28f876c4a9b9fdb`.

## Validação final em staging

Em 2026-08-14, após a validação do acesso SSH, a VPS foi atualizada exclusivamente pela branch `staging`, por fast-forward de `ce1c45c7722c1223aeb92e5c08650f1c186ded42` para `a8210d9bc03cf03f48ee930d7555717745b8d2a7`.

- Diretório: `/opt/plansmart/sistemas/psfinance/staging/repo`.
- Branch da VPS: `staging`.
- `HEAD` da VPS e `origin/staging`: `a8210d9bc03cf03f48ee930d7555717745b8d2a7`.
- Árvore de trabalho da VPS: limpa.
- Serviços `psfinance-staging` e `psfinance-staging-gate`: ativos.
- `GET /health`, `/gate`, `/financeiro/analise` e `/financeiro/extrato` na porta `5001`: HTTP 200.
- `/health`: `status=healthy`, `branch=staging`, commit `a8210d9`, banco PostgreSQL.
- Logs dos serviços após a estabilização: sem entradas de nível warning ou superior.
- O primeiro acesso imediatamente após o restart retornou HTTP 502 durante a subida do Gunicorn; a repetição após o serviço ficar pronto retornou HTTP 200 e não houve recorrência nos logs.

Validação funcional no PostgreSQL real de staging:

- Análise com `id_empresa=2`: empresa `PLANSMART` permaneceu selecionada.
- Ao abrir o Extrato na mesma sessão, a preferência `PLANSMART` foi preservada.
- O seletor de contas do Extrato ficou vazio para essa empresa, comprovando que contas de outras empresas não foram oferecidas.
- Sem filtro, as duas telas continuaram apresentando a opção `Todas as empresas`.

Evidências visuais:

- `docs/evidencias/PLA-2453/analise-empresa-plansmart-staging-5001.png` - Análise de Resultado real na porta `5001`, filtrada pela empresa PLANSMART.
- `docs/evidencias/PLA-2453/extrato-empresa-plansmart-staging-5001.png` - Extrato real na porta `5001`, com a mesma empresa selecionada e contas incompatíveis ausentes.

Não houve merge na `main`, deploy em produção, migration ou escrita no banco de produção.
