from collections import defaultdict


def _sale_products_count(sale) -> int:
    """Calcula la cantidad total de productos en una venta."""
    return sum(sale_detail.quantity for sale_detail in sale.products)


def _sale_income_from_product_prices(sale) -> float:
    """Calcula el importe total de una venta usando `quantity * product.price`."""
    return sum(sp.quantity * sp.product.price for sp in sale.products)


def _sale_income_from_total_amount(sale) -> float:
    """Devuelve el importe total persistido en la venta."""
    return sale.total_amount


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
        total_products = _sale_products_count(sale)
        total_income = _sale_income_from_total_amount(sale)

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
        total_products += _sale_products_count(sale)
        total_income += _sale_income_from_product_prices(sale)

    return {
        "total_products": total_products,
        "total_income": total_income,
    }


def calculate_sale_detail_totals(sale):
    """Calcula los totales de productos e importe para una venta."""
    total_products = _sale_products_count(sale)
    total_income = _sale_income_from_product_prices(sale)
    return total_products, total_income


def group_products(sale):
    """Agrupa los productos de una venta por nombre."""
    products_dict = defaultdict(lambda: {"quantity": 0, "import": 0})
    for sale_detail in sale.products:
        name = sale_detail.product.name
        products_dict[name]["quantity"] += sale_detail.quantity
        products_dict[name]["import"] += sale_detail.total_price
    return products_dict


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
            sale_total_products = _sale_products_count(sale)
            sale_total_income = _sale_income_from_total_amount(sale)

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
