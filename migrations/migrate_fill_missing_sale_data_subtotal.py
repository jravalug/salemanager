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
            if sale.subtotal_amount is None:
                sale.subtotal_amount = sum(sp.total_price for sp in sale.products)

        # Confirmar todos los cambios en la base de datos
        db.session.commit()
        print("Todos los datos han sido actualizados correctamente.")


# Ejecutar el script
if __name__ == "__main__":
    fill_missing_sale_data()
