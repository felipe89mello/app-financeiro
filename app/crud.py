from datetime import date
from calendar import monthrange

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from . import models, schemas


# ---------- Categoria ----------
def criar_categoria(db: Session, categoria: schemas.CategoriaCreate) -> models.Categoria:
    db_categoria = models.Categoria(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


def listar_categorias(db: Session, apenas_ativas: bool = False) -> list[models.Categoria]:
    query = db.query(models.Categoria)
    if apenas_ativas:
        query = query.filter(models.Categoria.ativa == True)  # noqa: E712
    return query.order_by(models.Categoria.nome).all()


def definir_categoria_ativa(db: Session, categoria_id: int, ativa: bool) -> models.Categoria | None:
    categoria = db.get(models.Categoria, categoria_id)
    if not categoria:
        return None
    categoria.ativa = ativa
    db.commit()
    db.refresh(categoria)
    return categoria


def atualizar_categoria(
    db: Session, categoria_id: int, dados: schemas.CategoriaUpdate
) -> models.Categoria | None:
    categoria = db.get(models.Categoria, categoria_id)
    if not categoria:
        return None
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(categoria, campo, valor)
    db.commit()
    db.refresh(categoria)
    return categoria


def contar_transacoes_da_categoria(db: Session, categoria_id: int) -> int:
    return (
        db.query(models.Transacao)
        .filter(models.Transacao.categoria_id == categoria_id)
        .count()
    )


def excluir_categoria(db: Session, categoria_id: int) -> str:
    """Retorna 'ok', 'nao_encontrada' ou 'em_uso' (nesse caso não exclui —
    excluir uma categoria com lançamentos deixaria esses lançamentos "órfãos"
    e quebraria as telas que mostram a categoria de cada um)."""
    categoria = db.get(models.Categoria, categoria_id)
    if not categoria:
        return "nao_encontrada"
    if contar_transacoes_da_categoria(db, categoria_id) > 0:
        return "em_uso"
    db.delete(categoria)
    db.commit()
    return "ok"


# ---------- Forma de Pagamento ----------
def criar_forma_pagamento(db: Session, dados: schemas.FormaPagamentoCreate) -> models.FormaPagamento:
    fp = models.FormaPagamento(**dados.model_dump())
    db.add(fp)
    db.commit()
    db.refresh(fp)
    return fp


def listar_formas_pagamento(db: Session) -> list[models.FormaPagamento]:
    return db.query(models.FormaPagamento).order_by(models.FormaPagamento.nome).all()


def obter_forma_pagamento(db: Session, forma_id: int) -> models.FormaPagamento | None:
    return db.get(models.FormaPagamento, forma_id)


def atualizar_forma_pagamento(
    db: Session, forma_id: int, dados: schemas.FormaPagamentoUpdate
) -> models.FormaPagamento | None:
    fp = db.get(models.FormaPagamento, forma_id)
    if not fp:
        return None
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(fp, campo, valor)
    db.commit()
    db.refresh(fp)
    return fp


def excluir_forma_pagamento(db: Session, forma_id: int) -> bool:
    # Forma de pagamento é só uma lista de sugestões pro formulário — o valor
    # já lançado em cada transação é salvo como texto próprio, então excluir
    # daqui não afeta lançamentos antigos (diferente de categoria, que é
    # referenciada de verdade e por isso protegida contra exclusão em uso).
    fp = db.get(models.FormaPagamento, forma_id)
    if not fp:
        return False
    db.delete(fp)
    db.commit()
    return True


# ---------- Transação ----------
def criar_transacao(db: Session, transacao: schemas.TransacaoCreate) -> models.Transacao:
    db_transacao = models.Transacao(**transacao.model_dump())
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    return db_transacao


def listar_transacoes(
    db: Session,
    ano: int | None = None,
    mes: int | None = None,
    categoria_id: int | None = None,
) -> list[models.Transacao]:
    query = db.query(models.Transacao)
    if ano is not None:
        query = query.filter(extract("year", models.Transacao.data) == ano)
    if mes is not None:
        query = query.filter(extract("month", models.Transacao.data) == mes)
    if categoria_id is not None:
        query = query.filter(models.Transacao.categoria_id == categoria_id)
    return query.order_by(models.Transacao.data.desc()).all()


def obter_categoria(db: Session, categoria_id: int) -> models.Categoria | None:
    return db.get(models.Categoria, categoria_id)


def obter_transacao(db: Session, transacao_id: int) -> models.Transacao | None:
    return db.get(models.Transacao, transacao_id)


def atualizar_transacao(
    db: Session, transacao_id: int, dados: schemas.TransacaoUpdate
) -> models.Transacao | None:
    transacao = db.get(models.Transacao, transacao_id)
    if not transacao:
        return None
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(transacao, campo, valor)
    db.commit()
    db.refresh(transacao)
    return transacao


def excluir_transacao(db: Session, transacao_id: int) -> bool:
    transacao = db.get(models.Transacao, transacao_id)
    if not transacao:
        return False
    db.delete(transacao)
    db.commit()
    return True


# ---------- Resumo ----------
def resumo_mensal(db: Session, ano: int, mes: int) -> schemas.ResumoMensal:
    base = db.query(models.Transacao).filter(
        extract("year", models.Transacao.data) == ano,
        extract("month", models.Transacao.data) == mes,
    )

    total_despesas = (
        base.filter(models.Transacao.tipo == models.TipoTransacao.despesa)
        .with_entities(func.coalesce(func.sum(models.Transacao.valor), 0.0))
        .scalar()
    )
    total_ganhos = (
        base.filter(models.Transacao.tipo == models.TipoTransacao.ganho)
        .with_entities(func.coalesce(func.sum(models.Transacao.valor), 0.0))
        .scalar()
    )

    por_categoria_rows = (
        base.filter(models.Transacao.tipo == models.TipoTransacao.despesa)
        .join(models.Categoria)
        .with_entities(models.Categoria.id, models.Categoria.nome, func.sum(models.Transacao.valor))
        .group_by(models.Categoria.id, models.Categoria.nome)
        .all()
    )

    por_categoria_ganhos_rows = (
        base.filter(models.Transacao.tipo == models.TipoTransacao.ganho)
        .join(models.Categoria)
        .with_entities(models.Categoria.id, models.Categoria.nome, func.sum(models.Transacao.valor))
        .group_by(models.Categoria.id, models.Categoria.nome)
        .all()
    )

    return schemas.ResumoMensal(
        mes=f"{ano:04d}-{mes:02d}",
        total_despesas=total_despesas,
        total_ganhos=total_ganhos,
        saldo=total_ganhos - total_despesas,
        por_categoria=[
            schemas.ResumoCategoria(categoria_id=cid, categoria=nome, total=total)
            for cid, nome, total in por_categoria_rows
        ],
        por_categoria_ganhos=[
            schemas.ResumoCategoria(categoria_id=cid, categoria=nome, total=total)
            for cid, nome, total in por_categoria_ganhos_rows
        ],
    )


def balanco_anual(db: Session, ano: int) -> schemas.BalancoAnual:
    meses = []
    saldo_total = 0.0
    total_despesas_ano = 0.0
    total_ganhos_ano = 0.0
    for mes in range(1, 13):
        r = resumo_mensal(db, ano, mes)
        meses.append(schemas.BalancoMes(
            mes=mes,
            total_despesas=r.total_despesas,
            total_ganhos=r.total_ganhos,
            saldo=r.saldo,
        ))
        saldo_total += r.saldo
        total_despesas_ano += r.total_despesas
        total_ganhos_ano += r.total_ganhos
    return schemas.BalancoAnual(
        ano=ano, meses=meses,
        total_despesas_ano=total_despesas_ano,
        total_ganhos_ano=total_ganhos_ano,
        saldo_total=saldo_total,
    )
