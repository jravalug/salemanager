from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class MonthForm(FlaskForm):
    month = StringField(
        "Mes (YYYY-MM)",
        validators=[
            DataRequired(message="Por favor, selecciona un mes en formato YYYY-MM.")
        ],
    )
