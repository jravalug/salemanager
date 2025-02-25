from app.extensions import db


class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    unit = db.Column(
        db.String(20), nullable=False
    )  # Ejemplo: "kg", "litros", "unidades"
    stock = db.Column(db.Float, default=0.0)  # Cantidad disponible en inventario
    min_stock = db.Column(db.Float, nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
