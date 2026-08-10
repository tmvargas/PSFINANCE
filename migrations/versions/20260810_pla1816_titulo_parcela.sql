BEGIN;

CREATE TABLE IF NOT EXISTS titulo_parcela (
    id_parcela SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    id_titulo INTEGER NOT NULL REFERENCES titulo(id_titulo),
    numero_parcela INTEGER NOT NULL,
    vencimento DATE NOT NULL,
    valor NUMERIC(15, 2) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT ck_titulo_parcela_numero_pos CHECK (numero_parcela >= 1),
    CONSTRAINT ck_titulo_parcela_valor_pos CHECK (valor > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_titulo_parcela_numero_ativo
    ON titulo_parcela (id_titulo, numero_parcela)
    WHERE deleted = FALSE;

CREATE INDEX IF NOT EXISTS ix_titulo_parcela_titulo_vencimento
    ON titulo_parcela (id_titulo, vencimento)
    WHERE deleted = FALSE;

COMMIT;
