# PLA-1376 - Vincular contas a empresa no PSFINANCE

## Projeto

PSFINANCE.

## Demanda atendida

Vincular contas de caixa/banco a uma empresa ativa, como complemento da
estrutura de `PLA-1179`.

## Regra aplicada

- Toda nova conta exige uma empresa ativa.
- Edicoes de conta tambem exigem empresa ativa.
- A empresa vinculada passa a ser exibida nas listagens de contas ativas e
  inativas.
- Empresa com conta ativa vinculada nao pode ser desativada.
- Conta inativa so pode ser reativada quando possuir empresa ativa vinculada.
- Movimentacoes de entrada, saida e transferencia exigem que a conta usada
  pertenca a empresa selecionada na movimentacao.
- Baixas de titulos so aceitam conta ativa pertencente a empresa do titulo.
- Contas historicas sem empresa devem ser vinculadas por migration controlada.

## Arquitetura

Skills consultadas:

- `plansmart-governanca-desenvolvimento`;
- `plansmart-projeto-psfinance`;
- `plansmart-projeto-vps-sistemas`.

Arquivos por camada:

- Modelo: `models.py`;
- Regras compartilhadas: `financeiro/regras_empresa_centro.py`;
- Controllers Flask: `financeiro/routes_contas.py` e
  `financeiro/routes_empresa.py`, `financeiro/routes_titulos.py`;
- Templates: `templates/conta_form.html`, `templates/contas_list.html`,
  `templates/contas_inativas.html`, `templates/movimentacao_form.html`,
  `templates/movimentacao_edit_form.html` e `templates/titulo_baixa_form.html`;
- Banco: `migrations/versions/20260805_pla1376_conta_empresa.sql`;
- Documentacao: `docs/decisoes.md` e este arquivo.

## Banco de dados

O script PostgreSQL versionado:

- adiciona `conta.id_empresa`;
- vincula contas existentes sem empresa a empresa ativa de codigo `1`, somente
  quando existir exatamente uma;
- aborta se houver ambiguidade ou ausencia da empresa padrao para contas
  historicas sem vinculo;
- aplica `NOT NULL` depois do backfill;
- cria indice parcial para contas ativas por empresa.

Nenhuma escrita em producao esta autorizada por esta entrega.

## Validacao local

Executar:

```text
.venv/bin/python -m compileall src financeiro database.py models.py
```

Teste focal recomendado com banco temporario:

- criar empresa ativa;
- abrir `/financeiro/contas/nova` e confirmar select de empresa;
- tentar criar conta sem empresa e confirmar bloqueio;
- criar conta com empresa ativa e confirmar persistencia;
- editar conta mantendo empresa ativa;
- listar contas ativas e inativas confirmando coluna Empresa;
- tentar desativar empresa com conta ativa e confirmar bloqueio.
- criar duas empresas ativas e duas contas, uma para cada empresa;
- tentar registrar entrada, saida e transferencia na empresa A usando conta da
  empresa B e confirmar mensagem "Conta nao pertence a empresa selecionada.";
- tentar baixar titulo da empresa A usando conta da empresa B e confirmar
  bloqueio;
- confirmar que os selects de movimentacao ocultam contas de outras empresas
  apos selecionar a empresa.

## Evidencias coletadas

- Backfill no banco PostgreSQL de `staging`, consulta agregada em 2026-08-05:
  `total_contas=9`, `contas_com_empresa=9`, `contas_sem_empresa=0`,
  `contas_empresa_1=9`.
- Evidencia visual local com banco temporario:
  `docs/mockups/evidencias/PLA-1376-contas-empresa.png`.
- Evidencia visual local do formulario de movimentacao com empresa selecionada:
  `docs/mockups/evidencias/PLA-1376-movimentacao-contas-por-empresa.png`.
- Validacao focal por POST manipulado confirmou bloqueio de conta de outra
  empresa em `/financeiro/movimentacoes/nova` e
  `/financeiro/titulos/1/baixar` com mensagem
  "Conta nao pertence a empresa selecionada.".
- Validacao DOM (Modelo de Objetos do Documento) confirmou que, ao selecionar
  a empresa `1`, a conta da empresa `2` fica oculta no select da tela de
  movimentacao.

## Limites

- Nao altera `main`.
- Nao executa migration em producao.
- Nao copia dados entre staging e producao.
- A validacao final em staging exige deploy da branch `staging` e porta
  corporativa `5001`.
