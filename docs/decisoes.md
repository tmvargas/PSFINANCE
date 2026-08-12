# Decisoes - PSCONTROL

## 2026-08-12 - Sincronizacao da parcela unica do titulo conforme Sienge

Decisao: na edicao de um titulo existente com exatamente uma parcela ativa, o
PSFINANCE passa a sincronizar a parcela unica com o valor total e a data do
primeiro vencimento salvos na tela principal do titulo. Para titulos com duas
ou mais parcelas ativas, a distribuicao permanece sob controle exclusivo da aba
`Parcelas`, com inclusao aberta somente por botao, numero de parcela como
rotulo e exclusao por lixeira com marcacao visual antes de salvar.

Motivo: o fluxo validado para o PSFINANCE segue o comportamento do Sienge em
que a aba `Parcelas` controla inclusao e distribuicao, uma parcela por vez, e o
valor do titulo reflete as parcelas; para parcela unica, manter titulo e parcela
divergentes gera erro operacional.

Impacto: a correcao preserva a regra ja validada de multiplas parcelas, evita
divergencia em titulos simples e aproxima a experiencia visual da referencia do
Sienge, sem migration, sem banco de producao e sem alteracao de infraestrutura
de producao.

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

## 2026-08-05 - PLA-1480 menu Apoio e estado inicial fechado

Decisao: transformar `APOIO` em um item expansivel unico no menu lateral da
aplicacao real, mantendo `Empresa`, `Centro de Custo`, `Contas`, `Credor` e
`Plano Financeiro` dentro do submenu, remover a abertura automatica inicial
dos submenus por endpoint ativo e iniciar o menu lateral compacto por padrao
quando nao houver preferencia salva pelo usuario.

Motivo: a demanda solicita ajustar o menu `APOIO` e o estado inicial fechado.
O comportamento anterior deixava `APOIO` como lista direta no menu aberto,
podia renderizar submenus ja abertos ao acessar rotas internas e nao aplicava
o modo compacto no primeiro carregamento sem parametro de URL ou estado salvo
no navegador.

Impacto: a entrega altera somente `templates/base.html` e documentacao da
tarefa. Nao altera regras de negocio, banco de dados, migrations, variaveis de
ambiente, VPS, `main` ou producao.

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

## 2026-08-04 - PLA-1290 - Backfill empresa 1 centro 1001 nos lancamentos

- Projeto: PSFINANCE.
- Decisao: preparar script PostgreSQL para preencher lancamentos historicos
  ativos de `titulo` e `movimentacao_conta` ainda sem empresa ou centro de
  custo com a empresa ativa de codigo `1` e o centro de custo ativo de codigo
  `1001` pertencente a essa empresa.
- Seguranca: o script aborta quando os cadastros esperados nao existem ou
  quando existe ambiguidade de empresa/centro ativo.
- Limite: script preparado para staging; nenhuma escrita em producao, merge em
  `main`, copia de dados entre ambientes ou deploy produtivo esta autorizado.

## 2026-08-05 - PLA-1359 - Layout da consulta de titulos a pagar

- Projeto: PSFINANCE.
- Decisao: melhorar a tela de consulta de titulos a pagar no template
  `templates/titulos_list.html`, mantendo a consulta, filtros por vencimento,
  totais e acoes existentes sem alterar backend, banco de dados ou rotas.
- Motivo: a consulta possuia tabela larga com muitas acoes textuais por linha,
  dificultando leitura operacional. A tela passa a ter resumo financeiro,
  filtros destacados, status visual e acoes agrupadas por titulo.
- Limite: alteracao restrita a apresentacao. Nao autoriza mudanca em `main`,
  deploy produtivo, migration ou escrita em banco de producao.
- Complemento: as acoes por titulo foram ajustadas para botoes compactos com
  icones e atributos `title`/`aria-label`, atendendo ao pedido de reduzir
  botoes textuais grandes na consulta.

## 2026-08-05 - PLA-1370 - Coluna Titulo na consulta de titulos a pagar

- Projeto: PSFINANCE.
- Decisao: a consulta de titulos a pagar deve exibir uma coluna explicita
  `Titulo`, reunindo o identificador interno sem prefixo `#` e a referencia
  do documento em uma unica coluna operacional.
