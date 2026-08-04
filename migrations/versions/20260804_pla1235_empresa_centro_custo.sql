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
