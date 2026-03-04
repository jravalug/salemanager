from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class InventoryItemForm(FlaskForm):
    """Formulario para crear y actualizar items de inventario."""

    name = StringField(
        "Nombre",
        validators=[DataRequired(message="El nombre del item es obligatorio.")],
    )
    unit = StringField(
        "Unidad",
        validators=[DataRequired(message="La unidad es obligatoria.")],
    )
