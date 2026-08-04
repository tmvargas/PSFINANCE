-- PLA-1235 - Cadastros Empresa e Centro de Custo PSFINANCE
-- Script preparado para staging. Nao executar em producao sem autorizacao
-- expressa de Thiago e pacote de producao aprovado.

CREATE TABLE IF NOT EXISTS empresa (
    id_empresa SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    codigo VARCHAR(50) NOT NULL,
    nome VARCHAR(255) NOT NULL,
    tipo_empresa VARCHAR(20) NOT NULL,
    codigo_externo VARCHAR(100),
    observacao VARCHAR(1000),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT ck_empresa_tipo
        CHECK (tipo_empresa IN ('EMPRESA', 'SPE', 'SCP'))
);

CREATE INDEX IF NOT EXISTS ix_empresa_codigo_ativo
    ON empresa (codigo)
    WHERE deleted = FALSE;

CREATE TABLE IF NOT EXISTS centro_custo (
    id_centro_custo SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,
    id_empresa INTEGER NOT NULL REFERENCES empresa (id_empresa),
    codigo VARCHAR(50) NOT NULL,
    nome VARCHAR(255) NOT NULL,
    codigo_externo VARCHAR(100),
    observacao VARCHAR(1000),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_centro_custo_empresa_codigo_ativo
    ON centro_custo (id_empresa, codigo)
    WHERE deleted = FALSE;

CREATE INDEX IF NOT EXISTS ix_centro_custo_empresa_ativo
    ON centro_custo (id_empresa)
    WHERE deleted = FALSE;

ALTER TABLE titulo
    ADD COLUMN IF NOT EXISTS id_empresa INTEGER REFERENCES empresa (id_empresa);

ALTER TABLE titulo
    ADD COLUMN IF NOT EXISTS id_centro_custo INTEGER REFERENCES centro_custo (id_centro_custo);

CREATE INDEX IF NOT EXISTS ix_titulo_empresa_centro_custo
    ON titulo (id_empresa, id_centro_custo)
    WHERE deleted = FALSE;

ALTER TABLE movimentacao_conta
    ADD COLUMN IF NOT EXISTS id_empresa INTEGER REFERENCES empresa (id_empresa);

ALTER TABLE movimentacao_conta
    ADD COLUMN IF NOT EXISTS id_centro_custo INTEGER REFERENCES centro_custo (id_centro_custo);

CREATE INDEX IF NOT EXISTS ix_movimentacao_empresa_centro_custo
    ON movimentacao_conta (id_empresa, id_centro_custo)
    WHERE deleted = FALSE;
