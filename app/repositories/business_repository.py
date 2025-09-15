from app.models import Business


class BusinessRepository:

    def _query_business(self, filters=None, order_by=None):
        """
        Método privado para realizar consultas genéricas sobre negocios.
        :param filters: Filtros a aplicar en la consulta (opcional).
        :param order_by: Campo por el cual ordenar los resultados (opcional).
        :return: Lista de negocios que cumplen con los criterios.
        """

        try:
            query = Business.query
            if filters:
                if isinstance(filters, dict):
                    query = query.filter_by(**filters)
                else:
                    query = query.filter_by(*filters)
            if order_by is not None:  # ✅ Corrección clave
                query = query.order_by(order_by)
            return query.all()
        except Exception as e:
            raise RuntimeError(f"Error al consultar los negocios: {str(e)}")

    def get_all_business(self):
        """Consulta todos los negocios."""
        return self._query_business(order_by=Business.name.asc())

    def get_parent_business(self):
        """Devuelve los negocios generales."""
        filters = {"is_general": True}
        return self._query_business(filters=filters, order_by=Business.name.asc())

    def get_sub_business(self):
        """Devuelve los negocios específicos."""
        filters = [Business.is_general == False]
        return self._query_business(filters=filters, order_by=Business.name.asc())

    def get_business_with_sub_business(self):
        """
        Devuelve los negocios generales que tienen al menos un negocio específico asociado.
        """
        filters = [
            Business.is_general == True,
            Business.sub_businesses.any(),
        ]
        return self._query_business(filters=filters, order_by=Business.name.asc())

    def get_sub_business_parent(self, sub_business_id):
        """
        Devuelve el negocio general de un negocio específico.
        :param sub_business_id: El ID del negocio específico.
        :return: El negocio general (parent_business) asociado al negocio específico.
        """
        try:
            # Obtener el negocio específico
            sub_business = Business.query.get_or_404(sub_business_id)

            # Verificar si el negocio tiene un negocio padre
            if not sub_business.parent_business_id:
                raise ValueError(
                    "El negocio específico no está asociado a un negocio general."
                )

            # Obtener y devolver el negocio general
            parent_business = Business.query.get_or_404(sub_business.parent_business_id)
            return parent_business

        except Exception as e:
            raise RuntimeError(f"Error al consultar el negocio general: {e}")
