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
possuía Chromium, Chrome, Firefox ou Playwright instalado; por isso a evidência
de rede foi coletada diretamente do HTML servido e de todas as dependências da
página, sem instalação ou aumento de escopo na VPS.

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

## Dependências de ambiente

Não requer banco, migration ou nova variável de ambiente. O deploy já foi
executado somente em `staging`. Produção, `main` e banco de produção não foram
alterados.
