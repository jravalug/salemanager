from flask_wtf import FlaskForm
from wtforms import FloatField
from wtforms.validators import DataRequired, NumberRange


class AccountingSettingsForm(FlaskForm):
    accounting_fiscal_threshold = FloatField(
        "Umbral fiscal anual (CUP)",
        validators=[
            DataRequired(message="El umbral es obligatorio."),
            NumberRange(min=0, message="El umbral no puede ser negativo."),
        ],
    )
