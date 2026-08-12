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
- Apos a consolidacao das evidencias da devolucao, o `origin/staging` e a VPS
  de teste passaram ao commit `9745b5e7cb4991c4429078b7046aa23a1cf09c63`.
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
- Revisao da devolucao executiva: confirmado que o staging real da porta `5001`
  esta no commit `9745b5e7cb4991c4429078b7046aa23a1cf09c63`, com os elementos
  visuais e funcionais exigidos.

## Validacao

Executada em 2026-08-12 na porta publica corporativa `5001`.

| Caso | Resultado |
| --- | --- |
| `GET /health` | HTTP 200, `branch=staging`, `commit=9745b5e7cb4991c4429078b7046aa23a1cf09c63`, `db_dialect=postgresql`, `database_url_source=PSFINANCE_STAGING_DATABASE_URL` |
| `GET /financeiro/titulos/1/editar` | HTTP 200, HTML contem `Parcelas do titulo`, `Valor total`, `Data do 1º Vencimento` e link `/financeiro/titulos/1/parcelas` |
| `GET /financeiro/titulos/1/parcelas` | HTTP 200, HTML contem `Parcelas do Titulo #1`, `Valor total do titulo`, `Soma das parcelas` e `Salvar parcelas` |
| Banco de staging | Tabela `titulo_parcela` criada com colunas `id_parcela`, `uuid`, `id_titulo`, `numero_parcela`, `vencimento`, `valor`, `created_at`, `updated_at` e `deleted` |

## Evidencias visuais

Referencia de rejeicao de Thiago: print anexado na tarefa mae indicando que a
tela real de staging ainda mostrava `Valor`, `Data de Vencimento` e nao
mostrava `Parcelas do titulo`.

Screenshots reais gerados contra `http://vps69143.publiccloud.com.br:5001`:

- `docs/evidencias/PLA-2106/edicao-titulo-staging-5001.png` - Tela `Editar Titulo`
  com botao `Parcelas do titulo`, rotulo `Valor total` e rotulo
  `Data do 1º Vencimento`.
- `docs/evidencias/PLA-2106/parcelas-titulo-staging-5001-antes.png` - Guia de
  parcelas aberta pelo staging real, com `Valor total do titulo`,
  `Soma das parcelas` e `Salvar parcelas`.
- `docs/evidencias/PLA-2106/parcelas-titulo-staging-5001-apos-inclusao.png` -
  Validacao de inclusao de parcela de teste e recalculo para `R$ 2694,39`.
- `docs/evidencias/PLA-2106/parcelas-titulo-staging-5001-restaurado.png` -
  Estado final restaurado para uma parcela ativa e soma `R$ 2594,39`.
- `docs/evidencias/PLA-2106/edicao-titulo-staging-5001-restaurado.png` - Tela
  `Editar Titulo` apos restauracao, mantendo botao e rotulos solicitados.

Comparacao objetiva com o print de Thiago:

| Item rejeitado no print | Resultado validado no staging real |
| --- | --- |
| Ausencia da aba/botao de parcelas | Botao `Parcelas do titulo` visivel no topo da tela `Editar Titulo`, apontando para `/financeiro/titulos/1/parcelas` |
| Campo aparecia como `Valor` | Campo aparece como `Valor total` |
| Campo aparecia como `Data de Vencimento` | Campo aparece como `Data do 1º Vencimento` |
| Alteracao nao visivel no staging acessado por Thiago | Validado diretamente em `http://vps69143.publiccloud.com.br:5001` |

## Validacao funcional de parcelas

| Caso | Acao executada | Resultado |
| --- | --- | --- |
| Leitura inicial | `GET /financeiro/titulos/1/parcelas` | Uma parcela ativa, `Valor total do titulo` e `Soma das parcelas` em `R$ 2594,39` |
| Inclusao | `POST /financeiro/titulos/1/parcelas` mantendo parcela 1 e adicionando parcela 2 de `R$ 100,00` em `2026-01-10` | Retorno HTTP 302 para a propria guia; leitura posterior mostrou duas parcelas e soma recalculada para `R$ 2694,39` |
| Restauracao | `POST /financeiro/titulos/1/parcelas` excluindo a parcela de teste e preservando a parcela 1 | Retorno HTTP 302; leitura posterior voltou para uma parcela ativa e soma `R$ 2594,39` |
| Leitura posterior da edicao | `GET /financeiro/titulos/1/editar` | Tela permaneceu com `Parcelas do titulo`, `Valor total`, `Data do 1º Vencimento` e valor restaurado |

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
  textos esperados; screenshots e teste funcional confirmam que a aba de
  parcelas, os rotulos e o recalculo estao visiveis no staging real.

## Riscos e limites

- Nao houve alteracao em `main`.
- Nao houve deploy em producao.
- Nao houve escrita no banco de producao.
- Nao foram expostos valores de secrets, tokens, senhas ou URLs completas de
  banco.
