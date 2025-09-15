from flask import (
    Blueprint,
    current_app,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from matplotlib.dates import relativedelta
from sqlalchemy.orm import joinedload
from collections import defaultdict
from datetime import datetime
from sqlite3 import IntegrityError
from app.extensions import db
from app.forms import (
    SaleForm,
    SaleDetailForm,
    UpdateSaleDetailForm,
    RemoveSaleDetailForm,
)

from app.services import SalesService, BusinessService
from app.models import Business, Product, Sale, SaleDetail
from app.utils.sale_utils import calculate_month_totals, group_sales_by_month
import logging

bp = Blueprint("sale", __name__, url_prefix="/business/<int:business_id>/sale")

# Obtener el logger de la aplicación
logger = logging.getLogger(__name__)


@bp.route("/list", methods=["GET", "POST"])
def sales(business_id):
    """
    Muestra la lista de ventas y maneja la creación de nuevas ventas.
    """
    sale_service = SalesService()
    business_service = BusinessService()

    # Obtener el negocio
    try:
        business = Business.query.get_or_404(business_id)

        # Determinar los filtros para las ventas
        filters = business_service.get_parent_filters(business=business)

    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("business.business_list"))

    # Obtener todas las ventas con sus productos cargados
    all_sales = (
        Sale.query.options(joinedload(Sale.products))
        .filter_by(**filters)
        .order_by(Sale.date.desc())
        .all()
    )
    print(f"Los filtros son: {business.is_general}")

    # Crear una instancia del formulario
    add_sale_form = SaleForm(
        parent_business_id=filters["business_id"], prefix="add_sale"
    )

    # Manejar la validación y creación de nuevas ventas
    if add_sale_form.validate_on_submit():
        try:
            new_sale = sale_service.add_sale(
                business=business,
                form=add_sale_form,
            )
            flash("Venta creada correctamente", "success")
            return redirect(
                url_for(
                    "sale.details",
                    business_id=business.id,
                    sale_id=new_sale.id,
                )
            )
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de integridad al crear la venta: {str(e)}")
            flash("Error: Ya existe una venta con estos datos.", "error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error inesperado al crear la venta: {str(e)}")
            flash(f"Error inesperado: {str(e)}", "error")
            return redirect(url_for("sale.sales", business_id=business.id))

    # Agrupar ventas por mes y calcular totales
    sales_by_months = group_sales_by_month(all_sales)
    month_totals = calculate_month_totals(sales_by_months)

    # Renderizar la plantilla con los datos
    return render_template(
        "sale/list.html",
        business=business,
        sales_by_months=sales_by_months,
        month_totals=month_totals,
        add_sale_form=add_sale_form,
    )


@bp.route("/<int:sale_id>", methods=["GET", "POST"])
def details(business_id, sale_id):
    """
    Muestra los detalles de una venta específica y maneja las operaciones relacionadas.
    """
    print(f"El negocio es: {business_id}. La venta es: {sale_id}")
    sale_service = SalesService()
    business_service = BusinessService()

    # Obtener el negocio
    try:
        business = Business.query.get_or_404(business_id)

        # Determinar los filtros según el tipo de negocio
        filters = business_service.get_parent_filters(business=business)

        sale = sale_service.get_sale(sale_id, filters["business_id"])
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("sale.sales", business_id=business_id))

    # Inicialización de formularios
    add_product_form = SaleDetailForm(prefix="add_product")
    update_product_form = UpdateSaleDetailForm(prefix="update_product")
    remove_product_form = RemoveSaleDetailForm(prefix="remove_product")
    update_sale_form = SaleForm(
        parent_business_id=filters["business_id"], obj=sale, prefix="update_sale"
    )
    add_sale_form = SaleForm(
        parent_business_id=filters["business_id"], prefix="add_sale"
    )

    # Cargar opciones de productos disponibles
    add_product_form.set_product_choices(
        sale_service.get_available_products(filters["business_id"])
    )

    # Función auxiliar para redirigir a los detalles de la venta
    def redirect_to_sale():
        return redirect(
            url_for("sale.details", business_id=business.id, sale_id=sale.id)
        )

    # Procesar formularios
    try:
        if remove_product_form.validate_on_submit():
            sale_detail = SaleDetail.query.get_or_404(
                remove_product_form.sale_detail_id.data
            )
            removed_product = sale_service.remove_product_from_sale(
                sale=sale, sale_detail=sale_detail
            )
            flash(f"Producto '{removed_product.name}' eliminado", "success")
            return redirect_to_sale()

        if add_product_form.validate_on_submit():
            new_sale_detail = sale_service.add_product_to_sale(
                sale=sale,
                product_id=add_product_form.product_id.data,
                quantity=add_product_form.quantity.data,
                discount=add_product_form.discount.data,
            )
            flash(f"Producto '{new_sale_detail.product.name}' agregado", "success")
            return redirect_to_sale()

        if update_product_form.validate_on_submit():
            sale_detail = SaleDetail.query.get_or_404(
                update_product_form.sale_detail_id.data
            )

            sale_service.update_sale_detail(
                sale=sale,
                sale_detail=sale_detail,
                quantity=update_product_form.quantity.data,
                discount=update_product_form.discount.data,
            )
            flash("Producto actualizado correctamente", "success")
            return redirect_to_sale()

        if update_sale_form.validate_on_submit():
            sale_service.update_sale(sale=sale, form=update_sale_form)
            flash("Venta actualizada correctamente", "success")
            return redirect_to_sale()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error en venta {sale_id}: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return redirect_to_sale()

    # Manejar la validación y creación de nuevas ventas
    if add_sale_form.validate_on_submit():
        try:
            new_sale = sale_service.add_sale(
                business=business,
                form=add_sale_form,
            )
            flash("Venta creada correctamente", "success")
            return redirect(
                url_for(
                    "sale.details",
                    business_id=business.id,
                    sale_id=new_sale.id,
                )
            )
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Error de integridad al crear la venta: {str(e)}")
            flash("Error: Ya existe una venta con estos datos.", "error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error inesperado al crear la venta: {str(e)}")
            flash(f"Error inesperado: {str(e)}", "error")
            return redirect(url_for("sale.sales", business_id=business.id))

    # Obtener productos para mostrar
    sale_details = sale_service.get_sale_details(sale.id)

    return render_template(
        "sale/details.html",
        business=business,
        sale=sale,
        products=sale_details,
        add_product_form=add_product_form,
        remove_product_form=remove_product_form,
        update_product_form=update_product_form,
        update_sale_form=update_sale_form,
        add_sale_form=add_sale_form,
    )


