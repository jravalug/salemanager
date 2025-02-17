from app.models import Business, Sale, SaleProduct, Product


class SalesRepository:
    def get_sales_for_month(self, business_id, start_date, end_date):
        """Consulta las ventas de un negocio en un rango de fechas."""
        try:
            return (
                Sale.query.filter(
                    Sale.business_id == business_id,
                    Sale.date.between(start_date, end_date),
                )
                .join(Sale.products)
                .join(SaleProduct.product)
                .order_by(Sale.date.asc())
                .all()
            )
        except Exception as e:
            raise RuntimeError(f"Error al consultar las ventas: {e}")
