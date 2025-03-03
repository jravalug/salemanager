from app.models import Business
from app.extensions import db
from app.repositories.business_repository import BusinessRepository


class BusinessService:
    def __init__(self):
        self.repository = BusinessRepository()

    def create_business(self, **kwargs):
        """
        Crea un nuevo negocio en la base de datos.

        :param kwargs: Campos y valores para crear el negocio (por ejemplo, name, description, logo, etc.).
        :return: El objeto `Business` recién creado.
        """
        try:
            # Validar que los campos obligatorios estén presentes
            required_fields = ["name"]
            for field in required_fields:
                if field not in kwargs:
                    raise ValueError(
                        f"El campo '{field}' es obligatorio para crear un negocio."
                    )

            # Crear una nueva instancia de Business con los campos proporcionados
            new_business = Business(**kwargs)
            db.session.add(new_business)
            db.session.commit()
            return new_business

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al crear el negocio: {e}")

    def update_business(self, business, **kwargs):
        """
        Actualiza un negocio existente en la base de datos.

        :param business: Objeto `Business` a actualizar.
        :param kwargs: Campos y valores para actualizar el negocio (por ejemplo, name, description, logo, etc.).
        :return: El objeto `Business` actualizado.
        """
        try:
            # Actualizar los campos del negocio con los valores proporcionados
            for key, value in kwargs.items():
                if hasattr(business, key):  # Verificar que el campo exista en el modelo
                    setattr(business, key, value)
                else:
                    raise ValueError(
                        f"El campo '{key}' no es válido para el modelo Business."
                    )

            db.session.commit()
            return business

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al actualizar el negocio: {e}")

    def get_parent_filters(self, business):
        """
        Devuelve los filtros necesarios para consultar ventas u otros datos relacionados con un negocio.

        :param business: Objeto `Business` para el cual se generan los filtros.
        :return: Un diccionario con los filtros aplicables.
        """
        filters = {
            "business_id": (
                business.id if business.is_general else business.parent_business_id
            )
        }
        if not business.is_general:
            filters["specific_business_id"] = business.id
        return filters