@bp.route("/test", methods=["GET", "POST"])
def test(business_id):
    business = Business.query.get_or_404(business_id)
    sorted_sales = []
    selected_month = None

    if request.method == "POST":
        month_str = request.form.get("month")
        if not month_str:
            flash("Por favor, selecciona un mes.", "error")
            return redirect(url_for("sale.test", business_id=business_id))

        try:
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
            start_date = selected_month.replace(day=1)
            end_date = start_date + relativedelta(months=1, days=-1)

            # Consultar ventas del mes
            monthly_sales = (
                Sale.query.filter(
                    Sale.business_id == business.id,
                    Sale.date.between(start_date, end_date),
                    Sale.discount != 0,
                )
                .join(Sale.products)
                .join(SaleDetail.product)
                .all()
            )

            # Procesar cada venta
            sorted_sales = []
            for sale in monthly_sales:
                sorted_sales.append(
                    {
                        "importe": round(sale.total_amount, 2),
                        "fecha": sale.date.strftime("%d/%m/%Y"),  # Formato DD/MM/YYYY
                        "numero_venta": sale.sale_number,
                    }
                )

            # Ordenar por importe descendente
            sorted_sales.sort(key=lambda x: x["importe"], reverse=True)

        except ValueError:
            flash("Formato de mes inválido. Usa YYYY-MM.", "error")

    return render_template(
        "sale/test.html",
        business=business,
        sorted_sales=sorted_sales,
        selected_month=selected_month,
    )


@bp.route("/test1", methods=["GET", "POST"])
def test1(business_id):
    business = Business.query.get_or_404(business_id)
    grouped_sales = []
    selected_month = None
    print(f"Testing amount: {business.id}")

    if request.method == "POST":
        month_str = request.form.get("month")
        if not month_str:
            flash("Selecciona un mes válido.", "error")
            return redirect(url_for("sale.sales", business_id=business.id))

        try:
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
            start_date = selected_month.replace(day=1)
            end_date = start_date + relativedelta(months=1, days=-1)

            # Obtener ventas del mes
            monthly_sales = (
                Sale.query.filter(
                    Sale.business_id == business.id,
                    Sale.date.between(start_date, end_date),
                )
                .join(Sale.products)
                .join(SaleDetail.product)
                .filter(
                    SaleDetail.unit_price != Product.price,
                    Product.category != "cocteleria",
                )
                .order_by(Sale.date.asc())
                .all()
            )

            # Agrupar por importe total de la venta
            importe_groups = defaultdict(lambda: [])
            for sale in monthly_sales:
                print(f"Testing amount: {sale.total_amount}")
                importe_groups[str(sale.total_amount)].append(
                    {
                        "date": sale.date.strftime("%d/%m/%Y"),
                        "sale_number": sale.sale_number,
                        "sale_id": sale.id,
                        "excluded": sale.excluded,
                    }
                )

            # Ordenar por importe descendente
            grouped_sales = sorted(
                importe_groups.items(), key=lambda x: x[0], reverse=True
            )

        except ValueError:
            flash("Formato de mes inválido. Usa YYYY-MM.", "error")

    return render_template(
        "sale/test1.html",
        business=business,
        grouped_sales=grouped_sales,
        selected_month=selected_month,
    )


