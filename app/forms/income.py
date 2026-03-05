from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Optional, NumberRange

from app.forms.business import DailyIncomeForm
from app.models.business import Business


class IncomeForm(FlaskForm):
    """Formulario para crear y editar ingresos detallados."""

    specific_business_id = SelectField(
        "Negocio Específico",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
        choices=[("", "--- Seleccionar ---")],
    )
    sale_number = StringField("Número de Ingreso")
    date = DateField(
        "Fecha del Ingreso",
        format="%Y-%m-%d",
        validators=[DataRequired(message="La fecha del ingreso es obligatoria.")],
    )
    payment_method = SelectField(
        "Método de Pago",
        choices=[
            ("cash", "Efectivo"),
            ("transfer", "Transferencia"),
            ("check", "Cheque"),
        ],
        validators=[Optional()],
    )
    debtor_type = SelectField(
        "Tipo de Deudor",
        choices=[
            ("", "--- Seleccionar ---"),
            ("natural", "Persona Natural"),
            ("legal", "Persona Jurídica"),
        ],
        validators=[Optional()],
    )
    debtor_natural_full_name = StringField(
        "Nombre y Apellidos (Natural)",
        validators=[Optional()],
    )
    debtor_natural_identity_number = StringField(
        "Carnet de Identidad / NIT (Natural)",
        validators=[Optional()],
    )
    debtor_natural_bank_account = StringField(
        "Cuenta Bancaria (Natural)",
        validators=[Optional()],
    )
    debtor_legal_entity_name = StringField(
        "Nombre de la Entidad (Jurídica)",
        validators=[Optional()],
    )
    debtor_legal_reeup_code = StringField(
        "Código REEUP (Jurídica)",
        validators=[Optional()],
    )
    debtor_legal_address = StringField(
        "Dirección (Jurídica)",
        validators=[Optional()],
    )
    debtor_legal_credit_branch = StringField(
        "Sucursal de Crédito (Jurídica)",
        validators=[Optional()],
    )
    debtor_legal_bank_account = StringField(
        "Número de Cuenta (Jurídica)",
        validators=[Optional()],
    )
    debtor_legal_contract_number = StringField(
        "Número de Contrato (Jurídica)",
        validators=[Optional()],
    )
    status = SelectField(
        "Estado del Ingreso",
        choices=[
            ("completed", "Completado"),
            ("pending", "Pendiente"),
            ("cancelled", "Cancelado"),
            ("returned", "Devuelto"),
        ],
        default="completed",
        validators=[DataRequired(message="El estado del ingreso es obligatorio.")],
    )
    customer_name = StringField("Nombre del Cliente", validators=[Optional()])
    discount = FloatField(
        "Descuento (%)",
        default=0.0,
        validators=[
            Optional(),
            NumberRange(min=0.0, message="El descuento no puede ser negativo."),
        ],
    )
    tax = FloatField(
        "Impuesto (%)",
        default=0.0,
        validators=[
            Optional(),
            NumberRange(min=0.0, message="El impuesto no puede ser negativo."),
        ],
    )
    excluded = BooleanField(
        "Ingreso Excluido",
        false_values=(False, "false", "", "n", "no", "0"),
        description="Marque esta casilla para excluir el ingreso.",
    )

    def __init__(self, parent_business_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sub_businesses = Business.query.filter_by(
            parent_business_id=parent_business_id
        ).all()
        self.specific_business_id.choices = [("", "Seleccionar sub-negocio ...")] + [
            (b.id, b.name) for b in sub_businesses
        ]

    def validate(self, extra_validators=None):
        is_valid = super().validate(extra_validators=extra_validators)
        payment_method = (self.payment_method.data or "").strip().lower()

        if payment_method not in {"transfer", "check"}:
            return is_valid

        debtor_type = (self.debtor_type.data or "").strip().lower()
        if debtor_type not in {"natural", "legal"}:
            self.debtor_type.errors.append(
                "Debe seleccionar el tipo de deudor para pagos por transferencia o cheque."
            )
            return False

        if debtor_type == "natural":
            required_natural_fields = [
                (
                    self.debtor_natural_full_name,
                    "El nombre y apellidos es obligatorio.",
                ),
                (
                    self.debtor_natural_identity_number,
                    "El carnet de identidad o NIT es obligatorio.",
                ),
                (
                    self.debtor_natural_bank_account,
                    "La cuenta bancaria es obligatoria.",
                ),
            ]
            for field, message in required_natural_fields:
                if not (field.data or "").strip():
                    field.errors.append(message)
                    is_valid = False

        if debtor_type == "legal":
            required_legal_fields = [
                (
                    self.debtor_legal_entity_name,
                    "El nombre de la entidad es obligatorio.",
                ),
                (self.debtor_legal_reeup_code, "El código REEUP es obligatorio."),
                (self.debtor_legal_address, "La dirección es obligatoria."),
                (
                    self.debtor_legal_credit_branch,
                    "La sucursal de crédito es obligatoria.",
                ),
                (
                    self.debtor_legal_bank_account,
                    "El número de cuenta es obligatorio.",
                ),
                (
                    self.debtor_legal_contract_number,
                    "El número de contrato es obligatorio.",
                ),
            ]
            for field, message in required_legal_fields:
                if not (field.data or "").strip():
                    field.errors.append(message)
                    is_valid = False

        return is_valid


class IncomeDetailForm(FlaskForm):
    """Formulario para agregar detalle de ingreso."""

    product_id = SelectField(
        "Producto",
        coerce=int,
        validators=[DataRequired(message="El producto es obligatorio.")],
    )
    quantity = IntegerField(
        "Cantidad",
        validators=[
            DataRequired(message="La cantidad es obligatoria."),
            NumberRange(min=1, message="La cantidad debe ser al menos 1."),
        ],
        default=1,
    )
    discount = FloatField(
        "Descuento",
        default=0.0,
        validators=[
            Optional(),
            NumberRange(min=0.0, max=1, message="El descuento no puede ser negativo."),
        ],
    )

    def set_product_choices(self, products):
        self.product_id.choices = [
            (product.id, f"{product.name} - ${product.price:.2f}")
            for product in products
        ]


class UpdateIncomeDetailForm(FlaskForm):
    """Formulario para actualizar detalle de ingreso."""

    sale_detail_id = HiddenField(
        "ID del Ingreso del Producto",
        validators=[DataRequired(message="El ID del detalle es obligatorio.")],
    )
    quantity = IntegerField(
        "Cantidad",
        validators=[
            DataRequired(message="La cantidad es obligatoria."),
            NumberRange(min=1, message="La cantidad debe ser al menos 1."),
        ],
        default=1,
    )
    discount = FloatField(
        "Descuento",
        default=0.0,
        validators=[
            Optional(),
            NumberRange(min=0.0, message="El descuento no puede ser negativo."),
        ],
    )


class RemoveIncomeDetailForm(FlaskForm):
    """Formulario para remover detalle de ingreso."""

    sale_detail_id = HiddenField(
        "ID del Ingreso del Producto",
        validators=[DataRequired(message="El ID del detalle es obligatorio.")],
    )
    submit = SubmitField("Eliminar Producto")


class DailyManualIncomeForm(DailyIncomeForm):
    """Formulario para registrar ingreso manual diario."""
