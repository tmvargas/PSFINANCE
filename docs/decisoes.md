# Decisoes - PSCONTROL

## 2026-07-20 - Criacao do repositorio

Decisao: iniciar o repositorio com documentacao e estrutura minima, sem fixar stack ou deploy.

Motivo: o MVP funcional ainda precisa ser definido e a VPS SISTEMAS ainda precisa receber acesso SSH.

Impacto: proximas alteracoes devem priorizar escopo, modelo de dados e fluxo operacional antes de implementacao pesada.

## 2026-07-30 - Implantacao piloto do PSFINANCE na VPS Sistemas

Decisao: tratar PSFINANCE como nome oficial do sistema e conduzir a implantacao piloto na VPS Sistemas primeiro em staging, sob responsabilidade tecnica do GDSIS, antes de qualquer acao em producao.

Motivo: a governanca exige validacao tecnica proporcional, uso da branch `staging`, evidencias de ambiente e separacao entre staging e producao antes da apresentacao da entrega.

Impacto: producao, merge na `main`, migrations ou escrita em banco produtivo permanecem condicionados a evidencias de staging e autorizacao expressa aplicavel.

## 2026-07-30 - Healthcheck minimo para staging do PSFINANCE

Decisao: criar uma aplicacao Flask minima com Gunicorn para validar o staging do PSFINANCE na VPS Sistemas, usando `/health` na porta interna `5104` e `/gate` na porta corporativa `5001`.

Motivo: o repositorio ainda estava apenas com documentacao inicial, mas a governanca exige validacao objetiva da branch `staging`, commit, servico e porta `5001`.

Impacto: a preparacao nao cria banco, nao altera producao e nao substitui a definicao futura do produto; serve como base operacional de staging ate a evolucao funcional do PSFINANCE.

## 2026-07-30 - Liberacao externa do gate de staging do PSFINANCE

Decisao: liberar o acesso externo de staging do PSFINANCE pela URL `http://vps69143.publiccloud.com.br:5001/gate`, usando Nginx na porta publica `5001` e mantendo os servicos Gunicorn vinculados apenas a `127.0.0.1`.

Motivo: Thiago precisava acessar o staging fora da VPS, mas a validacao anterior deixava a porta corporativa `5001` disponivel somente em loopback. A solucao preserva a aplicacao em porta interna e usa Nginx como ponto publico.

Impacto: o staging ficou acessivel para validacao externa sem alterar producao, banco de dados, branch `main` ou dados operacionais. A configuracao segue como provisoria ate formalizacao de dominio e HTTPS publico do PSFINANCE.

## 2026-07-30 - URL publica com prefixo /staging/psfinance

Decisao: manter as rotas tecnicas existentes (`/`, `/health` e `/gate`) e adicionar rotas equivalentes sob o prefixo `/staging/psfinance` para o staging publico do PSFINANCE, com Nginx publicando a URL principal na porta HTTP padrao `80`.

Motivo: a demanda PLA-825 exige uma URL de homologacao identificavel por sistema e sem porta explicita, sem depender apenas da rota tecnica `/gate`, preservando compatibilidade com as validacoes ja implantadas na porta corporativa `5001`.

Impacto: a URL publica principal de staging passa a aceitar `http://vps69143.publiccloud.com.br/staging/psfinance`, com healthcheck em `/staging/psfinance/health` e gate em `/staging/psfinance/gate`. A porta `5001` permanece como gate corporativo auxiliar, sem alterar producao, banco de dados ou credenciais.

## 2026-07-30 - Homologacao do PSFINANCE com pagina HTML

Decisao: alterar a rota de entrada do staging do PSFINANCE para retornar uma pagina HTML de homologacao, mantendo `/health` e `/gate` como respostas JSON tecnicas.

Motivo: a URL publica de homologacao estava abrindo diretamente o JSON operacional da aplicacao, o que nao atende ao uso esperado para acesso humano de validacao.

Impacto: `http://vps69143.publiccloud.com.br/staging/psfinance` e `/` passam a exibir uma pagina HTML simples com metadados do ambiente. As rotas tecnicas permanecem compativeis para monitoramento, porta `5001` e validacao automatizada.

## 2026-07-31 - Base real do PSFINANCE ainda nao localizada em operacao

Decisao: registrar que o PSFINANCE em operacao na VPS Sistemas permanece como staging tecnico sem banco real conectado.

Motivo: a verificacao da PLA-836 confirmou servicos `psfinance-staging` e `psfinance-staging-gate` ativos, branch `staging` no commit `e7c1b1ed566dc9f715d676bc3b94d6cd632a6376`, mas sem `DATABASE_URL`, sem `PSFINANCE_STAGING_DATABASE_URL`, sem PostgreSQL local ativo, sem `Docker` e sem diretorio produtivo do PSFINANCE.

