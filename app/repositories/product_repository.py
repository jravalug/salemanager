from app.extensions import db
from app.models import Product, Business, ProductDetail
from sqlalchemy.orm import joinedload


class ProductRepository:
    """
    Repositorio para manejar las operaciones relacionadas con el modelo Product.
    """

    def get_all_products(self, business_id):
        """
        Obtiene todos los productos asociados a un negocio específico.

        :param business_id: ID del negocio.
        :return: Lista de productos ordenados por nombre.
        """
        try:
            return (
                Product.query.filter_by(business_id=business_id)
                .order_by(Product.name.asc())
                .all()
            )
        except Exception as e:
            raise RuntimeError(f"Error al consultar los productos: {e}")

    def get_product_by_id(self, business_id, product_id):
        """
        Obtiene un producto por su ID, verificando que pertenezca a un negocio específico.

        :param business_id: ID del negocio al que debe pertenecer el producto.
        :param product_id: ID del producto.
        :return: Objeto Product si existe y pertenece al negocio, None en caso contrario.
        """
        try:
            # Consultar el producto asegurándose de que pertenezca al negocio
            product = Product.query.filter_by(
                id=product_id, business_id=business_id
            ).first()
            return product
        except Exception as e:
            raise RuntimeError(f"Error al consultar el producto: {e}")

    def get_product_with_raw_materials(self, business_id, product_id):
        """
        Obtiene un producto específico que pertenece a un negocio dado,
        incluyendo sus materias primas asociadas.

        :param business_id: ID del negocio al que pertenece el producto.
        :param product_id: ID del producto a buscar.
        :return: Objeto Product si existe y pertenece al negocio, None en caso contrario.
        """
        try:
            # Consulta el producto asegurándose de que pertenezca al negocio
            product = (
                Product.query.filter_by(id=product_id, business_id=business_id)
                .options(joinedload(Product.raw_materials))  # Cargar relaciones
                .first()
            )

            if not product:
                raise ValueError(
                    "El producto no existe o no pertenece al negocio especificado."
                )

            return product

        except Exception as e:
            raise RuntimeError(f"Error al consultar el producto: {e}")

    def get_products_with_raw_materials(self, business_id):
        """
        Obtiene todos los productos de un negocio junto con sus materias primas asociadas.

        :param business_id: ID del negocio.
        :return: Lista de productos con sus materias primas cargadas.
        """
        try:
            return (
                Product.query.filter_by(business_id=business_id)
                .options(joinedload(Product.raw_materials))  # Cargar relaciones
                .order_by(Product.name.asc())
                .all()
            )
        except Exception as e:
            raise RuntimeError(
                f"Error al consultar los productos con materias primas: {e}"
            )

    def create_product(self, business_id, **kwargs):
        """
        Crea un nuevo producto asociado a un negocio.

        :param business_id: ID del negocio al que pertenece el producto.
        :param kwargs: Atributos adicionales del producto (name, price, description, etc.).
        :return: El objeto Product recién creado.
        """
        try:
            # Validar campos obligatorios
            required_fields = ["name", "price"]
            for field in required_fields:
                if field not in kwargs:
                    raise ValueError(f"El campo '{field}' es obligatorio.")

            # Validar que el negocio exista
            business = Business.query.get(business_id)
            if not business:
                raise ValueError("El negocio no existe.")

            # Validar que el precio sea positivo
            if kwargs["price"] <= 0:
                raise ValueError("El precio debe ser mayor que cero.")

            # Crear el producto
            new_product = Product(business_id=business_id, **kwargs)
            db.session.add(new_product)
            db.session.commit()
            return new_product

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al crear el producto: {e}")

    def update_product(self, product, **kwargs):
        """
        Actualiza un producto existente.

        :param product: Objeto Product a actualizar.
        :param kwargs: Campos y valores a actualizar (por ejemplo, name, price, etc.).
        :return: El objeto Product actualizado.
        """
        try:
            # Validar que el objeto 'product' sea una instancia válida del modelo Product
            if not isinstance(product, Product):
                raise ValueError(
                    "El parámetro 'product' debe ser una instancia de Product."
                )

            # Validar campos específicos antes de actualizar
            if "name" in kwargs and not kwargs["name"]:
                raise ValueError("El campo 'name' no puede estar vacío.")

            if "price" in kwargs:
                if kwargs["price"] is None or kwargs["price"] <= 0:
                    raise ValueError("El campo 'price' debe ser mayor que cero.")

            # Iterar sobre los campos proporcionados en kwargs
            for key, value in kwargs.items():
                # Verificar si el campo existe en el modelo Product
                if hasattr(product, key):
                    setattr(product, key, value)
                else:
                    raise ValueError(
                        f"El campo '{key}' no es válido para el modelo Product."
                    )

            # Guardar los cambios en la base de datos
            db.session.commit()
            return product

        except ValueError as ve:
            # Capturar errores de validación específicos
            db.session.rollback()
            raise ValueError(f"Error de validación: {ve}")

        except Exception as e:
            # Capturar cualquier otro error durante la actualización
            db.session.rollback()
            raise RuntimeError(f"Error al actualizar el producto: {e}")

    def delete_product(self, product):
        """
        Elimina un producto de la base de datos.

        :param product: Objeto Product a eliminar.
        """
        try:
            db.session.delete(product)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al eliminar el producto: {e}")

    def add_product_detail(self, product_id, raw_material_id, quantity):
        """
        Agrega una materia prima a un producto.

        :param product_id: ID del producto.
        :param raw_material_id: ID de la materia prima.
        :param quantity: Cantidad de la materia prima.
        :return: La relación ProductDetail creada.
        :raises ValueError: Si la materia prima ya está asociada al producto.
        :raises RuntimeError: Si ocurre un error durante la operación.
        """
        try:
            # Validar que la relación no exista previamente
            self._validate_product_detail_relation(product_id, raw_material_id)

            # Crear la nueva relación
            new_relation = ProductDetail(
                product_id=product_id,
                raw_material_id=raw_material_id,
                quantity=quantity,
            )
            db.session.add(new_relation)
            db.session.commit()
            return new_relation

        except ValueError as ve:
            db.session.rollback()
            raise ValueError(str(ve))

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al agregar la materia prima: {str(e)}")

    def update_product_detail(self, product_id, raw_material_id, quantity):
        """
        Actualiza la cantidad de una materia prima asociada a un producto.

        :param product_id: ID del producto.
        :param raw_material_id: ID de la materia prima.
        :param quantity: Nueva cantidad de la materia prima.
        :return: La relación ProductDetail actualizada.
        :raises ValueError: Si la relación no existe.
        :raises RuntimeError: Si ocurre un error durante la operación.
        """
        try:
            # Buscar la relación existente
            product_detail = ProductDetail.query.filter_by(
                product_id=product_id, raw_material_id=raw_material_id
            ).first()

            if not product_detail:
                raise ValueError(
                    "La relación entre el producto y la materia prima no existe."
                )

            # Actualizar la cantidad
            product_detail.quantity = quantity

            # Guardar los cambios en la base de datos
            db.session.commit()
            return product_detail

        except ValueError as ve:
            db.session.rollback()
            raise ValueError(str(ve))

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al actualizar la relación: {str(e)}")

    def remove_product_detail(self, product_id, raw_material_id):
        """
        Elimina una relación entre un producto y una materia prima.

        :param product_id: ID del producto.
        :param raw_material_id: ID de la materia prima.
        :return: True si la relación fue eliminada correctamente.
        :raises ValueError: Si la relación no existe.
        :raises RuntimeError: Si ocurre un error durante la operación.
        """
        try:
            # Buscar la relación existente
            product_detail = ProductDetail.query.filter_by(
                product_id=product_id, raw_material_id=raw_material_id
            ).first()

            if not product_detail:
                raise ValueError(
                    "La relación entre el producto y la materia prima no existe."
                )

            # Eliminar la relación
            db.session.delete(product_detail)

            # Guardar los cambios en la base de datos
            db.session.commit()
            return True

        except ValueError as ve:
            db.session.rollback()
            raise ValueError(str(ve))

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al eliminar la relación: {str(e)}")

    def _validate_require_product_fields(**kwargs):
        # Validar campos obligatorios
        required_fields = ["name", "price"]
        for field in required_fields:
            if field not in kwargs:
                raise ValueError(f"El campo '{field}' es obligatorio.")

    def _validate_product_detail_relation(self, product_id, raw_material_id):
        """
        Valida que no exista una relación previa entre el producto y la materia prima.

        :param product_id: ID del producto.
        :param raw_material_id: ID de la materia prima.
        :raises ValueError: Si la relación ya existe.
        """
        existing_relation = ProductDetail.query.filter_by(
            product_id=product_id, raw_material_id=raw_material_id
        ).first()

        if existing_relation:
            raise ValueError("Esta materia prima ya está asociada al producto.")
