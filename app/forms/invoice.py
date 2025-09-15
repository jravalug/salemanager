from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, DateField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class InvoiceForm(FlaskForm):
    """
    Formulario para la creación y edición de facturas.

    Este formulario permite a los usuarios ingresar información sobre la factura,
    incluyendo el número de factura, el nombre del proveedor, la fecha y la categoría.

    Attributes:
        invoice_number (StringField): Número de factura, campo requerido
        supplier_name (StringField): Nombre del proveedor, campo opcional
        date (StringField): Fecha de la factura, campo requerido
        category (SelectField): Categoría de la factura, solo permite "compra" o "servicio", campo requerido
    """
    invoice_number = StringField('Número de factura', validators=[DataRequired(), Length(max=5)])
    supplier_name = StringField('Nombre del proveedor', validators=[Optional(), Length(max=50)])
    date = DateField('Fecha', validators=[DataRequired()])
    category = SelectField('Categoría', choices=[('compra', 'Compra'), ('servicio', 'Servicio')], validators=[DataRequired()])