"""
Backup automático do gastos.db.

Roda toda vez que o app abre (ver app/main.py). Duas coisas acontecem:

1. Guarda uma cópia datada em %APPDATA%\\AppFinanceiro\\backups\\, mantendo só
   as últimas N (as mais antigas são apagadas sozinhas).
2. Se existir um arquivo backup_destino.txt (na mesma pasta do gastos.db) com
   um caminho de pasta escrito nele, copia o banco pra lá também — pensado
   pra apontar pra uma pasta sincronizada com o Google Drive/OneDrive/etc,
   que sozinho vai levar a cópia pra nuvem.
"""

import os
import shutil
from datetime import datetime

MANTER_BACKUPS = 10
NOME_ARQUIVO_CONFIG = "backup_destino.txt"


def _rotacionar(pasta_backups: str, manter: int) -> None:
    arquivos = sorted(
        f for f in os.listdir(pasta_backups)
        if f.startswith("gastos_backup_") and f.endswith(".db")
    )
    excesso = len(arquivos) - manter
    for antigo in arquivos[:max(excesso, 0)]:
        try:
            os.remove(os.path.join(pasta_backups, antigo))
        except OSError:
            pass  # não trava o app por causa de backup


def fazer_backup(caminho_banco: str, pasta_dados: str) -> None:
    log = []
    log.append(f"--- backup {datetime.now().isoformat()} ---")
    log.append(f"caminho_banco = {caminho_banco!r}")
    log.append(f"pasta_dados = {pasta_dados!r}")
    log.append(f"caminho_banco existe? {os.path.exists(caminho_banco)}")

    if not os.path.exists(caminho_banco):
        log.append("banco não existe, saindo sem fazer nada")
        _gravar_log(pasta_dados, log)
        return

    # 1) backup local rotativo
    pasta_backups = os.path.join(pasta_dados, "backups")
    os.makedirs(pasta_backups, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(pasta_backups, f"gastos_backup_{carimbo}.db")
    try:
        shutil.copy2(caminho_banco, destino)
        _rotacionar(pasta_backups, MANTER_BACKUPS)
        log.append(f"backup local OK: {destino}")
    except OSError as e:
        log.append(f"ERRO no backup local: {e!r}")

    # 2) backup extra opcional, numa pasta escolhida pelo usuário
    arquivo_config = os.path.join(pasta_dados, NOME_ARQUIVO_CONFIG)
    log.append(f"arquivo_config = {arquivo_config!r}")
    log.append(f"arquivo_config existe? {os.path.exists(arquivo_config)}")

    if os.path.exists(arquivo_config):
        pasta_extra = ""
        try:
            # utf-8-sig: remove o BOM que o Bloco de Notas do Windows 11
            # costuma gravar no início do arquivo ao salvar como UTF-8 —
            # sem isso, o caminho lido ficava com um caractere invisível
            # na frente e a comparação falhava silenciosamente.
            with open(arquivo_config, "r", encoding="utf-8-sig") as f:
                pasta_extra = f.read().strip()
            log.append(f"pasta_extra lida = {pasta_extra!r}")
        except OSError as e:
            log.append(f"ERRO lendo arquivo_config: {e!r}")

        log.append(f"pasta_extra é pasta válida? {os.path.isdir(pasta_extra) if pasta_extra else 'N/A (vazio)'}")

        if pasta_extra and os.path.isdir(pasta_extra):
            destino_extra = os.path.join(pasta_extra, "gastos_backup.db")
            try:
                shutil.copy2(caminho_banco, destino_extra)
                log.append(f"backup extra OK: {destino_extra}")
            except OSError as e:
                log.append(f"ERRO no backup extra: {e!r}")
    else:
        log.append("arquivo backup_destino.txt não existe, pulando backup extra")

    _gravar_log(pasta_dados, log)


def _gravar_log(pasta_dados: str, linhas: list) -> None:
    try:
        caminho_log = os.path.join(pasta_dados, "backup_debug.log")
        with open(caminho_log, "a", encoding="utf-8") as f:
            f.write("\n".join(linhas) + "\n\n")
    except OSError:
        pass
