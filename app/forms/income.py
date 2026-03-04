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
            ("card", "Tarjeta"),
            ("transfer", "Transferencia"),
            ("mix", "Mixto"),
            ("other", "Otro"),
        ],
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
