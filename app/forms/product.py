from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from app.models import ProductDetail, InventoryItem  # Importa el modelo ProductDetail


class ProductForm(FlaskForm):
    name = StringField(
        "Nombre del Producto",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    price = FloatField(
        "Precio",
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="El precio debe ser mayor que 0."),
        ],
    )
    instructions = TextAreaField(
        "Instrucciones de Elaboración",
        render_kw={"rows": 4},  # Altura del área de texto
        validators=[Optional()],  # Campo opcional
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
            for material in InventoryItem.query.all()
        ]
