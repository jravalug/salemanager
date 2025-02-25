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

from app.services import SalesService
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

    try:
        business = Business.query.get_or_404(business_id)
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("business.list"))

    # Crear una instancia del formulario
    add_sale_form = SaleForm(prefix="add_sale")

    def handle_add_sale():

        print(f"Entrando al servicio add_sale")
        new_sale = sale_service.add_sale(
            form_data=add_sale_form, business_id=business.id
        )
        print(f"Saliendo del servicio add_sale con: {new_sale}")
        flash("Venta creada correctamente", "success")
        return new_sale

    try:
        if add_sale_form.validate_on_submit():
            print(f"Entrando al handle_add_sale")
            sale = handle_add_sale()
            print(f"Saliendo del handle_add_sale")
            return redirect(
                url_for(
                    "sale.details",
                    business_id=business.id,
                    sale_id=sale.id,
                )
            )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al crear la venta: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("sale.list", business_id=business.id))

    # Obtener todas las ventas con sus productos cargados
    all_sales = (
        Sale.query.options(joinedload(Sale.products))
        .filter_by(business_id=business.id)
        .order_by(Sale.date.desc())
        .all()
    )

    # Agrupar ventas por mes y fecha
    sales_by_months = group_sales_by_month(all_sales)

    return render_template(
        "sale/list.html",
        business=business,
        sales_by_months=sales_by_months,
        month_totals=calculate_month_totals(sales_by_months),
        add_sale_form=add_sale_form,  # Pasar el formulario a la plantilla
    )


@bp.route("/<int:sale_id>", methods=["GET", "POST"])
def details(business_id, sale_id):
    sale_service = SalesService()

    try:
        business = Business.query.get_or_404(business_id)
        sale = sale_service.get_sale(sale_id, business.id)
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("sale.list", business_id=business_id))

    # Inicialización de formularios
    add_product_form = SaleDetailForm(prefix="add_product")
    update_product_form = UpdateSaleDetailForm(prefix="update_product")
    remove_product_form = RemoveSaleDetailForm(prefix="remove_product")
    update_sale_form = SaleForm(request.form, obj=sale, prefix="update_sale")

    # Cargar opciones de productos
    add_product_form.set_product_choices(
        sale_service.get_available_products(business.id)
    )

    # Funciones helper con acceso al scope exterior
    def redirect_to_sale():
        return redirect(
            url_for("sale.details", business_id=business.id, sale_id=sale.id)
        )

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

    def handle_update_sale():
        updated_sale = sale_service.update_sale(sale=sale, form_data=update_sale_form)
        flash("Venta actualizada correctamente", "success")

    def handle_update_product():
        sale_detail_id = request.form.get("update_product-id")
        sale_detail = SaleDetail.query.get_or_404(sale_detail_id)
        updated_product = sale_service.update_sale_detail(
            sale_detail=sale_detail,
            quantity=update_product_form.quantity.data,
            discount=update_product_form.discount.data,
        )
        flash("Producto actualizado correctamente", "success")

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
