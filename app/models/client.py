from app.extensions import db


class Client(db.Model):
    __tablename__ = "clients"

    REGIME_FISCAL = "fiscal"
    REGIME_FINANCIAL = "financiera"

    TYPE_TCP = "tcp"
    TYPE_MIPYME = "mipyme"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    identity_number = db.Column(db.String(30), nullable=True, unique=True)
    nit = db.Column(db.String(30), nullable=True, unique=True)

    legal_street = db.Column(db.String(120), nullable=True)
    legal_number = db.Column(db.String(30), nullable=True)
    legal_between_streets = db.Column(db.String(120), nullable=True)
    legal_apartment = db.Column(db.String(50), nullable=True)
    legal_district = db.Column(db.String(100), nullable=True)
    legal_municipality = db.Column(db.String(100), nullable=True)
    legal_province = db.Column(db.String(100), nullable=True)
    legal_postal_code = db.Column(db.String(20), nullable=True)

    phone_numbers = db.Column(db.JSON, nullable=True)
    primary_phone_number = db.Column(db.String(30), nullable=True)
    email_addresses = db.Column(db.JSON, nullable=True)
    primary_email_address = db.Column(db.String(120), nullable=True)

    fiscal_account_number = db.Column(db.String(50), nullable=True)
    fiscal_account_card_number = db.Column(db.String(30), nullable=True)

    client_type = db.Column(db.String(20), nullable=False, default=TYPE_TCP)
    accounting_regime = db.Column(
        db.String(20), nullable=False, default=REGIME_FISCAL
    )
    regime_changed_at = db.Column(db.DateTime, nullable=True)
    regime_change_reason = db.Column(db.String(255), nullable=True)
    last_regime_evaluation_year = db.Column(db.Integer, nullable=True)
    last_regime_evaluated_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        comment="Fecha de creación del cliente",
    )
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        comment="Fecha de actualización del cliente",
    )

    businesses = db.relationship(
        "Business",
        back_populates="client",
        lazy="dynamic",
    )

    __table_args__ = (
        db.CheckConstraint(
            "client_type IN ('tcp', 'mipyme')",
            name="client_type_allowed_values",
        ),
        db.CheckConstraint(
            "accounting_regime IN ('fiscal', 'financiera')",
            name="client_accounting_regime_allowed_values",
        ),
    )

    def __repr__(self):
        return f"<Client {self.name}>"

    @property
    def is_financial_regime(self) -> bool:
        return self.accounting_regime == self.REGIME_FINANCIAL

    @property
    def is_fiscal_regime(self) -> bool:
        return self.accounting_regime == self.REGIME_FISCAL
