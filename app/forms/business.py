from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms.validators import DataRequired


class BusinessForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired()])
    description = TextAreaField("Descripción")
    logo = FileField("Logo")
