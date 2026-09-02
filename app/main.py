from datetime import date
from urllib.parse import quote

from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, models, schemas, utils
from .backup import fazer_backup
from .database import engine, get_db, SessionLocal, CAMINHO_BANCO
from .migrations import migrar
from .paths import caminho_recurso, pasta_dados

# Cria as tabelas no arquivo gastos.db se ainda não existirem.
models.Base.metadata.create_all(bind=engine)

# Atualiza bancos já existentes de versões anteriores do app (ver app/migrations.py).
migrar(engine)

# Formas de pagamento: semeia a lista padrão só na primeira vez (tabela vazia).
_db_seed = SessionLocal()
try:
    if not crud.listar_formas_pagamento(_db_seed):
        for _nome in utils.FORMAS_PAGAMENTO:
            crud.criar_forma_pagamento(_db_seed, schemas.FormaPagamentoCreate(nome=_nome))
finally:
    _db_seed.close()

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
    status = crud.excluir_categoria(db, categoria_id)
    if status == "nao_encontrada":
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    if status == "em_uso":
        raise HTTPException(
            status_code=409,
            detail="Categoria tem lançamentos associados e não pode ser excluída",
        )
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
    categorias = crud.listar_categorias(db, apenas_ativas=True)
    formas_pagamento = crud.listar_formas_pagamento(db)
    contas_fixas = crud.listar_contas_fixas_com_status(db, ano, mes)
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
            "formas_pagamento": [f.nome for f in formas_pagamento],
            "contas_fixas": contas_fixas,
            "hoje": date.today().isoformat(),
        },
    )


@app.post("/ui/contas-fixas/{conta_fixa_id}/alternar")
def form_alternar_pagamento_conta_fixa(
    conta_fixa_id: int,
    voltar_ano: int = Form(...),
    voltar_mes: int = Form(...),
    db: Session = Depends(get_db),
):
    crud.alternar_pagamento_conta_fixa(db, conta_fixa_id, voltar_ano, voltar_mes)
    return RedirectResponse(url=f"/dashboard/{voltar_ano}/{voltar_mes}", status_code=303)


