# PLA-2581 - Transferência sem apropriação e centro de custo

## Regra aplicada

Transferência movimenta recurso entre duas contas da mesma empresa. Ela não é
receita nem despesa e, portanto, não solicita nem persiste plano financeiro ou
centro de custo. Entrada e saída preservam as validações anteriores.

## Arquitetura e governança

- Skills consultadas: `plansmart-governanca-desenvolvimento`,
  `plansmart-projeto-psfinance` e `plansmart-projeto-vps-sistemas`.
- Controller e regra de persistência: `financeiro/routes_contas.py`.
- Interface de criação e edição: `templates/movimentacao_form.html` e
  `templates/movimentacao_edit_form.html`.
- Teste focal: `tests/test_transferencia_sem_apropriacao.py`.
- Decisão de negócio: `docs/decisoes.md`.
- Branch original: `fix/PLA-2581-remover-apropriacao-centro-transferencias`.
- Commit original: `89fe904450645f663b65ee90a2c819c39769ed87`.
- Merge em `staging`: `8288040ab1a325337c5ffc64cf0189a2bfc66f11`.

Não houve alteração de model, migration ou estrutura do banco.

## Matriz integral de aceite

| Critério | Evidência | Resultado |
| --- | --- | --- |
| Criar transferência sem plano e centro | POST real na porta `5001` com PostgreSQL | Aprovado |
| Ocultar campos e limpar valores antigos | Screenshot do formulário e inspeção do DOM: ambos `display:none`, valores limpos e centro sem `required` | Aprovado |
| Ignorar POST manipulado | POST real enviou `id_centro_custo=1` e `id_plano=9`; listagem exibiu `- / -` | Aprovado |
| Origem e destino corretos, sem duplicidade | Registro único exibiu `Origem: BB THIAGO` e `Destino: C6`; teste automatizado confirma um único objeto | Aprovado |
| Rejeitar origem igual ao destino | Teste automatizado focal | Aprovado |
| Preservar Entrada e Saída | Teste automatizado confirma centro e plano ainda obrigatórios nos dois tipos | Aprovado |
| Editar transferência legada | Teste cria legado com vínculos residuais, edita e confirma ambos nulos | Aprovado |
| Copiar transferência legada | Não aplicável: movimentações não possuem rota, botão ou fluxo de cópia; busca no controller e template confirma somente criar, listar, editar e excluir. Não foi criada funcionalidade fora do escopo | Inaplicável no produto atual |
| Extrato e Análise não tratam transferência como receita/despesa | Consultas existentes filtram movimentações financeiras pelos tipos `E` e `S` e ignoram `T`; persistência sem plano/centro elimina apropriação residual | Aprovado |

## Jornada operacional completa em staging

Executada em 15/08/2026 no ambiente público corporativo:

1. `GET /health` retornou HTTP 200, `branch=staging`,
   `commit=8288040ab1a325337c5ffc64cf0189a2bfc66f11`,
   `db_dialect=postgresql` e
   `database_url_source=PSFINANCE_STAGING_DATABASE_URL`.
2. `GET /gate` retornou HTTP 200.
3. A tela real `/financeiro/movimentacoes/nova` foi aberta em navegador
   automatizado na porta `5001`.
4. Ao selecionar `Transferência`, Plano Financeiro e Centro de Custo ficaram
   ocultos; o `required` do centro foi removido.
5. Foi enviado POST manipulado com empresa `1`, origem `5`, destino `1`, centro
   `1`, plano `9`, documento temporário `PLA2581-EVIDENCIA-20260815` e valor
   `R$ 123,45`.
6. O backend respondeu HTTP 302 e criou um único registro. A listagem posterior
   mostrou Transferência, origem `BB THIAGO`, destino `C6` e `- / -` para centro
   e plano.
7. O registro temporário funcional, id `97`, foi excluído por POST; a resposta
   foi HTTP 302. Uma segunda captura visual controlada usou o id `98`, também
   excluído após a evidência. As listagens posteriores não apresentaram os
   documentos. Nenhum dado de evidência ficou ativo no staging.

## Evidências visuais

- `docs/evidencias/PLA-2581/transferencia-sem-apropriacao-staging-5001.png` -
  formulário real após selecionar Transferência, sem Plano Financeiro e Centro
  de Custo.
- `docs/evidencias/PLA-2581/transferencia-persistida-sem-apropriacao-staging-5001.png` -
  listagem real após POST manipulado, com origem/destino e `- / -` nos vínculos
  indevidos.

## Testes automatizados

Comando focal:

```bash
.venv/bin/python -m unittest tests.test_transferencia_sem_apropriacao
```

Cobertura: criação sem apropriação, requisição manipulada, registro único,
origem/destino, contas distintas e válidas para a empresa, edição de legado,
regressão de Entrada/Saída e controle visual dos formulários.

## Risco residual

Baixo. A alteração é focal e não muda o banco. A ausência de uma funcionalidade
de cópia de movimentação foi registrada como inaplicabilidade, sem expansão de
escopo. Produção não foi alterada.
