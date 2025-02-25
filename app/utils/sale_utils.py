from collections import defaultdict

from flask import flash, session


def group_sales_by_month(sales):
    """Agrupa las ventas por mes y fecha."""
    grouped_sales = defaultdict(
        lambda: defaultdict(
            lambda: {"sales": [], "total_products": 0, "total_income": 0}
        )
    )

    for sale in sales:
        month_key = sale.date.strftime("%Y-%m")
        date_key = sale.date.strftime("%Y-%m-%d")

        # Calcular totales por venta
        total_products = sum(sale_detail.quantity for sale_detail in sale.products)
        total_income = sum(
            sale_detail.product.price * sale_detail.quantity
            for sale_detail in sale.products
        )

        # Agregar datos a la estructura
        grouped_sales[month_key][date_key]["total_products"] += total_products
        grouped_sales[month_key][date_key]["total_income"] += total_income
        grouped_sales[month_key][date_key]["sales"].append(sale)

    return {month: dict(dates) for month, dates in grouped_sales.items()}


def calculate_month_totals(sales_by_months):
    """Calcula los totales de ingresos por mes."""
    month_totals = {}
    for month, dates in sales_by_months.items():
        month_totals[month] = sum(data["total_income"] for data in dates.values())
    return month_totals


def get_excluded_sales():
    """Obtiene las ventas excluidas de la sesión."""
    try:
        return [
            int(excluded_sale) for excluded_sale in session.get("excluded_sales", [])
        ]
    except (ValueError, TypeError):
        flash("Error en el formato de las ventas excluidas.", "error")
        return []


def calculate_sales_totals(sales):
    """
    Calcula el total de productos y el total de importe a partir de un grupo de ventas.

    :param sales: Lista de objetos de venta. Cada venta debe tener una propiedad `products`
                  que sea una lista de productos con `quantity` y `price`.
    :return: Un diccionario con los totales calculados:
             - total_products: Total de productos vendidos.
             - total_income: Total de ingresos generados.
    """
    total_products = 0
    total_income = 0

    for sale in sales:
        # Itera sobre los productos de cada venta
        for sp in sale.products:
            total_products += sp.quantity
            total_income += sp.quantity * sp.product.price

    return {
        "total_products": total_products,
        "total_income": total_income,
    }


def calculate_sale_detail_totals(sale):
    """Calcula los totales de productos e importe para una venta."""
    total_products = sum(sp.quantity for sp in sale.products)
    total_income = sum(sp.quantity * sp.product.price for sp in sale.products)
    return total_products, total_income


def group_products(sale):
    """Agrupa los productos de una venta por nombre."""
    products_dict = defaultdict(lambda: {"quantity": 0, "import": 0})
    for sale_detail in sale.products:
        name = sale_detail.product.name
        quantity = sale_detail.quantity
        price = sale_detail.product.price
        products_dict[name]["quantity"] += quantity
        products_dict[name]["import"] += quantity * price
    return products_dict


# def format_daily_sales(sales_by_day):
#     """Formatea las ventas diarias para la plantilla."""
#     daily_sales = []
#     for date, sales in sales_by_day.items():
#         daily_sales_data = {
#             "date": date,
#             "sales": [],
#         }
#         for sale in sales:
#             total_products, total_income = calculate_sale_detail_totals(sale)
#             products_dict = group_products(sale)
#             products_list = [
#                 {"name": name, "quantity": data["quantity"], "import": data["import"]}
#                 for name, data in products_dict.items()
#             ]
#             daily_sales_data["sales"].append(
#                 {
#                     "sale_number": sale.sale_number,
#                     "total_products": total_products,
#                     "total_income": total_income,
#                     "products": products_list,
#                 }
#             )
#         daily_sales.append(daily_sales_data)
#     return daily_sales


def format_daily_sales(sales_by_day):
    """
    Formatea las ventas diarias para la plantilla.

    :param sales_by_day: Diccionario con las ventas agrupadas por día.
    :return: Lista de ventas diarias formateadas.
    """
    daily_sales = []

    for date, sales in sales_by_day.items():
        # Inicializar totales diarios
        total_products = 0
        total_income = 0
        formatted_sales = []

        for sale in sales:
            # Calcular totales para esta venta
            sale_total_products, sale_total_income = calculate_sale_detail_totals(sale)

            # Agrupar productos por nombre
            products_dict = group_products(sale)

            # Convertir el diccionario de productos a una lista
            products_list = [
                {"name": name, "quantity": data["quantity"], "import": data["import"]}
                for name, data in products_dict.items()
            ]

            # Agregar la venta formateada
            formatted_sales.append(
                {
                    "sale_number": sale.sale_number,
                    "total_products": sale_total_products,
                    "total_income": sale_total_income,
                    "products": products_list,
                }
            )

            # Actualizar totales diarios
            total_products += sale_total_products
            total_income += sale_total_income

        # Agregar el día formateado
        daily_sales.append(
            {
                "date": date,
                "total_products": total_products,
                "total_income": total_income,
                "sales": formatted_sales,
            }
        )

    return daily_sales


def calculate_sale_total_amount(original_price, discounts, taxes):
    """
    Calcula el total de una venta.
    """

    total_product_price = original_price
    total_discount = original_price * discounts
    total_taxes = original_price * taxes

    total_amount = total_product_price - total_discount + total_taxes
    return total_amount, total_product_price, total_discount, total_taxes


def calculate_sale_detail_total_price(price, quantity, discount):
    """
    Calcula el total de los productos de una venta.
    """
    original_price = price * quantity
    discounted_price = original_price * discount
    total_price = original_price - discounted_price
    return total_price, original_price, discounted_price
