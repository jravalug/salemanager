from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    FileField,
    IntegerField,
    FloatField,
    SubmitField,
    DateField,
)
from wtforms.validators import DataRequired, NumberRange
from werkzeug.utils import secure_filename


class SaleForm(FlaskForm):
    date = DateField(
        "Fecha",
        format="%Y-%m-%d",
        validators=[DataRequired(message="La fecha es obligatoria.")],
    )
    submit = SubmitField("Registrar Venta")


class EditSaleProductForm(FlaskForm):
    quantity = IntegerField(
        "Cantidad",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="La cantidad debe ser al menos 1."),
        ],
    )
    submit = SubmitField("Guardar Cambios")