@bp.route("/test2", methods=["GET", "POST"])
def categorized_report(business_id):
    business = Business.query.get_or_404(business_id)
    categorized_sales = defaultdict(lambda: [])
    selected_month = None

    if request.method == "POST":
        month_str = request.form.get("month")
        if not month_str:
            flash("Selecciona un mes válido.", "error")
            return redirect(url_for("sale.categorized_report", business_id=business_id))

        try:
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
            start_date = selected_month.replace(day=1)
            end_date = start_date + relativedelta(months=1, days=-1)

            # Consultar ventas del mes
            monthly_sales = (
                Sale.query.filter(
                    Sale.business_id == business.id,
                    Sale.date.between(start_date, end_date),
                )
                .join(Sale.products)
                .order_by(Sale.date.asc())
                .all()
            )

            # Clasificar ventas por rango de productos
            for sale in monthly_sales:
                total_products = sum(sp.quantity for sp in sale.products)
                total_income = sale.total_amount

                if total_products <= 2:
                    category = "1-2 productos"
                elif 3 <= total_products <= 5:
                    category = "3-5 productos"
                elif 6 <= total_products <= 10:
                    category = "6-10 productos"
                elif 11 <= total_products <= 15:
                    category = "11-15 productos"
                elif 16 <= total_products <= 20:
                    category = "16-20 productos"
                else:
                    category = "21+ productos"

                categorized_sales[category].append(
                    {
                        "date": sale.date.strftime("%d/%m/%Y"),
                        "sale_id": sale.id,
                        "sale_number": sale.sale_number,
                        "total_products": total_products,
                        "total_income": round(total_income, 2),
                    }
                )

            # Ordenar categorías y ventas internas
            ordered_categories = [
                "1-2 productos",
                "3-5 productos",
                "6-10 productos",
                "11-15 productos",
                "16-20 productos",
                "21+ productos",
            ]
            categorized_sales = {
                cat: sorted(sales_list, key=lambda x: x["date"])
                for cat, sales_list in categorized_sales.items()
                if cat in ordered_categories
            }

        except ValueError:
            flash("Formato de mes inválido. Usa YYYY-MM.", "error")

    return render_template(
        "sale/test2.html",
        business=business,
        categorized_sales=categorized_sales,
        selected_month=selected_month,
    )


@bp.route("/coctel", methods=["GET", "POST"])
def coctel_report(business_id):
    business = Business.query.get_or_404(business_id)
    coctel_sales = defaultdict(lambda: [])
    selected_month = None

    if request.method == "POST":
        month_str = request.form.get("month")
        if not month_str:
            flash("Selecciona un mes válido.", "error")
            return redirect(url_for("sale.categorized_report", business_id=business_id))

        try:
            selected_month = datetime.strptime(month_str, "%Y-%m").date()
            start_date = selected_month.replace(day=1)
            end_date = start_date + relativedelta(months=1, days=-1)

            # Consultar ventas del mes
            monthly_sales = (
                Sale.query.filter(
                    Sale.business_id == business.id,
                    Sale.date.between(start_date, end_date),
                )
                .join(Sale.products)
                .join(SaleDetail.product)
                .filter(Product.category == "cocteleria")
                .order_by(Sale.date.asc())
                .all()
            )

            # Clasificar ventas por rango de productos
            for sale in monthly_sales:
                total_products = sum(sp.quantity for sp in sale.products)
                total_income = sale.total_amount

                categorized_sales[category].append(
                    {
                        "date": sale.date.strftime("%d/%m/%Y"),
                        "sale_id": sale.id,
                        "sale_number": sale.sale_number,
                        "total_products": total_products,
                        "total_income": round(total_income, 2),
                    }
                )

            # Ordenar categorías y ventas internas
            ordered_categories = [
                "1-2 productos",
                "3-5 productos",
                "6-10 productos",
                "11-15 productos",
                "16-20 productos",
                "21+ productos",
            ]
            categorized_sales = {
                cat: sorted(sales_list, key=lambda x: x["date"])
                for cat, sales_list in categorized_sales.items()
                if cat in ordered_categories
            }

        except ValueError:
            flash("Formato de mes inválido. Usa YYYY-MM.", "error")

    return render_template(
        "sale/test2.html",
        business=business,
        categorized_sales=categorized_sales,
        selected_month=selected_month,
    )
