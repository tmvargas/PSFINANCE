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

## Bloqueio do gate de ambiente

Em 2026-08-14, a porta pública `5001` ainda retornava HTTP 200 com PostgreSQL e branch `staging`, porém no commit anterior `ce1c45c7722c1223aeb92e5c08650f1c186ded42`.

O executor não possui arquivo de configuração SSH nem chave privada disponível. Tentativas em modo somente leitura e `BatchMode` para os usuários `root`, `ubuntu` e `plansmart` no host oficial retornaram `Permission denied (publickey,password)`.

Impacto: faltam deploy do commit atual da `staging`, validação de `/health`, `/gate`, `/financeiro/analise` e `/financeiro/extrato` na porta `5001`, consultas de controle no PostgreSQL real e screenshots das duas telas. Nenhuma ação em produção foi executada.

Desbloqueio: responsável com acesso operacional à VPS deve disponibilizar a identidade SSH ao executor ou executar o deploy exclusivamente da `staging` em `/opt/plansmart/sistemas/psfinance/staging/repo`; depois o GDSIS deve concluir os gates e encaminhar ao CEO pelo `executionPolicy` nativo já configurado.
