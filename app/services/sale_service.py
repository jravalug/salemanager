from app import db
from app.models import Sale, Product, SaleProduct
from app.repositories.sales_repository import SalesRepository


class SalesService:
    def __init__(self):
        self.repository = SalesRepository()

    # Nuevos métodos para operaciones CRUD

    def get_sale_details(self, sale_id, business_id):
        """Obtiene los detalles completos de una venta con sus relaciones"""
        return (
            Sale.query.options(
                db.joinedload(Sale.products).joinedload(SaleProduct.product)
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

    def get_sale_products(self, sale_id):
        """Obtiene los productos de una venta específica"""
        return SaleProduct.query.filter_by(sale_id=sale_id).join(Product).all()

    def add_sale(self, form_data, business_id):
        """Actualiza los datos principales de una venta"""
        print(f"En el servicio add_sale antes de guardar la venta")
        new_sale = Sale(
            sale_number=form_data.sale_number.data,
            date=form_data.date.data,
            payment_method=form_data.payment_method.data,
            status=form_data.status.data,
            excluded=form_data.excluded.data,
            discount=form_data.discount.data,
            tax=form_data.tax.data,
            subtotal_amount=0,
            total_amount=0,
            business_id=business_id,
        )
        print(f"En el servicio add_sale despues de guardar la venta")
        db.session.add(new_sale)
        db.session.commit()
        return new_sale

    def update_sale(self, sale, form_data):
        """Actualiza los datos principales de una venta"""
        sale.sale_number = form_data.sale_number.data
        sale.date = form_data.date.data
        sale.payment_method = form_data.payment_method.data
        sale.status = form_data.status.data
        sale.excluded = form_data.excluded.data
        sale.customer_name = form_data.customer_name.data
        sale.discount = form_data.discount.data
        sale.tax = form_data.tax.data

        self._update_sale_totals(sale)
        db.session.commit()
        return sale

    def add_product_to_sale(self, sale, product_id, quantity, discount):
        """Agrega un producto a una venta existente"""
        product = Product.query.get_or_404(product_id)

        new_sale_product = SaleProduct(
            sale_id=sale.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price,
            discount=discount or 0.0,
            total_price=self.calculate_sale_product_total(
                product.price, quantity, discount
            ),
        )

        db.session.add(new_sale_product)
        self._update_sale_totals(sale)
        db.session.commit()
        return new_sale_product

    def remove_product_from_sale(self, sale, sale_product_id):
        """Elimina un producto de una venta"""
        sale_product = SaleProduct.query.filter_by(
            id=sale_product_id, sale_id=sale.id
        ).first_or_404()
        removed_product = Product.query.first_or_404(sale_product.product_id)
        db.session.delete(sale_product)
        self._update_sale_totals(sale)
        db.session.commit()
        return removed_product

    def update_sale_product(self, sale_product, quantity, discount):
        """Actualiza un producto en una venta"""
        sale_product.quantity = quantity
        sale_product.discount = discount or 0.0
        sale_product.unit_price = sale_product.unit_price or sale_product.product.price
        sale_product.total_price = self.calculate_sale_product_total(
            sale_product.unit_price, quantity, sale_product.discount
        )

        self._update_sale_totals(sale_product.sale)
        db.session.commit()
        return sale_product

    # Helpers Methods

    def _update_sale_totals(self, sale):
        """Actualiza los totales de la venta"""
        sale.subtotal_amount = self.calculate_sale_subtotal(sale)
        sale.total_amount = self.calculate_sale_total(sale)

    def calculate_sale_product_total(self, unit_price, quantity, discount):
        """Calcula el total por producto considerando descuentos"""
        return round(unit_price * quantity * (1 - (discount or 0.0)), 2)

    def calculate_sale_subtotal(self, sale):
        """Calcula el subtotal de la venta considerando la suma de los productos"""
        return round(sum(sale_product.total_price for sale_product in sale.products), 2)

    def calculate_sale_total(self, sale):
        """Calcula el total de la venta considerando descuentos e impuestos"""
        return round(
            sale.subtotal_amount
            * (1 - (sale.discount or 0.0))
            * (1 + (sale.tax or 0.0)),
            2,
        )
