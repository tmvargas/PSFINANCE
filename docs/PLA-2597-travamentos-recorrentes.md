# PLA-2597 — Travamentos recorrentes no Extrato

## Escopo e causa

A ocorrência foi reproduzida na rota:

`/staging/psfinance/financeiro/extrato?id_empresa=1&id_conta=14&data_ini=2026-08-01&data_fim=2026-08-16`

Foram identificadas duas causas de risco:

- o layout dependia do Bootstrap carregado pelo `cdn.jsdelivr.net`, permitindo
  que uma conexão externa lenta ou bloqueada mantivesse o navegador em estado
  de carregamento após a entrega do HTML;
- a rota carregava todo o histórico anterior em memória e podia fazer consultas
  adicionais por documento (N+1).

A correção serve CSS e JavaScript do Bootstrap pelo próprio PSFINANCE, agrega o
saldo anterior no PostgreSQL e carrega os documentos do período junto com as
consultas principais. Não houve alteração de banco, migration ou regra de
conciliação.

## Rastreabilidade

- Branch funcional: `fix/PLA-2597-travamentos-recorrentes`.
- Commit funcional: `ca976a93876fdf22125b71f7bd434a4b1344eb3c`.
- Head do PR: `d20f809463a038cf5b8ba0cb8e5db02b271083c0`.
- PR: `https://github.com/tmvargas/PSFINANCE/pull/90`, base `staging`.
- Commit integrado e publicado em `staging`:
  `1c8fb6aacb2ec44a1796f6d3415e883d94ca53f6`.
- VPS de teste: repositório limpo, branch `staging`, `HEAD` igual a
  `origin/staging` no commit acima.

## Gate da porta 5001

Validação executada em 2026-08-19 após o deploy:

- `psfinance-staging.service`: `active/running`, dois workers Gunicorn e zero
  reinícios;
- `psfinance-staging-gate.service`: `active/running`, um worker Gunicorn e zero
  reinícios;
- `/health`: HTTP 200, PostgreSQL, branch `staging`, commit `1c8fb6a`;
- `/gate`: HTTP 200 e aplicação interna em `127.0.0.1:5104` saudável;
- CSS Bootstrap local: HTTP 200, 232.803 bytes, 6,09 ms;
- JavaScript Bootstrap local: HTTP 200, 80.721 bytes, 2,32 ms.

Durante o restart controlado houve dois HTTP 502 às 16:33:29 BRT, restritos ao
intervalo de substituição dos processos. Na primeira verificação posterior os
dois healthchecks retornaram HTTP 200. Não houve novo erro no intervalo dos
testes de carga.

## Tempos da URL exata

Cinco medições externas pela porta pública `5001`:

| Medição | DNS | Conexão | Primeiro byte | Total | HTTP |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2,07 ms | 12,03 ms | 29,44 ms | 36,09 ms | 200 |
| 2 | 1,37 ms | 5,28 ms | 23,27 ms | 31,05 ms | 200 |
| 3 | 1,45 ms | 5,64 ms | 22,12 ms | 30,22 ms | 200 |
| 4 | 1,53 ms | 12,38 ms | 31,81 ms | 39,78 ms | 200 |
| 5 | 1,87 ms | 5,92 ms | 24,36 ms | 32,30 ms | 200 |

## Teste sequencial e concorrente

Cada resposta da rota teve 46.475 bytes.

| Cenário | Requisições | p50 | p95 | Máximo | Erros | Timeouts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sequencial | 30 | 13,16 ms | 16,75 ms | 162,82 ms | 0 | 0 |
| Concorrente, 6 workers | 30 | 74,85 ms | 83,70 ms | 85,70 ms | 0 | 0 |

As 60 requisições retornaram HTTP 200. O máximo sequencial ocorreu na primeira
requisição após o restart; as 29 seguintes ficaram entre 10,69 ms e 16,82 ms.

## Rede da página

A coleta da página publicada enumerou todos os elementos `link[href]` e
`script[src]`, solicitou cada recurso com timeout de 10 segundos e registrou:

