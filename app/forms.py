from flask_wtf import FlaskForm
from wtforms import StringField, FileField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename

class BusinessForm(FlaskForm):
    name = StringField('Nombre del Negocio', validators=[DataRequired()])
    description = StringField('Descripción')
    logo = FileField('Logo')  # Campo para subir el logo