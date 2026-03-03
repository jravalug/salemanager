import logging
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from config import get_config
from .logging_config import setup_logging

from .context_processors import inject_now, inject_request
from .extensions import db, migrate
from .filters import (
    format_currency_filter,
    format_payment_method,
    format_sale_status,
    format_sale_status_badge,
)
from .routes import register_web_blueprints
from .routes.api import register_api_blueprints

# Configurar logging
logger = logging.getLogger(__name__)

# Constantes
LIBSQL_DIALECT_NAME = "libsql"
LIBSQL_MODULE = "sqlalchemy_libsql"
LIBSQL_DIALECT_CLASS = "SQLiteDialect_libsql"


def create_app(env=None):
    """
    Flask application factory.

    Args:
        env (str, optional): Environment to use. Defaults to FLASK_ENV or 'development'.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load environment configuration
    _load_environment_config(env)

    # Apply configuration
    config_instance = _configure_app(app, env)

    # Setup logging
    setup_logging(app)

    # Setup database
    _setup_database(app, config_instance)

    # Register template components
    _register_template_components(app)

    # Register blueprints
    _register_blueprints(app)

    # Auto-update client accounting regimes
    _run_client_regime_auto_update(app)

    logger.info("🚀 Flask application created successfully")
    return app


def _load_environment_config(env):
    """Load environment variables from .env files for development/testing."""
    effective_env = env or os.environ.get("FLASK_ENV", "development")
    project_root = Path(__file__).resolve().parents[1]

    if effective_env in ("development", "testing"):
        env_local = project_root / ".env.local"
        env_default = project_root / ".env"

        if env_local.exists():
            load_dotenv(env_local)
            logger.debug(f"Loaded environment from {env_local}")
        elif env_default.exists():
            load_dotenv(env_default)
            logger.debug(f"Loaded environment from {env_default}")


def _configure_app(app, env):
    """Apply configuration to the Flask app."""
    config_class = get_config(env)
    config_instance = config_class()
    app.config.from_object(config_instance)
    logger.info(f"Applied {config_instance.ENV} configuration")
    return config_instance


def _setup_database(app, config_instance):
    """Initialize database extensions and register libsql dialect if needed."""
    # Register libsql dialect for Turso connections
    if LIBSQL_DIALECT_NAME in str(config_instance.SQLALCHEMY_DATABASE_URI):
        _register_libsql_dialect()

    # Initialize database extensions
    db.init_app(app)
    migrate.init_app(app, db)
    logger.info("Database extensions initialized")


def _register_libsql_dialect():
    """Register the libsql dialect for SQLAlchemy."""
    try:
        import sqlalchemy_libsql
        from sqlalchemy.dialects import registry

        registry.register(LIBSQL_DIALECT_NAME, LIBSQL_MODULE, LIBSQL_DIALECT_CLASS)
        logger.info("🔧 Registered libsql dialect for Turso connections")
    except ImportError as e:
        logger.error(
            f"❌ Failed to register libsql dialect: {LIBSQL_MODULE} not installed. "
            f"Error: {e}"
        )
        raise RuntimeError(
            f"sqlalchemy-libsql is required for Turso connections. "
            f"Please install it with: pip install sqlalchemy-libsql"
        ) from e


def _register_template_components(app):
    """Register custom template filters and context processors."""
    # Register filters
    filters = {
        "currency": format_currency_filter,
        "format_payment_method": format_payment_method,
        "format_sale_status": format_sale_status,
        "format_sale_status_badge": format_sale_status_badge,
    }

    for name, func in filters.items():
        app.template_filter(name)(func)

    # Register context processors
    app.context_processor(inject_now)
    app.context_processor(inject_request)

    logger.debug("Template components registered")


def _register_blueprints(app):
    """Register application blueprints."""
    register_web_blueprints(app)
    register_api_blueprints(app)
    logger.debug("Blueprints registered")


def _run_client_regime_auto_update(app):
    """Evalúa y aplica transición de régimen contable de clientes en enero."""
    if not app.config.get("ACCOUNTING_REGIME_AUTO_UPDATE", True):
        logger.info("Client regime auto-update is disabled by configuration")
        return

    auto_update_month = int(app.config.get("ACCOUNTING_REGIME_AUTO_UPDATE_MONTH", 1))
    today = date.today()

    if today.month < auto_update_month:
        logger.debug(
            "Skipping client regime auto-update until month %s", auto_update_month
        )
        return

    try:
        from .services.client_accounting_service import ClientAccountingService

        with app.app_context():
            summary = ClientAccountingService().evaluate_annual_regime_transition(
                process_date=today
            )

        logger.info(
            "Client regime auto-update completed: reviewed_year=%s, target_year=%s, "
            "evaluated_clients=%s, updated_clients=%s",
            summary["reviewed_year"],
            summary["target_year"],
            summary["evaluated_clients"],
            summary["updated_clients"],
        )
    except Exception as exc:
        logger.warning("Client regime auto-update skipped: %s", exc)
