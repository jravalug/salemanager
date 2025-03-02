from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    SelectField,
    FloatField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from app.models import ProductDetail, InventoryItem  # Importa el modelo ProductDetail


class ProductForm(FlaskForm):
    name = StringField(
        "Nombre del Producto",
        validators=[
            DataRequired(message="El nombre del producto es obligatorio."),
            Length(
                min=2, max=100, message="El nombre no puede exceder los 100 caracteres."
            ),
        ],
    )
    price = FloatField(
        "Precio de Venta",
        validators=[
            DataRequired(message="El precio de venta es obligatorio."),
            NumberRange(min=0.01, message="El precio debe ser un valor positivo."),
        ],
    )
    instructions = TextAreaField(
        "Instrucciones de Elaboración",
        render_kw={"rows": 4},  # Altura del área de texto
        validators=[Optional()],  # Campo opcional
    )
    description = TextAreaField(
        "Descripción",
        render_kw={"rows": 4},  # Altura del área de texto
        validators=[
            Optional(),
            Length(
                max=500, message="La descripción no puede exceder los 500 caracteres."
            ),
        ],
    )
    category = SelectField(
        "Categoría",
        choices=[
            ("comida", "Comida"),
            ("cocteles", "Cocteles"),
            ("vinos", "Vinos"),
            ("bebidas", "Bebidas"),
            ("tragos", "Tragos"),
            ("botellas", "Botellas"),
        ],
        validators=[Optional()],
    )
    sku = StringField(
        "SKU (Código Único)",
        validators=[
            Optional(),
            Length(max=50, message="El SKU no puede exceder los 50 caracteres."),
        ],
    )
    is_active = BooleanField("Activo", default=True)
    is_batch_prepared = BooleanField(
        "Por lotes",
        false_values=(
            False,
            "false",
            "",
            "n",
            "no",
            "0",
        ),  # Valores que se consideran False
        description="Marque esta casilla si se prepara por lotes.",
    )
    batch_size = FloatField(
        "Tamaño del lote",
        validators=[
            Optional(),
            NumberRange(min=1, message="La cantidad debe ser mayor que 1."),
        ],
        default=1,
    )
    submit = SubmitField("Guardar Producto")


class ProductDetailForm(FlaskForm):
    inventory_item = SelectField(
        "Materia Prima",
        coerce=int,  # Asegura que el valor seleccionado sea un entero
        validators=[DataRequired()],
    )
    quantity = FloatField(
        "Cantidad",
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="La cantidad debe ser mayor que 0."),
        ],
    )
    submit = SubmitField("Agregar Materia Prima")

    def __init__(self, *args, **kwargs):
        super(ProductDetailForm, self).__init__(*args, **kwargs)
        # Cargar las opciones del campo "inventory_item" con las materias primas disponibles
        self.inventory_item.choices = [
            (material.id, f"{material.name} ({material.unit})")
            for material in InventoryItem.query.order_by(InventoryItem.name).all()
        ]
