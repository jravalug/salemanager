from flask import Blueprint, jsonify
from app.models import Business

bp = Blueprint("api_business", __name__)


@bp.route("/businesses", methods=["GET"])
def get_businesses():
    businesses = Business.query.all()
    business_list = [
        {
            "id": business.id,
            "name": business.name,
            "description": business.description,
        }
        for business in businesses
    ]
    return jsonify(business_list)
