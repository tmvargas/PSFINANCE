BEGIN;

CREATE TABLE cliente (
    id_cliente SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    nome VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(18),
    endereco VARCHAR(255),
    bairro VARCHAR(120),
    cep VARCHAR(9),
    id_cidade INTEGER REFERENCES cidade(id_cidade),
    whats VARCHAR(30),
    fone VARCHAR(30),
    email VARCHAR(255),
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_cliente_nome_ativo ON cliente (nome) WHERE deleted = FALSE;

COMMIT;
