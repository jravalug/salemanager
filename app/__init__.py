from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Crear una única instancia de SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar la base de datos con la aplicación
    db.init_app(app)

    # Importar y registrar blueprints/rutas
    from .routes import bp
    app.register_blueprint(bp)

    # Cargar datos iniciales después de que la app esté configurada
    with app.app_context():
        # Importar load_initial_data dentro del contexto para evitar circular imports
        from .models import load_initial_data
        load_initial_data()

    return app

