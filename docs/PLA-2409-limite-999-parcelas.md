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
| Limite válido | novo título, valor `999,00`, 999 parcelas | Um título e 999 parcelas; numeração 1 a 999; soma `999,00` | Aprovado |
| Acima do limite | novo título com 1000 parcelas | Mensagem de validação e nenhuma persistência | Aprovado |
| Regressão focal | exclusão de parcela com e sem baixa | Preservar o bloqueio de parcela baixada e a exclusão da parcela livre | Aprovado |

## Validação local

```bash
.venv/bin/python -m compileall -q financeiro src database.py models.py
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

Resultado: compilação sem erros e 6 testes aprovados. O único aviso foi a
depreciação já existente de `datetime.utcnow()` no SQLAlchemy, sem falha.

## Riscos e pendências

- Risco baixo: gerar 999 registros exige mais processamento que o limite
  anterior, mas o teste focal concluiu a criação e validou a soma das parcelas.
- Pendente antes da entrega: push da branch, PR com base `staging`, integração,
  deploy de `staging` e validação do gate corporativo na porta `5001`.
- Não requer banco, migration, nova variável de ambiente ou produção.
