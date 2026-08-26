import os
import sys


def rodando_empacotado() -> bool:
    """True quando o app está rodando como .exe gerado pelo PyInstaller."""
    return hasattr(sys, "_MEIPASS")


def caminho_recurso(relativo: str) -> str:
    """
    Caminho de arquivos que vão DENTRO do pacote (templates, static) —
    read-only, empacotados junto com o .exe.
    """
    base = sys._MEIPASS if rodando_empacotado() else os.path.abspath(".")
    return os.path.join(base, relativo)


def pasta_dados() -> str:
    """
    Pasta onde o gastos.db mora de verdade — read/write, e principalmente:
    PRECISA sobreviver a uma atualização do .exe. Por isso fica fora da pasta
    temporária que o PyInstaller usa pra extrair o pacote (%APPDATA% no Windows),
    e não dentro do executável.
    Em modo desenvolvimento (rodando com `uvicorn` direto), continua sendo a
    pasta atual, como já era.
    """
    if not rodando_empacotado():
        return os.path.abspath(".")

    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    pasta = os.path.join(base, "AppFinanceiro")
    os.makedirs(pasta, exist_ok=True)
    return pasta
