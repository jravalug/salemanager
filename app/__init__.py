from flask import Flask
from config import Config
from .extensions import db, migrate
from .filters import (
    format_currency_filter,
    format_payment_method,
    format_sale_status,
    format_sale_status_badge,
)
from .context_processors import inject_now
from app.routes import register_web_blueprints
from app.routes.api import register_api_blueprints


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)

    # Registrar filtros personalizados
    app.template_filter("currency")(format_currency_filter)
    app.template_filter("format_payment_method")(format_payment_method)
    app.template_filter("format_sale_status")(format_sale_status)
    app.template_filter("format_sale_status_badge")(format_sale_status_badge)

    # Registrar context processors
    app.context_processor(inject_now)

    # Registrar blueprints
    register_web_blueprints(app)
    register_api_blueprints(app)

    return app
