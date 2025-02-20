from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from app.models import RawMaterial  # Importa el modelo RawMaterial


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


class ProductInstructionsForm(FlaskForm):
    instructions = TextAreaField(
        "Instrucciones de Elaboración",
        render_kw={"rows": 4},  # Altura del área de texto
        validators=[DataRequired(), Length(min=50)],
    )
    submit = SubmitField("Guardar Instrucciones")


class ProductRawMaterialForm(FlaskForm):
    raw_material = SelectField(
        "Materia Prima",
        coerce=int,  # Asegura que el valor seleccionado sea un entero (ID de la materia prima)
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
        super(ProductRawMaterialForm, self).__init__(*args, **kwargs)
        # Cargar las opciones del campo "raw_material" con las materias primas disponibles
        self.raw_material.choices = [
            (material.id, f"{material.name} ({material.unit})")
            for material in RawMaterial.query.all()
        ]
