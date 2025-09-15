from enum import Enum
from datetime import date
from app.extensions import db


class Category(Enum):
    PURCHASE = "compra"
    SERVICE = "servicio"


class Invoice(db.Model):
    """
    Representa una factura en la base de datos.

    Attributes:
        id (int): Identificador único de la factura
        invoice_number (str): Número de la factura, no puede ser nulo
        supplier_name (str): Nombre del proveedor, puede ser nulo
        date (date): Fecha de la factura, no puede ser nulo, por defecto la fecha actual
        category (str): Categoría de la factura, puede ser "compra" o "servicio", no puede ser nulo, por defecto "compra"
        total_amount (float): Total de la factura, no puede ser nulo
        business_id (int): Identificador del negocio asociado, no puede ser nulo
        specific_business_id (int): Identificador del negocio específico (opcional)

        business (Business): Relación con el negocio asociado
        specific_business (Business): Relación con el negocio específico (opcional)
        purchase_details (List[InvoicePurchaseDetail]): Detalles de la compra asociados a la factura
        service_details (List[InvoiceServiceDetail]): Detalles del servicio asociados a la factura
    """

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(3), nullable=False)  # Número de factura
    supplier_name = db.Column(db.String(100), nullable=True)  # Nombre del proveedor
    date = db.Column(db.Date, nullable=False, default=date.today)  # Fecha de la factura
    category = db.Column(
        db.Enum(Category), nullable=False, default=Category.PURCHASE.value
    )  # Categoría de la factura (compra o servicio)
    total_amount = db.Column(db.Float, nullable=False)  # Total de la factura

    # Foreign Keys
    business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=False
    )  # Asociación con el negocio
    specific_business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=True
    )  # Negocio específico (opcional)

    # Relaciones
    business = db.relationship(
        "Business", foreign_keys=[business_id], backref="invoices"
    )
    specific_business = db.relationship(
        "Business", foreign_keys=[specific_business_id], backref="specific_invoices"
    )
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
    invoice = db.relationship("Invoice", back_populates="purchace_details")
    inventory_item = db.relationship("InventoryItem")


class InvoiceServiceDetail(db.Model):
    """
    Represents a detail of an invoice service.
    """

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    ac_element_id = db.Column(
        db.Integer, db.ForeignKey("ac_element.id"), nullable=False
    )
    service_name = db.Column(db.String(100), nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    # Relaciones
    invoice = db.relationship("Invoice", back_populates="service_details")
    ac_element = db.relationship("ACElement")
