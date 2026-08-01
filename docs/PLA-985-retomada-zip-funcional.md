# PLA-985 - Retomada da PLA-981 com ZIP funcional reenviado

Data da execucao: 2026-08-01

## Objetivo

Retomar a PLA-981 a partir do ZIP funcional reenviado por Thiago e preparar o
PSFINANCE para staging funcional, sem versionar banco, uploads, documentos ou
dados operacionais.

## Skills consultadas

- `plansmart-governanca-desenvolvimento`;
- `plansmart-projeto-psfinance`;
- `plansmart-projeto-vps-sistemas`.

## Artefato localizado

- ZIP interno do Paperclip: `finance.zip`.
- Tamanho aproximado: 8,9 MB.
- Conteudo confirmado: aplicacao Flask, templates, `financeiro.db` SQLite e
  anexos em `uploads`/`instance/uploads`.

## Decisao aplicada

Somente o codigo fonte funcional foi incorporado ao repositório. O banco SQLite
`financeiro.db` e os anexos foram mantidos fora do Git por conterem dados
operacionais e documentos privados.

## Validacao local

Executado com banco SQLite copiado somente para `instance/financeiro.db`,
diretorio ignorado pelo Git:

```text
.venv/bin/python -m compileall src database.py models.py financeiro
PSFINANCE_DATABASE_URL=sqlite:///instance/financeiro.db .venv/bin/python <teste focal Flask>
```

Rotas validadas pelo cliente de teste Flask:

- `/health` retornou HTTP 200;
- `/gate` retornou HTTP 200;
- `/` redirecionou para `/financeiro/`;
- `/financeiro/` retornou HTTP 200;
- `/financeiro/titulos` retornou HTTP 200;
- `/staging/psfinance/health` retornou HTTP 200;
- `/staging/psfinance` redirecionou para `/staging/psfinance/financeiro/`;
- `/staging/psfinance/financeiro/` retornou HTTP 200.

## Pendencias para staging na VPS

- Copiar o `financeiro.db` do artefato para o diretório operacional
  `instance/` do staging, sem publicar no Git.
- Copiar os anexos necessários para `instance/uploads/titulos`, sem publicar no
  Git.
- Configurar `PSFINANCE_DATABASE_URL`, `PSFINANCE_INSTANCE_PATH`,
  `PSFINANCE_UPLOAD_TITULOS_FOLDER` e `PSFINANCE_SECRET_KEY` no serviço de
  staging.
- Atualizar a VPS de teste a partir da branch `staging` e validar a porta
  corporativa `5001`.

## Fora do escopo

- Merge na `main`;
- deploy em producao;
- migration ou escrita em banco produtivo;
- publicação de banco SQLite, uploads ou documentos no Git.
