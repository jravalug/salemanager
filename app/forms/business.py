from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, TextAreaField, FileField
from wtforms.validators import DataRequired, Optional


class BusinessForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired()])
    description = TextAreaField("Descripción", validators=[Optional()])
    is_general = BooleanField(
        "Negocio Principal",
        false_values=(
            False,
            "false",
            "",
            "n",
            "no",
            "0",
        ),  # Valores que se consideran False
        description="Marque esta casilla para convertir en negocio pricipal.",
    )
    logo = FileField("Logo", validators=[Optional()])  # Campo opcional
