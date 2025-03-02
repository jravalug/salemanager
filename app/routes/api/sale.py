from flask import Blueprint, jsonify
from app.models import Sale

bp = Blueprint("api_sale", __name__)


@bp.route("/sales", methods=["GET"])
def get_sales():
    sales = Sale.query.all()
    sale_list = [
        {
            "id": sale.id,
            "date": sale.date.strftime("%Y-%m-%d"),
            "total": sum(sp.quantity * sp.product.price for sp in sale.products),
        }
        for sale in sales
    ]
    return jsonify(sale_list)
