from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from datetime import datetime
from babel.numbers import format_currency

# Crear una única instancia de SQLAlchemy
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Filtro personalizado para formatear moneda

    @app.template_filter("currency")
    def format_currency_filter(value):
        if value is None:
            return "$ 0.00"
        # Formatea el valor como moneda con separador de miles y dos decimales
        return format_currency(value, "USD", locale="en_US").replace("USD", "$")

    # Inicializar la base de datos con la aplicación
    db.init_app(app)

    # Context processor para añadir la fecha actual a todos los templates
    @app.context_processor
    def inject_now():
        return {"now": datetime.now}

    # Importar y registrar blueprints/rutas
    from .routes import bp

    app.register_blueprint(bp)

    # Cargar datos iniciales después de que la app esté configurada
    with app.app_context():
        db.create_all()  # Crea las tablas en la base de datos
        # Importar load_initial_data dentro del contexto para evitar circular imports
        from .models import load_initial_data_arquitecto, load_initial_data_solar

        load_initial_data_arquitecto()
        load_initial_data_solar()

    return app
