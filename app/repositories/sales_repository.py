from sqlalchemy.orm import joinedload
from sqlalchemy import func
from app.extensions import db
from app.models import Business, Sale, SaleDetail, Product


class SalesRepository:

    def _base_query(self):
        """Consulta base con relaciones pre-cargadas"""
        return Sale.query.options(
            joinedload(Sale.products).joinedload(SaleDetail.product)
        )

    def _query_sales(self, filters: dict = None, order_by: dict = None) -> Sale:
        """
        Método privado para realizar consultas genéricas sobre ventas.
        Args:
            filters (dict): Filtros a aplicar en la consulta (opcional).
            order_by (dict): Campo por el cual ordenar los resultados (opcional).
        Returns:
            Sale: Lista de ventas que cumplen con los criterios.
        """

        try:
            query = self._base_query()
            if filters:
                query = query.filter_by(**filters)
            if order_by is not None:  # ✅ Corrección clave
                query = query.order_by(order_by)
            return query.all()
        except Exception as e:
            raise RuntimeError(f"Error al consultar los ventas: {str(e)}")

    def _query_sale(self, filters: dict = None, order_by: dict = None) -> Sale:
        """
        Método privado para realizar consultas genéricas sobre ventas.
        Args:
            sale_id (int): ID de la venta.
            filters (dict): Filtros a aplicar en la consulta (opcional).
            order_by (dict): Campo por el cual ordenar los resultados (opcional).
        Returns:
            Sale: Lista de ventas que cumplen con los criterios.
        """

        try:
            query = self._base_query()

            if filters:
                query = query.filter_by(**filters)
            if order_by is not None:  # ✅ Corrección clave
                query = query.order_by(order_by)
            return query.first()
        except Exception as e:
            raise RuntimeError(f"Error al consultar los ventas: {str(e)}")

    def _calculate_sale_subtotal(self, sale_id: int):
        """Calcula el subtotal de la venta considerando la suma de los productos"""
        try:
            sale = self.get_sale_by_id(sale_id)
            sale.subtotal_amount = round(
                sum(sale_detail.total_price for sale_detail in sale.products), 2
            )
            db.session.commit()
            self._calculate_sale_total(sale)
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al calcular el subtotal de la venta: {e}")

    def _calculate_sale_total(self, sale: Sale):
        """Calcula el subtotal de la venta considerando la suma de los productos"""
        total = (sale.subtotal_amount * (1 - sale.discount)) + (
            sale.subtotal_amount * sale.tax
        )
        print(
            f"El subtotal es: {sale.subtotal_amount}, \n El descuento es: {sale.subtotal_amount * (1 - sale.discount)}, \n El impuesto es: {sale.subtotal_amount * sale.tax} \n El total es: {total}"
        )
        try:
            sale.total_amount = round(total, 2)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al calcular el total de la venta: {e}")

    def get_sale_by_id(self, sale_id: int) -> Sale:
        """
        Obtiene una venta por su ID, verificando que pertenezca a un negocio específico.

        :param sale_id: ID del venta.
        :return: Objeto Sale si existe y pertenece al negocio, None en caso contrario.
        """
        try:
            # Consultar el venta asegurándose de que pertenezca al negocio
            filters = {
                "id": sale_id,
            }

            sale = self._query_sale(filters=filters)
            return sale
        except Exception as e:
            raise RuntimeError(f"Error al consultar el venta: {e}")

    def get_sales_for_month(self, business_id, start_date, end_date):
        """Consulta las ventas de un negocio en un rango de fechas."""
        try:
            return (
                Sale.query.filter(
                    Sale.business_id == business_id,
                    Sale.date.between(start_date, end_date),
                )
                .join(Sale.products)
                .join(SaleDetail.product)
                .order_by(Sale.date.asc())
                .all()
            )
        except Exception as e:
            raise RuntimeError(f"Error al consultar las ventas: {e}")

    def add_sale(self, business_id, **kwargs):
        """
        Crea una nueva venta asociado a un negocio.

        :param business_id: ID del negocio al que pertenece la venta.
        :param kwargs: Atributos adicionales de la venta.
        :return: El objeto Sale recién creado.
        """
        try:
            # Validar campos obligatorios
            required_fields = ["date"]
            for field in required_fields:
                if field not in kwargs:
                    raise ValueError(f"El campo '{field}' es obligatorio.")

            # Validar que el negocio exista
            business = Business.query.get(business_id)
            if not business:
                raise ValueError("El negocio no existe.")

            # Crear la Venta
            new_sale = Sale(business_id=business_id, **kwargs)
            db.session.add(new_sale)
            db.session.commit()
            return new_sale

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al crear la venta: {e}")

    def update_sale(self, sale, **kwargs):
        """
        Actualiza una venta existente.

        :param sale: Objeto Sale a actualizar.
        :param kwargs: Campos y valores a actualizar.
        :return: El objeto Sale actualizado.
        """
        try:
            # Validar que el objeto 'sale' sea una instancia válida del modelo Sale
            if not isinstance(sale, Sale):
                raise ValueError("El parámetro 'sale' debe ser una instancia de Sale.")

            # Validar campos específicos antes de actualizar
            if "date" in kwargs and not kwargs["date"]:
                raise ValueError("El campo 'date' no puede estar vacío.")

            if "sale_number" in kwargs and not kwargs["sale_number"]:
                raise ValueError("El campo 'sale_number' no puede estar vacío.")

            if "payment_method" in kwargs and not kwargs["payment_method"]:
                raise ValueError("El campo 'payment_method' no puede estar vacío.")

            if "status" in kwargs and not kwargs["status"]:
                raise ValueError("El campo 'status' no puede estar vacío.")

            if "discount" in kwargs:
                if kwargs["discount"] is None or kwargs["discount"] < 0:
                    raise ValueError("El campo 'discount' no puede estar vacío.")

            if "tax" in kwargs and not kwargs["tax"]:
                if kwargs["tax"] is None or kwargs["tax"] < 0:
                    raise ValueError("El campo 'tax' no puede estar vacío.")

            # Iterar sobre los campos proporcionados en kwargs
            for key, value in kwargs.items():
                # Verificar si el campo existe en el modelo Sale
                if hasattr(sale, key):
                    setattr(sale, key, value)
                else:
                    raise ValueError(
                        f"El campo '{key}' no es válido para el modelo Sale."
                    )

            # Guardar los cambios en la base de datos
            db.session.commit()
            # Recalculo los totales
            self._calculate_sale_total(sale)
            return sale

        except ValueError as ve:
            # Capturar errores de validación específicos
            db.session.rollback()
            raise ValueError(f"Error de validación: {ve}")

        except Exception as e:
            # Capturar cualquier otro error durante la actualización
            db.session.rollback()
            raise RuntimeError(f"Error al actualizar la venta: {e}")

    def delete_sale(self, sale):
        """
        Elimina una venta de la base de datos.

        :param sale: Objeto Sale a eliminar.
        """
        try:
            db.session.delete(sale)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al eliminar el venta: {e}")

    def add_sale_detail(
        self,
        sale_id: int,
        product_id: int,
        quantity: int,
        unit_price: float,
        discount: float,
        total_price: float,
    ) -> SaleDetail:
        """
        Agrega una materia prima a un producto.

        Args:
            sale_id (int): ID de la venta.
            product_id (int): ID del producto.
            quantity (int): Cantidad del producto.
            unit_price (float): Precio unitario del producto.
            discount (float): Descuento de la venta del producto.
            total_price (float): Precio Total de la venta del producto.
        Returns:
            SaleDetail: La relación SaleDetail creada.
        Raises:
            RuntimeError: Si ocurre un error durante la operación.
        """
        try:
            # Crear la nueva relación
            new_relation = SaleDetail(
                sale_id=sale_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount,
                total_price=total_price,
            )
            db.session.add(new_relation)
            db.session.commit()
            # Recalculo los totales
            self._calculate_sale_subtotal(sale_id)
            return new_relation

        except ValueError as ve:
            db.session.rollback()
            raise ValueError(str(ve))

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al agregar el producto: {str(e)}")

    def update_sale_detail(
        self,
        sale_id: int,
        sale_detail_id: int,
        quantity: int,
        unit_price: float,
        discount: float,
        total_price: float,
    ) -> SaleDetail:
        """
        Actualiza la cantidad de un producto asociada a una venta.

        Args:
            sale_id (int): ID de la venta.
            sale_detail_id (int): ID de la venta del producto.
            quantity (int): Cantidad del producto.
            unit_price (float): Precio unitario del producto.
            discount (float): Descuento de la venta del producto.
            total_price (float): Precio Total de la venta del producto.
        Returns:
            SaleDetail: La relación SaleDetail actualizada.
        Raises:
            ValueError: Si la relación no existe.
            RuntimeError: Si ocurre un error durante la operación.
        """
        try:
            # Buscar la relación existente
            sale_detail = SaleDetail.query.filter_by(
                id=sale_detail_id, sale_id=sale_id
            ).first()

            if not sale_detail:
                raise ValueError("La relación entre la venta y el producto no existe.")

            # Actualizar la cantidad
            sale_detail.quantity = quantity
            sale_detail.discount = discount
            sale_detail.unit_price = unit_price
            sale_detail.total_price = total_price

            # Guardar los cambios en la base de datos
            db.session.commit()
            # Recalculo los totales
            self._calculate_sale_subtotal(sale_id)
            return sale_detail

        except ValueError as ve:
            db.session.rollback()
            raise ValueError(str(ve))

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al actualizar la relación: {str(e)}")

    def remove_sale_detail(self, sale_id: int, sale_detail_id: int) -> bool:
        """
        Elimina una relación entre una venta y un producto.
        Args:
            sale_id (int): ID de la venta.
            sale_detail_id (int): ID de la venta del producto.
        Returns:
            bool: True si la relación fue eliminada correctamente.
        Raises:
            ValueError: Si la relación no existe.
            RuntimeError: Si ocurre un error durante la operación.
        """
        try:
            # Buscar la relación existente
            sale_detail = SaleDetail.query.filter_by(
                id=sale_detail_id,
                sale_id=sale_id,
            ).first()

            if not sale_detail:
                raise ValueError("La relación entre la venta y el producto no existe.")

            # Eliminar la relación
            db.session.delete(sale_detail)

            # Guardar los cambios en la base de datos
            db.session.commit()
            # Recalculo los totales
            self._calculate_sale_subtotal(sale_id)
            return True

        except ValueError as ve:
            db.session.rollback()
            raise ValueError(str(ve))

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Error al eliminar la relación: {str(e)}")

    def get_sales_monthly_totals(self, filters: dict = None) -> dict:
        """
        Crea un listado de ventas mensuales

        Args:
            filters (dict): Filtros a aplicar en la consulta (opcional).

        Returns:
            dict: Diccionario que contiene los meses y los totales.

        Raises:
            RuntimeError: Si ocurre un error durante la operación.
        """
        try:
            monthly_totals = (
                db.session.query(
                    func.strftime("%Y-%m", Sale.date).label("month"),
                    func.sum(Sale.total_amount).label("total"),
                )
                .filter_by(**filters)
                .group_by(func.strftime("%Y-%m", Sale.date))
                .all()
            )
            return monthly_totals
        except Exception as e:
            raise RuntimeError(
                f"Error al crear el listado de ventas mensuales: {str(e)}"
            )
