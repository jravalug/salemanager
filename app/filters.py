from babel.numbers import format_currency


def format_currency_filter(value):
    if value is None:
        return "$ 0.00"
    return format_currency(value, "CUP", locale="es_CU").replace("CUP", "$")


# Registrar un filtro personalizado
def format_payment_method(payment_method):
    """
    Transforma el valor de payment_method en un formato legible.
    """
    payment_methods = {
        "cash": "Efectivo",
        "card": "Tarjeta",
        "transfer": "Transferencia",
        "mix": "Mixto",
    }
    return payment_methods.get(payment_method, "Método no especificado")


# Registrar un filtro personalizado
def format_sale_status(status):
    """
    Transforma el valor de status en un formato legible.
    """
    payment_methods = {
        "completed": "Completada",
        "pending": "Pendiente",
        "cancelled": "Cancelada",
        "returned": "Devuelta",
    }
    return payment_methods.get(status, "Estado no especificado")


# Registrar un filtro personalizado TODO: Terminar de poner los badges
def format_sale_status_badge(status):
    """
    Transforma el valor de status en un formato legible.
    """
    payment_methods = {
        "completed": "<span class='bg-green-100 text-green-800 text-sm font-medium me-2 px-2.5 py-0.5 rounded-sm dark:bg-gray-700 dark:text-green-400 border border-green-400'>Completada</span>",
        "pending": "<span class='bg-yellow-100 text-yellow-800 text-sm font-medium me-2 px-2.5 py-0.5 rounded-sm dark:bg-yellow-900 dark:text-yellow-300'>Pendiente</span>",
        "cancelled": "<span class='bg-red-100 text-red-800 text-sm font-medium me-2 px-2.5 py-0.5 rounded-sm dark:bg-red-900 dark:text-red-300'>Cancelada</span>",
        "returned": "<span class='bg-gray-100 text-gray-800 text-sm font-medium me-2 px-2.5 py-0.5 rounded-sm dark:bg-gray-700 dark:text-gray-300'>Devuelta</span>",
    }
    return payment_methods.get(status, "Estado no especificado")
