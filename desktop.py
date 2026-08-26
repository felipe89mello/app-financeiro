"""
Ponto de entrada do app desktop.

Em vez de rodar `uvicorn app.main:app` e abrir o navegador manualmente,
este arquivo sobe o servidor FastAPI numa thread em segundo plano e abre
uma janela nativa (via pywebview) apontando pra ele — assim vira um
"aplicativo" de verdade, sem barra de endereço, sem aba de navegador.

É este arquivo (não app/main.py) que o PyInstaller empacota como .exe.
"""

import socket
import threading
import time

import uvicorn
import webview

from app.main import app


def porta_livre() -> int:
    """Pede ao sistema operacional uma porta TCP livre, pra não colidir
    com nada que já esteja rodando na máquina do usuário."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    porta = s.getsockname()[1]
    s.close()
    return porta


def sobe_servidor(porta: int) -> None:
    uvicorn.run(app, host="127.0.0.1", port=porta, log_level="warning")


def espera_servidor_pronto(porta: int, tentativas: int = 40) -> None:
    """Só abre a janela depois que o servidor realmente aceitar conexões —
    evita a janela abrir em branco/com erro nos primeiros milissegundos."""
    for _ in range(tentativas):
        try:
            with socket.create_connection(("127.0.0.1", porta), timeout=0.25):
                return
        except OSError:
            time.sleep(0.15)


def main() -> None:
    porta = porta_livre()

    thread_servidor = threading.Thread(target=sobe_servidor, args=(porta,), daemon=True)
    thread_servidor.start()

    espera_servidor_pronto(porta)

    webview.create_window(
        "Livro-Caixa — Controle Financeiro",
        f"http://127.0.0.1:{porta}",
        width=1080,
        height=760,
        min_size=(820, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()