- Motivo: evitar a separacao entre `ID` e `Documento` na listagem, deixando a
  identificacao do titulo mais direta para consulta e acoes por linha.

## 2026-08-05 - PLA-1376 - Vincular contas a empresa

- Projeto: PSFINANCE.
- Decisao: contas de caixa/banco passam a exigir vinculo com uma empresa ativa
  no cadastro e na edicao.
- Aplicacao: a regra de empresa ativa foi centralizada em
  `financeiro/regras_empresa_centro.py` e aplicada no fluxo de contas.
- Complemento de integridade: movimentacoes manuais e baixas de titulos passam
  a validar que a conta escolhida pertence a empresa da operacao. Em
  movimentacoes, a referencia e a empresa selecionada no formulario; em baixas,
  a referencia e a empresa vinculada ao titulo.
- Banco: `conta.id_empresa` passa a ser obrigatorio pela migration PostgreSQL
  versionada, com backfill seguro para contas historicas usando a empresa ativa
  de codigo `1` quando existir exatamente uma.
- Integridade: empresa com conta ativa vinculada nao pode ser desativada, e
  conta inativa sem empresa ativa vinculada nao pode ser reativada.
- Evidencia de staging em 2026-08-05: 9 contas totais, 9 contas com empresa,
  0 contas sem empresa e 9 contas vinculadas a empresa `1`.
- Producao: nenhuma migration, escrita em banco produtivo, merge em `main`,
  copia de dados entre ambientes ou deploy produtivo esta autorizado.
- Evidencia visual da PLA-1376 deve ser gerada no gate de staging apos deploy
  da branch `staging`.

## 2026-08-06 - PLA-1618 - Padronizacao do layout das consultas

- Projeto: PSFINANCE.
- Decisao: padronizar as consultas de contas, contas inativas, movimentacoes,
  empresas, centros de custo, credores e plano financeiro conforme o layout da
  consulta de titulos.
- Aplicacao: estilos comuns foram centralizados em `templates/base.html` com
  cabecalho, kicker, subtitulo, shell de tabela, estado vazio e botoes de acao
  por icone. As listagens passam a usar esses estilos sem alterar rotas,
  controllers, models, banco de dados ou regras de negocio.
- Motivo: reduzir divergencia visual entre consultas e manter o padrao
  operacional criado para titulos a pagar.
- Limite: alteracao restrita a apresentacao. Nao autoriza migration, escrita
  em banco de producao, alteracao em `main` ou deploy produtivo.
- Complemento de evidencia: a consulta real de referencia e
  `/financeiro/titulos`, documentada com screenshots desktop e mobile no pacote
  da PLA-1618. A comparacao objetiva entre a referencia e as rotinas ajustadas
  fica registrada em `docs/PLA-1618-padronizar-layout-consultas.md`.

## 2026-08-07 - PLA-1655 - Cadastro Geral dentro de Apoio

- Projeto: PSFINANCE.
- Decisao: manter `APOIO` como unico menu principal dessa area e posicionar
  `CADASTRO GERAL` como submenu expansivo dentro de `APOIO`, contendo
  exatamente `Credor`, `Plano Financeiro`, `Empresa`, `Centro de Custo` e
  `Conta`.
- Motivo: atender ao esclarecimento de Thiago na revisao da PLA-1655 e eliminar
  a divisao incorreta em dois grupos principais, preservando endpoints, rotas,
  banco de dados e regras de negocio.
- Limite: alteracao restrita a apresentacao. Nao autoriza migration, escrita
  em banco de producao, alteracao em `main` ou deploy produtivo.

## 2026-08-08 - PLA-1655 - Remocao de duplicidade visual de Apoio

- Projeto: PSFINANCE.
- Decisao: remover o segundo `APOIO` visivel que ainda aparecia como item e
  titulo de submenu, mantendo `APOIO` apenas como grupo principal e
  `Cadastro Geral` como submenu expansivo direto desse grupo.
- Motivo: Thiago rejeitou novamente a entrega por duplicidade de `APOIO`; a
  correcao precisa comprovar objetivamente a hierarquia `APOIO > Cadastro
  Geral > Credor, Plano Financeiro, Empresa, Centro de Custo, Conta`.
