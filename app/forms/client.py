from flask_wtf import FlaskForm
from wtforms import (
    SelectField,
    StringField,
    BooleanField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional


class ClientForm(FlaskForm):
    """Formulario de alta/edición de clientes con datos legales y de contacto."""

    name = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre del cliente es obligatorio."),
            Length(max=120),
        ],
    )
    identity_number = StringField(
        "Número de identidad",
        validators=[Optional(), Length(max=30)],
    )
    nit = StringField(
        "NIT",
        validators=[Optional(), Length(max=30)],
    )

    legal_street = StringField(
        "Domicilio legal: calle/avenida", validators=[Optional(), Length(max=120)]
    )
    legal_number = StringField(
        "Domicilio legal: número/edificio", validators=[Optional(), Length(max=30)]
    )
    legal_between_streets = StringField(
        "Domicilio legal: entrecalles", validators=[Optional(), Length(max=120)]
    )
    legal_apartment = StringField(
        "Domicilio legal: apartamento", validators=[Optional(), Length(max=50)]
    )
    legal_district = StringField(
        "Domicilio legal: reparto", validators=[Optional(), Length(max=100)]
    )
    legal_municipality = StringField(
        "Domicilio legal: municipio", validators=[Optional(), Length(max=100)]
    )
    legal_province = StringField(
        "Domicilio legal: provincia", validators=[Optional(), Length(max=100)]
    )
    legal_postal_code = StringField(
        "Domicilio legal: código postal", validators=[Optional(), Length(max=20)]
    )

    phone_numbers_input = TextAreaField(
        "Teléfonos (separados por coma)", validators=[Optional()]
    )
    primary_phone_number = StringField(
        "Teléfono principal", validators=[Optional(), Length(max=30)]
    )
    email_addresses_input = TextAreaField(
        "Correos electrónicos (separados por coma)", validators=[Optional()]
    )
    primary_email_address = StringField(
        "Correo principal", validators=[Optional(), Length(max=120)]
    )

    fiscal_account_number = StringField(
        "Número de cuenta fiscal", validators=[Optional(), Length(max=50)]
    )
    fiscal_account_card_number = StringField(
        "Número de tarjeta asociada", validators=[Optional(), Length(max=30)]
    )

    client_type = SelectField(
        "Tipo de cliente",
        validators=[DataRequired(message="El tipo de cliente es obligatorio.")],
        choices=[
            ("tcp", "TCP"),
            ("mipyme", "MIPYME"),
        ],
        default="tcp",
    )
    accounting_regime = SelectField(
        "Régimen contable",
        validators=[DataRequired(message="El régimen contable es obligatorio.")],
        choices=[
            ("fiscal", "Fiscal"),
            ("financiera", "Financiera"),
        ],
        default="fiscal",
    )
    is_active = BooleanField("Activo", default=True)
