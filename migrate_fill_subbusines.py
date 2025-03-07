from app import create_app, db
from app.models import Sale


def fill_missing_sale_data():
    app = create_app()  # Crea la aplicación Flask
    with app.app_context():
        # Obtener todas las ventas con campos incompletos
        sales = Sale.query.filter_by(business_id=1).order_by(Sale.date.desc()).all()

        print(f"Procesando {len(sales)} ventas...")

        for sale in sales:
            # Campos con valores por defecto
            if not sale.excluded:
                sale.specific_business_id = 6

        # Confirmar todos los cambios en la base de datos
        db.session.commit()
        print("Todos los datos han sido actualizados correctamente.")


# Ejecutar el script
if __name__ == "__main__":
    fill_missing_sale_data()
