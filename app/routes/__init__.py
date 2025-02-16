from .main import bp as main_bp
from .business import bp as business_bp
from .sale import bp as sales_bp
from .product import bp as products_bp
from .reports import bp as reports_bp


def register_blueprints(app):
    """
    Registra todos los blueprints en la aplicación.
    """
    app.register_blueprint(main_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(reports_bp)
