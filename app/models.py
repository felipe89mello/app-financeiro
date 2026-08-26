import enum
from datetime import date

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class TipoTransacao(str, enum.Enum):
    despesa = "despesa"
    ganho = "ganho"


class Categoria(Base):
    __tablename__ = "categorias"
    __table_args__ = (
        # "Outros", por exemplo, pode existir como categoria de despesa E como
        # fonte de ganho ao mesmo tempo — o que não pode repetir é o par (nome, tipo).
        UniqueConstraint("nome", "tipo", name="uq_categoria_nome_tipo"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    tipo = Column(Enum(TipoTransacao), nullable=False, default=TipoTransacao.despesa)

    transacoes = relationship("Transacao", back_populates="categoria")


class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, nullable=False, default=date.today)
    descricao = Column(String, nullable=True)
    valor = Column(Float, nullable=False)
    forma_pagamento = Column(String, nullable=True)
    tipo = Column(Enum(TipoTransacao), nullable=False)

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    categoria = relationship("Categoria", back_populates="transacoes")
