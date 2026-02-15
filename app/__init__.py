import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv
from config import get_config
from .extensions import db, migrate
from .filters import (
    format_currency_filter,
    format_payment_method,
    format_sale_status,
    format_sale_status_badge,
)
from .context_processors import inject_now, inject_request
from app.routes import register_web_blueprints
from app.routes.api import register_api_blueprints


def create_app(env=None):
    """
    Factory para crear la aplicación Flask.

    Args:
        env (str): Ambiente a usar. Si no se proporciona, usa FLASK_ENV.

    Returns:
        Flask: Instancia de la aplicación configurada.
    """
    app = Flask(__name__)

    # Decidir si debemos cargar archivos .env automáticamente.
    # Sólo cargar automáticamente en `development` o `testing` para evitar
    # filtrar secretos en staging/production.
    effective_env = env or os.environ.get("FLASK_ENV", "development")
    project_root = Path(__file__).resolve().parents[1]
    env_local = project_root / ".env.local"
    env_default = project_root / ".env"
    if effective_env in ("development", "testing"):
        if env_local.exists():
            load_dotenv(env_local)
        elif env_default.exists():
            load_dotenv(env_default)

    # Obtener y aplicar configuración según el ambiente
    config_class = get_config(env)
    app.config.from_object(config_class)

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
    app.context_processor(inject_request)

    # Registrar blueprints
    register_web_blueprints(app)
    register_api_blueprints(app)

    return app
