# migrate_sale_numbers.py
from app import create_app, db
from app.models import Sale

from app.repositories.sales_repository import SalesRepository

sale_repo = SalesRepository()


def migrate_sale_numbers():
    app = create_app()  # Crea la aplicación Flask
    with app.app_context():
        # Agrupar ventas por business_id y date
        filters = {"business_id": 2, "excluded": True}
        sales = sale_repo._query_sales(filters=filters)

        # Agrupar ventas por business_id y date
        for sale in sales:
            try:
                for detail in sale.products:
                    db.session.delete(detail)
                    db.session.commit()
                db.session.delete(sale)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise RuntimeError(f"Error al eliminar el venta: {e}")

        # Guardar cambios en la base de datos
        print("Migración completada exitosamente.")


if __name__ == "__main__":
    migrate_sale_numbers()