| Recurso | Origem | HTTP | Tempo | Pendente/erro |
| --- | --- | ---: | ---: | --- |
| `bootstrap.min.css` | PSFINANCE local | 200 | 6,09 ms | não |
| `bootstrap.bundle.min.js` | PSFINANCE local | 200 | 2,32 ms | não |

Não restou host externo, recurso pendente ou erro. O ambiente de execução não
possuía Chromium, Chrome, Firefox ou Playwright instalado na primeira coleta;
essa limitação foi eliminada na complementação solicitada pela revisão do CEO.

## Complementação da revisão executiva — navegador real

Em 2026-08-19, a URL exata foi aberta em Chromium real automatizado, pela porta
pública `5001`, aguardando `networkidle`:

- HTTP 200 e conclusão da navegação em 826 ms;
- `DOMContentLoaded` em 398,40 ms e evento `load` em 420,00 ms;
- CSS local concluído em 45,10 ms;
- JavaScript local concluído em 37,20 ms;
- zero falhas e zero requisições pendentes após `networkidle`;
- screenshot: `docs/evidencias/PLA-2597/extrato-navegador-real-staging.png`;
- waterfall HAR: `docs/evidencias/PLA-2597/extrato-waterfall.har`;
- métricas estruturadas: `docs/evidencias/PLA-2597/navegador-real.json`.

A inspeção visual confirma a tela Extrato de Conta / Conciliação renderizada,
com filtros, totais e oito movimentações do período, sem indicador de
carregamento persistente.

## Medição SQL e eliminação do N+1

A rota foi executada no Flask com eventos `before_cursor_execute` e
`after_cursor_execute` do SQLAlchemy. A conexão foi forçada por `PGOPTIONS` a
`default_transaction_read_only=on`; a própria captura confirmou o modo somente
leitura antes do teste.

| Métrica | Resultado |
| --- | ---: |
| HTTP | 200 |
| Tempo total da rota instrumentada | 159,888 ms |
| Consultas SQL | 8 `SELECT` |
| Tempo SQL total | 10,516 ms |
| Maior consulta | 2,125 ms |
| Escritas | 0 |

As oito consultas têm quantidade fixa por carregamento (empresas, contas,
saldo anterior, movimentações, baixas, documentos e parcelas). Os documentos
de movimentações e títulos são obtidos por duas consultas em lote com `JOIN`,
e não por consulta individual por linha. Para os oito registros exibidos no
screenshot, a contagem permaneceu em oito consultas totais: não foi detectado
N+1. Evidência: `docs/evidencias/PLA-2597/sql-readonly.json`.

## CPU, workers e pool PostgreSQL durante carga

Nova carga controlada de 30 requisições, concorrência 6, foi executada entre
19:44:52Z e 19:44:56Z, com 30 amostras de CPU e memória dos processos Gunicorn:

| Métrica | Resultado |
| --- | ---: |
| Respostas HTTP 200 | 30/30 |
| Erros/timeouts | 0/0 |
| Média | 70,241 ms |
| Máximo | 85,251 ms |
| CPU Gunicorn média | 0,50% |
| CPU Gunicorn máxima | 0,50% |
| RSS máximo dos processos | 241.648 KiB |
| `max_connections` PostgreSQL | 100 |
| Conexões do banco após carga | 4 |
| Ativas após carga | 1 (a própria coleta) |
| Ociosas após carga | 3 |
| Aguardando lock | 0 |

Os dois workers do serviço permaneceram ativos. Evidência estruturada:
`docs/evidencias/PLA-2597/runtime-readonly.json`.

No mesmo intervalo, o access log do Nginx registrou 30 requisições da URL e
30 respostas HTTP 200. Os journals do `psfinance-staging`/Gunicorn e do
PostgreSQL não registraram erro, exceção, timeout, saída de worker, `FATAL` ou
deadlock. Evidência correlacionada:
`docs/evidencias/PLA-2597/logs-correlacionados.txt`.

## Smoke tests das demais jornadas

O mesmo Chromium real, aguardando `networkidle` em cada navegação, confirmou:

| Jornada | HTTP | Tempo |
| --- | ---: | ---: |
| Healthcheck | 200 | 672 ms |
| Home | 200 | 1.036 ms |
| Consulta de títulos | 200 | 856 ms |
| Análise financeira | 200 | 793 ms |

