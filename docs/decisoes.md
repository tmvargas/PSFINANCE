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
