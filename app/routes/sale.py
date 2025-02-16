from flask import Blueprint, render_template, redirect, url_for, flash, request
from collections import defaultdict
from datetime import datetime
from sqlite3 import IntegrityError
from app.extensions import db
from app.forms import EditSaleProductForm
from app.models import Business, Product, Sale, SaleProduct

bp = Blueprint("sale", __name__, url_prefix="/business/<int:business_id>/sale")


@bp.route("/list", methods=["GET", "POST"])
def list(business_id):
    business = Business.query.get_or_404(business_id)

    if request.method == "POST":
        date_str = request.form["date"]
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Obtener el último número de venta para esta ubicación y año
        last_sale = (
            Sale.query.filter_by(
                business_id=business.id,
                # date=date  # Asegúrate de que sea del mismo año si es necesario
            )
            .order_by(Sale.sale_number.desc())
            .first()
        )

        year = date.year

        if last_sale and last_sale.year == year:
            new_sale_number = last_sale.sale_number + 1
        else:
            new_sale_number = 1

        # Verificar que el par (business_id, sale_number) no exista
        try:
            new_sale = Sale(
                sale_number=new_sale_number,
                date=date,
                year=date.year,
                business_id=business.id,
            )
            db.session.add(new_sale)
            db.session.commit()
            flash("Venta creada correctamente", "success")
            return redirect(
                url_for(
                    "sale.add_products",
                    business_id=business.id,
                    sale_id=new_sale.id,
                )
            )
        except IntegrityError:
            db.session.rollback()
            flash("Error al crear la venta. El número ya existe.", "danger")
            return redirect(url_for("sale.list", business_id=business.id))

    # Obtener todas las órdenes
    all_sales = (
        Sale.query.filter_by(business_id=business.id).order_by(Sale.date.desc()).all()
    )

    # Agrupar órdenes por mes y fecha
    sales_by_months = defaultdict(
        lambda: defaultdict(
            lambda: {"total_products": 0, "total_income": 0, "sales": []}
        )
    )
    month_totals = defaultdict(float)

    for sale in all_sales:
        month_key = sale.date.strftime("%Y-%m")
        date_key = sale.date.strftime("%Y-%m-%d")

        # Calcular totales por venta
        total_products = sum(sale_product.quantity for sale_product in sale.products)
        total_income = sum(
            sale_product.product.price * sale_product.quantity
            for sale_product in sale.products
        )

        # Agregar datos a la estructura
        sales_by_months[month_key][date_key]["total_products"] += total_products
        sales_by_months[month_key][date_key]["total_income"] += total_income
        sales_by_months[month_key][date_key]["sales"].append(sale)

        # Acumular totales por mes
        month_totals[month_key] += total_income

    # Convertir defaultdict a diccionarios regulares para Jinja2
    sales_by_months = {month: dict(dates) for month, dates in sales_by_months.items()}
    month_totals = dict(month_totals)

    return render_template(
        "sale/list.html",
        business=business,
        sales_by_months=sales_by_months,
        month_totals=month_totals,
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
