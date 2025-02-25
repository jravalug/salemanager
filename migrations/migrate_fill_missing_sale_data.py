from app import create_app, db
from app.models import Sale, SaleDetail, Product


def fill_missing_sale_data():
    app = create_app()  # Crea la aplicación Flask
    with app.app_context():
        # Obtener todas las ventas con campos incompletos
        sales = Sale.query.all()

        print(f"Procesando {len(sales)} ventas...")

        for sale in sales:
            # Campos con valores por defecto
            if sale.status is None:
                sale.status = "completed"

            if sale.discount is None:
                sale.discount = 0.0

            if sale.tax is None:
                sale.tax = 0.0

            if sale.excluded is None:
                sale.excluded = False

            # Calcular total_amount desde los productos relacionados
            if sale.total_amount is None or sale.total_amount == 0:
                # Calcular subtotal (productos con descuentos)
                subtotal = sum(
                    sp.total_price * (1 - (sp.discount or 0.0)) for sp in sale.products
                )

                # Aplicar impuesto de la venta
                tax_rate = sale.tax if sale.tax is not None else 0.0
                total = subtotal * (1 + tax_rate)

                sale.total_amount = round(total, 2)

            # Asignar valores razonables para campos opcionales
            if sale.payment_method is None:
                sale.payment_method = "cash"  # Valor por defecto común

            if sale.customer_name is None:
                sale.customer_name = "Cliente ocasional"  # Placeholder

        # Confirmar todos los cambios en la base de datos
        db.session.commit()
        print("Todos los datos han sido actualizados correctamente.")


# Ejecutar el script
if __name__ == "__main__":
    fill_missing_sale_data()