Não houve falha de request durante a sessão. Os detalhes estão em
`docs/evidencias/PLA-2597/navegador-real.json`.

## Infraestrutura e PostgreSQL

- Aplicação: aproximadamente 97 MB no cgroup do serviço;
- gate: aproximadamente 61 MB no cgroup do serviço;
- workers permaneceram ativos e responsivos durante a concorrência;
- conexões PostgreSQL do PSFINANCE após o teste: três conexões `idle`, em
  `ClientRead`;
- locks observados: somente locks concedidos; nenhum lock bloqueante ou espera
  de banco;
- Nginx registrou as 60 respostas HTTP 200 da rota e as respostas HTTP 200 dos
  dois assets locais.
- a carga complementar registrou CPU máxima de 0,50%, quatro conexões de 100
  disponíveis e zero espera por lock no PostgreSQL;
- Nginx, Gunicorn e PostgreSQL foram correlacionados no intervalo
  `2026-08-19T19:44:52Z/2026-08-19T19:44:57Z`, sem erro de aplicação ou banco.

## Testes e gate de recorrência

- `python -m unittest -v tests.test_filtro_empresa_analise_extrato`: 12 testes
  aprovados;
- `python -m compileall -q financeiro tests/test_filtro_empresa_analise_extrato.py`:
  aprovado;
- erro anterior: navegador permanecia carregando e a rota escalava com histórico
  e documentos;
- prevenção: remoção da dependência externa, agregação SQL do histórico e eager
  loading dos documentos;
- não recorrência: 60 requisições pós-correção sem erro/timeout, recursos locais
  concluídos e gate `5001` alinhado ao commit servido;
- risco residual: um navegador real específico ainda pode sofrer interferência
  de extensão, cache ou rede do usuário; o servidor e os recursos da jornada não
  apresentaram conexão pendente no teste controlado.

## Arquivos da correção

- `financeiro/routes_contas.py` - Agrega o saldo anterior no PostgreSQL e carrega documentos sem N+1.
- `templates/base.html` - Substitui os assets Bootstrap externos por arquivos locais.
- `src/static/vendor/bootstrap-5.3.3/bootstrap.min.css` - Disponibiliza o CSS Bootstrap no PSFINANCE.
- `src/static/vendor/bootstrap-5.3.3/bootstrap.bundle.min.js` - Disponibiliza o JavaScript Bootstrap no PSFINANCE.
- `tests/test_filtro_empresa_analise_extrato.py` - Valida assets locais e preservação do saldo agregado.
- `docs/decisoes.md` - Registra causa, correção e preservação das regras existentes.
- `docs/PLA-2597-travamentos-recorrentes.md` - Consolida os gates pós-correção e a evidência de não recorrência.
- `scripts/pla2597_capture_browser.js` - Captura screenshot, HAR, métricas de navegação e smoke tests em Chromium real.
- `scripts/pla2597_measure_sql.py` - Mede quantidade e duração das consultas da rota em transação somente leitura.
- `scripts/pla2597_measure_runtime_readonly.sh` - Mede carga, CPU e conexões PostgreSQL sem escrita.
- `docs/evidencias/PLA-2597/extrato-navegador-real-staging.png` - Comprova a tela real renderizada.
- `docs/evidencias/PLA-2597/extrato-waterfall.har` - Registra o waterfall completo do navegador.
- `docs/evidencias/PLA-2597/navegador-real.json` - Registra métricas e smoke tests do Chromium.
- `docs/evidencias/PLA-2597/sql-readonly.json` - Registra as oito consultas SQL e seus tempos.
- `docs/evidencias/PLA-2597/runtime-readonly.json` - Registra CPU, memória, carga e pool PostgreSQL.
- `docs/evidencias/PLA-2597/logs-correlacionados.txt` - Correlaciona Nginx, Gunicorn e PostgreSQL no intervalo da carga.

## Dependências de ambiente

Não requer banco, migration ou nova variável de ambiente. O deploy já foi
executado somente em `staging`. Produção, `main` e banco de produção não foram
alterados.
