import os
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .paths import pasta_dados, rodando_empacotado, caminho_recurso

# Banco em arquivo único — fica em uma pasta persistente (fora do .exe),
# pra não ser apagado quando o app é atualizado. Ver app/paths.py.
CAMINHO_BANCO = os.path.join(pasta_dados(), "gastos.db")

# Primeira vez rodando o .exe instalado: se ainda não existe um banco na
# pasta persistente, copia o "gastos_seed.db" empacotado junto (o histórico
# já importado) — assim o usuário abre o app pela primeira vez e já
# encontra os dados, sem precisar copiar arquivo manualmente.
if rodando_empacotado() and not os.path.exists(CAMINHO_BANCO):
    semente = caminho_recurso("gastos_seed.db")
    if os.path.exists(semente):
        shutil.copy(semente, CAMINHO_BANCO)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{CAMINHO_BANCO}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # SQLite por padrão só permite uso pela thread que abriu a conexão;
    # o FastAPI usa threads diferentes por requisição, então precisamos liberar isso.
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Abre uma sessão de banco por requisição e garante que ela é fechada no final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
