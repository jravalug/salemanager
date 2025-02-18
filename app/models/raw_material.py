from app.extensions import db


class RawMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    unit = db.Column(
        db.String(20), nullable=False
    )  # Ejemplo: "kg", "litros", "unidades"
    stock = db.Column(db.Float, default=0.0)  # Cantidad disponible en inventario
