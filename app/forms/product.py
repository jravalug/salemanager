from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    HiddenField,
    SelectField,
    FloatField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from app.models import ProductDetail, InventoryItem  # Importa el modelo ProductDetail


class ProductForm(FlaskForm):
    """
    Formulario para crear o actualizar un producto.
    """

    # === Información Básica ===
    name = StringField(
        "Nombre del Producto",
        validators=[
            DataRequired(message="El nombre del producto es obligatorio."),
            Length(
                min=2,
                max=100,
                message="El nombre debe tener entre 2 y 100 caracteres.",
            ),
        ],
        description="Nombre único del producto.",
    )
    price = FloatField(
        "Precio de Venta",
        validators=[
            DataRequired(message="El precio de venta es obligatorio."),
            NumberRange(min=0.01, message="El precio debe ser mayor que cero."),
        ],
        description="Precio unitario del producto.",
    )

    # === Descripción e Instrucciones ===
    instructions = TextAreaField(
        "Instrucciones de Elaboración",
        render_kw={"rows": 4},  # Altura del área de texto
        validators=[Optional()],
        description="Pasos para preparar o elaborar el producto (opcional).",
    )
    description = TextAreaField(
        "Descripción",
        render_kw={"rows": 4},  # Altura del área de texto
        validators=[
            Optional(),
            Length(
                max=500,
                message="La descripción no puede exceder los 500 caracteres.",
            ),
        ],
        description="Descripción detallada del producto (opcional).",
    )

    # === Categorización ===
    category = SelectField(
        "Categoría",
        choices=[
            ("comida", "Comida"),
            ("cocteles", "Cocteles"),
            ("vinos", "Vinos"),
            ("bebidas", "Bebidas"),
            ("tragos", "Tragos"),
            ("botellas", "Botellas"),
        ],
        validators=[Optional()],
        description="Categoría del producto (opcional).",
    )
    sku = StringField(
        "SKU (Código Único)",
        validators=[
            Optional(),
            Length(
                max=50,
                message="El SKU no puede exceder los 50 caracteres.",
            ),
        ],
        description="Código único del producto (opcional).",
    )

    # === Estado y Configuración ===
    is_active = BooleanField(
        "Activo",
        default=True,
        description="Indica si el producto está disponible para la venta.",
    )
    is_batch_prepared = BooleanField(
        "Preparación por Lotes",
        false_values=(False, "false", "", "n", "no", "0"),
        description="Marque esta casilla si el producto se prepara por lotes.",
    )
    batch_size = FloatField(
        "Tamaño del Lote",
        validators=[
            Optional(),
            NumberRange(
                min=1,
                message="El tamaño del lote debe ser al menos 1.",
            ),
        ],
        default=1,
        description="Cantidad de unidades o raciones por lote (opcional).",
    )

    # === Botón de Envío ===
    submit = SubmitField("Guardar Producto")


class ProductDetailForm(FlaskForm):
    """
    Formulario para agregar o actualizar materias primas asociadas a un producto.
    """

    # === Selección de Materia Prima ===
    raw_material_id = SelectField(
        "Materia Prima",
        coerce=int,  # Asegura que el valor seleccionado sea un entero
        validators=[DataRequired(message="Debe seleccionar una materia prima.")],
        description="Seleccione la materia prima que desea asociar al producto.",
    )

    # === Cantidad de Materia Prima ===
    quantity = FloatField(
        "Cantidad",
        validators=[
            DataRequired(message="La cantidad es obligatoria."),
            NumberRange(min=0.01, message="La cantidad debe ser mayor que cero."),
        ],
        description="Cantidad de materia prima necesaria para el producto.",
    )

    # === Botón de Envío ===
    submit = SubmitField("Agregar Materia Prima")

    def __init__(self, *args, **kwargs):
        super(ProductDetailForm, self).__init__(*args, **kwargs)
        # Cargar las opciones del campo "inventory_item" con las materias primas disponibles
        self.raw_material_id.choices = self._load_raw_materials()

    @staticmethod
    def _load_raw_materials():
        """
        Carga las materias primas disponibles desde la base de datos.

        :return: Lista de tuplas (id, nombre) para el campo SelectField.
        """
        return [
            (material.id, f"{material.name} ({material.unit})")
            for material in InventoryItem.query.order_by(InventoryItem.name).all()
        ]


class DeleteProductDetailForm(FlaskForm):
    """
    Formulario para eliminar una relación entre un producto y una materia prima.
    """

    raw_material_id = HiddenField(
        "ID de la Materia Prima",
        validators=[DataRequired(message="El ID de la materia prima es obligatorio.")],
        description="ID de la materia prima asociada.",
    )
    submit = SubmitField("Eliminar Relación")
