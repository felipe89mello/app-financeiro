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


def excluir_serie_transacao(db: Session, transacao_id: int) -> int:
    """Exclui a transação informada e, se ela fizer parte de uma compra
    parcelada, todas as outras parcelas da mesma série (mesmo
    parcela_grupo). Retorna quantos lançamentos foram excluídos."""
    transacao = db.get(models.Transacao, transacao_id)
    if not transacao:
        return 0
    if not transacao.parcela_grupo:
        db.delete(transacao)
        db.commit()
        return 1
    qtd = (
        db.query(models.Transacao)
        .filter(models.Transacao.parcela_grupo == transacao.parcela_grupo)
        .delete()
    )
    db.commit()
    return qtd


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
    despesas_por_categoria: dict[int, dict] = {}
    ganhos_por_categoria: dict[int, dict] = {}

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

        for item in r.por_categoria:
            acumulado = despesas_por_categoria.setdefault(
                item.categoria_id, {"categoria": item.categoria, "total": 0.0}
            )
            acumulado["total"] += item.total
        for item in r.por_categoria_ganhos:
            acumulado = ganhos_por_categoria.setdefault(
                item.categoria_id, {"categoria": item.categoria, "total": 0.0}
            )
            acumulado["total"] += item.total

    return schemas.BalancoAnual(
        ano=ano, meses=meses,
        total_despesas_ano=total_despesas_ano,
        total_ganhos_ano=total_ganhos_ano,
        saldo_total=saldo_total,
        por_categoria=[
            schemas.ResumoCategoria(categoria_id=cid, categoria=v["categoria"], total=v["total"])
            for cid, v in despesas_por_categoria.items()
        ],
        por_categoria_ganhos=[
            schemas.ResumoCategoria(categoria_id=cid, categoria=v["categoria"], total=v["total"])
            for cid, v in ganhos_por_categoria.items()
        ],
    )


# ---------- Conta Fixa (lembrete de conta a pagar) ----------
def criar_conta_fixa(db: Session, dados: schemas.ContaFixaCreate) -> models.ContaFixa:
    cf = models.ContaFixa(**dados.model_dump())
    db.add(cf)
    db.commit()
    db.refresh(cf)
    return cf


def listar_contas_fixas(db: Session, apenas_ativas: bool = False) -> list[models.ContaFixa]:
    query = db.query(models.ContaFixa)
    if apenas_ativas:
        query = query.filter(models.ContaFixa.ativa == True)  # noqa: E712
    return query.order_by(models.ContaFixa.nome).all()


def obter_conta_fixa(db: Session, conta_fixa_id: int) -> models.ContaFixa | None:
    return db.get(models.ContaFixa, conta_fixa_id)


def atualizar_conta_fixa(
    db: Session, conta_fixa_id: int, dados: schemas.ContaFixaUpdate
) -> models.ContaFixa | None:
    cf = db.get(models.ContaFixa, conta_fixa_id)
    if not cf:
        return None
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(cf, campo, valor)
    db.commit()
    db.refresh(cf)
    return cf


def excluir_conta_fixa(db: Session, conta_fixa_id: int) -> bool:
    cf = db.get(models.ContaFixa, conta_fixa_id)
    if not cf:
        return False
    db.delete(cf)  # cascade apaga o histórico de pago/não pago dela também
    db.commit()
    return True


def listar_contas_fixas_com_status(
    db: Session, ano: int, mes: int
) -> list[schemas.ContaFixaComStatus]:
    contas = listar_contas_fixas(db, apenas_ativas=True)
    pagamentos = {
        p.conta_fixa_id: p
        for p in db.query(models.ContaFixaPagamento).filter(
            models.ContaFixaPagamento.ano == ano,
            models.ContaFixaPagamento.mes == mes,
        ).all()
    }
    return [
        schemas.ContaFixaComStatus(
            id=c.id,
            nome=c.nome,
            valor_esperado=c.valor_esperado,
            dia_vencimento=c.dia_vencimento,
            pago=pagamentos[c.id].pago if c.id in pagamentos else False,
        )
        for c in contas
    ]


def alternar_pagamento_conta_fixa(db: Session, conta_fixa_id: int, ano: int, mes: int) -> None:
    pagamento = (
        db.query(models.ContaFixaPagamento)
        .filter(
            models.ContaFixaPagamento.conta_fixa_id == conta_fixa_id,
            models.ContaFixaPagamento.ano == ano,
            models.ContaFixaPagamento.mes == mes,
        )
        .first()
    )
    if not pagamento:
        pagamento = models.ContaFixaPagamento(
            conta_fixa_id=conta_fixa_id, ano=ano, mes=mes, pago=False
        )
        db.add(pagamento)

    pagamento.pago = not pagamento.pago
    pagamento.data_pagamento = date.today() if pagamento.pago else None
    db.commit()
