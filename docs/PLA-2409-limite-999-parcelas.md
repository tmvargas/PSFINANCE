# PLA-2409 - Permitir até 999 parcelas por título

## Projeto e objetivo

- Projeto: PSFINANCE.
- Objetivo: ampliar de 120 para 999 a quantidade máxima permitida na criação
  ou cópia de um título.
- Skill específica consultada: `plansmart-projeto-psfinance`.
- Governança consultada: `plansmart-governanca-desenvolvimento` e
  `plansmart-projeto-vps-sistemas`.

## Gate de arquitetura

- Controller Flask: `financeiro/routes_titulos.py` mantém a validação
  obrigatória no backend e define `LIMITE_PARCELAS_TITULO = 999`.
- Template: `templates/titulo_form.html` recebe o limite do controller para o
  atributo `max` e para a prévia JavaScript, evitando duplicação da regra.
- Teste: `tests/test_limite_parcelas_titulo.py` cobre os limites 999 e 1000 e a
  renderização do formulário.
- Banco: sem alteração de model, tabela, constraint ou migration.
- Exceção de arquitetura: nenhuma.

## Regra aplicada

- Quantidade válida: de 1 a 999 parcelas.
- O backend recusa valores acima de 999 mesmo quando a requisição ignora o
  limite do navegador.
- A geração mensal, a divisão exata do valor por centavos e o redirecionamento
  para revisão das parcelas permanecem inalterados.

## Matriz funcional

| Caso | Entrada | Resultado esperado | Resultado local |
| --- | --- | --- | --- |
| Formulário | `GET /financeiro/titulos/novo` | Campo com `max="999"` e prévia limitada a 999 | Aprovado |
| Limite anterior | novo título, valor `999,00`, 120 parcelas | Um título e 120 parcelas, preservando o caso antes aceito | Aprovado |
| Caso informado por Thiago | novo título, valor `999,00`, 180 parcelas | Um título e 180 parcelas; numeração 1 a 180; soma `999,00` | Aprovado |
| Limite válido | novo título, valor `999,00`, 999 parcelas | Um título e 999 parcelas; numeração 1 a 999; soma `999,00` | Aprovado |
| Acima do limite | novo título com 1000 parcelas | Mensagem de validação e nenhuma persistência | Aprovado |
| Cópia | abrir e salvar cópia de título com 180 parcelas | Campo permanece editável com valor 180 e cópia gera 180 parcelas | Aprovado |
| Edição | editar dados gerais de título com 180 parcelas | Campo mostra 180 desabilitado e as 180 parcelas permanecem ativas | Aprovado |
| Regressão focal | exclusão de parcela com e sem baixa | Preservar o bloqueio de parcela baixada e a exclusão da parcela livre | Aprovado |

## Validação local

```bash
.venv/bin/python -m compileall -q financeiro src database.py models.py
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

Resultado após a correção solicitada na revisão: compilação sem erros e `12`
testes do repositório aprovados. Os `7` testes focais incluem casos explícitos
de 120, 180, 999, 1000, cópia e edição. O único aviso foi a
depreciação já existente de `datetime.utcnow()` no SQLAlchemy, sem falha.

- Medição local da criação e consulta de 999 parcelas: `1,880 s`.
- Medição na VPS de staging da criação e consulta de 999 parcelas: `0,232 s`;
  suíte focal completa na VPS: `2,30 s`.
- Evidência visual na porta `5001`: campo preenchido com `180`, atributo
  `max="999"` confirmado pelo navegador e prévia exibindo `180 parcelas`.
- Screenshot: `docs/evidencias/PLA-2409/campo-180-parcelas-staging-5001.png`.

## Riscos e pendências

- Risco baixo: gerar 999 registros exige mais processamento que o limite
  anterior. A medição objetiva do teste focal e a medição no staging estão
  registradas abaixo; a geração continua síncrona e deve ser observada se o
  volume simultâneo crescer.
- Não requer banco, migration, nova variável de ambiente ou produção.

## GitHub e staging

- Branch: `fix/PLA-2409-limite-999-parcelas`.
- Commit da tarefa: `9b9ebc7b6b79cc7a04d2a5978a13bc19fe4730aa`.
- PR: `https://github.com/tmvargas/PSFINANCE/pull/70`, base `staging`.
- Commit de integração inicial em `staging`:
  `c52355f8d10131c617a61022afee1212123f3d0e`.
- VPS: `/opt/plansmart/sistemas/psfinance/staging/repo`, branch `staging`,
  diretório sem alterações locais e HEAD igual ao `origin/staging`.
- Serviços `psfinance-staging` e `psfinance-staging-gate`: ativos.
- Runtime da VPS: Python `3.12`, com os 7 testes focais aprovados.

## Validação na porta 5001

| Verificação | Resultado |
| --- | --- |
| `GET /health` | HTTP 200, `status=healthy`, branch `staging`, commit `c52355f` |
| `GET /gate` | HTTP 200, aplicação interna em `127.0.0.1:5104` aprovada |
| `GET /financeiro/titulos/novo` | HTTP 200, HTML com `max="999"` e `Math.min(999, ...)` |
| `GET /financeiro/titulos` | HTTP 200 |
| Logs após deploy | Sem entradas de nível warning ou superior |

Na primeira chamada imediatamente após o restart, `/health` e `/gate`
retornaram HTTP 502 enquanto os workers Gunicorn inicializavam. A inspeção
confirmou os processos vinculados às portas internas e a repetição após a
inicialização retornou HTTP 200 de forma consistente, sem erro nos logs.

## Recomendação

- Entrega apta para revisão do CEO em staging.
- Produção não faz parte desta tarefa. Qualquer promoção exige Pacote de
  Produção e autorização expressa de Thiago.
