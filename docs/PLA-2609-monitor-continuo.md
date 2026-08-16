# PLA-2609 — Monitor contínuo dos travamentos do PSFINANCE

## Objetivo

Manter uma coleta somente leitura por até 24 horas, ou até a captura de uma
nova ocorrência, para correlacionar indisponibilidade percebida com aplicação,
proxy, sistema operacional e PostgreSQL de staging.

## Escopo técnico

O script `scripts/monitor_pla2609_readonly.sh` coleta a cada 120 segundos:

- timestamp UTC, PID e número da amostra;
- PID, workers, CPU, memória, disco, listeners e reinícios dos serviços;
- conexões, esperas e locks agregados do PostgreSQL;
- HTTP e tempos de `/health`, `/gate`, Home, Extrato filtrado, Títulos e
  Análise pela porta corporativa `5001`;
- journal e logs do Nginx sanitizados.

O arquivo de estado informa `status`, PID, início, atualização, prazo final,
amostra e caminho do log. O log é rotacionado ao atingir 10 MiB por padrão,
mantendo somente o arquivo atual e uma geração anterior.

## Limites de segurança

- Nenhuma escrita é realizada no PostgreSQL.
- Nenhuma migration, seed, carga ou teste persistente é executado.
- Nenhum serviço da aplicação é reiniciado.
- Nenhuma ação é realizada em produção ou na branch `main`.
- O monitor termina automaticamente após 86.400 segundos.

## Validação esperada

1. `bash -n scripts/monitor_pla2609_readonly.sh` sem erro.
2. Arquivo de estado com `status=running`, PID existente e deadline em UTC.
3. Duas amostras consecutivas separadas pelo intervalo configurado.
4. Seis rotas com código HTTP e tempos registrados.
5. Log e estado sem IP, usuário, User-Agent, credencial ou valor de banco.
