from app.extensions import db


class ACAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(
        db.String(20), nullable=False, unique=True
    )  # Código de la cuenta (ej. 800)
    name = db.Column(
        db.String(100), nullable=False
    )  # Nombre de la cuenta (ej. Gastos de Operaciones)
    subaccounts = db.relationship("ACSubAccount", back_populates="account")


class ACSubAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_code = db.Column(
        db.String(20), db.ForeignKey("ac_account.code"), nullable=False
    )
    code = db.Column(db.String(20), nullable=False)  # Código de la partida (ej. 11000)
    name = db.Column(
        db.String(100), nullable=False
    )  # Nombre de la partida (ej. Materias Primas y Materiales)
    elements = db.relationship("ACElement", back_populates="subaccount")

    # Relación con la cuenta principal
    account = db.relationship("ACAccount", back_populates="subaccounts")

    __table_args__ = (
        db.UniqueConstraint(
            "code",
            "account_code",
            name="unique_ac_subaccount_code_per_ac_account_code",
        ),
    )


class ACElement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subaccount_code = db.Column(
        db.String(20), db.ForeignKey("ac_sub_account.code"), nullable=False
    )
    code = db.Column(db.String(20), nullable=False)  # Código del elemento (ej. 01)
    name = db.Column(
        db.String(100), nullable=False
    )  # Nombre del elemento (ej. Alimento)

    # Relación con la partida
    subaccount = db.relationship("ACSubAccount", back_populates="elements")
    # details = db.relationship("PurchaseDetail", back_populates="element")

    __table_args__ = (
        db.UniqueConstraint(
            "code",
            "subaccount_code",
            name="unique_ac_element_code_per_ac_subaccount_code",
        ),
    )
