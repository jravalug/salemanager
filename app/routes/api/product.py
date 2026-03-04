from flask import Blueprint, jsonify
from app.services import ProductService

bp = Blueprint("api_product", __name__)

product_service = ProductService()


@bp.route("/products", methods=["GET"])
def get_products(client_slug, business_slug):
    return jsonify(product_service.get_products_api_data(client_slug, business_slug))
