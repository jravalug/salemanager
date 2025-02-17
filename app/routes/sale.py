from flask import Blueprint, render_template, redirect, url_for, flash, request

from sqlalchemy.orm import joinedload
from collections import defaultdict
from datetime import datetime
from sqlite3 import IntegrityError
from app.extensions import db
from app.forms import SaleForm, EditSaleProductForm
from app.models import Business, Product, Sale, SaleProduct
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
    # Obtener el negocio
    business = Business.query.get_or_404(business_id)

    # Crear una instancia del formulario
    form = SaleForm()
    logger.debug(f"Formulario de venta creado para negocio {business.name}")

    if form.validate_on_submit():  # Validar el formulario
        date = form.date.data  # Obtener la fecha validada

        # Registrar la fecha en el log
        logger.debug(f"Fecha de venta ingresada: {date}")

        # Crear la nueva venta (el sale_number se genera automáticamente)
        try:
            new_sale = Sale(
                date=date,
                business_id=business.id,
            )
            db.session.add(new_sale)
            db.session.commit()
            flash("Venta creada correctamente.", "success")
            return redirect(
                url_for(
                    "sale.add_products",
                    business_id=business.id,
                    sale_id=new_sale.id,
                )
            )
        except IntegrityError:
            db.session.rollback()
            flash("Error al crear la venta. Inténtalo nuevamente.", "danger")
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
        form=form,  # Pasar el formulario a la plantilla
    )


@bp.route(
    "/<int:sale_id>/add_products",
    methods=["GET", "POST"],
)
def add_products(business_id, sale_id):
    business = Business.query.get_or_404(business_id)

    sale = Sale.query.get_or_404(sale_id)
    if request.method == "POST":
        product_id = int(request.form["product_id"])
        quantity = int(request.form["quantity"])
        sale_product = SaleProduct(
            sale_id=sale.id, product_id=product_id, quantity=quantity
        )
        db.session.add(sale_product)
        db.session.commit()
        flash("Producto agregado a la venta", "success")
        return redirect(
            url_for("sale.add_products", business_id=business.id, sale_id=sale.id)
        )

    products_list = (
        Product.query.filter_by(business_id=business.id)
        .order_by(Product.name.asc())
        .all()
    )

    total = sum(
        sale_product.product.price * sale_product.quantity
        for sale_product in sale.products
    )

    return render_template(
        "sale/add_products.html",
        business=business,
        sale=sale,
        products=products_list,
        total=total,
    )


@bp.route(
    "/<int:sale_id>/edit-product/<int:product_id>",
    methods=["GET", "POST"],
)
def edit_product(business_id, sale_id, product_id):
    # Obtener el negocio
    business = Business.query.get_or_404(business_id)

    # Obtener la venta y el producto específico
    sale = Sale.query.get_or_404(sale_id)
    sale_product = SaleProduct.query.filter_by(
        sale_id=sale_id, product_id=product_id
    ).first_or_404()

    # Crear el formulario
    form = EditSaleProductForm(
        obj=sale_product
    )  # Prellenar el formulario con los datos actuales

    if form.validate_on_submit():
        # Actualizar los datos del producto en la venta
        sale_product.quantity = form.quantity.data
        db.session.commit()

        flash("El producto ha sido actualizado correctamente.", "success")
        return redirect(
            url_for("sale.details", business_id=business_id, sale_id=sale_id)
        )

    return render_template(
        "sale/edit_product.html",
        business=business,
        sale=sale,
        sale_product=sale_product,
        form=form,
    )


@bp.route("/<int:sale_id>")
def details(business_id, sale_id):
    business = Business.query.get_or_404(business_id)

    sale = Sale.query.get_or_404(sale_id)
    total = sum(
        sale_product.product.price * sale_product.quantity
        for sale_product in sale.products
    )
    return render_template(
        "sale/details.html", business=business, sale=sale, total=total
    )


@bp.route(
    "/<int:sale_id>/remove-product/<int:product_id>",
    methods=["POST"],
)
def remove_product_from_sale(business_id, sale_id, product_id):
    # Obtener el negocio
    business = Business.query.get_or_404(business_id)

    # Obtener la venta y el producto específico
    sale_product = SaleProduct.query.filter_by(
        sale_id=sale_id, product_id=product_id
    ).first_or_404()

    # Acceder al nombre del producto antes de eliminarlo
    product_name = sale_product.product.name

    # Eliminar el producto de la venta
    db.session.delete(sale_product)
    db.session.commit()

    flash(
        f"El producto '{sale_product.product.name}' ha sido eliminado de la venta.",
        "success",
    )
    return redirect(url_for("sale.details", business_id=business_id, sale_id=sale_id))
