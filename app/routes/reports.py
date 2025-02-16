from collections import defaultdict
from datetime import datetime
from io import BytesIO
import json
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    jsonify,
    send_file,
    session,
    url_for,
)
from openpyxl import Workbook
from app.models import Business, Sale, SaleProduct
from app.extensions import db
from dateutil.relativedelta import relativedelta

bp = Blueprint("report", __name__, url_prefix="/business/<int:business_id>/report")


@bp.route("/monthly/sales-by-product", methods=["GET", "POST"])
def monthly_sales_by_produc(business_id):
    # Obtener el negocio (asegúrate de que exista)
    business = Business.query.get_or_404(business_id)

    # Inicializar variables
    daily_sales = []
    selected_month = None
    excluded_sales = []
    excluded_products = []

    if request.method == "POST":
        # Obtener el mes seleccionado desde el formulario
        month_str = request.form.get("month")

        if not month_str:
            flash("Por favor, selecciona un mes.", "error")
            return render_template(
                "report/monthly_sales_by_product.html",
                business=business,
                daily_sales=daily_sales,
                selected_month=selected_month,
            )

        try:
            # Convertir el mes a un objeto datetime
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
            start_date = selected_month.replace(day=1)
            end_date = start_date + relativedelta(months=1, days=-1)

            # Consultar las órdenes dentro del rango de fechas
            sales = (
                Sale.query.filter(
                    Sale.business_id == business.id,
                    Sale.date.between(start_date, end_date),
                )
                .join(Sale.products)  # Join con SaleProduct
                .join(SaleProduct.product)  # Join con Product
                .order_by(
                    Sale.date.asc(),  # Primero por fecha
                )
                .all()
            )

            # Procesar los datos
            sales_by_day = {}
            for sale in sales:
                date_key = sale.date.strftime("%Y-%m-%d")
                if date_key not in sales_by_day:
                    sales_by_day[date_key] = {
                        "total_products": 0,
                        "total_income": 0,
                        "products": {},
                    }

                # Ordenar los productos dentro de la venta por nombre
                sorted_products = sorted(
                    sale.products, key=lambda sale_product: sale_product.product.name
                )
                # logging.debug("Datos generados para el reporte: %s", sale.products)

                for sale_product in sorted_products:
                    product_key = sale_product.product.name
                    if product_key not in sales_by_day[date_key]["products"]:
                        sales_by_day[date_key]["products"][product_key] = {
                            "quantity": 0,
                            "total_amount": 0,
                            "orders": set(),  # Usamos un conjunto para evitar duplicados,
                        }

                    sales_by_day[date_key]["products"][product_key][
                        "quantity"
                    ] += sale_product.quantity
                    sales_by_day[date_key]["products"][product_key]["total_amount"] += (
                        sale_product.quantity * sale_product.product.price
                    )

                    # Añadir la tupla (sale_id, sale_number) al conjunto
                    sales_by_day[date_key]["products"][product_key]["orders"].add(
                        (sale.id, sale.sale_number)
                    )

                # Actualizar totales
                sales_by_day[date_key]["total_products"] += sum(
                    sale_product.quantity for sale_product in sale.products
                )
                sales_by_day[date_key]["total_income"] += sum(
                    sale_product.quantity * sale_product.product.price
                    for sale_product in sale.products
                )

            # Formatear los datos para la plantilla
            for date, data in sales_by_day.items():
                # Ordenar los productos por nombre
                sorted_products = sorted(
                    data["products"].items(),
                    key=lambda item: item[
                        0
                    ],  # Ordenar por el nombre del producto (item[0])
                )

                daily_sales.append(
                    {
                        "date": date,
                        "total_products": data["total_products"],
                        "total_income": data["total_income"],
                        "products": [
                            {
                                "name": name,
                                "quantity": product["quantity"],
                                "total_amount": product["total_amount"],
                                "orders": sorted(
                                    list(product["orders"]), key=lambda order: order[1]
                                ),
                            }
                            for name, product in sorted_products  # Usar los productos ordenados
                        ],
                    }
                )

        except ValueError:
            # Manejar errores si el formato del mes es incorrecto
            flash("Por favor, selecciona un mes válido.", "error")

    # logging.basicConfig(level=logging.DEBUG)
    # logging.debug("Datos generados para el reporte: %s", daily_sales)

    return render_template(
        "report/monthly_sales_by_product.html",
        business=business,
        daily_sales=daily_sales,
        daily_sales_json=json.dumps(daily_sales),
        selected_month=selected_month,
    )


