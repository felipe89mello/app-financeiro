from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .models import TipoTransacao


# ---------- Categoria ----------
class CategoriaBase(BaseModel):
    nome: str
    tipo: TipoTransacao


class CategoriaCreate(CategoriaBase):
    pass


class Categoria(CategoriaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ativa: bool = True


class CategoriaUpdate(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[TipoTransacao] = None
    ativa: Optional[bool] = None


# ---------- Forma de Pagamento ----------
class FormaPagamentoBase(BaseModel):
    nome: str


class FormaPagamentoCreate(FormaPagamentoBase):
    pass


class FormaPagamentoUpdate(BaseModel):
    nome: Optional[str] = None


class FormaPagamento(FormaPagamentoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Transação ----------
class TransacaoBase(BaseModel):
    data: date
    descricao: Optional[str] = None
    valor: float
    forma_pagamento: Optional[str] = None
    tipo: TipoTransacao
    categoria_id: int


class TransacaoCreate(TransacaoBase):
    pass


class TransacaoUpdate(BaseModel):
    data: Optional[date] = None
    descricao: Optional[str] = None
    valor: Optional[float] = None
    forma_pagamento: Optional[str] = None
    tipo: Optional[TipoTransacao] = None
    categoria_id: Optional[int] = None


class Transacao(TransacaoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    categoria: Categoria


# ---------- Resumo ----------
class ResumoCategoria(BaseModel):
    categoria_id: int
    categoria: str
    total: float


class ResumoMensal(BaseModel):
    mes: str  # formato "YYYY-MM"
    total_despesas: float
    total_ganhos: float
    saldo: float
    por_categoria: list[ResumoCategoria]
    por_categoria_ganhos: list[ResumoCategoria] = []


# ---------- Balanço Anual ----------
class BalancoMes(BaseModel):
    mes: int
    total_despesas: float
    total_ganhos: float
    saldo: float


class BalancoAnual(BaseModel):
    ano: int
    meses: list[BalancoMes]
    total_despesas_ano: float
    total_ganhos_ano: float
    saldo_total: float
    por_categoria: list[ResumoCategoria] = []
    por_categoria_ganhos: list[ResumoCategoria] = []


# ---------- Conta Fixa (lembrete de conta a pagar) ----------
class ContaFixaBase(BaseModel):
    nome: str
    valor_esperado: Optional[float] = None
    dia_vencimento: Optional[int] = None


class ContaFixaCreate(ContaFixaBase):
    pass


class ContaFixaUpdate(BaseModel):
    nome: Optional[str] = None
    valor_esperado: Optional[float] = None
    dia_vencimento: Optional[int] = None
    ativa: Optional[bool] = None


class ContaFixa(ContaFixaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ativa: bool = True


class ContaFixaComStatus(BaseModel):
    """Como aparece no dashboard de um mês: os dados da conta + se já foi paga."""
    id: int
    nome: str
    valor_esperado: Optional[float] = None
    dia_vencimento: Optional[int] = None
    pago: bool = False
