from datetime import date
from app.extensions import db


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(3), nullable=False)  # Número de factura
    supplier_name = db.Column(db.String(100), nullable=True)  # Nombre del proveedor
    date = db.Column(db.Date, nullable=False, default=date.today)  # Fecha de la factura
    category = db.Column(
        db.String(20), nullable=False, default="purchase"
    )  # Categoria de la factura
    total_amount = db.Column(db.Float, nullable=False)  # Total de la factura

    # Foreing Keys
    business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=False
    )  # Asociación con el negocio

    # Relaciones
    purchace_details = db.relationship(
        "InvoicePurchaseDetail", back_populates="invoice"
    )  # Detalles de la compra
    service_details = db.relationship(
        "InvoiceServiceDetail", back_populates="invoice"
    )  # Detalles del servicio


class InvoicePurchaseDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    inventory_item_id = db.Column(
        db.Integer, db.ForeignKey("inventory_item.id"), nullable=False
    )
    quantity = db.Column(db.Float, nullable=False)  # Cantidad comprada
    unit = db.Column(db.String(20), nullable=False)  # Unidad de medida (ej. lata, kg)
    price_per_unit = db.Column(db.Float, nullable=False)  # Precio por unidad
    subtotal = db.Column(
        db.Float, nullable=False
    )  # Subtotal (quantity * price_per_unit)

    # Relaciones
    invoice = db.relationship("PurchaseInvoice", back_populates="purchace_details")
    inventory_item = db.relationship("InventoryItem")


class InvoiceServiceDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    ac_element_id = db.Column(
        db.Integer, db.ForeignKey("ac_element.id"), nullable=False
    )
    service_name = db.Column(db.String(100), nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    # Relaciones
    invoice = db.relationship("PurchaseInvoice", back_populates="service_details")
    ac_element = db.relationship("ACElement")
