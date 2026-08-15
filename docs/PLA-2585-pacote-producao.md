# PLA-2585 - Pacote de Produção atualizado do PSFINANCE

## Disposição executiva

- Data da análise: 15/08/2026.
- Projeto: PSFINANCE, no projeto guarda-chuva `VPS - SISTEMAS`.
- Skills consultadas: `plansmart-governanca-desenvolvimento`,
  `plansmart-projeto-psfinance` e `plansmart-projeto-vps-sistemas`.
- Commit de `staging`: `45edca507b5b7038d647f663b25059ede26d32d2`.
- Commit atual de `main`: `23821c7786e98c5c489c60c2ac60760e3cdc17c1`.
- Recomendação do GDSIS: **não recomenda a promoção neste estado**.
- Nenhuma ação foi executada em `main`, banco de produção ou ambiente de
  produção.

## Escopo identificado entre `main` e `staging`

A diferença contém `219` commits e `214` arquivos. O merge sintático de Git
(`git merge-tree --write-tree origin/main origin/staging`) concluiu sem conflito
textual e produziu a árvore temporária
`719d4cd094a6dc8bc1c25095c4850a6eaeab6a57`. Isso comprova apenas a ausência
de conflito textual; não substitui a homologação funcional nem autoriza o merge.

Tarefas rastreadas nas mensagens dos commits:

`PLA-747`, `PLA-814`, `PLA-815`, `PLA-825`, `PLA-831`, `PLA-836`, `PLA-981`,
`PLA-985`, `PLA-988`, `PLA-1005`, `PLA-1016`, `PLA-1019`, `PLA-1022`,
`PLA-1027`, `PLA-1031`, `PLA-1036`, `PLA-1043`, `PLA-1235`, `PLA-1290`,
`PLA-1359`, `PLA-1370`, `PLA-1376`, `PLA-1480`, `PLA-1618`, `PLA-1655`,
`PLA-1816`, `PLA-2073`, `PLA-2106`, `PLA-2111`, `PLA-2117`, `PLA-2148`,
`PLA-2155`, `PLA-2171`, `PLA-2264`, `PLA-2272`, `PLA-2276`, `PLA-2315`,
`PLA-2407`, `PLA-2409`, `PLA-2424`, `PLA-2453`, `PLA-2479`, `PLA-2577` e
`PLA-2581`.

O escopo material inclui a retomada da aplicação Flask, PostgreSQL, cadastros
de empresa e centro de custo, vínculos por empresa, títulos e parcelas, baixas
por parcela, filtros financeiros, transferências, templates, testes, scripts de
migração e infraestrutura de staging. A `main` ainda representa a base legada
PSCONTROL e não contém a aplicação funcional atual do PSFINANCE.

## Gate de staging

Validação executada na VPS `vps69143.publiccloud.com.br`:

- diretório: `/opt/plansmart/sistemas/psfinance/staging/repo`;
- branch: `staging`;
- `HEAD` da VPS = `origin/staging` =
  `45edca507b5b7038d647f663b25059ede26d32d2`;
- árvore de trabalho da VPS: limpa;
- serviços `psfinance-staging` e `psfinance-staging-gate`: ativos;
- `/health` interno em `5104`: HTTP 200, PostgreSQL e commit correto;
- `/health`, `/gate`, `/financeiro/`, `/financeiro/titulos`,
  `/financeiro/extrato` e `/financeiro/analise` na porta `5001`: HTTP 200;
- logs dos dois serviços sem entradas de nível warning ou superior após a
  estabilização;
- houve HTTP 502 transitório durante o restart controlado; as repetições após
  a subida do Gunicorn retornaram HTTP 200 e o erro não persistiu.

O metadado operacional `GIT_COMMIT` foi alinhado ao commit publicado. Foram
preservados backups recuperáveis dos arquivos operacionais alterados. Nenhum
segredo foi exposto.

## Testes

- `.venv/bin/python -m unittest discover -s tests -v`: `29` testes aprovados.
- `.venv/bin/python -m compileall -q src financeiro tests`: aprovado.
- `git diff --check`: aprovado.
- Evidências funcionais e visuais de staging permanecem nos documentos das
  tarefas listadas, inclusive PLA-2453, PLA-2577 e PLA-2581.

Limitação: o conjunto automatizado atual cobre quatro módulos de teste e não
constitui homologação integral dos `219` commits. Antes de produção, cada
funcionalidade incluída precisa ter aceite executivo consolidado.

## Banco de dados

### Estrutura e scripts versionados

1. `20260804_pla1235_empresa_centro_custo.sql` cria `empresa` e
   `centro_custo`, inclui vínculos em `titulo` e `movimentacao_conta` e cria
   índices.
2. `20260804_pla1290_backfill_empresa_1_centro_1001.sql` atualiza títulos e
   movimentações sem vínculo para a empresa `1` e centro `1001`, abortando se
   as pré-condições não forem únicas.
3. `20260805_pla1376_conta_empresa.sql` cria `conta.id_empresa`, preenche contas
   sem empresa e torna a coluna obrigatória.
