import datetime
from app.extensions import db


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_item_id = db.Column(
        db.Integer, db.ForeignKey("inventory_item.id"), nullable=False
    )
    location = db.Column(
        db.String(20), nullable=True
    )  # "warehouse" (almacén) o "pantry" (despensa)
    quantity = db.Column(db.Float, nullable=False)  # Cantidad disponible
    unit = db.Column(
        db.String(20), nullable=False
    )  # Unidad de medida en que se compra (ej. lata, kg)
    conversion_factor = db.Column(
        db.Float, nullable=False
    )  # Factor de conversión (ej. 1 lata = 400 ml)
    purchase_price = db.Column(db.Float, nullable=False)  # Precio de compra
    date = db.Column(db.Date, nullable=False)  # Fecha de entrada al almacén

    # Foreing Keys
    invoice_id = db.Column(
        db.Integer, db.ForeignKey("invoice.id"), nullable=True
    )  # Referencia cruzada con la factura
    business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=False
    )  # Asociación con el negocio
    specific_business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=True
    )  # Negocio específico (opcional)

    # Relations
    business = db.relationship(
        "Business", foreign_keys=[business_id], backref="inventory"
    )
    specific_business = db.relationship(
        "Business", foreign_keys=[specific_business_id], backref="specific_inventory"
    )
    extractions = db.relationship("InventoryExtraction", back_populates="inventory")


class InventoryExtraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(
        db.Integer, db.ForeignKey("inventory.id"), nullable=False
    )  # Artículo extraído
    quantity = db.Column(db.Float, nullable=False)  # Cantidad extraída
    date = db.Column(
        db.DateTime, nullable=False, default=db.func.current_timestamp()
    )  # Fecha de la extracción
    reason = db.Column(
        db.Integer, db.ForeignKey("ac_element.id"), nullable=False
    )  # Motivo de la extracción (opcional)

    # Relaciones
    inventory = db.relationship("Inventory", back_populates="extractions")


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

    # Relación con ProductDetail
    products = db.relationship("ProductDetail", back_populates="raw_material")
