from flask import (
    Blueprint,
    current_app,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

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
def list(business_id):
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
        return redirect(url_for("business.list"))

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
            new_sale = sale_service.add_sale(form_data=add_sale_form, business=business)
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
            return redirect(url_for("sale.list", business_id=business.id))

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
        return redirect(url_for("sale.list", business_id=business_id))

    # Inicialización de formularios
    add_product_form = SaleDetailForm(prefix="add_product")
    update_product_form = UpdateSaleDetailForm(prefix="update_product")
    remove_product_form = RemoveSaleDetailForm(prefix="remove_product")
    update_sale_form = SaleForm(
        parent_business_id=filters["business_id"], obj=sale, prefix="update_sale"
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

    # Manejadores de acciones específicas
    def handle_remove_product():
        sale_detail_id = remove_product_form.sale_detail_id.data
        removed_product = sale_service.remove_product_from_sale(
            sale=sale, sale_detail_id=sale_detail_id
        )
        flash(f"Producto '{removed_product.name}' eliminado", "success")

    def handle_add_product():
        new_sale_detail = sale_service.add_product_to_sale(
            sale=sale,
            product_id=add_product_form.product_id.data,
            quantity=add_product_form.quantity.data,
            discount=add_product_form.discount.data,
        )
        flash(f"Producto '{new_sale_detail.product.name}' agregado", "success")

    def handle_update_product():
        sale_detail_id = request.form.get("update_product-id")
        sale_detail = SaleDetail.query.get_or_404(sale_detail_id)
        updated_product = sale_service.update_sale_detail(
            sale_detail=sale_detail,
            quantity=update_product_form.quantity.data,
            discount=update_product_form.discount.data,
        )
        flash("Producto actualizado correctamente", "success")

    def handle_update_sale():
        updated_sale = sale_service.update_sale(sale=sale, form_data=update_sale_form)
        flash("Venta actualizada correctamente", "success")

    # Procesar formularios
    try:
        if remove_product_form.validate_on_submit():
            handle_remove_product()
            return redirect_to_sale()

        if add_product_form.validate_on_submit():
            handle_add_product()
            return redirect_to_sale()

        if update_product_form.validate_on_submit():
            handle_update_product()
            return redirect_to_sale()

        if update_sale_form.validate_on_submit():
            handle_update_sale()
            return redirect_to_sale()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error en venta {sale_id}: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return redirect_to_sale()

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
    )
