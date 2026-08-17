# PLA-2641 - Recorrência dos filtros da Consulta de Títulos

## Falha reproduzida e causa técnica

A entrega anterior classificava a situação pelo saldo global do título. Na
consulta mensal, isso mantinha em `Em aberto` uma parcela integralmente quitada
no mês sempre que o mesmo título possuía parcelas futuras; por consequência,
`Baixada` podia ficar vazia na jornada real, embora a tela exibisse valores
pagos no período.

A correção presente no `staging` `334a3d9767b3f401bfd88c39be1b08f4c38f8ddf`
calcula a situação pelo saldo das parcelas exibidas no mês, depois de mês, ano
e empresa já terem limitado o conjunto e antes da montagem das linhas e dos
totais. A interface e os indicadores mensais passam a usar a mesma regra.

## Jornada real autenticada

Validação em 17/08/2026 pela interface real, acessada por túnel SSH autenticado
até o Gunicorn de staging (`127.0.0.1:5104`). Em cada caso, o script selecionou
os campos e clicou no botão `Filtrar`; a URL final, a seleção devolvida pela
tela, o tempo e os indicadores foram lidos do DOM (Modelo de Objetos do
Documento). Nenhuma escrita em banco foi realizada.

| Empresa | Mês/ano | Situação enviada | Situação exibida | Títulos | Valor títulos | Parcela mês | Pago mês | Não pago mês | Tempo |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 - THIAGO | 08/2026 | `todas` | Todas | 9 | R$ 88.924,81 | R$ 4.875,89 | R$ 2.892,25 | R$ 1.983,64 | 139 ms |
| 1 - THIAGO | 08/2026 | `em_aberto` | Em aberto | 6 | R$ 74.305,55 | R$ 1.983,64 | R$ 0,00 | R$ 1.983,64 | 110 ms |
| 1 - THIAGO | 08/2026 | `baixada` | Baixada | 3 | R$ 14.619,26 | R$ 2.892,25 | R$ 2.892,25 | R$ 0,00 | 96 ms |
| 1 - THIAGO | 08/2026 | `invalida` | Todas | 9 | R$ 88.924,81 | R$ 4.875,89 | R$ 2.892,25 | R$ 1.983,64 | 83 ms |
| Todas | 08/2026 | `todas` | Todas | 10 | R$ 295.361,27 | R$ 6.024,41 | R$ 4.040,77 | R$ 1.983,64 | 100 ms |
| 1 - THIAGO | 07/2026 | `todas` | Todas | 3 | R$ 75.797,50 | R$ 2.696,54 | R$ 0,00 | R$ 2.696,54 | 98 ms |
| 1 - THIAGO | 08/2025 | `todas` | Todas | 0 | R$ 0,00 | R$ 0,00 | R$ 0,00 | R$ 0,00 | 88 ms |

Parâmetros completos e resultados estruturados estão em
`docs/evidencias/PLA-2641/jornada-real.json`. O host local `15104` registrado
nesse arquivo é apenas a ponta do túnel SSH; o destino efetivo foi o staging na
VPS, sem exposição pública adicional.

### Coerência dos conjuntos e totais

- `Todas = Em aberto + Baixada`: 9 = 6 + 3.
- Valor dos títulos: R$ 88.924,81 = R$ 74.305,55 + R$ 14.619,26.
- Parcela do mês: R$ 4.875,89 = R$ 1.983,64 + R$ 2.892,25.
- Pago no mês: R$ 2.892,25 = R$ 0,00 + R$ 2.892,25.
- Não pago no mês: R$ 1.983,64 = R$ 1.983,64 + R$ 0,00.
- Empresa, mês e ano alteraram efetivamente os conjuntos; o parâmetro inválido
  foi normalizado para `Todas` e reproduziu exatamente seu conjunto e totais.

## Evidência visual

- `docs/evidencias/PLA-2641/consulta-titulos-todas-staging.png` - seleção
  `Todas`, 9 títulos e totais correspondentes.
- `docs/evidencias/PLA-2641/consulta-titulos-em-aberto-staging.png` - seleção
  `Em aberto`, 6 títulos e totais correspondentes.
- `docs/evidencias/PLA-2641/consulta-titulos-baixada-staging.png` - seleção
  `Baixada`, 3 títulos e totais correspondentes.
- `docs/evidencias/PLA-2641/consulta-titulos-invalida-staging.png` - parâmetro
  inválido normalizado visualmente para `Todas`.

## Separação entre massa real e testes focais

A massa real de agosto/2026 comprova títulos parcelados com parcelas mensais em
aberto e integralmente baixadas, títulos legados simples, múltiplas empresas e
períodos com e sem registros. Ela também comprova a alteração dos totais e a
partição sem interseção entre `Em aberto` e `Baixada`.

Os cenários abaixo permanecem deliberadamente focais, pois criar ou modificar
dados de staging exigiria autorização expressa de Thiago:

| Cenário focal | Evidência automatizada |
| --- | --- |
| baixa parcial | saldo positivo permanece `Em aberto` |
| múltiplas baixas ativas | valores são somados antes da classificação |
| baixa excluída | não reduz o saldo |
| parcela excluída | não compõe o total ativo |
| todas as parcelas excluídas | saldo ativo zero |
| título simples sem parcelas | usa o valor do título como fallback |
| título parcelado com saldo futuro | parcela do mês quitada fica `Baixada` |

O arquivo `tests/test_filtro_situacao_titulos.py` executou 10 testes com
resultado `OK`. Compilação de `financeiro` e `tests` e `git diff --check`
também foram aprovados.

## Rastreabilidade do staging

- Branch funcional já integrada: `fix/PLA-2639-situacao-saldo-mensal`.
- Commit funcional: `7de976c136332f8b73dcecc7d6e68fe9cece0bca`.
- Commit servido e `origin/staging`: `334a3d9767b3f401bfd88c39be1b08f4c38f8ddf`.
- VPS: branch `staging`, árvore limpa e commit igual ao remoto.
- Serviço: `psfinance-staging.service` ativo, Gunicorn em `127.0.0.1:5104`.
- Porta corporativa `5001`: `/` HTTP 200 em 43 ms; `/gate` HTTP 200 em 3 ms.
- Logs após reinício: workers iniciados sem erro de aplicação ou banco.
- Automação reproduzível: `scripts/pla2641_capture_jornada.js`.

## Escopo, risco e prevenção

Não houve alteração de banco, migration, variável de ambiente, `main` ou
produção. A prevenção combina cálculo mensal explícito, teste focal do caso que
falhou, partição matemática dos conjuntos na massa real e captura automatizada
da interface. Risco residual baixo: a massa real não contém todos os casos de
exclusão lógica, que permanecem cobertos pelos testes focais sem escrita de
dados.
