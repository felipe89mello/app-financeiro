"""
Migrações leves, feitas na mão — sem Alembic, porque o app é pequeno o
suficiente pra isso ainda valer a pena. Cada função aqui é "segura de
rodar de novo": ela confere se a mudança já existe antes de aplicar, então
não tem problema chamar toda vez que o app abre.

Isso existe porque `Base.metadata.create_all()` (em app/main.py) só cria
tabelas que NÃO existem — ele nunca adiciona uma coluna nova numa tabela
que já existe. Sem isso, quem já tem um gastos.db de antes ficaria com o
banco desatualizado e o app quebraria tentando usar uma coluna que não
existe no arquivo.
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def _coluna_existe(engine: Engine, tabela: str, coluna: str) -> bool:
    with engine.connect() as conn:
        linhas = conn.execute(text(f"PRAGMA table_info({tabela})")).fetchall()
    nomes_colunas = {linha[1] for linha in linhas}  # índice 1 = nome da coluna
    return coluna in nomes_colunas


def migrar(engine: Engine) -> None:
    if not _coluna_existe(engine, "categorias", "ativa"):
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE categorias ADD COLUMN ativa BOOLEAN NOT NULL DEFAULT 1"
            ))
            conn.commit()

    # Compras parceladas (ver app/models.py — Transacao.parcela_*).
    colunas_parcela = [
        ("parcela_grupo", "ALTER TABLE transacoes ADD COLUMN parcela_grupo VARCHAR"),
        ("parcela_numero", "ALTER TABLE transacoes ADD COLUMN parcela_numero INTEGER"),
        ("parcela_total", "ALTER TABLE transacoes ADD COLUMN parcela_total INTEGER"),
    ]
    for coluna, ddl in colunas_parcela:
        if not _coluna_existe(engine, "transacoes", coluna):
            with engine.connect() as conn:
                conn.execute(text(ddl))
                conn.commit()
