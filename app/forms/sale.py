from flask_wtf import FlaskForm
from wtforms import (
    HiddenField,
    StringField,
    FileField,
    IntegerField,
    FloatField,
    SubmitField,
    DateField,
)
from wtforms.validators import DataRequired, NumberRange
from werkzeug.utils import secure_filename


from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, FloatField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange

from app.models.business import Business


class SaleForm(FlaskForm):
    specific_business_id = SelectField(
        "Negocio Específico",
        coerce=lambda x: int(x) if x else None,  # Acepta valores nulos
        validators=[Optional()],
        choices=[("", "--- Seleccionar ---")],  # Opción vacía por defecto
    )
    sale_number = StringField(
        "Número de Venta",
    )

    date = DateField(
        "Fecha de la Venta",
        format="%Y-%m-%d",
        validators=[DataRequired(message="La fecha de la venta es obligatoria.")],
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
        "Estado de la Venta",
        choices=[
            ("completed", "Completada"),
            ("pending", "Pendiente"),
            ("cancelled", "Cancelada"),
            ("returned", "Devuelta"),
        ],
        default="completed",
        validators=[DataRequired(message="El estado de la venta es obligatorio.")],
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
        "Venta Excluida",
        false_values=(
            False,
            "false",
            "",
            "n",
            "no",
            "0",
        ),  # Valores que se consideran False
        description="Marque esta casilla para excluir la venta.",
    )

    def __init__(self, parent_business_id, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)

        # Obtener subnegocios
        sub_businesses = Business.query.filter_by(
            parent_business_id=parent_business_id
        ).all()

        # Siempre incluir la opción vacía al inicio
        self.specific_business_id.choices = [("", "Seleccionar sub-negocio ...")] + [
            (b.id, b.name) for b in sub_businesses
        ]


class SaleDetailForm(FlaskForm):
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
        default=1,  # Valor predeterminado válido
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
        """
        Configura las opciones del campo product_id.
        Cada opción muestra el nombre del producto y su precio.
        """
        self.product_id.choices = [
            (product.id, f"{product.name} - ${product.price:.2f}")
            for product in products
        ]


class UpdateSaleDetailForm(FlaskForm):
    sale_detail_id = HiddenField(
        "ID de la Venta del Producto",
        validators=[
            DataRequired(message="El ID de la Venta del Producto es obligatorio.")
        ],
        description="ID de la relacion de la Venta y el Producto.",
    )
    quantity = IntegerField(
        "Cantidad",
        validators=[
            DataRequired(message="La cantidad es obligatoria."),
            NumberRange(min=1, message="La cantidad debe ser al menos 1."),
        ],
        default=1,  # Valor predeterminado válido
    )
    discount = FloatField(
        "Descuento",
        default=0.0,
        validators=[
            Optional(),
            NumberRange(min=0.0, message="El descuento no puede ser negativo."),
        ],
    )


class RemoveSaleDetailForm(FlaskForm):
    sale_detail_id = HiddenField(
        "ID de la Venta del Producto",
        validators=[
            DataRequired(message="El ID de la Venta del Producto es obligatorio.")
        ],
        description="ID de la relacion de la Venta y el Producto.",
    )
    submit = SubmitField("Eliminar Producto")
