from sqlalchemy import event
from app.extensions import db


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(3), nullable=False)  # Número de Venta
    date = db.Column(db.Date, nullable=False)  # Fecha de la Venta
    payment_method = db.Column(
        db.String(50), nullable=False, default="cash"
    )  # Método de pago (efectivo, tarjeta, transferencia, etc.)
    status = db.Column(
        db.String(20),
        default="completed",
        nullable=False,
    )  # Estado de la venta (pendiente, completada, cancelada, devuelta)
    excluded = db.Column(
        db.Boolean, default=True
    )  # Indica si la venta fue excluida (opcional)
    customer_name = db.Column(
        db.String(100), nullable=True
    )  # Nombre del cliente (opcional)

    # Monetary
    subtotal_amount = db.Column(
        db.Float, default=0.0, nullable=False
    )  # Total de la suma de total_price en SaleDetail
    discount = db.Column(
        db.Float, default=0.0, nullable=False
    )  # Descuento aplicado a la venta (porcentaje o monto fijo)
    tax = db.Column(
        db.Float, default=0.0, nullable=False
    )  # Impuesto aplicado a la venta (IVA, etc.)
    total_amount = db.Column(
        db.Float, nullable=False
    )  # Total de la venta (incluyendo descuento e impuesto)

    # Foreing Keys
    business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=False
    )  # Asociación con el negocio
    specific_business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=True
    )  # Negocio específico (opcional)

    # Relations
    business = db.relationship(
        "Business",
        foreign_keys=[business_id],  # Especifica la clave foránea correcta
        back_populates="sales",
    )
    specific_business = db.relationship(
        "Business", foreign_keys=[specific_business_id], backref="specific_sales"
    )
    products = db.relationship("SaleDetail", back_populates="sale")

    __table_args__ = (
        db.UniqueConstraint(
            "business_id",
            "sale_number",
            "date",
            name="unique_sale_per_business_per_date",
        ),
    )
    # Añadir check constraint para tax >= 0
    __table_args__ = (db.CheckConstraint("tax >= 0", name="tax_non_negative"),)
    __table_args__ = (
        db.CheckConstraint("discount >= 0", name="discount_non_negative"),
    )

    def calculate_total(self):
        self.subtotal_amount = sum(sp.total_price for sp in self.products)
        self.total_amount = self.subtotal_amount * (1 - self.discount) * (1 + self.tax)

    def __repr__(self):
        return f"Sale #{self.sale_number} - Business: {self.business.name} - Date: {self.date}"


class SaleDetail(db.Model):
    id = db.Column(
        db.Integer, primary_key=True
    )  # Identificador único para cada registro de producto en una venta
    sale_id = db.Column(
        db.Integer, db.ForeignKey("sale.id"), nullable=False
    )  # Relación con la tabla Sale. Cada producto pertenece a una venta específica
    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id"), nullable=False
    )  # Relación con la tabla Product. Cada producto en una venta corresponde a un producto existente en la base de datos

    # Atributos adicionales para la información del producto vendido:
    quantity = db.Column(
        db.Integer, nullable=False
    )  # Cantidad del producto vendido en esa venta
    unit_price = db.Column(
        db.Float, nullable=False
    )  # Precio unitario del producto vendido
    discount = db.Column(
        db.Float, default=0.0
    )  # Descuento aplicado al producto vendido en esa venta
    total_price = db.Column(
        db.Float, nullable=False
    )  # Total de la compra para el producto en esa venta (cantidad * precio unitario)

    # Relationships
    product = db.relationship(
        "Product", back_populates="sale_details"
    )  # Cada Producto tiene una lista de SaleDetails asociados a él
    sale = db.relationship(
        "Sale", back_populates="products"
    )  # Cada Sale tiene una lista de SaleDetails asociados a ella


# Evento para generar el sale_number antes de insertar una nueva venta
@event.listens_for(Sale, "before_insert")
def generate_sale_number(mapper, connection, target):
    # Obtener la fecha y el business_id de la venta
    sale_date = target.date
    business_id = target.business_id

    # Consultar la última venta del mismo día y negocio
    last_sale = (
        Sale.query.filter(Sale.business_id == business_id, Sale.date == sale_date)
        .order_by(Sale.sale_number.desc())
        .first()
    )

    # Generar el siguiente sale_number
    if last_sale:
        last_number = int(last_sale.sale_number)
        target.sale_number = f"{last_number + 1:03}"  # Incrementar y formatear
    else:
        target.sale_number = "001"  # Primera venta del día
