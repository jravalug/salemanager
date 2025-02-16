from babel.numbers import format_currency


def format_currency_filter(value):
    if value is None:
        return "$ 0.00"
    return format_currency(value, "CUP", locale="es_CU").replace("CUP", "$")
