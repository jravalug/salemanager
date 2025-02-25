from sqlalchemy import event
from datetime import date
from app.extensions import db


class PurchaseInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(3), nullable=False)  # Número de Venta
    supplier_name = db.Column(db.String(100), nullable=True)  # Nombre del proveedor
    date = db.Column(db.Date, nullable=False, default=date.today)  # Fecha de la compra
    total_amount = db.Column(db.Float, nullable=False)  # Total de la factura

    # Foreing Keys
    business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=False
    )  # Asociación con el negocio

    # Relaciones
    details = db.relationship(
        "PurchaseDetail", back_populates="invoice"
    )  # Detalles de la compra


class PurchaseDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(
        db.Integer, db.ForeignKey("purchase_invoice.id"), nullable=False
    )
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
    invoice = db.relationship("PurchaseInvoice", back_populates="details")
    inventory_item = db.relationship("InventoryItem")


# Evento para generar el invoice_number antes de insertar una nueva compra
@event.listens_for(PurchaseInvoice, "before_insert")
def generate_invoice_number(mapper, connection, target):
    # Obtener la fecha y el business_id de la compra
    invoice_date = target.date
    business_id = target.business_id

    # Consultar la última factura del mismo día y negocio
    last_invoice = (
        PurchaseInvoice.query.filter(
            PurchaseInvoice.business_id == business_id,
            PurchaseInvoice.date == invoice_date,
        )
        .order_by(PurchaseInvoice.invoice_number.desc())
        .first()
    )

    # Generar el siguiente invoice_number
    if last_invoice:
        last_number = int(last_invoice.invoice_number)
        target.invoice_number = f"{last_number + 1:03}"  # Incrementar y formatear
    else:
        target.invoice_number = "001"  # Primera venta del día
