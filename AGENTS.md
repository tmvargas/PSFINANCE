# Instrucoes para agentes - PSCONTROL

Este arquivo vale para todo o repositorio `PSCONTROL`.

## Contexto

PSCONTROL e um projeto PlanSmart para controle interno, acompanhamento operacional, gestao de rotinas, indicadores, usuarios e processos.

## Regras obrigatorias

- Responder sempre em portugues do Brasil.
- Nao trabalhar direto na `main`.
- Nao expor tokens, secrets, dados de clientes ou documentos privados.
- Nao duplicar regras de negocio sem necessidade.
- Documentar qualquer decisao relevante em `docs/decisoes.md`.
- Quando Thiago pedir "consulta com cadastro em popup", seguir o padrão registrado em `docs/decisoes.md`: modal sólido acima da navegação, busca sem sobreposição, janela auxiliar sem menu/header e retorno automático do registro ao formulário chamador.

## Padrao de entrega

Ao entregar alteracao de desenvolvimento, informar:

1. Qual demanda foi atendida.
2. Quais arquivos foram alterados.
3. Qual regra ou decisao foi aplicada.
4. Como testar.
5. Se precisa banco, variavel de ambiente, VPS ou deploy.

## Infraestrutura

- VPS planejada: `vps69143.publiccloud.com.br` (`191.252.93.136`).
- Stack tecnica ainda pendente.
