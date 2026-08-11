# PLA-2073 - Visibilidade da guia de parcelas no titulo

## Projeto

PSFINANCE.

## Demanda

Corrigir a visibilidade da guia de parcelas no titulo.

## Regra aplicada

- A guia de parcelas deve ficar acessivel durante a edicao de um titulo ja
  existente.
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
- Acionar o botao e confirmar acesso a
  `/financeiro/titulos/<id_titulo>/parcelas`.
- Confirmar que novo titulo e copia de titulo continuam exibindo o campo
  `Parcelas` para criacao inicial, sem botao de edicao da guia.

Comandos executados:

```bash
.venv/bin/python -m compileall src financeiro database.py models.py
```

Resultado: compilacao concluida sem erro.

Teste focal com banco SQLite temporario e `Flask test_client`:

```text
OK PLA-2073: botao visivel na edicao, oculto em novo titulo, guia acessivel
```

Validacao local na porta corporativa `5001`:

- `GET http://127.0.0.1:5001/health` retornou HTTP 200.
- `GET http://127.0.0.1:5001/financeiro/titulos/1/editar` retornou HTTP 200.
- HTML renderizado contem `Parcelas do titulo`, link
  `/financeiro/titulos/1/parcelas` e texto de apoio da guia.

## Evidencia visual

- `docs/evidencias/PLA-2073/edicao-titulo-botao-parcelas-desktop.png` -
  Edicao de titulo existente com botao `Parcelas do titulo` visivel no
  cabecalho em desktop.
- `docs/evidencias/PLA-2073/edicao-titulo-botao-parcelas-mobile.png` -
  Edicao de titulo existente com cabecalho quebrando linha sem sobreposicao em
  mobile.

## Pendencias

- Nao houve escrita em banco de producao, alteracao de variavel de ambiente,
  VPS ou producao.
