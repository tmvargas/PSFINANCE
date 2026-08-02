# PLA-988 - Migracao do staging PSFINANCE para PostgreSQL

## Objetivo

Migrar o banco de staging do PSFINANCE de SQLite para PostgreSQL preservando os
dados operacionais existentes e mantendo producao fora do escopo.

## Escopo

- Origem: SQLite operacional em `instance/financeiro.db`.
- Destino: PostgreSQL de staging via `PSFINANCE_STAGING_DATABASE_URL`.
- Tabelas migradas: `documento`, `plano_de_contas`, `credor`, `conta`,
  `titulo`, `titulo_anexo`, `baixa` e `movimentacao_conta`.
- Dados preservados: chaves primarias, UUIDs, valores, datas, vinculos e
  caminhos de anexos.
- Ajuste tecnico durante a copia: campos de auditoria `created_at` e
  `updated_at` nulos recebem o horario da migracao; `deleted` e `conciliado`
  nulos recebem `false`.

## Inventario local em 2026-08-01

| Tabela | Registros |
| --- | ---: |
| `baixa` | 37 |
| `conta` | 9 |
| `credor` | 12 |
| `documento` | 5 |
| `movimentacao_conta` | 94 |
| `plano_de_contas` | 41 |
| `titulo` | 47 |
| `titulo_anexo` | 28 |

## Procedimento

1. Confirmar backup do SQLite operacional antes da execucao.
2. Configurar `PSFINANCE_STAGING_DATABASE_URL` no ambiente de staging, sem
   registrar o valor em Git ou Paperclip.
3. Instalar dependencias do `requirements.txt`.
4. Executar:

```bash
.venv/bin/python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-url sqlite:////caminho/seguro/financeiro.db
```

5. Se o destino nao estiver vazio, interromper, validar backup e executar
   novamente somente com autorizacao explicita usando `--truncate-target`.
6. Reiniciar o servico de staging com `PSFINANCE_STAGING_DATABASE_URL`
   configurada.
7. Validar `/health`, `/staging/psfinance`, rotas financeiras criticas e gate
   corporativo na porta `5001`.

## Validacao esperada

- Script encerra com contagem por tabela igual ao inventario de origem.
- Aplicacao responde usando PostgreSQL.
- Porta `5001` retorna HTTP 200 no gate.
- Logs do servico de staging sem erro de conexao PostgreSQL ou SQLAlchemy.

## Rollback de staging

1. Parar o servico de staging.
2. Remover `PSFINANCE_STAGING_DATABASE_URL` ou restaurar a URL SQLite anterior.
3. Recolocar o backup validado em `instance/financeiro.db`, se necessario.
4. Reiniciar o servico.
5. Validar `/health`, `/staging/psfinance` e porta `5001`.

## Riscos

- Se o PostgreSQL de staging ja tiver dados, a migracao deve parar para evitar
  mistura ou sobrescrita sem decisao.
- Caminhos de anexos sao preservados como referencias; arquivos fisicos em
  `instance/uploads/titulos` continuam sendo responsabilidade operacional fora
  do Git.
- Criacao de banco, usuario e escrita em producao nao fazem parte deste escopo.
