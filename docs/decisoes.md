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