- Limite: alteracao restrita a apresentacao. Nao altera rotas, banco de dados,
  migrations, permissoes, `main` ou producao.

## 2026-08-08 - PLA-1655 - Comportamento compacto de Apoio

- Projeto: PSFINANCE.
- Decisao: separar a renderizacao do menu `APOIO` entre estado aberto e estado
  compacto, mantendo a hierarquia aberta aprovada e criando no compacto um
  acionador proprio de `APOIO` que abre o flyout com `Cadastro Geral` e seus
  itens.
- Motivo: Thiago aprovou o menu aberto, mas rejeitou o comportamento encolhido
  por estar diferente dos demais menus; o clique no icone de `APOIO` deve abrir
  o flyout compacto, sem expor diretamente `Cadastro Geral` como item principal
  do estado encolhido.
- Limite: alteracao restrita a apresentacao do menu compacto. Nao altera nomes,
  hierarquia aberta, rotas, banco de dados, migrations, permissoes, `main` ou
  producao.

## 2026-08-08 - PLA-1655 - Icone compacto de Cadastro Geral

- Projeto: PSFINANCE.
- Decisao: manter `APOIO` apenas como grupo do menu aberto e, no menu compacto,
  usar o acionador visual de `Cadastro Geral`, com o mesmo icone do submenu
  aberto e flyout contendo `Credor`, `Plano Financeiro`, `Empresa`,
  `Centro de Custo` e `Conta`.
- Motivo: Thiago rejeitou a revisao porque o estado compacto ainda mostrava o
  icone de `APOIO` como menu, enquanto os demais grupos compactos acionam o
  submenu navegavel. A correcao alinha `Cadastro Geral` ao mesmo padrao.
- Limite: alteracao restrita a apresentacao do menu compacto. Nao altera a
  hierarquia aberta aprovada, nomes exibidos no menu aberto, rotas, banco de
  dados, migrations, permissoes, `main` ou producao.

## 2026-08-09 - PLA-1655 - Comparacao visual obrigatoria entre menus equivalentes

- Projeto: PSFINANCE.
- Decisao: quando Thiago solicitar comportamento "igual ao outro menu", a
  validacao visual deve comparar o estado equivalente lado a lado antes de
  devolver ao CEO. Nao basta validar apenas DOM ou intencao tecnica.
- Motivo: a rejeicao da PLA-1655 mostrou que o compacto/flyout de `Cadastro
  Geral` ainda exibia um titulo textual adicional que nao aparece no padrao
  real de `FINANCEIRO > Contas a Pagar`.
- Aplicacao: no compacto/flyout, `Cadastro Geral` deve seguir o mesmo padrao de
  `Contas a Pagar`: acionador visual por icone no menu compacto e flyout com os
  itens do submenu, sem titulo/label textual adicional quando o menu comparado
  tambem nao possui esse titulo.
- Limite: regra de qualidade visual e ajuste de template. Nao altera rotas,
  banco de dados, migrations, permissoes, `main` ou producao.

## 2026-08-09 - PLA-1655 - Evidencia executiva do menu Cadastro Geral

- Projeto: PSFINANCE.
- Decisao: remover tambem os titulos internos redundantes do submenu aberto de
  `Cadastro Geral`, inclusive o segundo `APOIO` que permanecia como
  `.submenu-title`, e registrar screenshots especificos para revisao executiva.
- Motivo: a devolucao do CEO apontou que as evidencias anteriores nao
  comprovavam de forma objetiva o flyout comparativo nem a hierarquia aberta
  `APOIO > Cadastro Geral > itens`.
- Evidencia: novos screenshots em `docs/evidencias/PLA-1655/` com menu aberto,
  flyout compacto de `Cadastro Geral`, referencia compacta de `Contas a Pagar`
  e viewport mobile.
- Limite: alteracao restrita a apresentacao e documentacao. Nao altera rotas,
  banco de dados, migrations, permissoes, `main` ou producao.

## 2026-08-10 - PLA-1816 - Multi parcela em titulo

- Projeto: PSFINANCE.
- Decisao: manter o titulo como registro principal com valor total e criar a
  tabela relacional `titulo_parcela` para controlar numero, vencimento e valor
  de cada parcela.
