# migrate_sale_numbers.py
from app import create_app, db
from app.models import Sale
from collections import defaultdict


def migrate_sale_numbers():
    app = create_app()  # Crea la aplicación Flask
    with app.app_context():
        # Agrupar ventas por business_id y date
        sales = Sale.query.order_by(Sale.business_id, Sale.date, Sale.id).all()
        grouped_sales = defaultdict(list)

        # Agrupar ventas por business_id y date
        for sale in sales:
            key = (sale.business_id, sale.date)
            grouped_sales[key].append(sale)

        # Asignar números consecutivos por día
        for key, sales_group in grouped_sales.items():
            for index, sale in enumerate(sales_group, start=1):
                sale.sale_number = f"{index:03}"  # Formato '001', '002', etc.

        # Guardar cambios en la base de datos
        db.session.commit()
        print("Migración completada exitosamente.")


if __name__ == "__main__":
    migrate_sale_numbers()
