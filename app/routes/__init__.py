from .main import bp as main_bp
from .business import bp as business_bp
from .income import bp as income_bp
from .cash_flow import bp as cash_flow_bp
from .product import bp as products_bp
from .reports import bp as reports_bp
from .inventory import bp as inventory_bp
from .client import bp as clients_bp


def register_web_blueprints(app):
    """
    Registra todos los blueprints en la aplicación.
    """
    app.register_blueprint(main_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(cash_flow_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)  # Registra el blueprint de la API
    app.register_blueprint(clients_bp)
