# PLA-2407 - Impedir exclusão de parcela com baixa

## Objetivo

Preservar a integridade do vínculo entre parcelas e baixas, impedindo a
exclusão lógica de uma parcela que possua baixa ativa.

## Regra de negócio

- Parcela com baixa ativa vinculada por `baixa.id_parcela` não pode ser
  excluída.
- A validação do backend é obrigatória e protege inclusive contra requisição
  POST manipulada.
- Na tela, a lixeira da parcela com baixa fica desabilitada e a linha exibe
  `Possui baixa`.
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

## Validação local

```bash
.venv/bin/python -m py_compile models.py financeiro/routes_titulos.py src/app.py tests/test_parcela_exclusao_baixa.py
.venv/bin/python -m unittest -v tests/test_parcela_exclusao_baixa.py
git diff --check
```

Resultado: três testes aprovados, compilação aprovada e nenhuma inconsistência
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

## Riscos e pendências

- Risco residual baixo: a regra depende do vínculo `baixa.id_parcela`, já
  estabelecido pelo fluxo de baixas por parcela. Baixas legadas sem parcela não
  identificam uma parcela específica e, portanto, não bloqueiam individualmente
  a exclusão.
- Produção não faz parte desta entrega e exige Pacote de Produção e autorização
  expressa de Thiago.
