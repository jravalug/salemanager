from app.extensions import db


class SaleProduct(db.Model):
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
        db.Integer, nullable=True
    )  # Cantidad del producto vendido en esa venta
    unit_price = db.Column(
        db.Float, nullable=True
    )  # Precio unitario del producto vendido
    total_price = db.Column(
        db.Float, nullable=True
    )  # Total de la compra para el producto en esa venta (cantidad * precio unitario)
    discount = db.Column(
        db.Float, default=0.0
    )  # Descuento aplicado al producto vendido en esa venta

    # Relationships
    product = db.relationship(
        "Product", back_populates="sale_products"
    )  # Cada Producto tiene una lista de SaleProducts asociados a él
    sale = db.relationship(
        "Sale", back_populates="products"
    )  # Cada Sale tiene una lista de SaleProducts asociados a ella