Impacto: qualquer evolucao funcional com persistencia depende de aprovacao previa para criar ou conectar banco, definir usuario, variaveis de ambiente e modelo multicliente. A URL publica de homologacao nao deve ser tratada como evidencia de banco operacional.

## 2026-08-01 - PLA-981 bloqueada por artefatos funcionais nao localizados

Decisao: nao substituir o staging tecnico do PSFINANCE por uma implementacao funcional inventada ou por codigo de outro projeto enquanto o codigo fonte completo e a base fornecida por Thiago nao forem localizados.

Motivo: a PLA-981 autoriza configurar e subir em staging o sistema funcional ja fornecido, preservando dados. A verificacao em workspace, GitHub, historico Paperclip e VPS Sistemas nao localizou o codigo funcional completo nem o banco fornecido.

Impacto: a tarefa deve permanecer bloqueada por dependencia de artefatos, com desbloqueio sob responsabilidade de Thiago/CEO ao indicar caminho, repositorio, anexo ou origem segura do codigo e da base. Producao, `main`, banco produtivo e migrations produtivas continuam fora do escopo.

## 2026-08-01 - URL base do staging funcional com HTTP 200

Decisao: fazer a entrada `/staging/psfinance` renderizar diretamente o dashboard financeiro funcional, em vez de responder com redirecionamento para `/financeiro/`.

Motivo: a PLA-981 exige validar a URL publica de homologacao com HTTP 200 e tela funcional, mantendo `/health` e o gate corporativo `5001` como rotas tecnicas.

Impacto: o navegador continua exibindo o dashboard financeiro, mas a validacao objetiva da URL base passa a retornar HTTP 200 sem depender de redirect. Producao, `main` e banco produtivo permanecem fora do escopo.

## 2026-08-01 - PLA-985 retomada com ZIP funcional reenviado

Decisao: incorporar ao repositório somente o código funcional Flask recebido no ZIP `finance.zip`, mantendo o banco SQLite `financeiro.db` e anexos de títulos fora do Git por conterem dados operacionais.

Motivo: a PLA-985 destrava a PLA-981 ao localizar o artefato reenviado por Thiago, mas a governança proíbe versionar dados de clientes, documentos privados, dumps, bancos e uploads.

Impacto: o staging funcional deve usar `PSFINANCE_DATABASE_URL` ou `DATABASE_URL` apontando para um banco em `instance/`, e uploads devem permanecer em diretório operacional não versionado. Produção, `main`, banco produtivo e migrations produtivas continuam fora do escopo.

## 2026-08-01 - PLA-988 migracao controlada do staging para PostgreSQL

Decisao: preparar o PSFINANCE para priorizar `PSFINANCE_STAGING_DATABASE_URL`
no staging e versionar um script transacional de migracao SQLite para
PostgreSQL, sem versionar o banco SQLite nem arquivos anexos.

Motivo: a PLA-988 exige substituir o SQLite do staging por PostgreSQL
preservando dados. O inventario local confirmou dados operacionais nas tabelas
financeiras e cinco registros de `documento` com auditoria tecnica nula.

Impacto: o script cria a estrutura pelo SQLAlchemy, copia os dados para um
PostgreSQL vazio, preserva chaves e vinculos e preenche apenas campos tecnicos
de auditoria ausentes. Producao, `main` e escrita em banco produtivo continuam
fora do escopo.

## 2026-08-02 - PLA-1005 evidencia oficial do backend PostgreSQL em staging

Decisao: expor em `/health` e `/gate` metadados nao sensiveis do banco em uso
pela aplicacao (`db_dialect` e `database_url_source`), sem retornar URL,
usuario, senha ou qualquer conteudo de `.env`.

Motivo: a divergencia da PLA-1004 foi causada por validacao manual sem carregar
o `EnvironmentFile` do systemd, o que fazia a leitura local cair no fallback
SQLite. Com o ambiente real do servico carregado, o staging usa PostgreSQL e as
contagens operacionais foram preservadas.

Impacto: a validacao oficial da porta `5001` passa a comprovar diretamente se o
processo em execucao esta usando `PSFINANCE_STAGING_DATABASE_URL` e o dialeto
PostgreSQL, reduzindo risco de nova evidencia ambigua. Producao, `main` e banco
produtivo permanecem fora do escopo.

## 2026-08-02 - PLA-1016 mockup estatico do layout inicial do PSFINANCE

