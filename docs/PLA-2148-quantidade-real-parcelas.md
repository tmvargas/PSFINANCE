# PLA-2148 - Quantidade real de parcelas no titulo

## Objetivo

Corrigir a tela principal de titulo do PSFINANCE para exibir a quantidade real
de parcelas ativas relacionadas ao titulo, sem voltar a mostrar `1` para titulo
existente com multiplas parcelas.

## Regra aplicada

- Em edicao de titulo existente, o campo `Parcelas` recebe a contagem real de
  parcelas ativas persistidas em `titulo_parcela`.
- Em edicao, o campo permanece desabilitado; inclusao, exclusao, vencimento e
  valor seguem centralizados na tela `Parcelas do titulo`.
- A mensagem explicativa abaixo do campo `Parcelas` foi removida somente na
  edicao, conforme retorno de revisao.
- Em novo titulo ou copia, a orientacao de fluxo permanece visivel porque o
  campo segue editavel e controla a geracao/revisao inicial das parcelas.

## Validacao local

Validacao executada em 2026-08-12 com a aplicacao local na porta `5001`,
usando a base `instance/pla2073_gate`, que possui o titulo `1` com `6`
parcelas ativas. Revalidacao final feita na branch `staging`, commit
`86ef904`:

- `GET /financeiro/titulos/1/editar`: HTTP 200.
- `GET /financeiro/titulos/1/parcelas`: HTTP 200.
- `/health`: HTTP 200, `status=healthy`, ambiente `staging`, banco
  `sqlite_fallback`.
- Campo `quantidade_parcelas`: renderizado com `value="6"` e `disabled`.
- Texto removido: `Edição mantém a quantidade atual` ausente no HTML da edicao.
- Acao `Parcelas do titulo`: preservada no cabecalho da edicao.
- Aba `Parcelas`: `Nova parcela` fechada por padrao via `d-none`, abre pelo
  botao `Adicionar parcela`, numeros seguem como rotulos, lixeira preservada e
  linha marcada com classe `is-deleting` antes de salvar.

## Evidencias

- `docs/evidencias/PLA-2148/edicao-titulo-quantidade-real-sem-texto.png` -
  Edicao do titulo `1` exibindo `Parcelas = 6`, campo desabilitado e sem a
  mensagem removida.
- `docs/evidencias/PLA-2148/aba-parcelas-preservada.png` - Aba de parcelas
  preservada com seis parcelas ativas e `Nova parcela` fechada.
- `docs/evidencias/PLA-2148/aba-parcelas-adicionar-parcela-aberta.png` - Aba de
  parcelas apos clicar em `Adicionar parcela`.
- `docs/evidencias/PLA-2148/aba-parcelas-lixeira-linha-vermelha.png` - Aba de
  parcelas apos acionar a lixeira, com linha marcada antes de salvar.

## Limites

Nao houve alteracao de banco, migration, `main`, producao, credenciais ou dados
produtivos.
