from flask import Flask
from config import Config
from .extensions import db, migrate
from .filters import format_currency_filter
from .context_processors import inject_now
from app.routes import register_blueprints


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)

    # Registrar filtros personalizados
    app.template_filter("currency")(format_currency_filter)

    # Registrar context processors
    app.context_processor(inject_now)

    # Registrar blueprints
    register_blueprints(app)

    return app