@app.post("/ui/transacoes")
def form_criar_transacao(
    data: date = Form(...),
    descricao: str = Form(""),
    tipo: str = Form(...),
    categoria_id: int = Form(...),
    valor: float = Form(...),
    forma_pagamento: str = Form(""),
    voltar_ano: int = Form(...),
    voltar_mes: int = Form(...),
    db: Session = Depends(get_db),
):
    crud.criar_transacao(db, schemas.TransacaoCreate(
        data=data, descricao=descricao or None, tipo=tipo,
        categoria_id=categoria_id, valor=valor, forma_pagamento=forma_pagamento or None,
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


@app.get("/ui/transacoes/{transacao_id}/editar")
def pagina_editar_transacao(
    transacao_id: int,
    voltar_ano: int,
    voltar_mes: int,
    request: Request,
    db: Session = Depends(get_db),
):
    transacao = crud.obter_transacao(db, transacao_id)
    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    categorias = crud.listar_categorias(db, apenas_ativas=True)
    # Se a categoria atual do lançamento foi arquivada depois, ela precisa
    # continuar aparecendo aqui — senão o formulário "perde" a seleção dela.
    if not any(c.id == transacao.categoria_id for c in categorias):
        categorias = categorias + [transacao.categoria]
    return templates.TemplateResponse(
        request,
        "editar_transacao.html",
        {
            "ativo": "dashboard",
            "transacao": transacao,
            "categorias": categorias,
            "formas_pagamento": [f.nome for f in crud.listar_formas_pagamento(db)],
            "voltar_ano": voltar_ano,
            "voltar_mes": voltar_mes,
        },
    )


@app.post("/ui/transacoes/{transacao_id}/editar")
def form_editar_transacao(
    transacao_id: int,
    data: date = Form(...),
    descricao: str = Form(""),
    tipo: str = Form(...),
    categoria_id: int = Form(...),
    valor: float = Form(...),
    forma_pagamento: str = Form(""),
    voltar_ano: int = Form(...),
    voltar_mes: int = Form(...),
    db: Session = Depends(get_db),
):
    crud.atualizar_transacao(db, transacao_id, schemas.TransacaoUpdate(
        data=data, descricao=descricao or None, tipo=tipo,
        categoria_id=categoria_id, valor=valor, forma_pagamento=forma_pagamento or None,
    ))
    return RedirectResponse(url=f"/dashboard/{voltar_ano}/{voltar_mes}", status_code=303)


@app.get("/categorias-ui")
def pagina_categorias(request: Request, erro: str | None = None, db: Session = Depends(get_db)):
    todas = crud.listar_categorias(db)
    return templates.TemplateResponse(
        request,
        "categorias.html",
        {
            "ativo": "categorias",
            "despesa_ativas": [c for c in todas if c.tipo.value == "despesa" and c.ativa],
            "despesa_arquivadas": [c for c in todas if c.tipo.value == "despesa" and not c.ativa],
            "ganho_ativas": [c for c in todas if c.tipo.value == "ganho" and c.ativa],
            "ganho_arquivadas": [c for c in todas if c.tipo.value == "ganho" and not c.ativa],
            "erro": erro,
        },
    )


@app.post("/ui/categorias")
def form_criar_categoria(
    nome: str = Form(...), tipo: str = Form(...), db: Session = Depends(get_db)
):
    crud.criar_categoria(db, schemas.CategoriaCreate(nome=nome, tipo=tipo))
    return RedirectResponse(url="/categorias-ui", status_code=303)


@app.get("/ui/categorias/{categoria_id}/editar")
def pagina_editar_categoria(categoria_id: int, request: Request, db: Session = Depends(get_db)):
    categoria = crud.obter_categoria(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return templates.TemplateResponse(
        request,
        "editar_categoria.html",
        {"ativo": "categorias", "categoria": categoria},
    )


@app.post("/ui/categorias/{categoria_id}/editar")
def form_editar_categoria(
    categoria_id: int, nome: str = Form(...), db: Session = Depends(get_db)
):
    crud.atualizar_categoria(db, categoria_id, schemas.CategoriaUpdate(nome=nome))
    return RedirectResponse(url="/categorias-ui", status_code=303)


@app.post("/ui/categorias/{categoria_id}/arquivar")
def form_arquivar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    crud.definir_categoria_ativa(db, categoria_id, ativa=False)
    return RedirectResponse(url="/categorias-ui", status_code=303)


@app.post("/ui/categorias/{categoria_id}/reativar")
def form_reativar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    crud.definir_categoria_ativa(db, categoria_id, ativa=True)
    return RedirectResponse(url="/categorias-ui", status_code=303)


@app.post("/ui/categorias/{categoria_id}/excluir")
def form_excluir_categoria(categoria_id: int, db: Session = Depends(get_db)):
    status = crud.excluir_categoria(db, categoria_id)
    if status == "em_uso":
        categoria = crud.obter_categoria(db, categoria_id)
        n = crud.contar_transacoes_da_categoria(db, categoria_id)
        nome = categoria.nome if categoria else "?"
        erro = f'A categoria "{nome}" tem {n} lançamento(s) e não pode ser excluída. Você pode arquivá-la em vez disso.'
        return RedirectResponse(url=f"/categorias-ui?erro={quote(erro)}", status_code=303)
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
            "por_categoria": balanco.por_categoria,
            "por_categoria_ganhos": balanco.por_categoria_ganhos,
        },
    )


@app.get("/contas-fixas-ui")
def pagina_contas_fixas(request: Request, db: Session = Depends(get_db)):
    todas = crud.listar_contas_fixas(db)
    return templates.TemplateResponse(
        request,
        "contas_fixas.html",
        {
            "ativo": "contas_fixas",
            "ativas": [c for c in todas if c.ativa],
            "arquivadas": [c for c in todas if not c.ativa],
        },
    )


@app.post("/ui/contas-fixas")
def form_criar_conta_fixa(
    nome: str = Form(...),
    valor_esperado: str = Form(""),
    dia_vencimento: str = Form(""),
    db: Session = Depends(get_db),
):
    crud.criar_conta_fixa(db, schemas.ContaFixaCreate(
        nome=nome,
        valor_esperado=float(valor_esperado) if valor_esperado else None,
        dia_vencimento=int(dia_vencimento) if dia_vencimento else None,
    ))
    return RedirectResponse(url="/contas-fixas-ui", status_code=303)


@app.get("/ui/contas-fixas/{conta_fixa_id}/editar")
def pagina_editar_conta_fixa(conta_fixa_id: int, request: Request, db: Session = Depends(get_db)):
    cf = crud.obter_conta_fixa(db, conta_fixa_id)
    if not cf:
        raise HTTPException(status_code=404, detail="Conta fixa não encontrada")
    return templates.TemplateResponse(
        request,
        "editar_conta_fixa.html",
        {"ativo": "contas_fixas", "conta_fixa": cf},
    )


@app.post("/ui/contas-fixas/{conta_fixa_id}/editar")
def form_editar_conta_fixa(
    conta_fixa_id: int,
    nome: str = Form(...),
    valor_esperado: str = Form(""),
    dia_vencimento: str = Form(""),
    db: Session = Depends(get_db),
):
    crud.atualizar_conta_fixa(db, conta_fixa_id, schemas.ContaFixaUpdate(
        nome=nome,
        valor_esperado=float(valor_esperado) if valor_esperado else None,
        dia_vencimento=int(dia_vencimento) if dia_vencimento else None,
    ))
    return RedirectResponse(url="/contas-fixas-ui", status_code=303)


@app.post("/ui/contas-fixas/{conta_fixa_id}/arquivar")
def form_arquivar_conta_fixa(conta_fixa_id: int, db: Session = Depends(get_db)):
    crud.atualizar_conta_fixa(db, conta_fixa_id, schemas.ContaFixaUpdate(ativa=False))
    return RedirectResponse(url="/contas-fixas-ui", status_code=303)


@app.post("/ui/contas-fixas/{conta_fixa_id}/reativar")
def form_reativar_conta_fixa(conta_fixa_id: int, db: Session = Depends(get_db)):
    crud.atualizar_conta_fixa(db, conta_fixa_id, schemas.ContaFixaUpdate(ativa=True))
    return RedirectResponse(url="/contas-fixas-ui", status_code=303)


@app.post("/ui/contas-fixas/{conta_fixa_id}/excluir")
def form_excluir_conta_fixa(conta_fixa_id: int, db: Session = Depends(get_db)):
    crud.excluir_conta_fixa(db, conta_fixa_id)
    return RedirectResponse(url="/contas-fixas-ui", status_code=303)


@app.get("/formas-pagamento-ui")
def pagina_formas_pagamento(request: Request, db: Session = Depends(get_db)):
    formas = crud.listar_formas_pagamento(db)
    return templates.TemplateResponse(
        request,
        "formas_pagamento.html",
        {"ativo": "formas_pagamento", "formas": formas},
    )


@app.post("/ui/formas-pagamento")
def form_criar_forma_pagamento(nome: str = Form(...), db: Session = Depends(get_db)):
    crud.criar_forma_pagamento(db, schemas.FormaPagamentoCreate(nome=nome))
    return RedirectResponse(url="/formas-pagamento-ui", status_code=303)


@app.get("/ui/formas-pagamento/{forma_id}/editar")
def pagina_editar_forma_pagamento(forma_id: int, request: Request, db: Session = Depends(get_db)):
    forma = crud.obter_forma_pagamento(db, forma_id)
    if not forma:
        raise HTTPException(status_code=404, detail="Forma de pagamento não encontrada")
    return templates.TemplateResponse(
        request,
        "editar_forma_pagamento.html",
        {"ativo": "formas_pagamento", "forma": forma},
    )


@app.post("/ui/formas-pagamento/{forma_id}/editar")
def form_editar_forma_pagamento(forma_id: int, nome: str = Form(...), db: Session = Depends(get_db)):
    crud.atualizar_forma_pagamento(db, forma_id, schemas.FormaPagamentoUpdate(nome=nome))
    return RedirectResponse(url="/formas-pagamento-ui", status_code=303)


@app.post("/ui/formas-pagamento/{forma_id}/excluir")
def form_excluir_forma_pagamento(forma_id: int, db: Session = Depends(get_db)):
    crud.excluir_forma_pagamento(db, forma_id)
    return RedirectResponse(url="/formas-pagamento-ui", status_code=303)


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
