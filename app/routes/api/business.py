from flask import Blueprint, jsonify
from app.services import BusinessService

bp = Blueprint("api_business", __name__)

business_service = BusinessService()


@bp.route("/businesses", methods=["GET"])
def get_businesses():
    return jsonify(business_service.get_businesses_api_data())