Decisao: entregar a PLA-1016 como mockup HTML estatico em `docs/mockups/`,
sem alterar templates da aplicacao Flask, banco, rotas, VPS ou producao.

Motivo: a tarefa solicita validacao visual antes de implementacao em codigo e
define como requisitos a referencia ABF, variacao verde e menu lateral com
comportamento de recolhimento vertical e horizontal.

Impacto: a entrega permite revisao visual navegavel pelo CEO antes de qualquer
implementacao no produto. A aplicacao PSFINANCE em staging permanece sem
alteracao funcional nesta etapa.

## 2026-08-02 - PLA-1019 ajustes do mockup de menu inicial

Decisao: manter os ajustes da PLA-1019 no mesmo artefato estatico de mockup
criado para a PLA-1016, em `docs/mockups/PLA-1016-layout-inicial.html`, sem
alterar templates da aplicacao Flask, rotas, banco, VPS ou producao.

Motivo: a demanda e um refinamento visual do menu inicial e depende da base do
mockup ainda nao integrada a `staging`; implementar diretamente no produto antes
da validacao visual quebraria a decisao da PLA-1016.

Impacto: o menu inicial passa a refletir a hierarquia solicitada por Thiago:
`Titulos` e `Baixas` sob `FINANCEIRO > CONTAS A PAGAR`, `Movimentacoes` e
`Extrato` sob `FINANCEIRO > CAIXAS E BANCOS`, com expansao lateral pelo icone e
icones/siglas em todos os menus, mantendo o escopo restrito a
documentacao/mockup.

## 2026-08-02 - PLA-1022 refacao do mockup de menu rejeitado

Decisao: refazer o menu do mockup estatico em
`docs/mockups/PLA-1016-layout-inicial.html`, corrigindo nomes e grupos para os
termos exatos da tarefa, removendo resumo e contadores do menu lateral e
mantendo evidencia reproduzivel de submenu expandido a direita quando o menu
esta recolhido.

Motivo: a versao anterior da `PLA-1019` foi rejeitada por Thiago e o screenshot
evidenciava sobreposicao do submenu sobre a area principal, alem de ruido visual
no menu lateral para uma tela operacional.

Impacto: a `PLA-1022` mantem a hierarquia financeira ja solicitada, corrige
`GERENCIAL`, `APOIO`, `Título`, `Baixa` e `Credor`, e entrega um menu mais
simples para revisao executiva, sem alterar aplicacao Flask, rotas, banco, VPS
ou producao.

## 2026-08-02 - PLA-1027 icones reais no mockup de menu

Decisao: substituir as siglas usadas como marcadores visuais no mockup
estatico por icones SVG embutidos em
`docs/mockups/PLA-1016-layout-inicial.html`, preservando a hierarquia e o
comportamento do menu da `PLA-1022`.

Motivo: a tarefa solicita corrigir o mockup com icones reais no menu. Manter os
icones embutidos evita dependencia externa para a revisao visual e preserva a
entrega como artefato navegavel em HTML estatico.

Impacto: grupos, menus, submenus e atalhos rapidos passam a exibir icones
visuais em vez de siglas, sem alterar aplicacao Flask, rotas, banco de dados,
VPS ou producao.

## 2026-08-02 - PLA-1031 estado fechado do menu no mockup

Decisao: corrigir o estado recolhido do mockup estatico em
`docs/mockups/PLA-1016-layout-inicial.html` para que `?compact=1` represente o
menu fechado limpo, sem grupos, itens, icones de navegacao, rotulos ou submenus
visiveis, mantendo somente um controle minimo para reabrir o menu.

Motivo: Thiago rejeitou a versao anterior com o criterio objetivo de que menu
fechado nao deve aparecer nada. A versao anterior ainda deixava uma coluna de
icones de navegacao visivel, o que parecia menu fechado com itens.

Impacto: o mockup passa a diferenciar corretamente menu aberto acionavel e menu
fechado limpo. Submenus continuam disponiveis no estado aberto para validar a
hierarquia, sem alterar aplicacao Flask, rotas, banco de dados, VPS ou
producao.

## 2026-08-02 - PLA-1031 publicacao do mockup em staging

Decisao: integrar a cadeia visual do mockup na branch `staging`, atualizar a VPS
de teste pela propria `staging` e ajustar apenas o metadado nao sensivel
`GIT_COMMIT` do ambiente de staging para refletir o commit publicado no gate
corporativo.

Motivo: a governanca exige que a branch `staging`, a VPS de teste e a porta
corporativa `5001` estejam coerentes antes de encaminhar a entrega para revisao.

Impacto: o gate publico
`http://vps69143.publiccloud.com.br:5001/gate` passa a validar a publicacao do
mockup na VPS de teste com status `healthy`, sem alterar producao, `main`,
banco de dados, dados operacionais ou segredos.

