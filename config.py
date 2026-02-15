import os
from pathlib import Path

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).parent


class Config:
    """Configuración base compartida por todos los ambientes"""

    # Seguridad y sesiones
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    # Sesiones
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 604800  # 7 días

    # Variables que deben ser sobrescritas en subclases
    SECRET_KEY = None
    SQLALCHEMY_DATABASE_URI = None
    DEBUG = False
    TESTING = False
    ENV = None


class DevelopmentConfig(Config):
    """Configuración para desarrollo local"""

    ENV = "development"
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR}/instance/dev.db"
    )

    # Caché deshabilitado en desarrollo
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 0

    # Redis para desarrollo local
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Celery
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/2"
    )


class StagingConfig(Config):
    """Configuración para staging (pre-producción)"""

    ENV = "staging"
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Caché habilitado
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = os.environ.get("REDIS_URL")
    CACHE_DEFAULT_TIMEOUT = 300

    # Redis
    REDIS_URL = os.environ.get("REDIS_URL")

    # Celery
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND")


class ProductionConfig(Config):
    """Configuración para producción"""

    ENV = "production"
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Caché habilitado y optimizado
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = os.environ.get("REDIS_URL")
    CACHE_DEFAULT_TIMEOUT = 600

    # Redis
    REDIS_URL = os.environ.get("REDIS_URL")

    # Celery
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND")

    # Seguridad extra para producción
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True


class TestingConfig(Config):
    """Configuración para tests"""

    ENV = "testing"
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Sin caché en tests
    CACHE_TYPE = "null"
    CACHE_DEFAULT_TIMEOUT = 0

    # Redis mock
    REDIS_URL = "redis://localhost:6379/15"


# Mapeo de ambientes a clases de configuración
config_by_env = {
    "development": DevelopmentConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(env=None):
    """
    Obtiene la configuración según el ambiente.

    Args:
        env (str): Nombre del ambiente. Si no se proporciona, usa FLASK_ENV

    Returns:
        Config: Clase de configuración apropiada
    """
    if env is None:
        env = os.environ.get("FLASK_ENV", "development")

    config_class = config_by_env.get(env)
    if config_class is None:
        raise ValueError(
            f"Unknown environment: {env}. "
            f"Must be one of: {', '.join(config_by_env.keys())}"
        )
    # Validaciones en tiempo de selección para evitar excepciones en import
    if env in ("staging", "production"):
        if not os.environ.get("SECRET_KEY"):
            raise ValueError("SECRET_KEY must be set in staging/production environment")
        if not os.environ.get("DATABASE_URL"):
            raise ValueError(
                "DATABASE_URL must be set in staging/production environment"
            )

    return config_class
