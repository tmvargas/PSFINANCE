# models.py
import uuid  # para sincronização futura
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class TimestampMixin:
    """Campos comuns para auditoria e sincronização futura."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)


# ---------------------------------------------------------------------
# DOCUMENTO (AV / CT / REC / NF)
# ---------------------------------------------------------------------
class Documento(Base, TimestampMixin):
    __tablename__ = "documento"

    id_doc = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)

    # Código curto (AV, CT, REC, NF)
    tipo_doc = Column(String(10), nullable=False, unique=True)

    # Nome descritivo
    nome_doc = Column(String(255), nullable=False)

    # relacionamentos
    titulos = relationship("Titulo", back_populates="documento")
    movimentacoes = relationship("MovimentacaoConta", back_populates="documento")

    def __repr__(self):
        return f"<Documento {self.tipo_doc} - {self.nome_doc}>"


# ---------------------------------------------------------------------
# PLANO DE CONTAS
# ---------------------------------------------------------------------
class PlanoDeContas(Base, TimestampMixin):
    __tablename__ = "plano_de_contas"

    id_plano = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)

    cod_estrutural = Column(String(50), nullable=False)
    nome_conta = Column(String(255), nullable=False)
    # 'totalizadora' ou 'analitica'
    tipo = Column(String(20), nullable=False)

    titulos = relationship("Titulo", back_populates="plano")
    movimentos = relationship("MovimentacaoConta", back_populates="plano")

    def __repr__(self):
        return f"<PlanoDeContas {self.cod_estrutural} - {self.nome_conta}>"


# ---------------------------------------------------------------------
# CREDOR
# ---------------------------------------------------------------------
class Credor(Base, TimestampMixin):
    __tablename__ = "credor"

    id_credor = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)

    nome = Column(String(255), nullable=False)

    titulos = relationship("Titulo", back_populates="credor")

    def __repr__(self):
        return f"<Credor {self.nome}>"


# ---------------------------------------------------------------------
# CONTA (CAIXA/BANCO)
# ---------------------------------------------------------------------
class Conta(Base, TimestampMixin):
    __tablename__ = "conta"

    id_conta = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)

    descricao = Column(String(255), nullable=False)
    id_banco = Column(String(50), nullable=True)
    # 'corrente', 'aplicacao', 'caixa'
    tipo = Column(String(20), nullable=False)

    saldo_inicial = Column(Numeric(15, 2), default=0, nullable=False)
    data_saldo_inicial = Column(Date, nullable=True)

    baixas = relationship("Baixa", back_populates="conta")

    movimentos_origem = relationship(
        "MovimentacaoConta",
        back_populates="conta_origem",
        foreign_keys="MovimentacaoConta.id_conta_origem",
    )
    movimentos_destino = relationship(
        "MovimentacaoConta",
        back_populates="conta_destino",
        foreign_keys="MovimentacaoConta.id_conta_destino",
    )

    # ---- composição de saldo ----
    @property
    def saldo_entradas(self):
        return sum(
            float(m.valor or 0)
            for m in self.movimentos_destino
            if m.tipo == "E" and not m.deleted
        )

    @property
    def saldo_saidas(self):
        return sum(
            float(m.valor or 0)
            for m in self.movimentos_origem
            if m.tipo == "S" and not m.deleted
        )

    @property
    def saldo_transf_entra(self):
        return sum(
            float(m.valor or 0)
            for m in self.movimentos_destino
            if m.tipo == "T" and not m.deleted
        )

    @property
    def saldo_transf_sai(self):
        return sum(
            float(m.valor or 0)
            for m in self.movimentos_origem
            if m.tipo == "T" and not m.deleted
        )

    @property
    def saldo_baixas(self):
        return sum(
            float(b.valor_baixa or 0)
            for b in self.baixas
            if not b.deleted
        )

    @property
    def saldo_atual(self):
        return (
            float(self.saldo_inicial or 0)
            + self.saldo_entradas
            + self.saldo_transf_entra
            - self.saldo_saidas
            - self.saldo_transf_sai
            - self.saldo_baixas
        )

    def __repr__(self):
        return f"<Conta {self.descricao} ({self.tipo})>"


# ---------------------------------------------------------------------
# TÍTULO (PROVISÃO)
# ---------------------------------------------------------------------
class Titulo(Base, TimestampMixin):
    __tablename__ = "titulo"

    id_titulo = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)

    # FK para Documento (AV/CT/REC/NF)
    id_doc = Column(Integer, ForeignKey("documento.id_doc"), nullable=False)

    nr_documento = Column(String(50), nullable=False)

    id_credor = Column(Integer, ForeignKey("credor.id_credor"), nullable=False)
    id_plano = Column(Integer, ForeignKey("plano_de_contas.id_plano"), nullable=False)

    valor = Column(Numeric(15, 2), nullable=False)

    emissao = Column(Date, nullable=False)
    vencimento = Column(Date, nullable=False)
    observacao = Column(String(1000), nullable=True)

    documento = relationship("Documento", back_populates="titulos")
    credor = relationship("Credor", back_populates="titulos")
    plano = relationship("PlanoDeContas", back_populates="titulos")
    baixas = relationship("Baixa", back_populates="titulo")

    anexos = relationship(
        "TituloAnexo",
        back_populates="titulo",
        cascade="all, delete-orphan",
    )

    @property
    def total_baixado(self):
        return float(
            sum(float(b.valor_baixa or 0) for b in self.baixas if not getattr(b, "deleted", False))
        )

    @property
    def saldo_aberto(self):
        return float(self.valor or 0) - self.total_baixado

    def __repr__(self):
        status = "QUITADO" if self.saldo_aberto <= 0 else "EM ABERTO"
        return f"<Titulo id={self.id_titulo} - {status}>"


class TituloAnexo(Base, TimestampMixin):
    __tablename__ = "titulo_anexo"

    id_anexo = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)

    id_titulo = Column(Integer, ForeignKey("titulo.id_titulo"), nullable=False)

    nome_arquivo = Column(String(255), nullable=False)
    caminho_arquivo = Column(String(255), nullable=False)

    titulo = relationship("Titulo", back_populates="anexos")

    def __repr__(self):
        return f"<TituloAnexo {self.nome_arquivo} (titulo_id={self.id_titulo})>"


# ---------------------------------------------------------------------
# BAIXA DE TÍTULO
# ---------------------------------------------------------------------
class Baixa(Base, TimestampMixin):
    __tablename__ = "baixa"

    id_baixa = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)

    data = Column(Date, nullable=False)

    id_conta = Column(Integer, ForeignKey("conta.id_conta"), nullable=False)
    id_titulo = Column(Integer, ForeignKey("titulo.id_titulo"), nullable=False)

    valor_baixa = Column(Numeric(15, 2), nullable=False)

    conciliado = Column(Boolean, default=False, nullable=False)

    conta = relationship("Conta", back_populates="baixas")
    titulo = relationship("Titulo", back_populates="baixas")

    def __repr__(self):
        return f"<Baixa {self.id_baixa} em {self.data} - R$ {float(self.valor_baixa or 0):.2f}>"


# ---------------------------------------------------------------------
# MOVIMENTAÇÃO DE CONTA (ENTRADA/SAÍDA/TRANSFERÊNCIA)
# ---------------------------------------------------------------------
class MovimentacaoConta(Base, TimestampMixin):
    __tablename__ = "movimentacao_conta"

    id_movimentacao = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)

    data = Column(Date, nullable=False)

    # E = entrada, S = saída, T = transferência
    tipo = Column(String(1), nullable=False)

    # FK para Documento (AV/CT/REC/NF)
    id_doc = Column(Integer, ForeignKey("documento.id_doc"), nullable=False)

    nr_documento = Column(String(30), nullable=False, default="NA")

    descricao = Column(String, nullable=True)
    valor = Column(Numeric(15, 2), nullable=False)

    id_conta_origem = Column(Integer, ForeignKey("conta.id_conta"), nullable=True)
    id_conta_destino = Column(Integer, ForeignKey("conta.id_conta"), nullable=True)

    conta_origem = relationship(
        "Conta",
        back_populates="movimentos_origem",
        foreign_keys=[id_conta_origem],
    )
    conta_destino = relationship(
        "Conta",
        back_populates="movimentos_destino",
        foreign_keys=[id_conta_destino],
    )

    # Apropriação no plano financeiro (somente E/S)
    id_plano = Column(Integer, ForeignKey("plano_de_contas.id_plano"), nullable=True)
    plano = relationship("PlanoDeContas", back_populates="movimentos")

    documento = relationship("Documento", back_populates="movimentacoes")

    conciliado = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<MovimentacaoConta {self.tipo} id={self.id_movimentacao} R$ {float(self.valor or 0):.2f}>"
