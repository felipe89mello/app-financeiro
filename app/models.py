import enum
from datetime import date

from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, Enum, UniqueConstraint
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
    # Categoria "arquivada" (ativa=False) some da lista de opções ao lançar algo
    # novo, mas continua existindo normalmente — o histórico dela não muda.
    ativa = Column(Boolean, nullable=False, default=True)

    transacoes = relationship("Transacao", back_populates="categoria")


class FormaPagamento(Base):
    __tablename__ = "formas_pagamento"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, nullable=False)


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

    # Compra parcelada (opcional): quando o lançamento faz parte de uma série
    # gerada automaticamente (ex: 12x), todas as parcelas compartilham o
    # mesmo parcela_grupo — isso permite mostrar "3/12" na tela e, se
    # preciso, excluir a série inteira de uma vez.
    parcela_grupo = Column(String, nullable=True, index=True)
    parcela_numero = Column(Integer, nullable=True)
    parcela_total = Column(Integer, nullable=True)


class ContaFixa(Base):
    """Um lembrete de conta mensal recorrente (aluguel, internet, etc.) —
    o cadastro em si, não o status de um mês específico."""
    __tablename__ = "contas_fixas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    valor_esperado = Column(Float, nullable=True)
    dia_vencimento = Column(Integer, nullable=True)  # 1–31, opcional
    ativa = Column(Boolean, nullable=False, default=True)

    pagamentos = relationship(
        "ContaFixaPagamento", back_populates="conta_fixa", cascade="all, delete-orphan"
    )


class ContaFixaPagamento(Base):
    """Se uma conta fixa foi marcada como paga num mês/ano específico."""
    __tablename__ = "contas_fixas_pagamentos"
    __table_args__ = (
        UniqueConstraint("conta_fixa_id", "ano", "mes", name="uq_conta_fixa_ano_mes"),
    )

    id = Column(Integer, primary_key=True, index=True)
    conta_fixa_id = Column(Integer, ForeignKey("contas_fixas.id"), nullable=False)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    pago = Column(Boolean, nullable=False, default=False)
    data_pagamento = Column(Date, nullable=True)

    conta_fixa = relationship("ContaFixa", back_populates="pagamentos")
