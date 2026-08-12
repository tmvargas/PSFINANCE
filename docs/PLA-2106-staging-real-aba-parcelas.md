# PLA-2106 - Staging real da aba de parcelas

## Projeto

PSFINANCE.

## Demanda

Corrigir o staging real da aba de parcelas.

## Causa confirmada

- A VPS de teste estava executando a branch `staging`, mas no commit
  `e17896e7838cdea30f6deea9f8aecd003cc3b0f0`.
- O GitHub `origin/staging` estava no commit
  `b7d10c1a18574aff8186573829aba2786c1df80c`, que ja continha as entregas
  PLA-1816 e PLA-2073.
- A tela real em `http://vps69143.publiccloud.com.br:5001/financeiro/titulos/1/editar`
  retornava HTTP 200, mas nao exibia `Parcelas do titulo`, `Valor total` nem
  `Data do 1º Vencimento`.
- A tabela `titulo_parcela` nao existia no PostgreSQL de staging real.

## Acao executada

- Atualizado o repositorio operacional da VPS em
  `/opt/plansmart/sistemas/psfinance/staging/repo` por fast-forward de
  `staging` ate `b7d10c1a18574aff8186573829aba2786c1df80c`.
- Aplicada no banco de staging a migration versionada
  `migrations/versions/20260810_pla1816_titulo_parcela.sql`.
- Atualizados os metadados nao sensiveis `GIT_BRANCH=staging` e
  `GIT_COMMIT=b7d10c1a18574aff8186573829aba2786c1df80c` dos servicos de
  staging.
- Reiniciados somente os servicos de staging:
  `psfinance-staging` e `psfinance-staging-gate`.

## Validacao

Executada em 2026-08-12 na porta publica corporativa `5001`.

| Caso | Resultado |
| --- | --- |
| `GET /health` | HTTP 200, `branch=staging`, `commit=b7d10c1a18574aff8186573829aba2786c1df80c`, `db_dialect=postgresql`, `database_url_source=PSFINANCE_STAGING_DATABASE_URL` |
| `GET /financeiro/titulos/1/editar` | HTTP 200, HTML contem `Parcelas do titulo`, `Valor total`, `Data do 1º Vencimento` e link `/financeiro/titulos/1/parcelas` |
| `GET /financeiro/titulos/1/parcelas` | HTTP 200, HTML contem `Parcelas do Titulo #1`, `Valor total do titulo`, `Soma das parcelas` e `Salvar parcelas` |
| Banco de staging | Tabela `titulo_parcela` criada com colunas `id_parcela`, `uuid`, `id_titulo`, `numero_parcela`, `vencimento`, `valor`, `created_at`, `updated_at` e `deleted` |

## Gate de recorrencia

- Erro anterior: a entrega estava documentada em branch e evidencias, mas o
  staging real publicado na VPS ainda estava em commit anterior e sem a tabela
  de parcelas.
- Causa: deploy de staging e migration de staging nao tinham acompanhado o
  `origin/staging`.
- Correcao: VPS de teste alinhada ao `origin/staging`, migration aplicada e
  metadados de healthcheck atualizados.
- Evidencia de nao recorrencia: `/health` na porta `5001` mostra o commit
  correto e as rotas reais de edicao e parcelas respondem HTTP 200 com os
  textos esperados.

## Riscos e limites

- Nao houve alteracao em `main`.
- Nao houve deploy em producao.
- Nao houve escrita no banco de producao.
- Nao foram expostos valores de secrets, tokens, senhas ou URLs completas de
  banco.
