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
  `financeiro/routes_empresa.py`;
- Templates: `templates/conta_form.html`, `templates/contas_list.html` e
  `templates/contas_inativas.html`;
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

## Limites

- Nao altera `main`.
- Nao executa migration em producao.
- Nao copia dados entre staging e producao.
- A validacao final em staging exige deploy da branch `staging` e porta
  corporativa `5001`.