4. `20260810_pla1816_titulo_parcela.sql` cria `titulo_parcela` com constraints e
   índices.
5. `20260812_pla2276_baixa_por_parcela.sql` cria `baixa.id_parcela` e vincula
   baixas quando o título possui exatamente uma parcela ativa.

### Classificação dos dados

- Estrutura: tabelas, colunas, chaves, constraints e índices listados acima.
- Configuração obrigatória: empresa código `1` e centro de custo `1001` são
  pré-condições dos backfills, mas ainda precisam ser confirmados na produção.
- Dados operacionais: títulos, movimentações, contas, parcelas e baixas reais
  devem ser preservados.
- Cópia de staging para produção: **não prevista e não recomendada**.

### Lacunas bloqueadoras do banco

O ambiente e o banco de produção do PSFINANCE não estão implantados na VPS.
Por isso, não foi possível executar comparação somente de leitura de schema,
contagens, volume, compatibilidade das pré-condições, duração das migrations
ou tamanho do backup. Os scripts não possuem migrations reversas completas; o
rollback de dados depende de backup validado e restauração controlada.

Pergunta obrigatória para Thiago, caso o pacote volte a ser apresentado para
autorização: **migrar dados de staging para produção ou preservar os dados
operacionais existentes em produção?** A recomendação técnica do GDSIS é
preservar os dados de produção e aplicar somente estrutura e configurações
obrigatórias, após validação.

## Infraestrutura de produção

Fatos confirmados por leitura na VPS:

- `/opt/plansmart/sistemas/psfinance/production/repo` não existe;
- não existe serviço de produção do PSFINANCE;
- a porta interna planejada `6104` não está em escuta;
- somente os serviços de staging estão instalados.

Também permanecem pendentes na skill: domínio oficial, HTTPS, modelo
multicliente, isolamento definitivo, política de branches e definição
operacional de serviços/logs de produção. Criar banco, usuário, diretório,
serviço ou domínio excede o escopo deste pacote e exige autorização aplicável.

## Riscos

Classificação geral: **alto**.

| Risco | Probabilidade | Impacto | Mitigação obrigatória |
| --- | --- | --- | --- |
| Produção inexistente | Confirmado | Crítico | Implantar e validar ambiente isolado antes do deploy |
| `main` legada e escopo de 219 commits | Alta | Alto | Homologação consolidada e janela controlada |
| Backfills sobre dados reais | Média | Alto | Leitura prévia, backup, contagens, transação e validação |
| Modelo multicliente pendente | Confirmado | Alto | Decisão formal de isolamento antes de uso produtivo |
| HTTPS/domínio produtivo pendentes | Confirmado | Alto | Configurar Nginx, DNS e certificado antes da liberação |
| Rollback de banco incompleto | Alta | Alto | Preparar reversão por migration ou restauração testada |
| Cobertura automatizada parcial | Alta | Médio | Executar matriz de regressão e jornadas críticas completas |

Estimativa de indisponibilidade: não pode ser calculada com segurança sem
ambiente produtivo, volume real e medição das migrations.

## Plano de implantação proposto, ainda não autorizado

1. Confirmar modelo multicliente, domínio, HTTPS e arquitetura de produção.
2. Criar ambiente produtivo isolado e banco dedicado, somente após autorização.
3. Executar inventário somente de leitura e comparar schema/dados obrigatórios.
4. Testar as cinco migrations, contagens e duração em clone sanitizado ou
   ambiente equivalente.
5. Consolidar a homologação das tarefas incluídas e congelar os commits.
6. Atualizar este pacote com backup, janela, indisponibilidade e rollback
   mensuráveis.
7. Submeter o pacote atualizado ao CEO e, depois, a Thiago para autorização
   expressa vinculada aos commits e scripts.
8. Somente após autorização: backup, migrations na ordem aprovada, merge de
   `staging` em `main`, deploy da `main`, restart, logs e validação funcional.

Responsável pela preparação técnica: GDSIS. Responsável pela revisão
executiva: CEO, pelo stage nativo de `review`. Autorização de produção: Thiago.

## Plano de rollback proposto

- Registrar commit anterior da `main` e do ambiente antes de qualquer ação.
- Criar e validar backup integral do banco produtivo e das configurações.
- Em falha de código, retornar ao commit anterior da `main` e reiniciar o serviço.
- Em falha estrutural ou de backfill, interromper a aplicação e restaurar o
  backup validado; rollback de código isolado não reverte banco.
- Validar banco, logs, autenticação e jornadas críticas após a restauração.

O tempo de recuperação permanece indeterminado até a medição do backup e da
restauração no ambiente equivalente.

## Gate e próxima decisão

O gate de arquitetura e o gate de staging foram comprovados. Os gates de banco,
infraestrutura produtiva, homologação integral e rollback mensurável estão
incompletos. Portanto, este documento é um Pacote de Produção atualizado para
revisão executiva, mas **não está pronto para solicitação de autorização de
produção**.

Próxima decisão solicitada ao CEO: confirmar a reprovação temporária da
promoção e organizar, por fluxo nativo de tarefas, o saneamento da
infraestrutura produtiva, do banco e da homologação antes de novo pacote.
