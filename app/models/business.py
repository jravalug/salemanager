from app.extensions import db


class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # Nombre del negocio
    description = db.Column(db.String(255))  # Descripción opcional del negocio
    logo = db.Column(db.String(255))  # Ruta del archivo del logo
    category = db.Column(
        db.String(50), nullable=True
    )  # Categoría del negocio (opcional)
    address = db.Column(db.String(255), nullable=True)  # Dirección del negocio
    phone_number = db.Column(
        db.String(15), nullable=True
    )  # Número de teléfono opcional
    email = db.Column(db.String(100), nullable=True)  # Correo electrónico opcional
    website = db.Column(db.String(255), nullable=True)  # URL del sitio web opcional
    tax_id = db.Column(
        db.String(20), nullable=True
    )  # Número de identificación fiscal opcional
    currency = db.Column(
        db.String(10), default="CUP"
    )  # Tipo de moneda que opera el negocio
    is_general = db.Column(db.Boolean, default=False)  # Indica si es un negocio general
    parent_business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=True
    )  # Negocio padre
    created_at = db.Column(
        db.DateTime, default=db.func.current_timestamp()
    )  # Fecha de creación del negocio
    updated_at = db.Column(
        db.DateTime, onupdate=db.func.current_timestamp()
    )  # Fecha de actualización del negocio

    # Relaciones con otros modelos
    parent_business = db.relationship(
        "Business", remote_side=[id], backref="sub_businesses"
    )
    products = db.relationship(
        "Product", backref="business", lazy=True
    )  # Relacion de Productos
    sales = db.relationship(
        "Sale",
        back_populates="business",
        foreign_keys="Sale.business_id",  # Especifica la clave foránea correcta
    )

    def __repr__(self):
        return f"<Business {self.name}>"
