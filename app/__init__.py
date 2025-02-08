from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    with app.app_context():
        from . import routes  # Importa tus rutas aquí
        app.register_blueprint(routes.bp)  # Registra el blueprint
        db.create_all()  # Crea las tablas de la base de datos
    
    return app