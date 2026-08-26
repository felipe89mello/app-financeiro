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


def listar_categorias(db: Session) -> list[models.Categoria]:
    return db.query(models.Categoria).order_by(models.Categoria.nome).all()


def excluir_categoria(db: Session, categoria_id: int) -> bool:
    categoria = db.get(models.Categoria, categoria_id)
    if not categoria:
        return False
    db.delete(categoria)
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

    return schemas.ResumoMensal(
        mes=f"{ano:04d}-{mes:02d}",
        total_despesas=total_despesas,
        total_ganhos=total_ganhos,
        saldo=total_ganhos - total_despesas,
        por_categoria=[
            schemas.ResumoCategoria(categoria_id=cid, categoria=nome, total=total)
            for cid, nome, total in por_categoria_rows
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
