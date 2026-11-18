from calendar import monthrange
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


def somar_meses(d: date, n: int) -> date:
    """Soma n meses a uma data, mantendo o dia quando possível — e, quando
    o mês de destino não tem esse dia (ex: dia 31 indo pra fevereiro),
    usa o último dia válido daquele mês. Usado para gerar as parcelas de
    uma compra parcelada, uma por mês, a partir da data do lançamento."""
    mes_total = d.month - 1 + n
    ano = d.year + mes_total // 12
    mes = mes_total % 12 + 1
    dia = min(d.day, monthrange(ano, mes)[1])
    return date(ano, mes, dia)
