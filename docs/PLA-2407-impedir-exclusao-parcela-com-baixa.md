# PLA-2407 - Impedir exclusão de parcela com baixa

## Objetivo

Preservar a integridade do vínculo entre parcelas e baixas, impedindo a
exclusão lógica de uma parcela que possua baixa ativa.

## Regra de negócio

- Parcela com baixa ativa vinculada por `baixa.id_parcela` não pode ser
  excluída.
- A validação do backend é obrigatória e protege inclusive contra requisição
  POST manipulada.
- Na tela, a lixeira da parcela com baixa fica desabilitada e a linha orienta
  `Possui baixa. Exclua a baixa primeiro para liberar a exclusão da parcela.`.
- Parcela sem baixa mantém o fluxo existente de exclusão lógica.
- Baixa excluída logicamente (`deleted = true`) não bloqueia a parcela.

## Gate de arquitetura

- Skill consultada: `plansmart-projeto-psfinance` em conjunto com
  `plansmart-governanca-desenvolvimento` e
  `plansmart-projeto-vps-sistemas`.
- Controller: `financeiro/routes_titulos.py` consulta as baixas ativas,
  rejeita a exclusão e prepara o estado da interface.
- Template: `templates/titulo_parcelas_form.html` comunica e desabilita a ação
  indisponível.
- Teste: `tests/test_parcela_exclusao_baixa.py` comprova backend, interface e
  preservação do fluxo sem baixa.
- Banco: sem migration ou mudança estrutural.

## Matriz de validação funcional

| Caso | Resultado esperado | Resultado local |
| --- | --- | --- |
| Parcela com baixa ativa; lixeira na tela | Botão desabilitado e texto `Possui baixa` | Aprovado |
| Parcela com baixa ativa; POST manipulado | Exclusão rejeitada e parcela preservada | Aprovado |
| Parcela sem baixa ativa | Exclusão lógica permanece disponível | Aprovado |
| Baixa não conciliada excluída antes da parcela | Baixa é excluída e a parcela passa a aceitar exclusão | Aprovado |
| Baixa conciliada | Exclusão da baixa é rejeitada e a parcela permanece protegida | Aprovado |

## Validação local

```bash
.venv/bin/python -m py_compile models.py financeiro/routes_titulos.py src/app.py tests/test_parcela_exclusao_baixa.py
.venv/bin/python -m unittest -v tests/test_parcela_exclusao_baixa.py
git diff --check
```

Resultado: cinco testes aprovados, compilação aprovada e nenhuma inconsistência
de whitespace encontrada.

## Validação no staging real

- Branch da VPS: `staging`.
- Commit inicialmente validado: `4e14c01cc956cdbf3697b387ecb52620fd590c68`.
- Banco: PostgreSQL de staging; nenhuma migration necessária.
- Serviços `psfinance-staging` e `psfinance-staging-gate`: ativos.
- `GET http://127.0.0.1:5001/health`: HTTP 200, `status=healthy`, branch
  `staging` e commit coerente com `origin/staging`.
- `GET /financeiro/titulos/1/parcelas` na porta `5001`: HTTP 200, com lixeira
  desabilitada e texto `Possui baixa` na parcela vinculada a baixa.
- POST manipulado solicitando a exclusão dessa parcela: resposta final HTTP
  200 com a mensagem `porque ela possui baixa`; leitura posterior comprovou a
  parcela preservada.
- Logs dos dois serviços após o deploy: sem entradas de nível warning ou
  superior relacionadas à validação.

### Revalidação após revisão executiva

- Commit da branch da tarefa: `664307ae1ed41121714681467be5540041dcc5b7`.
- Commit de `staging` publicado: `22fa86f57db35a9d06de2e84f7f91a9b0ab8bec2`.
- Cinco testes focais aprovados localmente e na VPS, incluindo a jornada de
  exclusão da baixa não conciliada seguida da exclusão da parcela e a proteção
  persistente de baixa conciliada.
- `GET http://127.0.0.1:5001/health`: HTTP 200, PostgreSQL, branch `staging` e
  commit `22fa86f57db35a9d06de2e84f7f91a9b0ab8bec2`.
- `GET http://127.0.0.1:5001/gate`: HTTP 200 e aplicação interna saudável.
- Serviços `psfinance-staging` e `psfinance-staging-gate`: ativos, sem warnings
  nos logs após o restart.

## Gate visual

| Item do pedido | Referência | Resultado |
| --- | --- | --- |
| Impedir a ação na parcela com baixa | Tela real existente da guia Parcelas | Lixeira preservada na mesma posição, mas desabilitada |
| Comunicar o motivo | Regra PLA-2407 | Texto `Possui baixa` exibido sob a ação |
| Preservar o layout | Tela real publicada | Menu, topo, campos, botões e ordem existentes preservados |

Evidência:

- `docs/evidencias/PLA-2407/parcela-com-baixa-bloqueada-5001.png` - Screenshot
  da tela real publicada na porta `5001`, mostrando a lixeira desabilitada e o
  texto `Possui baixa` sem alteração estrutural do layout.
- `docs/evidencias/PLA-2407/parcela-com-baixa-orientacao-revisao-5001.png` -
  Screenshot posterior à revisão executiva, comprovando na porta `5001` a
  orientação explícita para excluir a baixa primeiro.

## Riscos e pendências

- Risco residual baixo: a regra depende do vínculo `baixa.id_parcela`, já
  estabelecido pelo fluxo de baixas por parcela. Baixas legadas sem parcela não
  identificam uma parcela específica e, portanto, não bloqueiam individualmente
  a exclusão.
- Produção não faz parte desta entrega e exige Pacote de Produção e autorização
  expressa de Thiago.
