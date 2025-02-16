from flask_wtf import FlaskForm
from wtforms import StringField, FileField, IntegerField, FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from werkzeug.utils import secure_filename


class EditSaleProductForm(FlaskForm):
    quantity = IntegerField(
        "Cantidad",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="La cantidad debe ser al menos 1."),
        ],
    )
    submit = SubmitField("Guardar Cambios")
