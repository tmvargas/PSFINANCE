# PLA-2628 - Filtro de situacao na consulta de titulos

## Objetivo e regra

A consulta mensal de titulos passa a aceitar `Todas`, `Em aberto` e `Baixada`.
Mes e ano selecionam os titulos pelas parcelas do periodo. A situacao considera
o saldo global das parcelas ativas menos as baixas ativas: saldo maior que zero
e `Em aberto`; saldo igual a zero e `Baixada`. Parcelas e baixas excluidas nao
entram no calculo. `Todas` e o padrao. Quantidade, cards de resumo e rodape
totalizam apenas as linhas que atendem aos filtros combinados.

## Arquitetura

- Controller Flask: `financeiro/routes_titulos.py` normaliza e aplica a
  situacao pelo saldo global ativo, preservando o calculo financeiro mensal da
  linha. O refinamento integrado pela `PLA-2629` evita classificar como baixado
  um titulo parcelado que pagou apenas a parcela do mes.
- Template: `templates/titulos_list.html` apresenta o novo seletor sem alterar
  a ordem ou a estrutura da tabela.
- Teste focal: `tests/test_filtro_situacao_titulos.py` cobre estado padrao,
  valor invalido e limites entre baixada e em aberto.
- Decisao: `docs/decisoes.md` registra a regra e a ausencia de impacto em banco.

## Validacao local

```text
python -m py_compile: aprovado
unittest focal + limite de parcelas: 13 testes aprovados
git diff --check: aprovado
```

## Matriz funcional no staging

Periodo validado: agosto de 2026, todas as empresas, porta corporativa `5001`.

| Situacao | HTTP | Titulos | Deve aparecer | Nao deve aparecer | Totais observados |
| --- | ---: | ---: | --- | --- | --- |
| Todas | 200 | 10 | todos os titulos com parcela no periodo | nenhum titulo do periodo excluido pela situacao | parcela R$ 6.024,41; pago no mes R$ 4.040,77; nao pago no mes R$ 1.983,64 |
| Em aberto | 200 | 10 | titulos cujo saldo global ativo e maior que zero, inclusive os que pagaram a parcela do mes mas possuem saldo futuro | titulos globalmente quitados | parcela R$ 6.024,41; pago no mes R$ 4.040,77; nao pago no mes R$ 1.983,64 |
| Baixada | 200 | 0 | somente titulos cujo saldo global ativo e zero; nao havia caso no periodo | todos os 10 titulos ainda abertos | totais zerados |

O seletor preservou corretamente a opcao escolhida nas tres requisicoes. A
regra tambem foi validada em combinacao com mes, ano e empresa `Todas`; os
filtros de periodo e empresa preexistentes foram preservados.

## Gate visual

- Pedido: incluir uma unica escolha de situacao com `Todas`, `Em aberto` e
  `Baixada`.
- Referencia: tela real de Consulta de titulos publicada no staging.
- Resultado: o seletor foi inserido na barra de filtros existente; cabecalho,
  resumo, tabela, status e acoes foram preservados.
- Divergencias: nenhuma identificada.

Evidencias:

- `docs/evidencias/PLA-2628/titulos-filtro-todas-5001.png`;
- `docs/evidencias/PLA-2628/titulos-filtro-em-aberto-5001.png`;
- `docs/evidencias/PLA-2628/titulos-filtro-baixada-5001.png`.

## GitHub e staging

- Branch funcional: `feat/PLA-2628-filtro-situacao-titulos`.
- Commit funcional: `df8a2a857ed62ffa4b49e94f910ceb568a88d2b2`.
- PR funcional: `#95`, base `staging`.
- Commit funcional inicial em `staging`: `c4d5176ac3d9339b613263d5517757daa6c1ca4e`.
- Refinamento de saldo global integrado pela `PLA-2629`: `9409f71`.
- VPS: `/opt/plansmart/sistemas/psfinance/staging/repo`, branch `staging`,
  arvore limpa e commit igual ao `origin/staging`.
- Servicos `psfinance-staging` e `psfinance-staging-gate`: ativos.
- `/health` em `127.0.0.1:5104`: HTTP 200, PostgreSQL, branch e commit corretos.
- `/gate` em `127.0.0.1:5001`: HTTP 200, aplicacao interna saudavel.
- Logs recentes: nenhum warning.

## Impacto e risco

Nao exige banco, migration, variavel de ambiente, producao ou escrita de dados.
O risco residual e baixo e restrito ao calculo do saldo global ativo; a matriz
e os testes cobrem titulo simples, baixa parcial, multiplas baixas, titulo
parcelado, quitacao integral, sobrepagamento e exclusoes logicas.
