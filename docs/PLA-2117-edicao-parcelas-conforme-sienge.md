# PLA-2117 - Edicao de parcelas do titulo conforme Sienge

## Projeto

PSFINANCE.

## Demanda

Corrigir a edicao de parcelas do titulo conforme o comportamento do Sienge.

## Regra aplicada

- A aba `Parcelas` permanece como local de inclusao, exclusao e ajuste da
  distribuicao de parcelas do titulo.
- A inclusao manual permanece uma parcela por vez, aderente ao fluxo publicado
  no suporte Sienge para titulo a pagar.
- Ao salvar a aba `Parcelas`, o valor total do titulo continua refletindo a
  soma das parcelas ativas.
- Editar e salvar parcela existente nao dispara validacao de nova parcela.
- O bloco `Nova parcela` fica fechado por padrao e abre somente pelo botao
  `Adicionar parcela`.
- O numero da parcela aparece como texto/rotulo, nao como campo editavel.
- A exclusao usa icone de lixeira; ao acionar, a linha fica marcada em vermelho
  antes de salvar.
- Quando o titulo possui exatamente uma parcela ativa, a edicao do valor total
  ou da data do primeiro vencimento na tela principal tambem sincroniza essa
  parcela unica.
- Quando o titulo possui duas ou mais parcelas ativas, a tela principal nao
  redistribui parcelas automaticamente; os ajustes permanecem na aba
  `Parcelas`, preservando a regra ja validada nas PLAs 1816, 2073 e 2106.

## Fonte funcional usada

- Artigo publico Sienge `Como incluir parcelas em um titulo a pagar?`,
  consultado em 2026-08-12, informa que a inclusao ocorre pela aba `Parcelas`,
  com botao de adicionar, uma parcela por vez, e confirmacao de alteracao do
  valor do titulo ao salvar.

## Arquitetura

- Controller: `financeiro/routes_titulos.py`.
- Template: `templates/titulo_parcelas_form.html`.
- Nao houve alteracao em model, migration, banco de dados, CSS externo, VPS de
  producao ou producao.

## Validacao executada

```bash
.venv/bin/python -m compileall src financeiro database.py models.py
```

Resultado: compilacao concluida sem erro.

Teste focal com banco SQLite temporario e `Flask test_client`:

```text
OK PLA-2117: parcela unica sincronizada; multiplas parcelas preservadas para edicao pela aba Parcelas
OK PLA-2117 UI: edicao sem erro de nova parcela; add via botao; exclusao e recalculo preservados
```

Matriz funcional:

| Caso | Entrada | Resultado esperado |
| --- | --- | --- |
| Titulo com uma parcela ativa | Editar valor para `150,50` e vencimento para `2026-11-15` na tela principal | Titulo salvo; parcela unica ativa fica como parcela `1`, valor `150.50` e vencimento `2026-11-15` |
| Titulo com duas parcelas ativas | Editar valor e vencimento na tela principal | Titulo salvo; parcelas existentes continuam com valores e vencimentos originais para ajuste pela aba `Parcelas` |
| Edicao de parcela existente | Alterar valor/vencimento de parcela existente sem preencher nova parcela | Salvamento sem erro `Vencimento da nova parcela invalido`; titulo recalculado |
| Inclusao de nova parcela | Abrir `Adicionar parcela`, preencher vencimento e valor | Nova parcela persistida; titulo recalculado |
| Exclusao de parcela | Acionar lixeira, confirmar linha vermelha e salvar | Parcela marcada como excluida; titulo recalculado com parcelas ativas |

## Gate visual

Referencia obrigatoria da tarefa mae:

- `docs/evidencias/PLA-2117/referencia-sienge.png` - Print do Sienge anexado no
  comentario de Thiago na PLA-743.

Evidencias geradas em navegador automatizado local na porta `5001`:

- `docs/evidencias/PLA-2117/parcelas-inicial-nova-parcela-fechada.png` - Tela
  de parcelas com `Nova parcela` fechada por padrao, numeros exibidos como
  rotulos e lixeira por linha.
- `docs/evidencias/PLA-2117/parcelas-adicionar-parcela-aberta.png` - Tela apos
  clicar em `Adicionar parcela`, exibindo campos da nova parcela.
- `docs/evidencias/PLA-2117/parcelas-lixeira-linha-vermelha.png` - Tela apos
  clicar na lixeira, com a linha marcada em vermelho antes de salvar.
- `docs/evidencias/PLA-2117/staging-parcelas-inicial-nova-parcela-fechada.png`
  - Tela real de staging na porta `5001`, com `Nova parcela` fechada por
  padrao.
