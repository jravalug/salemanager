from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms.validators import DataRequired, Optional


class BusinessForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired()])
    description = TextAreaField("Descripción", validators=[Optional()])
    logo = FileField("Logo", validators=[Optional()])  # Campo opcional
