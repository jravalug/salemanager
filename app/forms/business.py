from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, TextAreaField, FileField
from wtforms.validators import DataRequired, Optional


class BusinessForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired()])
    description = TextAreaField("Descripción", validators=[Optional()])
    fiscal_street = StringField("Calle fiscal", validators=[Optional()])
    fiscal_number = StringField("Número fiscal", validators=[Optional()])
    fiscal_between_streets = StringField(
        "Entre calles (fiscal)", validators=[Optional()]
    )
    fiscal_apartment = StringField("Apto / Oficina fiscal", validators=[Optional()])
    fiscal_district = StringField("Reparto / Distrito fiscal", validators=[Optional()])
    fiscal_municipality = StringField("Municipio fiscal", validators=[Optional()])
    fiscal_province = StringField("Provincia fiscal", validators=[Optional()])
    fiscal_postal_code = StringField("Código postal fiscal", validators=[Optional()])
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
        description="Marque esta casilla para convertir en negocio principal.",
    )
    logo = FileField("Logo", validators=[Optional()])  # Campo opcional
