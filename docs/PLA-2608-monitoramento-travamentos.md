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

## Monitoramento sintetico

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

As rotas funcionais sem sessao autenticada medem a resposta da jornada publica
e podem retornar a tela de autenticacao; ainda assim comprovam Nginx, Gunicorn,
Flask e PostgreSQL responsivos durante a coleta.

## Causa tecnica

### Fatos confirmados

1. Nao houve queda do servidor, restart automatico de worker, OOM, timeout de
   proxy, HTTP 5xx, lock de banco ou requisicao lenta registrada no horario
   informado.
2. Nao chegou requisicao ao Extrato pelo Nginx na janela da ocorrencia. Logo, o
   travamento percebido nao foi produzido por uma requisicao que ficou presa no
   backend naquele momento.
3. A versao publicada na VPS era `staging` no commit
   `f0e7bef57f5207e7ef0464611ced3e6e88df2516`, anterior a correcao da PLA-2597.
4. O PR #90, commit `ca976a912430e1db4286fe39351cc46e7d8a5c23`, remove a
   dependencia de Bootstrap no `cdn.jsdelivr.net`, agrega o saldo anterior no
   PostgreSQL e elimina consultas N+1 dos documentos do Extrato.

### Conclusao

A evidencia do horario relatado descarta queda do backend e aponta o navegador
como origem imediata do estado de carregamento: os assets Bootstrap externos
podiam ficar lentos ou bloqueados antes de uma nova requisicao chegar ao
PSFINANCE. O Extrato publicado ainda tinha, adicionalmente, risco de lentidao
por carregar o historico anterior em memoria e consultar documentos em N+1.
As duas causas ja estao tratadas no PR #90, ainda nao publicado conforme o
limite desta tarefa.

Os acessos SSH automatizados e malsucedidos observados na mesma faixa nao
geraram carga relevante, evento de servico ou indisponibilidade correlacionada;
nao ha evidencia de que tenham causado o relato.

## Risco residual e proxima decisao

- Sem `request_time` e `upstream_response_time` no formato atual do access log,
  nao e possivel recuperar duracao historica precisa de requests.
- Sem `pg_stat_statements`, nao ha historico retroativo de consultas lentas.
- A correcao do PR #90 exige merge/deploy/restart, proibidos no escopo da
  PLA-2608. A decisao executiva e autorizar ou nao o fluxo ja preparado na
  PLA-2597, com rollback para o commit de staging anterior.

## Arquivos e ambientes

- Ambiente analisado: staging, porta corporativa `5001`.
- Branch publicada: `staging`.
- Commit publicado: `f0e7bef57f5207e7ef0464611ced3e6e88df2516`.
- Correcao pronta: PR #90, commit
  `ca976a912430e1db4286fe39351cc46e7d8a5c23`.
- Banco: nenhuma escrita e nenhuma alteracao estrutural.

