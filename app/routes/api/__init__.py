# app/routes/api/__init__.py

from .business import bp as business_bp
from .income import bp as income_bp
from .product import bp as product_bp


def register_api_blueprints(app):
    # Registrar los Blueprints con un prefijo de URL
    app.register_blueprint(business_bp, url_prefix="/api/business")
    app.register_blueprint(
        income_bp,
        url_prefix="/api/clients/<string:client_slug>/business/<string:business_slug>/income",
    )
    app.register_blueprint(
        product_bp,
        url_prefix="/api/clients/<string:client_slug>/business/<string:business_slug>/product",
    )
