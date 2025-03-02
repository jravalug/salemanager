from flask import Blueprint, jsonify
from app.models import Product

bp = Blueprint("api_product", __name__)


@bp.route("/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    product_list = [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        for product in products
    ]
    return jsonify(product_list)
