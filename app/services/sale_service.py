from typing import Dict, Optional
from sqlalchemy import desc, func

from app import db
from app.forms import SaleForm
from app.models import Sale, Product, SaleDetail
from app.models.business import Business
from app.repositories.sales_repository import SalesRepository
from app.services.business_service import BusinessService


class SalesService:
    """
    Servicio para manejar las operaciones relacionadas con el modelo Sale.
    """

    def __init__(self):
        self.repository = SalesRepository()
        self.business = BusinessService()

    # Nuevos métodos para operaciones CRUD

    def get_sales_by_business(self, business_id):
        """Obtiene las ventas de un negocio"""
        return (
            Sale.query.options(
                db.joinedload(Sale.products).joinedload(SaleDetail.product)
            )
            .filter(Sale.business_id == business_id)
            .first_or_404()
        )

    def get_sale(self, sale_id, business_id):
        """Obtiene los detalles completos de una venta con sus relaciones"""
        return (
            Sale.query.options(
                db.joinedload(Sale.products).joinedload(SaleDetail.product)
            )
            .filter(Sale.id == sale_id, Sale.business_id == business_id)
            .first_or_404()
        )

    def get_available_products(self, business_id):
        """Obtiene los productos disponibles para un negocio"""
        return (
            Product.query.filter_by(business_id=business_id)
            .order_by(Product.name.asc())
            .all()
        )

    def get_sale_details(self, sale_id):
        """Obtiene los productos de una venta específica"""
        return SaleDetail.query.filter_by(sale_id=sale_id).join(Product).all()

    def add_sale(self, business: Business, form: SaleForm) -> Sale:
        """
        Crea una nueva venta asociada a un negocio.


        Args:
            business (Business): Id del negocio al que pertenece la venta.
            form (SaleForm): Campos y valores para crear la venta.

        Returns:
            Sale: El objeto Venta recién generado.
        """
        business_filter = self.business.get_parent_filters(business)

        if business.is_general:
            specific_business_id = form.specific_business_id.data
        else:
            specific_business_id = business_filter["specific_business_id"]

        # Convertir el formulario en un diccionario
        data = {
            "sale_number": form.sale_number.data,
            "date": form.date.data,
            "payment_method": form.payment_method.data,
            "status": form.status.data,
            "excluded": form.excluded.data,
            "discount": form.discount.data or 0,
            "tax": form.tax.data or 0,
            "subtotal_amount": 0,
            "total_amount": 0,
            "specific_business_id": specific_business_id,
        }
        return self.repository.add_sale(business_filter["business_id"], **data)

    def update_sale(self, sale: Sale, form: SaleForm):
        """
        Actualiza una venta existente con los datos proporcionados en el formulario.

        Args:
            sale (Sale): Instancia de Sale a actualizar
            form (SaleForm): Formulario con los nuevos datos validados

        Returns:
            Sale: Instancia actualizada de Sale
        """
        # Convertir el formulario en un diccionario
        data = {
            "sale_number": form.sale_number.data,
            "date": form.date.data,
            "payment_method": form.payment_method.data,
            "status": form.status.data,
            "excluded": form.excluded.data,
            "discount": form.discount.data or 0,
            "tax": form.tax.data or 0,
            "specific_business_id": form.specific_business_id.data,
        }

        return self.repository.update_sale(sale, **data)

    def add_product_to_sale(
        self, sale: Sale, product_id: int, quantity: int, discount: float
    ) -> SaleDetail:
        """
        Agrega un producto a una venta existente

        Args:
            sale (Sale): Instancia de Sale a actualizar
            product_id (int): Id del producto
            quantity (int): Cantidad del producto
            discount (float): Descuento aplicado al producto en la venta
        Returns:
            SaleDetail: El objeto SaleDetail actualizado.
        """
        product = Product.query.get_or_404(product_id)

        return self.repository.add_sale_detail(
            sale_id=sale.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.price,
            discount=discount or 0.0,
            total_price=self._calculate_sale_detail_total(
                product.price, quantity, discount
            ),
        )

    def update_sale_detail(
        self,
        sale: Sale,
        sale_detail: SaleDetail,
        quantity: int,
        discount: float,
    ) -> SaleDetail:
        """
        Actualiza un producto en una venta

        Args:
            sale (Sale): Instancia de Sale a actualizar
            sale_detail (SaleDetail): El objeto SaleDetail a actualizar
            quantity (int): Cantidad del producto
            discount (float): Descuento aplicado al producto en la venta

        Returns:
            SaleDetail: El objeto SaleDetail actualizado.
        """
        if sale_detail.unit_price and sale_detail.unit_price > 0:
            unit_price = sale_detail.unit_price
        else:
            unit_price = sale_detail.product.price

        return self.repository.update_sale_detail(
            sale_id=sale.id,
            sale_detail_id=sale_detail.id,
            quantity=quantity,
            unit_price=unit_price,
            discount=discount or 0.0,
            total_price=self._calculate_sale_detail_total(
                unit_price, quantity, discount
            ),
        )

    def remove_product_from_sale(self, sale: Sale, sale_detail: SaleDetail) -> Product:
        """
        Elimina un producto de una venta

        Args:
            sale (Sale): Instancia de Sale a actualizar
            sale_detail (SaleDetail): El objeto SaleDetail a eliminar
        Returns:
            Product: El objeto Product que se eliminó de la venta.
        """
        removed_product = Product.query.first_or_404(sale_detail.product_id)
        self.repository.remove_sale_detail(sale.id, sale_detail.id)
        return removed_product

    # Helpers Methods
    def _calculate_sale_detail_total(
        self, unit_price: float, quantity: int, discount: float
    ):
        """
        Calcula el total por producto considerando descuentos

        Args:
            unit_price (float): Precio unitario del producto
            quantity (int): Cantidad del producto
            discount (float): Descuento aplicado al producto

        Returns:
            float: Total por producto
        """
        print(f"La cantidad es: {discount}")
        return round(unit_price * quantity * (1 - (discount or 0.0)), 2)

    @staticmethod
    def generate_monthly_totals_sales(
        business_id: int,
        specific_business_id: Optional[int] = None,  # Parámetro opcional
    ) -> Dict[str, float]:
        """
        Genera totales mensuales de ventas para un negocio.

        Args:
            business_id (int): Id del negocio
            specific_business_id (int): Id del negocio específico

        Returns:
            Dict[str, float]: Ventas mensuales para el negocio.
        """
        try:
            # Construir la consulta base
            query = db.session.query(
                func.strftime("%Y-%m", Sale.date).label("month"),
                func.sum(Sale.total_amount).label("total"),
            ).filter(Sale.business_id == business_id)

            # Aplicar filtro de sub negocio si existe
            if specific_business_id is not None:
                query = query.filter(Sale.specific_business_id == specific_business_id)

            # Agrupar y ordenar
            return (
                query.group_by(func.strftime("%Y-%m", Sale.date))
                .order_by(desc(func.strftime("%Y-%m", Sale.date)))
                .all()
            )

        except Exception as e:
            raise RuntimeError(f"Error generando totales mensuales: {str(e)}")
