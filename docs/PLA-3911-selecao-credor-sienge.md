# PLA-3911 — Seleção de credor conforme o Sienge

## Briefing e referência

- Resultado: substituir a combobox por campo com lupa, busca por digitação +
  `Tab`, escolha quando houver múltiplos resultados e retorno automático do
  cadastro auxiliar.
- Projeto/cliente/ambiente: PSFINANCE / PlanSmart / staging.
- Camadas: templates e JavaScript do título/credor, além da rota existente de
  cadastro de credor; sem mudança de schema.
- Referência funcional real: relato de Thiago no comentário
  `9fd7233a-9de2-42ac-bd9e-e839a36b597b` da PLA-747. Não foi anexada captura
  visual do Sienge ao comentário ou à PLA-3911.
- Referência anterior do PSFINANCE:
  `docs/evidencias/PLA-743/busca-credor-desktop.png` e
  `docs/evidencias/PLA-743/busca-credor-mobile.png`, nas quais a combobox ainda
  coexistia com a lupa.

## Resultado implementado

- Um único campo textual exibe o credor; `id_credor` permanece oculto para
  preservar o contrato e a validação do backend.
- Ao sair com `Tab`, resultado único é selecionado automaticamente. Zero ou
  múltiplos resultados abrem a mesma modal, respectivamente com orientação ou
  lista de escolha.
- A janela nomeada `psfinanceCadastroCredor` é reutilizada quando já está
  aberta. Após o cadastro, a janela envia ID/nome à origem, seleciona o novo
  credor e fecha.
- O restante do formulário do título não foi alterado.

## Validação sem escrita

- Teste focal de contrato: `python3 tests/test_pla3911_selecao_credor.py` — 3
  testes aprovados.
- `financeiro/routes_credor.py` compilado sem erro.
- Templates `titulo_form.html` e `credor_form.html` analisados pelo parser
  Jinja sem erro.
- Jornada Playwright no staging real: resultado único `Amico Celular`
  selecionado por digitação + `Tab`; zero resultados orientado; 15 resultados
  exibidos para escolha; segundo clique em novo credor manteve somente uma
  janela; desktop e móvel sem corte horizontal.
- Healthcheck `127.0.0.1:5104/health` e gate
  `127.0.0.1:5001/gate`: HTTP 200 após o deploy.
- Leitura PostgreSQL em transação `READ ONLY`: 15 credores, 57 títulos e 349
  parcelas ativos antes da futura jornada de persistência.

## Evidências

- `docs/evidencias/PLA-3911/credor-zero-resultados-desktop.png`;
- `docs/evidencias/PLA-3911/credor-multiplos-resultados-desktop.png`;
- `docs/evidencias/PLA-3911/selecao-credor-mobile.png`;
- `scripts/pla3911_capture_selecao_credor.py` reproduz a jornada somente leitura.

## Git e staging

- Branch: `feature/PLA-3911-selecao-credor-sienge`.
- Commit funcional: `80ddc105e31acef4924417d5811cabe00d60d554`.
- PR: `https://github.com/tmvargas/PSFINANCE/pull/112`, base `staging`.
- Merge/deploy de staging: `d14c33b2d54dfc6adf6f590a19588aae484dfd24`.

## Pendência autorizativa

A persistência real do novo credor e do título ainda não foi executada. Ela
depende de autorização expressa para criar registros temporários no PostgreSQL
de staging e, após validar a leitura posterior, marcá-los como excluídos para
restaurar as contagens iniciais. `main` e produção não foram tocadas.