- `docs/evidencias/PLA-2117/staging-parcelas-adicionar-parcela-aberta.png` -
  Tela real de staging apos clicar em `Adicionar parcela`.
- `docs/evidencias/PLA-2117/staging-parcelas-lixeira-linha-vermelha.png` -
  Tela real de staging com lixeira acionada e linha vermelha antes de salvar.

Comparacao objetiva com o print do Sienge:

| Item do Sienge | Resultado no PSFINANCE |
| --- | --- |
| Aba/grade de parcelas com linhas existentes | Preservada a tela `Parcelas do Titulo` com tabela de parcelas existentes |
| Numero da parcela aparece como texto | Corrigido: numero da parcela e rotulo, com valor oculto apenas para submissao |
| Lixeira por linha | Corrigido: exclusao por botao com icone de lixeira |
| Linha destacada ao selecionar/excluir | Corrigido: linha marcada em vermelho antes do salvamento |
| Inclusao acionada por botao `ADICIONAR` | Corrigido: campos de `Nova parcela` ficam fechados e abrem por `Adicionar parcela` |
| Valor total/soma coerente | Preservado: valor do titulo recalculado pela soma das parcelas ativas |

## Validacao em staging

Publicada em 2026-08-12 na VPS (Servidor Virtual Privado) Sistemas.

```text
Branch da VPS: staging
Commit funcional validado: 0ae81cd1606c47fef77f9049d5c7256d227a06fb
HEAD da VPS: 0ae81cd1606c47fef77f9049d5c7256d227a06fb
origin/staging na VPS: 0ae81cd1606c47fef77f9049d5c7256d227a06fb
git status da VPS: limpo
psfinance-staging: active
psfinance-staging-gate: active
PORT 5104 /health: HTTP 200, branch=staging, db=postgresql
PORT 5105 /health: HTTP 200, branch=staging, db=postgresql
PORT 5001 /health: HTTP 200, branch=staging, db=postgresql
GET /financeiro/titulos/1/editar na porta 5001: HTTP 200
GET /financeiro/titulos/1/parcelas na porta 5001: HTTP 200
```

Jornada operacional real validada na porta publica `5001`, em banco PostgreSQL
de staging, com titulo temporario `PLA-2117-TESTE`:

```text
Editar parcela existente e salvar: sem erro `Vencimento da nova parcela invalido`
Adicionar nova parcela pelo botao `Adicionar parcela`: aprovado
Excluir parcela por lixeira: linha ficou vermelha antes de salvar
Salvar exclusao: parcela removida logicamente e titulo recalculado
Limpeza posterior: titulo temporario sem registro ativo e parcelas temporarias sem registro ativo
```

Marcadores validados na tela de edicao:

- `Parcelas do titulo`;
- `Valor total`;
- `Data do 1º Vencimento`.

Marcadores validados na tela de parcelas:

- `Parcelas do Titulo`;
- `Valor total do titulo`;
- `Soma das parcelas`;
- `Salvar parcelas`.

Tambem foi corrigido o metadado nao sensivel de commit dos servicos de staging
em `/opt/plansmart/sistemas/psfinance/env/staging.env`, preservando backup
operacional do arquivo de ambiente e sem registrar valores de secrets.

## Gate de arquitetura

- Skill consultada: `plansmart-projeto-psfinance`, junto com
  `plansmart-governanca-desenvolvimento` e `plansmart-projeto-vps-sistemas`.
- Arquitetura preservada: regra aplicada no controller de titulos, sem criar
  camada paralela ou duplicar modelo de parcelas.
- Excecao: nenhuma.

## Gate de recorrencia

- Erro anterior: a edicao de titulo de parcela unica podia alterar o titulo sem
  atualizar a parcela relacional, criando divergencia entre a tela principal e a
  aba `Parcelas`.
- Causa: a rotina de edicao garantia a existencia da parcela unica, mas nao
  sincronizava valor e vencimento quando ela ja existia.
- Correcao: criada sincronizacao focal para atualizar somente a parcela unica.
- Evidencia de nao recorrencia: teste focal confirmou a sincronizacao da
  parcela unica e a preservacao das multiplas parcelas; staging confirmou
  edicao, inclusao e exclusao sem recorrencia do erro de nova parcela.
- Risco residual: validacao de escrita foi executada somente no banco
  PostgreSQL de staging com dado temporario removido logicamente ao final; nao
  houve validacao nem escrita em producao.

## Limites

- Nao houve escrita em banco de producao.
- Nao houve migration.
- Houve atualizacao apenas dos metadados nao sensiveis `GIT_BRANCH` e
  `GIT_COMMIT` no ambiente de staging.
- Houve deploy somente em staging, pela branch `staging`.
- Nao houve deploy em producao.