- Regra: a quantidade de parcelas deve ficar entre 1 e 120; a criacao inicial
  gera parcelas mensais a partir da Data do 1º Vencimento, preservando o dia
  original quando existir e usando o ultimo dia valido quando o mes nao possuir
  aquele dia.
- Ajuste manual: a guia de parcelas permite editar vencimentos e valores,
  excluir parcela e incluir nova parcela. Ao salvar, o valor total do titulo e
  atualizado pela soma das parcelas ativas e o vencimento do titulo acompanha a
  primeira parcela.
- Limite: migration preparada no repositorio para staging. Nao autoriza escrita
  no banco de producao, merge em `main` ou deploy produtivo.

## 2026-08-11 - PLA-2073 - Visibilidade da guia de parcelas no titulo

- Decisao: a edicao de titulo existente deve exibir acao explicita
  `Parcelas do titulo` no cabecalho, apontando para a guia de parcelas do
  proprio titulo, e manter os rotulos `Valor total` e
  `Data do 1º Vencimento` tambem na edicao.
- Regra: o campo `Parcelas` permanece desabilitado na edicao do titulo para
  preservar a quantidade atual; ajustes de vencimento, valor, inclusao e
  exclusao continuam centralizados na guia especifica de parcelas.
- Impacto: alteracao apenas visual/de navegacao em template, sem banco,
  migration, variavel de ambiente, VPS ou producao.

## 2026-08-12 - PLA-2106 - Staging real da aba de parcelas

- Projeto: PSFINANCE.
- Decisao: corrigir o staging real publicado na VPS de teste atualizando o
  repositorio operacional de `staging` do commit
  `e17896e7838cdea30f6deea9f8aecd003cc3b0f0` para o commit
  `b7d10c1a18574aff8186573829aba2786c1df80c`, ja existente em
  `origin/staging`; a entrega revisada com evidencias complementares ficou
  consolidada e publicada no commit
  `9745b5e7cb4991c4429078b7046aa23a1cf09c63`.
- Motivo: a porta publica `5001` respondia com tela funcional, mas a tela real
  de edicao de titulo ainda nao continha `Parcelas do titulo`, `Valor total` e
  `Data do 1º Vencimento`, porque a VPS estava defasada em relacao ao GitHub.
- Banco: aplicada no PostgreSQL de staging a migration versionada
  `migrations/versions/20260810_pla1816_titulo_parcela.sql`, pois a tabela
  `titulo_parcela` ainda nao existia no banco de staging real.
- Infraestrutura: atualizados somente metadados nao sensiveis de `GIT_BRANCH`
  e `GIT_COMMIT` do ambiente de staging, com backup do arquivo operacional de
  ambiente antes da alteracao.
- Evidencia complementar: revisao executiva solicitou screenshots, comparacao
  com o print de Thiago e validacao funcional de edicao/inclusao/recalculo das
  parcelas; esses itens foram registrados em
  `docs/PLA-2106-staging-real-aba-parcelas.md` e
  `docs/evidencias/PLA-2106/`.
- Limite: acao restrita a VPS e banco de staging. Nao altera `main`, producao,
  banco de producao, secrets, credenciais ou dados operacionais produtivos.

## 2026-08-12 - PLA-2111 - UX do cadastro de novo titulo

- Projeto: PSFINANCE.
- Decisao: o cadastro de novo titulo deve usar linguagem de negocio para o
  usuario final, tratando o plano financeiro como `Categoria financeira` e
  evitando expor a regra tecnica `Grupo 2` no rotulo principal.
- Regra de UX: o campo de valor passa a interpretar entrada simples em reais;
  por exemplo, `200` deve virar `200,00`, sem mascara obrigatoria em centavos.
- Regra de fluxo: Centro de Custo fica indisponivel ate a escolha da Empresa,
  exibindo somente centros compativeis com a empresa selecionada.
- Fluxo pos-salvamento: criacao ou copia com uma parcela retorna para a lista
  de titulos; somente criacao/copia com duas ou mais parcelas abre a revisao
  de parcelas apos salvar.
- Complemento: o formulario exibe orientacao para cadastros auxiliares ausentes
  e deixa anexos como secao secundaria, reduzindo ruido no primeiro cadastro.
- Limite: alteracao restrita a rota e template de titulos. Nao altera banco,
  migration, `main`, producao ou dados produtivos.