## 2026-08-02 - PLA-1036 menu encolhido com icones e flyout lateral

Decisao: ajustar o estado encolhido do mockup estatico em
`docs/mockups/PLA-1016-layout-inicial.html` para exibir uma coluna estreita com
icones reais de navegacao e permitir flyout lateral dos submenus a partir dos
icones.

Motivo: a PLA-1036 altera o criterio visual da PLA-1031. O estado encolhido
deixa de representar menu totalmente fechado e passa a representar navegacao
compacta acionavel, mantendo rotulos ocultos e submenu lateral para os itens
expansivos.

Impacto: `?compact=1` mostra os icones do menu principal; `?compact=1&open=`
permite evidenciar o flyout lateral de `contas-pagar` ou `caixas-bancos`. A
alteracao permanece restrita ao mockup/documentacao, sem alterar aplicacao
Flask, rotas, banco de dados, VPS, `main` ou producao.

## 2026-08-03 - PLA-1043 aplicacao do layout aprovado nas rotinas

Decisao: aplicar o layout aprovado do mockup ao produto real pelo template base
`templates/base.html`, transformando a navbar superior antiga em shell com menu
lateral, grupos `HOME`, `FINANCEIRO`, `GERENCIAL` e `APOIO`, submenus e modo
compacto com flyout.

Motivo: todas as rotinas da aplicacao Flask herdam o mesmo template base, entao
centralizar a mudanca aplica o visual aprovado nas telas existentes sem
duplicar estrutura de menu ou alterar regras de negocio.

Impacto: a entrega altera somente apresentacao, navegacao e estilos globais do
template base. Nao altera models, controllers, services, banco de dados,
variaveis de ambiente, VPS, `main` ou producao.

Complemento de entrega: apos merge da branch da tarefa na `staging`, a VPS de
teste foi atualizada pela propria `staging`. O metadado nao sensivel
`GIT_COMMIT` do ambiente de staging foi ajustado para o commit validado, sem
alterar segredos, banco de dados, `main` ou producao.

Complemento de correcao: apos revisao executiva complementar, o item `Contas`
foi removido do grupo `APOIO` no menu aberto e no flyout compacto, mantendo
somente `Credor` e `Plano Financeiro` conforme a hierarquia aprovada por
Thiago para a PLA-1015. As rotas e telas de contas existentes foram preservadas
fora da navegacao aprovada, sem alterar regras de negocio, banco de dados,
`main` ou producao.


## 2026-08-04 - PLA-1235 cadastros Empresa e Centro de Custo PSFINANCE

Decisao: implementar os cadastros funcionais `APOIO > Empresa` e
`APOIO > Centro de Custo` no PSFINANCE, conforme arquitetura aprovada na
`PLA-1221`.

Motivo: a `PLA-1221` consolidou a nomenclatura funcional e tecnica, mas nao
entregou diff funcional. A `PLA-1235` atende a etapa seguinte, criando os
modelos, rotas e telas minimas para que empresas e centros de custo possam ser
cadastrados antes da aplicacao do isolamento financeiro completo por
`id_empresa` e `id_centro_custo`.

Regra aplicada: `Empresa` aceita somente os tipos `EMPRESA`, `SPE` e `SCP`.
`Centro de Custo` exige vinculo com uma empresa ativa. Codigos ativos ficam
unicos por cadastro de empresa e por empresa no cadastro de centro de custo.
Desativacao de empresa com centro de custo ativo fica bloqueada.

Impacto: a entrega cria tabelas novas via `Base.metadata.create_all` quando a
aplicacao inicializar em ambiente sem essas tabelas e tambem prepara script SQL
versionado para staging. O script nao foi executado neste heartbeat. Nao altera
tabelas operacionais existentes, dados produtivos, variaveis de ambiente, VPS,
`main` ou producao.
## 2026-08-04 - PLA-1235 - Empresa e centro de custo em titulos e movimentacoes

- Projeto: PSFINANCE.
- Decisao: novos titulos e movimentacoes financeiras devem exigir empresa ativa
  e centro de custo ativo pertencente a empresa selecionada.
- Aplicacao: a validacao foi centralizada em `financeiro/regras_empresa_centro.py`
  e reutilizada nos fluxos de titulos e movimentacoes.
- Banco: as colunas preparadas em `titulo` e `movimentacao_conta` permanecem
  opcionais na migration para preservar dados historicos; a obrigatoriedade
  vale no backend para novos registros e edicoes.
- Producao: nenhuma migration ou escrita em producao esta autorizada por esta
  decisao.