@bp.route("/monthly/sales-by-date", methods=["GET", "POST"])
def monthly_sales_by_date(business_id):
    # Obtener el negocio
    business = Business.query.get_or_404(business_id)

    # Inicializar variables
    all_sales = []
    daily_sales = []
    excluded_sales = [  # Ventas excluidas almacenadas en la sesión
        int(excluded_sale) for excluded_sale in session.get("excluded_sales", [])
    ]
    selected_month = None

    if request.method == "POST":
        # Obtener el mes seleccionado desde el formulario
        month_str = request.form.get("month")
        if not month_str:
            flash("Por favor, selecciona un mes.", "error")
            return render_template(
                "report/monthly_sales_by_date.html",
                business=business,
                daily_sales=daily_sales,
                excluded_sales=excluded_sales,
                selected_month=selected_month,
            )

        try:
            # Convertir el mes a un objeto datetime
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
            start_date = selected_month.replace(day=1)
            end_date = start_date + relativedelta(months=1, days=-1)

            # Consultar todas las órdenes dentro del rango de fechas
            all_sales = (
                Sale.query.filter(
                    Sale.business_id == business.id,
                    Sale.date.between(start_date, end_date),
                )
                .join(Sale.products)  # Join con SaleProduct
                .join(SaleProduct.product)  # Join con Product
                .order_by(Sale.date.asc())  # Ordenar por fecha
                .all()
            )

            # Filtrar las ventas excluidas
            filtered_sales = [
                sale for sale in all_sales if sale.sale_number not in excluded_sales
            ]

            # Procesar los datos
            sales_by_day = defaultdict(
                lambda: {"sales": [], "total_products": 0, "total_income": 0}
            )

            for sale in filtered_sales:
                date_key = sale.date.strftime("%Y-%m-%d")

                # Calcular totales para esta venta
                total_products = sum(sp.quantity for sp in sale.products)
                total_income = sum(
                    sp.quantity * sp.product.price for sp in sale.products
                )
                sorted_products = sorted(
                    sale.products,
                    key=lambda sale_product: sale_product.product.name,
                )
                # Crear un diccionario para acumular las cantidades por producto
                reduced_products_dict = defaultdict(
                    lambda: {"quantity": 0, "import": 0}
                )

                # Recorrer la lista de productos y acumular las cantidades
                for sale_product in sorted_products:
                    name = sale_product.product.name
                    quantity = sale_product.quantity
                    price = sale_product.product.price

                    # Acumular la cantidad y asignar el precio (asumiendo que el precio es el mismo para cada producto)
                    reduced_products_dict[name]["quantity"] += quantity
                    reduced_products_dict[name]["import"] = quantity * price

                # Convertir el diccionario a una lista de productos reducidos
                saled_products = [
                    {
                        "name": name,
                        "quantity": data["quantity"],
                        "import": data["import"],
                    }
                    for name, data in reduced_products_dict.items()
                ]

                # Agregar la venta a la lista de ventas del día
                sales_by_day[date_key]["sales"].append(
                    {
                        "sale_number": sale.sale_number,
                        "total_products": total_products,
                        "total_income": total_income,
                        "products": saled_products,
                    }
                )

                # Actualizar totales acumulados para el día
                sales_by_day[date_key]["total_products"] += total_products
                sales_by_day[date_key]["total_income"] += total_income

            # Formatear los datos para la plantilla
            for date, data in sales_by_day.items():
                daily_sales.append(
                    {
                        "date": date,
                        "sales": data["sales"],
                        "total_products": data["total_products"],
                        "total_income": data["total_income"],
                    }
                )

        except ValueError:
            # Manejar errores si el formato del mes es incorrecto
            flash("Por favor, selecciona un mes válido.", "error")

    # Logging para depuración
    # logging.debug("Ventas en json: %s", json.dumps(daily_sales))

    return render_template(
        "report/monthly_sales_by_date.html",
        business=business,
        all_sales=all_sales,
        daily_sales=daily_sales,
        daily_sales_json=json.dumps(daily_sales),
        excluded_sales=excluded_sales,
        selected_month=selected_month,
    )


