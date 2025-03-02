# app/routes/api/__init__.py

from .business import bp as business_bp
from .sale import bp as sale_bp
from .product import bp as product_bp


def register_api_blueprints(app):
    # Registrar los Blueprints con un prefijo de URL
    app.register_blueprint(business_bp, url_prefix="/api/business")
    app.register_blueprint(sale_bp, url_prefix="/api/sale")
    app.register_blueprint(product_bp, url_prefix="/api/product")
