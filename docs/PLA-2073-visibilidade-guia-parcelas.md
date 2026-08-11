# PLA-2073 - Visibilidade da guia de parcelas no titulo

## Projeto

PSFINANCE.

## Demanda

Corrigir a visibilidade da guia de parcelas no titulo.

## Regra aplicada

- A guia de parcelas deve ficar acessivel durante a edicao de um titulo ja
  existente.
- A edicao do titulo deve exibir os rotulos `Valor total` e
  `Data do 1º Vencimento`, evitando que a nomenclatura fique visivel apenas na
  criacao.
- O campo `Parcelas` permanece bloqueado na edicao do titulo para preservar a
  regra da PLA-1816: ajustes de vencimento, valor, inclusao e exclusao devem
  ocorrer pela guia especifica de parcelas.

## Arquitetura

- Template: `templates/titulo_form.html`.
- Nao houve alteracao em controller, service, model, migration ou banco de
  dados.

## Validacao executada

- Abrir a edicao de um titulo existente.
- Confirmar que o botao `Parcelas do titulo` aparece no cabecalho da tela.
- Confirmar que a edicao exibe `Valor total` e `Data do 1º Vencimento`.
- Acionar o botao e confirmar acesso a
  `/financeiro/titulos/<id_titulo>/parcelas`.
- Confirmar que novo titulo e copia de titulo continuam exibindo o campo
  `Parcelas` para criacao inicial, sem botao de edicao da guia.
- Criar titulo com 5 parcelas e primeiro vencimento em `2027-01-29`,
  confirmando redirecionamento imediato para a guia de parcelas.
- Validar regra de vencimento mensal para dia 31.
- Editar vencimento e valor de parcelas existentes, incluir nova parcela
  manualmente e confirmar recálculo do valor total do titulo.

Comandos executados:

```bash
.venv/bin/python -m compileall src financeiro database.py models.py
```

Resultado: compilacao concluida sem erro.

Validacao da porta corporativa `5001` em 2026-08-11:

```text
GET http://127.0.0.1:5001/health -> HTTP 200
app=PSFINANCE
environment=staging
branch=staging
commit=f2659ef60755f32d94e62a8e20f7b16a5c3b4223
db_dialect=sqlite
```

Teste focal com banco SQLite temporario e `Flask test_client`:

```text
OK PLA-2073: botao visivel na edicao, oculto em novo titulo, guia acessivel
```

Validacao local na porta corporativa `5001`:

- `GET http://127.0.0.1:5001/health` retornou HTTP 200.
- `GET http://127.0.0.1:5001/financeiro/titulos/1/editar` retornou HTTP 200.
- HTML renderizado contem `Parcelas do titulo`, link
  `/financeiro/titulos/1/parcelas`, `Valor total`, `Data do 1º Vencimento` e
  texto de apoio da guia.

Revalidacao funcional em navegador automatizado na porta `5001`:

| Caso | Entrada | Resultado validado |
| --- | --- | --- |
| Criacao com 5 parcelas | Valor `100,00`, primeiro vencimento `2027-01-29`, parcelas `5` | HTTP 302 para `/financeiro/titulos/2/parcelas`; parcelas geradas em `2027-01-29`, `2027-02-28`, `2027-03-29`, `2027-04-29`, `2027-05-29`, todas com valor `20,00`. |
| Regra de dia 31 | Valor `100,00`, primeiro vencimento `2026-01-31`, parcelas `3` | HTTP 302 para `/financeiro/titulos/3/parcelas`; parcelas geradas em `2026-01-31`, `2026-02-28`, `2026-03-31`, com valores `33,34`, `33,33`, `33,33`. |
| Guia aberta apos salvar | Criacao de titulo com 5 parcelas | Tela carregada diretamente em `Parcelas do Titulo #1`, com mensagem `5 parcelas salvas com sucesso!`, botao `Editar titulo`, soma das parcelas e cinco linhas editaveis. |
| Edicao do titulo salvo | Acesso a `/financeiro/titulos/1/editar` | Tela `Editar Titulo` exibiu botao `Parcelas do titulo`, `Valor total`, `Data do 1º Vencimento` e campo `Parcelas` bloqueado com texto orientando uso da guia. |
| Edicao e inclusao manual | Alterada parcela 1 para vencimento `2027-01-31` e valor `30,00`; parcela 2 para `25,00`; incluida parcela 6 em `2027-06-30` com `50,00` | Guia salvou com mensagem `Parcelas salvas e valor total do titulo atualizado.`; titulo passou para valor total `165,00`, vencimento `2027-01-31` e seis parcelas ativas. |

## Evidencia visual

- `docs/evidencias/PLA-2073/criacao-titulo-campos-parcelas-desktop.png` -
  Tela de criacao com `Valor total`, `Data do 1º Vencimento` e `Parcelas`
  visiveis.
- `docs/evidencias/PLA-2073/guia-parcelas-aberta-apos-salvar-5-parcelas.png` -
  Guia de parcelas aberta automaticamente apos salvar titulo com 5 parcelas.
- `docs/evidencias/PLA-2073/edicao-titulo-botao-parcelas-desktop.png` -
  Edicao de titulo existente com botao `Parcelas do titulo`, `Valor total` e
  `Data do 1º Vencimento` visiveis em desktop.
- `docs/evidencias/PLA-2073/edicao-titulo-botao-parcelas-mobile.png` -
  Edicao de titulo existente com cabecalho quebrando linha sem sobreposicao em
  mobile.
- `docs/evidencias/PLA-2073/edicao-titulo-botao-parcelas-desktop-revalidado.png` -
  Revalidacao da edicao do titulo salvo com o botao `Parcelas do titulo`.
- `docs/evidencias/PLA-2073/guia-parcelas-editada-inclusao-recalculo.png` -
  Guia apos edicao de vencimento e valor, inclusao manual da parcela 6 e
  recálculo do total para `165,00`.

## Gate de recorrencia

- Erro anterior: Thiago nao visualizou a guia de parcelas nem os rotulos
  solicitados na tela real de edicao do titulo.
- Causa identificada na revisao: a entrega anterior tinha codigo e screenshots
  parciais, mas nao comprovava a porta `5001`, a tela de criacao, a guia aberta
  apos salvar e os casos funcionais obrigatorios.
- Correcao aplicada: revalidacao completa em `staging` no commit
  `f2659ef60755f32d94e62a8e20f7b16a5c3b4223`, com screenshots novos e matriz
  funcional dos casos solicitados.
- Evidencia de nao recorrencia: o navegador acessou a edicao do titulo salvo e
  mostrou o botao `Parcelas do titulo`, alem de acessar a guia pela propria tela
  de edicao.
- Risco residual: os testes foram executados em banco SQLite temporario isolado;
  nao houve escrita no banco de staging real nem producao.

## Pendencias

- Nao houve escrita em banco de producao, alteracao de variavel de ambiente,
  VPS ou producao.