@bp.route("/exclude-sales", methods=["POST"])
def exclude_sales():
    data = request.get_json()
    selected_sales = data.get("sales", [])

    # Guardar las ventas excluidas en la sesión
    session["excluded_sales"] = selected_sales

    # Logging para depuración
    # logging.debug("Ventas excluidas en exclude_sales: %s", session["excluded_sales"])

    return jsonify({"message": "Ventas excluidas correctamente"}), 200


@bp.route("/export-to-excel/sales-by-day", methods=["POST"])
def export_to_excel_sales_by_day(business_id):
    # Obtener el negocio
    business = Business.query.get_or_404(business_id)

    # Recuperar los datos del reporte mensual
    selected_month = request.form.get("selected_month")
    daily_sales_json = request.form.get("daily_sales_export")
    if not daily_sales_json:
        flash("No hay datos disponibles para exportar.", "error")
        return redirect(url_for("report.monthly_sales_by_day", business_id=business_id))

    try:
        # Convertir los datos JSON a una estructura de Python
        data = json.loads(daily_sales_json)
    except json.JSONDecodeError:
        flash("Los datos recibidos no son válidos.", "error")
        return redirect(url_for("report.monthly_report", business_id=business_id))

    # Crear un archivo Excel
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Reporte Mensual"

    # Encabezados
    headers = [
        "Fecha",
        "Orden",
        "Producto",
        "Cantidad",
        "Importe",
    ]
    sheet.append(headers)

    # Rellenar el archivo con los datos
    for day in data:
        date = day["date"]
        for sale in day["sales"]:
            sale_number = sale["sale_number"]
            for product in sale["products"]:
                row = [
                    date,
                    sale_number,
                    product["name"],
                    product["quantity"],
                    product["import"],
                ]
                sheet.append(row)

    # Guardar el archivo en memoria
    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)

    # Enviar el archivo como respuesta
    return send_file(
        excel_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{selected_month}_reporte_mensual_por_dia_{business.name}.xlsx",
    )


@bp.route("/export-to-excel/sales-by-product", methods=["POST"])
def export_to_excel_sales_by_product(business_id):
    # Obtener el negocio
    business = Business.query.get_or_404(business_id)

    # Recuperar los datos del reporte mensual
    daily_sales_json = request.form.get("daily_sales_export")
    if not daily_sales_json:
        flash("No hay datos disponibles para exportar.", "error")
        return redirect(
            url_for("report.monthly_sales_by_produc", business_id=business_id)
        )

    try:
        # Convertir los datos JSON a una estructura de Python
        data = json.loads(daily_sales_json)
    except json.JSONDecodeError:
        flash("Los datos recibidos no son válidos.", "error")
        return redirect(
            url_for("report.monthly_sales_by_produc", business_id=business_id)
        )

    # Procesar los datos para agrupar por producto
    product_summary = defaultdict(
        lambda: {"quantity": 0, "total_amount": 0, "orders": set()}
    )

    for day in data:
        if "products" not in day:
            flash("Los datos recibidos no tienen el formato esperado.", "error")
            return redirect(
                url_for("report.monthly_sales_by_produc", business_id=business_id)
            )

        for product in day["products"]:
            if (
                "name" not in product
                or "quantity" not in product
                or "total_amount" not in product
                or "orders" not in product
            ):
                flash("Los datos recibidos no tienen el formato esperado.", "error")
                return redirect(
                    url_for("report.monthly_sales_by_produc", business_id=business_id)
                )

            product_name = product["name"]
            product_summary[product_name]["quantity"] += product["quantity"]
            product_summary[product_name]["total_amount"] += product["total_amount"]

            # Agregar los números de orden al conjunto
            for order in product["orders"]:
                product_summary[product_name]["orders"].add(order[1])

    # Logging de los datos generados
    # logging.debug("Datos generados para el reporte: %s", dict(product_summary))

    # Crear un archivo Excel
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Reporte Mensual"

    # Encabezados
    headers = ["PRODUCTO", "CANTIDAD", "IMPORTE", "ORDENES"]
    sheet.append(headers)

    # Rellenar el archivo con los datos
    for product_name, details in product_summary.items():
        row = [
            product_name,
            details["quantity"],
            details["total_amount"],
            ", ".join(
                f"[{order}]" for order in sorted(list(details["orders"]))
            ),  # Formato [1], [2], [3]
        ]
        sheet.append(row)

    # Guardar el archivo en memoria
    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)

    # Enviar el archivo como respuesta
    return send_file(
        excel_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"reporte_mensual_por_producto_{business.name}.xlsx",
    )
