BEGIN;

CREATE TABLE openfinance_conexao (
    id_conexao SERIAL PRIMARY KEY, uuid VARCHAR(36) NOT NULL UNIQUE,
    provedor VARCHAR(40) NOT NULL DEFAULT 'santander', nome VARCHAR(120) NOT NULL,
    ambiente VARCHAR(20) NOT NULL DEFAULT 'sandbox', client_id VARCHAR(255),
    secret_env VARCHAR(120), consentimento_id VARCHAR(255),
    status VARCHAR(30) NOT NULL DEFAULT 'configuracao_pendente',
    sincronizado_em TIMESTAMP, erro_ultima_sincronizacao VARCHAR(1000),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE openfinance_conta (
    id_openfinance_conta SERIAL PRIMARY KEY, uuid VARCHAR(36) NOT NULL UNIQUE,
    id_conexao INTEGER NOT NULL REFERENCES openfinance_conexao(id_conexao),
    id_conta INTEGER REFERENCES conta(id_conta),
    id_centro_custo INTEGER REFERENCES centro_custo(id_centro_custo),
    external_id VARCHAR(255) NOT NULL, tipo VARCHAR(30) NOT NULL,
    nome VARCHAR(255) NOT NULL, moeda VARCHAR(3) NOT NULL DEFAULT 'BRL',
    ativa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_openfinance_conta_external UNIQUE (id_conexao, external_id)
);

CREATE TABLE openfinance_transacao (
    id_transacao SERIAL PRIMARY KEY, uuid VARCHAR(36) NOT NULL UNIQUE,
    id_openfinance_conta INTEGER NOT NULL REFERENCES openfinance_conta(id_openfinance_conta),
    external_id VARCHAR(255) NOT NULL, data DATE NOT NULL,
    descricao VARCHAR(1000) NOT NULL, valor NUMERIC(15,2) NOT NULL,
    natureza VARCHAR(10) NOT NULL CHECK (natureza IN ('entrada', 'saida')),
    id_plano INTEGER REFERENCES plano_de_contas(id_plano),
    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
    id_movimentacao INTEGER REFERENCES movimentacao_conta(id_movimentacao),
    processada_em TIMESTAMP, payload_hash VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_openfinance_transacao_external UNIQUE (id_openfinance_conta, external_id)
);

CREATE INDEX ix_openfinance_transacao_pendente
    ON openfinance_transacao (id_openfinance_conta, data) WHERE status = 'pendente' AND deleted = FALSE;
COMMIT;
