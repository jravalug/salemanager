from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Business, Product
from app.extensions import db


bp = Blueprint("product", __name__, url_prefix="/business/<int:business_id>/product")


@bp.route("/list", methods=["GET", "POST"])
def list(business_id):
    business = Business.query.get_or_404(business_id)

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        new_product = Product(name=name, price=price, business_id=business.id)
        db.session.add(new_product)
        db.session.commit()
        flash("Producto agregado correctamente", "success")
        return redirect(url_for("product.list", business_id=business.id))

    products_list = (
        Product.query.filter_by(business_id=business.id).order_by(Product.name).all()
    )
    return render_template(
        "product/list.html", business=business, products=products_list
    )


@bp.route("/<int:product_id>", methods=["POST"])
def update(business_id, product_id):
    business = Business.query.get_or_404(business_id)

    product = Product.query.get_or_404(product_id)
    product.name = request.form["name"]
    product.price = float(request.form["price"])
    db.session.commit()
    flash("Producto actualizado correctamente", "success")
    return redirect(url_for("product.list", business_id=business.id))
