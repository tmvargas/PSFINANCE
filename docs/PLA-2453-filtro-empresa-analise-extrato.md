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

- Seis testes focais de `tests/test_filtro_empresa_analise_extrato.py`: aprovados novamente em 2026-08-14 com `python -m unittest -v`.
- `python -m compileall -q financeiro tests/test_filtro_empresa_analise_extrato.py`: aprovado no ambiente virtual do projeto.
- `git diff --check`: aprovado.
- Banco dos testes: SQLite isolado e descartável; nenhuma escrita em staging ou produção.

## GitHub e staging

- Branch funcional: `feat/PLA-2453-filtro-empresa-analise-extrato`.
- PR funcional `#76`: `https://github.com/tmvargas/PSFINANCE/pull/76`, base `staging`, head `3d331e56db7940b9e4d41da1baf452ea7872bf3e` e merge `434de396fb5955254bc845f350398cb4ef09bee8`.
- Complemento de memória compartilhada: commit `a1f6a41b8f25539163ea25e5927f612ed4dff541`, integrado pelo merge `2adc116e92a709c287cc5b6ed28f876c4a9b9fdb`.
- Evidência funcional/documental da branch: commit `13bcedc256a1df1561d6376dc34efbf2454627cb`, integrado pelo merge `a8210d9bc03cf03f48ee930d7555717745b8d2a7`.
- PR de deploy/evidências `#77`: `https://github.com/tmvargas/PSFINANCE/pull/77`, base `staging`, head `d294eb1402fa21213ff5ffe6a6a452ea393f1157` e merge `c196e2aa4fddd43b6b3ce4019b8b0f47aec3002d`.
- Commit da `staging` usado na coleta anterior ao PR corretivo `#78`: `c196e2aa4fddd43b6b3ce4019b8b0f47aec3002d`. O hash final, posterior ao merge da própria correção documental, deve ser registrado na issue técnica junto com a leitura simultânea de GitHub, VPS, `/health` e `/gate`.

## Validação final em staging

Em 2026-08-14, após a validação do acesso SSH (Secure Shell, acesso remoto seguro), a VPS foi atualizada exclusivamente pela branch `staging`. A reconfirmação pedida na revisão executiva foi executada após o merge do PR `#77`.

- Diretório: `/opt/plansmart/sistemas/psfinance/staging/repo`.
- Branch da VPS: `staging`.
- `HEAD` da VPS e `origin/staging`: `c196e2aa4fddd43b6b3ce4019b8b0f47aec3002d`.
- Árvore de trabalho da VPS: limpa.
- Serviços `psfinance-staging` e `psfinance-staging-gate`: ativos.
- `GET /health`, `/gate`, `/financeiro/analise` e `/financeiro/extrato` na porta `5001`: HTTP 200.
- `/health`: `status=healthy`, `branch=staging`, commit `c196e2aa4fddd43b6b3ce4019b8b0f47aec3002d`, banco PostgreSQL.
- `/gate`: `status=healthy`, commit `c196e2aa4fddd43b6b3ce4019b8b0f47aec3002d` e check interno `psfinance_staging` aprovado.
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

### Comprovação complementar solicitada na revisão executiva

Em 2026-08-14, a validação foi repetida no PostgreSQL real de staging para o
período de agosto/2026, usando duas empresas com dados financeiros no período e
a opção `Todas`. Os identificadores abaixo são técnicos e os nomes das empresas,
contas e documentos não foram expostos.

Os valores foram apurados de duas formas independentes:

1. consultas somente de leitura pelo SQLAlchemy, reproduzindo os critérios das
   rotas (`deleted = false`, período, natureza, plano financeiro e empresa);
2. leitura dos totais renderizados por `/financeiro/analise` e
   `/financeiro/extrato` diretamente na porta `5001`.

As duas formas retornaram os mesmos valores, centavo a centavo.

| Análise de Resultado | Receitas | Despesas | Resultado |
| --- | ---: | ---: | ---: |
| Empresa técnica `1` | R$ 0,00 | R$ 2.863,25 | R$ -2.863,25 |
| Empresa técnica `4` | R$ 0,00 | R$ 1.148,52 | R$ -1.148,52 |
| `Todas` | R$ 0,00 | R$ 4.011,77 | R$ -4.011,77 |

A visão `Todas` é exatamente a soma das duas empresas que possuem valores
classificados no período: `R$ 2.863,25 + R$ 1.148,52 = R$ 4.011,77`. Não houve
valor de uma empresa na visualização isolada da outra.

| Extrato | Conta técnica | Saldo inicial | Entradas | Saídas | Saldo final |
| --- | ---: | ---: | ---: | ---: | ---: |
| Empresa técnica `1` | `1` | R$ -14.148,16 | R$ 8.800,00 | R$ 15.407,66 | R$ -20.755,82 |
| Empresa técnica `4` | `13` | R$ 0,00 | R$ 0,00 | R$ 1.148,52 | R$ -1.148,52 |
| `Todas`, conta técnica `13` | `13` | R$ 0,00 | R$ 0,00 | R$ 1.148,52 | R$ -1.148,52 |

O seletor apresentou `10` contas para a empresa técnica `1`, `2` contas para a
empresa técnica `4` e `14` contas em `Todas`. Assim, cada empresa recebeu apenas
suas contas autorizadas, enquanto `Todas` restaurou o conjunto consolidado. A
conta técnica `13` manteve o mesmo saldo quando consultada pela empresa correta
e por `Todas`, demonstrando que a limpeza da preferência não altera o cálculo.

No momento desta coleta, VPS, GitHub, `/health` e `/gate` estavam alinhados ao
commit `2d454521a1752ef035835b9ec336658baa3ae905` da branch `staging`; a árvore da
VPS estava limpa e os serviços `psfinance-staging` e
`psfinance-staging-gate` estavam ativos. Nenhuma escrita foi realizada no banco.

Não houve merge na `main`, deploy em produção, migration ou escrita no banco de produção.

## Correção de recorrência da PLA-2479

- Erro devolvido pelo CEO: a prestação de contas misturava o PR funcional `#76`, commits complementares e o commit efetivamente publicado na VPS.
- Causa: a documentação permaneceu com o commit `a8210d9` depois que o PR de evidências `#77` avançou a `staging` para `c196e2a`.
- Correção: PRs, heads, merges, commits complementares, `origin/staging` e commit da VPS foram separados explicitamente nesta evidência.
- Não recorrência: GitHub, workspace e VPS foram consultados novamente; `origin/staging`, `HEAD` local da VPS, metadados de `/health` e `/gate` convergiram para o mesmo hash. O valor final fica na issue técnica porque o merge deste próprio documento avança novamente a `staging`.
- Risco residual: baixo e restrito à rastreabilidade histórica; código funcional, banco, `main` e produção não foram alterados nesta correção.
