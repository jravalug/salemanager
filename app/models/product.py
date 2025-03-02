from app.extensions import db


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Id del producto
    name = db.Column(db.String(100), nullable=False)  # Nombre del producto
    price = db.Column(db.Float, nullable=False)  # Precio de venta
    description = db.Column(db.Text, nullable=True)  # Descripción del producto
    instructions = db.Column(db.Text, nullable=True)  # Instrucciones de elaboracion
    category = db.Column(
        db.String(50), nullable=True
    )  # Categoría del producto (comida, bebida, ropa, herramientas, etc.).
    sku = db.Column(
        db.String(50), nullable=True, unique=True
    )  # Código único del producto (SKU - Stock Keeping Unit).
    barcode = db.Column(
        db.String(50), nullable=True
    )  # Código de barras del producto (opcional)
    unit = db.Column(
        db.String(20), nullable=True
    )  # Unidad de medida (kilogramos, litros, unidades, etc.)
    is_active = db.Column(
        db.Boolean, default=True
    )  # Indica si el producto está activo (disponible para la venta)
    min_stock = db.Column(
        db.Float, nullable=True
    )  # Stock mínimo antes de emitir una alerta
    cost_price = db.Column(
        db.Float, nullable=True
    )  # Costo unitario del producto (útil para calcular márgenes de ganancia)
    is_batch_prepared = db.Column(db.Boolean, default=False)  # ¿Se prepara por lotes?
    batch_size = db.Column(
        db.Integer, nullable=True, default=1
    )  # Número de raciones por lote

    business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=False
    )  # Asociación con el negocio

    # Relaciones con otros modelos
    sale_details = db.relationship("SaleDetail", back_populates="product")
    inventory_items = db.relationship("ProductDetail", back_populates="product")


class ProductDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    inventory_item_id = db.Column(
        db.Integer, db.ForeignKey("inventory_item.id"), nullable=False
    )
    quantity = db.Column(
        db.Float, nullable=False
    )  # Cantidad de materia prima necesaria

    # Relaciones
    product = db.relationship("Product", back_populates="inventory_items")
    inventory_item = db.relationship("InventoryItem", backref="products")
