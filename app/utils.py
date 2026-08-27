from datetime import date

MESES_PT = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

FORMAS_PAGAMENTO = [
    "Cartão de Crédito", "Débito", "Pix", "Dinheiro", "Vale Alimentação", "Outro",
]


def nome_mes(ano: int, mes: int) -> str:
    return f"{MESES_PT[mes]} de {ano}"


def mes_anterior(ano: int, mes: int) -> tuple[int, int]:
    if mes == 1:
        return ano - 1, 12
    return ano, mes - 1


def mes_seguinte(ano: int, mes: int) -> tuple[int, int]:
    if mes == 12:
        return ano + 1, 1
    return ano, mes + 1


def mes_atual() -> tuple[int, int]:
    hoje = date.today()
    return hoje.year, hoje.month
