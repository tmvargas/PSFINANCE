# PLA-981 - Bloqueio para subir PSFINANCE funcional em staging

Data da execucao: 2026-08-01

## Objetivo

Subir o PSFINANCE funcional em staging na VPS (Servidor Virtual Privado)
Sistemas usando o codigo fonte completo e o banco de dados fornecidos por
Thiago, preservando dados e sem tocar producao.

## Escopo e governanca

- Projeto: `PSFINANCE`.
- Issue: `PLA-981`.
- Skills consultadas:
  - `plansmart-governanca-desenvolvimento`;
  - `plansmart-projeto-psfinance`;
  - `plansmart-projeto-vps-sistemas`.
- Ambiente analisado: workspace local, GitHub, historico Paperclip da
  `PLA-981` e da tarefa mae `PLA-743`, e VPS Sistemas.
- Acoes executadas: leitura, busca de artefatos, validacao HTTP, SSH
  (Secure Shell, acesso remoto seguro) de leitura, Git e verificacao de
  servicos/portas.
- Producao: nao houve merge na `main`, deploy produtivo, migration produtiva,
  escrita em banco produtivo ou exposicao de segredos.

## Fatos confirmados

### Repositorio oficial

- Repositorio local: `https://github.com/tmvargas/PSFINANCE.git`.
- Branch de trabalho criada a partir de `staging`:
  `docs/PLA-981-bloqueio-artefatos-funcionais`.
- `origin/staging`: `fb2b9dea247ba34ea91150cb10c20680c9c49a05`.
- `origin/main`: `23821c7786e98c5c489c60c2ac60760e3cdc17c1`.
- O repositorio oficial contem somente a aplicacao Flask minima de
  homologacao, `/health`, `/gate` e documentacao.
- Nao existem controllers, services, repositories, models, migrations,
  templates funcionais, autenticacao, integracao Sienge ou camada de
  persistencia no codigo versionado atual.

### Historico Paperclip

- A `PLA-981` nao possui comentarios, documentos ou work products proprios.
- A `PLA-743` contem o comentario de Thiago em 2026-08-01 informando que o
  codigo fonte e o banco de dados ja foram passados.
- No historico consultado da `PLA-743`, nao foi localizado caminho, link,
  anexo, nome de arquivo, repositorio alternativo ou instrucao operacional que
  identifique onde estao o codigo fonte completo e o banco fornecido.

### Workspace local

- Foram procurados arquivos de projeto e banco em formatos comuns, incluindo
  `.sql`, `.dump`, `.backup`, `.bak`, `.zip`, `.rar`, `.7z`, `.db`,
  `.sqlite`, `requirements.txt`, `package.json`, `composer.json`, `manage.py`
  e `app.py`.
- No workspace do PSFINANCE nao foi encontrado dump, banco local, pacote de
  codigo funcional ou aplicacao diferente da base Flask minima.
- Foram encontrados artefatos de outros projetos PlanSmart, mas eles nao devem
  ser usados por semelhanca, conforme a skill do PSFINANCE.

### GitHub

- As branches do `tmvargas/PSFINANCE` e do legado `tmvargas/PSCONTROL`
  apontam para o mesmo historico minimo conhecido.
- Nao foi localizado outro repositorio visivel ao agente com nome de
  PSFINANCE funcional ou pacote equivalente.

### VPS Sistemas

- Staging publico validado:
  `http://vps69143.publiccloud.com.br/staging/psfinance` retornou HTTP 200.
- Gate publico validado:
  `http://vps69143.publiccloud.com.br:5001/gate` retornou HTTP 200.
- O gate informa:
  - `app=PSFINANCE`;
  - `environment=staging-gate`;
  - `branch=staging`;
  - `commit=fb2b9dea247ba34ea91150cb10c20680c9c49a05`;
  - healthcheck interno `http://127.0.0.1:5104/health` com HTTP 200.
- Servicos ativos relacionados:
  - `psfinance-staging.service`;
  - `psfinance-staging-gate.service`;
  - `nginx.service`.
- Portas observadas:
  - `127.0.0.1:5104` com Gunicorn;
  - `127.0.0.1:5105` com Gunicorn;
  - `0.0.0.0:80` com Nginx;
  - `0.0.0.0:5001` com Nginx.
- Nao ha listener local identificado em `5432`, `3306` ou `27017`.
- O diretorio `/opt/plansmart/sistemas/psfinance/staging/repo` contem a mesma
  aplicacao minima versionada.
- O diretorio legado `/home/www/PSCONTROL` existe, mas e um checkout minimo do
  `https://github.com/tmvargas/PSCONTROL.git`, em `main`, sem codigo funcional
  completo e sem banco encontrado.

## Bloqueio real

Nao foi localizado o codigo fonte funcional completo nem a base de dados
fornecida por Thiago em nenhum dos locais verificados.

Sem esses artefatos, nao ha como substituir a pagina tecnica atual por uma
aplicacao financeira funcional preservando dados. Qualquer tentativa de
implementar funcionalidade nova do zero neste momento contrariaria o objetivo
da `PLA-981`, que e configurar e subir o sistema ja fornecido.

## Impacto

- O staging atual permanece tecnico, nao funcional.
- Nao e possivel importar, migrar ou preservar dados porque a base fornecida
  nao foi localizada.
- Nao e possivel abrir PR (Pull Request, solicitacao de revisao) funcional
  contra `staging` sem o codigo fonte correto.
- Nao ha base tecnica para deploy funcional na VPS sem risco de inventar regra
  de negocio ou misturar codigo de outro projeto.

## Tentativas executadas

- Consulta das skills obrigatorias do PSFINANCE e da VPS Sistemas.
- Validacao de branch, remoto, `origin/staging`, `origin/main` e status local.
- Leitura dos documentos `PLA-836`, `PLA-858`, `PLA-747` e correlatos.
- Consulta da `PLA-981` via API (Interface de Programacao de Aplicacoes) do
  Paperclip.
- Consulta da `PLA-743` e comentarios relevantes via Paperclip.
- Busca local por pacotes, dumps, bancos e arquivos de projeto.
- Busca na VPS em `/opt/plansmart/sistemas`, `/home`, `/home/www/PSCONTROL` e
  diretorios relacionados.
- Validacao HTTP da URL publica de staging e do gate corporativo `5001`.
- Verificacao de servicos e portas na VPS.
- Consulta de branches e repositorios GitHub visiveis ao agente.

## Acao necessaria para desbloqueio

Thiago ou CEO deve informar pelo menos uma destas origens, sem publicar
segredos:

1. caminho exato na VPS ou no workspace onde esta o codigo fonte completo;
2. repositorio Git correto e branch/tag do codigo funcional;
3. anexo/work product do Paperclip contendo o pacote do codigo;
4. caminho seguro da base fornecida e seu formato;
5. instrucao de acesso ao local onde a base esta armazenada.

Para a base de dados, basta registrar origem, formato e procedimento de acesso.
O conteudo do dump, credenciais e dados sensiveis nao devem ser colados na
tarefa.

## Trabalho que ainda pode continuar

- Manter o staging tecnico atual respondendo em `/staging/psfinance` e no gate
  `5001`.
- Preparar analise de importacao/migracao assim que a origem da base for
  localizada.
- Criar branch funcional a partir de `staging` assim que o codigo fonte
  completo for disponibilizado.

## Recomendacao do GDSIS

Marcar a `PLA-981` como `blocked` ate que a origem concreta do codigo fonte
funcional e da base fornecida seja informada. A responsabilidade de desbloqueio
e de Thiago/CEO, indicando o local dos artefatos ou disponibilizando-os por um
canal seguro.
