from flask import Blueprint, jsonify
from app.services import SalesService

bp = Blueprint("api_sale", __name__)

sale_service = SalesService()


@bp.route("/sales", methods=["GET"])
def get_sales(client_slug, business_slug):
    try:
        business, _ = sale_service.resolve_business_and_filters(
            client_slug=client_slug,
            business_slug=business_slug,
        )
    except ValueError:
        return jsonify([])
    return jsonify(sale_service.get_sales_api_data(business.id))
