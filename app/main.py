from datetime import date

from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, models, schemas, utils
from .backup import fazer_backup
from .database import engine, get_db, CAMINHO_BANCO
from .paths import caminho_recurso, pasta_dados

# Cria as tabelas no arquivo gastos.db se ainda não existirem.
models.Base.metadata.create_all(bind=engine)

# Backup automático: uma cópia datada a cada abertura do app (ver app/backup.py).
fazer_backup(CAMINHO_BANCO, pasta_dados())

app = FastAPI(title="App Financeiro")

app.mount("/static", StaticFiles(directory=caminho_recurso("app/static")), name="static")
templates = Jinja2Templates(directory=caminho_recurso("app/templates"))
templates.env.globals["ano_atual_nav"] = date.today().year


# ---------- Categorias ----------
@app.post("/categorias", response_model=schemas.Categoria)
def criar_categoria(categoria: schemas.CategoriaCreate, db: Session = Depends(get_db)):
    return crud.criar_categoria(db, categoria)


@app.get("/categorias", response_model=list[schemas.Categoria])
def listar_categorias(db: Session = Depends(get_db)):
    return crud.listar_categorias(db)


@app.delete("/categorias/{categoria_id}")
def excluir_categoria(categoria_id: int, db: Session = Depends(get_db)):
    if not crud.excluir_categoria(db, categoria_id):
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return {"ok": True}


# ---------- Transações ----------
@app.post("/transacoes", response_model=schemas.Transacao)
def criar_transacao(transacao: schemas.TransacaoCreate, db: Session = Depends(get_db)):
    return crud.criar_transacao(db, transacao)


@app.get("/transacoes", response_model=list[schemas.Transacao])
def listar_transacoes(
    ano: int | None = None, mes: int | None = None, db: Session = Depends(get_db)
):
    return crud.listar_transacoes(db, ano=ano, mes=mes)


@app.patch("/transacoes/{transacao_id}", response_model=schemas.Transacao)
def atualizar_transacao(
    transacao_id: int, dados: schemas.TransacaoUpdate, db: Session = Depends(get_db)
):
    transacao = crud.atualizar_transacao(db, transacao_id, dados)
    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return transacao


@app.delete("/transacoes/{transacao_id}")
def excluir_transacao(transacao_id: int, db: Session = Depends(get_db)):
    if not crud.excluir_transacao(db, transacao_id):
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return {"ok": True}


# ---------- Resumo ----------
@app.get("/resumo/{ano}/{mes}", response_model=schemas.ResumoMensal)
def resumo_mensal(ano: int, mes: int, db: Session = Depends(get_db)):
    return crud.resumo_mensal(db, ano, mes)


# ---------- Balanço Anual ----------
@app.get("/balanco-anual/{ano}", response_model=schemas.BalancoAnual)
def balanco_anual(ano: int, db: Session = Depends(get_db)):
    return crud.balanco_anual(db, ano)


# =========================================================
#  PÁGINAS (HTML) — telas do app, além da API JSON acima
# =========================================================

@app.get("/")
def raiz():
    ano, mes = utils.mes_atual()
    return RedirectResponse(url=f"/dashboard/{ano}/{mes}")


@app.get("/dashboard/{ano}/{mes}")
def pagina_dashboard(ano: int, mes: int, request: Request, db: Session = Depends(get_db)):
    resumo = crud.resumo_mensal(db, ano, mes)
    transacoes = crud.listar_transacoes(db, ano=ano, mes=mes)
    categorias = crud.listar_categorias(db)
    prev_ano, prev_mes = utils.mes_anterior(ano, mes)
    next_ano, next_mes = utils.mes_seguinte(ano, mes)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "ativo": "dashboard",
            "ano": ano,
            "mes": mes,
            "mes_nome": utils.nome_mes(ano, mes),
            "prev_ano": prev_ano, "prev_mes": prev_mes,
            "next_ano": next_ano, "next_mes": next_mes,
            "resumo": resumo,
            "transacoes": transacoes,
            "categorias": categorias,
            "hoje": date.today().isoformat(),
        },
    )


@app.post("/ui/transacoes")
def form_criar_transacao(
    data: date = Form(...),
    descricao: str = Form(""),
    tipo: str = Form(...),
    categoria_id: int = Form(...),
    valor: float = Form(...),
    voltar_ano: int = Form(...),
    voltar_mes: int = Form(...),
    db: Session = Depends(get_db),
):
    crud.criar_transacao(db, schemas.TransacaoCreate(
        data=data, descricao=descricao or None, tipo=tipo,
        categoria_id=categoria_id, valor=valor, forma_pagamento=None,
    ))
    return RedirectResponse(url=f"/dashboard/{voltar_ano}/{voltar_mes}", status_code=303)


@app.post("/ui/transacoes/{transacao_id}/excluir")
def form_excluir_transacao(
    transacao_id: int,
    voltar_ano: int = Form(...),
    voltar_mes: int = Form(...),
    db: Session = Depends(get_db),
):
    crud.excluir_transacao(db, transacao_id)
    return RedirectResponse(url=f"/dashboard/{voltar_ano}/{voltar_mes}", status_code=303)


@app.get("/categorias-ui")
def pagina_categorias(request: Request, db: Session = Depends(get_db)):
    todas = crud.listar_categorias(db)
    return templates.TemplateResponse(
        request,
        "categorias.html",
        {
            "ativo": "categorias",
            "categorias_despesa": [c for c in todas if c.tipo.value == "despesa"],
            "categorias_ganho": [c for c in todas if c.tipo.value == "ganho"],
        },
    )


@app.post("/ui/categorias")
def form_criar_categoria(
    nome: str = Form(...), tipo: str = Form(...), db: Session = Depends(get_db)
):
    crud.criar_categoria(db, schemas.CategoriaCreate(nome=nome, tipo=tipo))
    return RedirectResponse(url="/categorias-ui", status_code=303)


@app.post("/ui/categorias/{categoria_id}/excluir")
def form_excluir_categoria(categoria_id: int, db: Session = Depends(get_db)):
    crud.excluir_categoria(db, categoria_id)
    return RedirectResponse(url="/categorias-ui", status_code=303)


@app.get("/balanco/{ano}")
def pagina_balanco_anual(ano: int, request: Request, db: Session = Depends(get_db)):
    balanco = crud.balanco_anual(db, ano)
    meses_com_nome = [
        {**m.model_dump(), "nome_mes": utils.MESES_PT[m.mes]}
        for m in balanco.meses
    ]
    return templates.TemplateResponse(
        request,
        "balanco.html",
        {
            "ativo": "balanco",
            "ano": ano,
            "meses": meses_com_nome,
            "total_despesas_ano": balanco.total_despesas_ano,
            "total_ganhos_ano": balanco.total_ganhos_ano,
            "saldo_total": balanco.saldo_total,
        },
    )


@app.get("/categoria/{categoria_id}/{ano}/{mes}")
def pagina_categoria_detalhe(
    categoria_id: int, ano: int, mes: int, request: Request, db: Session = Depends(get_db)
):
    categoria = crud.obter_categoria(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    transacoes = crud.listar_transacoes(db, ano=ano, mes=mes, categoria_id=categoria_id)
    total = sum(t.valor for t in transacoes)
    return templates.TemplateResponse(
        request,
        "categoria_detalhe.html",
        {
            "ativo": "dashboard",
            "categoria": categoria,
            "ano": ano,
            "mes": mes,
            "mes_nome": utils.nome_mes(ano, mes),
            "transacoes": transacoes,
            "total": total,
        },
    )
