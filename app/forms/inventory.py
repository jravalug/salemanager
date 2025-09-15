from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class InventoryItemForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired()])
    unit = StringField("Unidad", validators=[DataRequired()])
