# PLA-2608 - Monitoramento dos travamentos do PSFINANCE

## Escopo e governanca

Diagnostico somente leitura realizado em 2026-08-16 na VPS de staging do
PSFINANCE. Foram consultadas as skills `plansmart-governanca-desenvolvimento`,
`plansmart-projeto-psfinance` e `plansmart-projeto-vps-sistemas`.

Nao houve deploy, merge, restart, migration, escrita em PostgreSQL ou uso de
SQLite.

## Janela correlacionada

- Ocorrencia informada por Thiago: 2026-08-16 14:20 UTC (11:20 UTC-3).
- Janela inspecionada: 11:15 a 11:30 UTC-3.
- `journalctl` de `psfinance-staging`, `psfinance-staging-gate`, Nginx e
  PostgreSQL: nenhum evento na janela.
- Access log do Nginx: nenhuma requisicao ao Extrato na janela. Houve somente
  um `GET /staging/psfinance/` as 11:29:20 UTC-3, respondido com HTTP 200.
- Error log do Nginx: sem erro na janela.
- Nao houve HTTP 499, 500, 502, 503 ou 504 associado ao relato.

## Estado observado do servidor

- Uptime: 27 dias e 17 horas.
- Carga: `0.12`, `0.04`, `0.01`.
- Memoria: 957 MiB totais, aproximadamente 402 MiB disponiveis; swap com
  aproximadamente 627 MiB livres.
- Disco raiz: 16% utilizado.
- Kernel desde 2026-08-01: sem OOM (Out of Memory, falta critica de memoria),
  processo morto, erro de I/O ou tarefa bloqueada.
- `psfinance-staging` e `psfinance-staging-gate`: ativos, `NRestarts=0`.
- Gunicorn: dois workers da aplicacao em `127.0.0.1:5104` e um worker do gate
  em `127.0.0.1:5105`.
- Nginx: porta corporativa `5001` ativa.
- PostgreSQL: quatro conexoes no instante da coleta, uma referente a propria
  consulta de diagnostico; zero locks nao concedidos; conexoes da aplicacao
  estavam ociosas e aguardando o cliente, nao bloqueadas no banco.
- `pg_stat_statements` nao esta instalado, portanto nao existe historico
  agregado de duracao de consultas para recuperar retroativamente.

## Monitoramento sintetico inicial

Foram executadas cinco passagens consecutivas, somente leitura, pela porta
`5001`. Todos os 30 requests retornaram HTTP 200:

| Rota | Menor tempo | Maior tempo |
| --- | ---: | ---: |
| `/health` | 1,47 ms | 2,02 ms |
| `/gate` | 2,98 ms | 3,41 ms |
| Home | 28,90 ms | 38,83 ms |
| Extrato | 4,73 ms | 7,47 ms |
| Titulos | 13,95 ms | 59,15 ms |
| Analise | 11,81 ms | 35,67 ms |

Essa coleta inicial nao comprovou o processamento completo do Extrato com uma
conta selecionada e, portanto, nao pode ser usada isoladamente para atribuir ou
descartar a causa do travamento percebido.

## Correcao exigida na revisao executiva

Em 2026-08-16, a rota real do Extrato foi verificada pela porta `5001` com uma
conta existente selecionada, sem gravacao de dados. A resposta apresentou o
titulo `Extrato de Conta`, os marcadores da tela, linhas da tabela e nenhum
marcador de login. O retorno foi HTTP 200, com 39.526 bytes e 12,44 ms no
servidor. Isso comprova que a coleta exercitou a renderizacao filtrada do
Extrato naquele instante; nao comprova a causa da ocorrencia anterior.

Foi iniciado o monitor `scripts/monitor_pla2608_readonly.sh`, em intervalo de
120 segundos. Cada amostra registra estado e reinicios dos servicos, PID,
memoria, CPU, disco, listeners, estado agregado de conexoes e locks do
PostgreSQL, tempo do Extrato filtrado, journal e linhas sanitizadas dos logs do
Nginx. O monitor nao grava no servidor nem no banco; a evidencia local e
acumulada em `docs/evidencias/PLA-2608-monitor-live.log`.

## Causa tecnica

### Fatos confirmados

1. Nao houve queda do servidor, restart automatico de worker, OOM, timeout de
   proxy, HTTP 5xx, lock de banco ou requisicao lenta registrada no horario
   informado.
2. Nao chegou requisicao ao Extrato pelo Nginx na janela informada. Esse fato
   impede correlacionar o relato com uma requisicao de backend, mas nao permite
   concluir onde ocorreu o travamento.
3. A versao publicada na VPS era `staging` no commit
   `f0e7bef57f5207e7ef0464611ced3e6e88df2516`, anterior a correcao da PLA-2597.
4. O PR #90, commit `ca976a912430e1db4286fe39351cc46e7d8a5c23`, remove a
   dependencia de Bootstrap no `cdn.jsdelivr.net`, agrega o saldo anterior no
   PostgreSQL e elimina consultas N+1 dos documentos do Extrato.

### Conclusao corrigida

A causa da ocorrencia das 14:20 UTC permanece **indeterminada**. A janela
historica nao apresenta evidencia de queda ou erro do backend, mas tambem nao
capturou uma requisicao do Extrato que permita reproduzir e atribuir a causa.
A dependencia externa de Bootstrap e as consultas custosas do Extrato sao
riscos tecnicos conhecidos, tratados no PR #90, mas nao foram comprovados como
causa do relato. A atribuicao anterior ao navegador/CDN foi retirada.

Os acessos SSH automatizados e malsucedidos observados na mesma faixa nao
geraram carga relevante, evento de servico ou indisponibilidade correlacionada;
nao ha evidencia de que tenham causado o relato.

## Risco residual e proxima decisao

- Sem `request_time` e `upstream_response_time` no formato atual do access log,
  nao e possivel recuperar duracao historica precisa de requests.
- Sem `pg_stat_statements`, nao ha historico retroativo de consultas lentas.
- A correcao do PR #90 exige merge/deploy/restart, proibidos no escopo da
  PLA-2608. O PR permanece apenas como contexto ate decisao separada.
- O monitor precisa capturar uma nova ocorrencia informada com horario e rota
  para que os dados de aplicacao, proxy, sistema operacional e banco sejam
  correlacionados na mesma janela.

## Arquivos e ambientes

- Ambiente analisado: staging, porta corporativa `5001`.
- Branch publicada: `staging`.
- Commit publicado: `f0e7bef57f5207e7ef0464611ced3e6e88df2516`.
- Correcao pronta: PR #90, commit
  `ca976a912430e1db4286fe39351cc46e7d8a5c23`.
- Banco: nenhuma escrita e nenhuma alteracao estrutural.
