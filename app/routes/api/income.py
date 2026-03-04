from flask import Blueprint, jsonify

from app.services import IncomeService

bp = Blueprint("api_income", __name__)

income_service = IncomeService()


@bp.route("/sales", methods=["GET"])
@bp.route("/records", methods=["GET"])
def get_income_sales(client_slug, business_slug):
    try:
        business, _ = income_service.resolve_business_and_filters(
            client_slug=client_slug,
            business_slug=business_slug,
        )
    except ValueError:
        return jsonify([])
    return jsonify(income_service.get_incomes_api_data(business.id))
