from app.extensions import db


class Business(db.Model):
    """
    Modelo que representa un negocio en el sistema.

    Relaciones:
        - parent_business: Relación con el negocio padre (si existe).
        - sub_businesses: Relación con los negocios específicos asociados.
    """

    __tablename__ = "business"

    INCOME_MODE_DAILY = "daily_income"
    INCOME_MODE_DETAILED = "detailed_sales"

    INCOME_ACTIVITY_SALE = "sale"
    INCOME_ACTIVITY_SERVICE = "service"

    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(
        db.String(100), nullable=False, unique=True, comment="Nombre del negocio"
    )
    description = db.Column(
        db.String(255), nullable=True, comment="Descripción opcional del negocio"
    )
    logo = db.Column(db.String(255), nullable=True, comment="Ruta del archivo del logo")
    category = db.Column(
        db.String(50), nullable=True, comment="Campo legado (usar business_activity)"
    )
    business_activity = db.Column(
        db.String(120), nullable=True, comment="Actividad del negocio"
    )
    income_entry_mode = db.Column(
        db.String(30),
        nullable=False,
        default=INCOME_MODE_DAILY,
        comment="Modo de registro de ingresos del negocio",
    )
    default_income_activity = db.Column(
        db.String(20),
        nullable=False,
        default=INCOME_ACTIVITY_SALE,
        comment="Actividad por defecto para Daily Income",
    )
    address = db.Column(db.String(255), nullable=True, comment="Dirección del negocio")
    phone_number = db.Column(
        db.String(15), nullable=True, comment="Número de teléfono opcional"
    )
    email = db.Column(
        db.String(100), nullable=True, comment="Correo electrónico opcional"
    )
    website = db.Column(
        db.String(255), nullable=True, comment="URL del sitio web opcional"
    )
    tax_id = db.Column(
        db.String(20), nullable=True, comment="Número de identificación fiscal opcional"
    )
    fiscal_street = db.Column(db.String(120), nullable=True)
    fiscal_number = db.Column(db.String(30), nullable=True)
    fiscal_between_streets = db.Column(db.String(120), nullable=True)
    fiscal_apartment = db.Column(db.String(50), nullable=True)
    fiscal_district = db.Column(db.String(100), nullable=True)
    fiscal_municipality = db.Column(db.String(100), nullable=True)
    fiscal_province = db.Column(db.String(100), nullable=True)
    fiscal_postal_code = db.Column(db.String(20), nullable=True)
    currency = db.Column(
        db.String(10), default="CUP", comment="Tipo de moneda que opera el negocio"
    )
    is_general = db.Column(
        db.Boolean, default=False, comment="Indica si es un negocio general"
    )
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id"),
        nullable=True,
        comment="Cliente al que pertenece el negocio",
    )
    parent_business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=True, comment="Negocio padre"
    )
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        comment="Fecha de creación del negocio",
    )
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        comment="Fecha de actualización del negocio",
    )

    # Relaciones con otros modelos
    # Relación con el negocio padre (si existe)
    parent_business = db.relationship(
        "Business",
        remote_side=[id],
        backref=db.backref("sub_businesses", lazy="dynamic"),
        uselist=False,
    )
    # Relación con el cliente del negocio
    client = db.relationship(
        "Client",
        back_populates="businesses",
    )
    # Relación con los productos asociados al negocio
    products = db.relationship(
        "Product",
        backref=db.backref("business", lazy="select"),
        lazy="dynamic",
    )
    # Relación con las ventas asociadas al negocio
    sales = db.relationship(
        "Sale",
        back_populates="business",
        foreign_keys="[Sale.business_id]",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Business {self.name}>"

    __table_args__ = (
        db.CheckConstraint(
            "income_entry_mode IN ('daily_income', 'detailed_sales')",
            name="business_income_entry_mode_allowed_values",
        ),
        db.CheckConstraint(
            "default_income_activity IN ('sale', 'service')",
            name="business_default_income_activity_allowed_values",
        ),
    )

    def to_dict(self):
        """
        Convierte el objeto Business en un diccionario para facilitar la serialización.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "logo": self.logo,
            "category": self.category,
            "business_activity": self.business_activity,
            "income_entry_mode": self.income_entry_mode,
            "default_income_activity": self.default_income_activity,
            "address": self.address,
            "phone_number": self.phone_number,
            "email": self.email,
            "website": self.website,
            "tax_id": self.tax_id,
            "fiscal_street": self.fiscal_street,
            "fiscal_number": self.fiscal_number,
            "fiscal_between_streets": self.fiscal_between_streets,
            "fiscal_apartment": self.fiscal_apartment,
            "fiscal_district": self.fiscal_district,
            "fiscal_municipality": self.fiscal_municipality,
            "fiscal_province": self.fiscal_province,
            "fiscal_postal_code": self.fiscal_postal_code,
            "currency": self.currency,
            "is_general": self.is_general,
            "client_id": self.client_id,
            "parent_business_id": self.parent_business_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def parent_name(self):
        """
        Retorna el nombre del negocio general si es un negocio especifico
        Si no tiene un negocio padre, retorna None.
        """
        if self.parent_business:
            return self.parent_business.name
        return None
