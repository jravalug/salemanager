from app import create_app, db
from app.models import SaleDetail, Product


def fill_missing_sale_detail_data():
    app = create_app()  # Crea la aplicación Flask
    with app.app_context():
        # Obtener todos los registros que necesitan actualización
        incomplete_records = SaleDetail.query.filter(
            (SaleDetail.unit_price.is_(None))
            | (SaleDetail.total_price.is_(None))
            | (SaleDetail.discount.is_(None))
        ).all()

        print(f"Registros incompletos encontrados: {len(incomplete_records)}")

        for record in incomplete_records:
            product = Product.query.get(record.product_id)

            if not product:
                print(f"No se encontró el producto con ID {record.product_id}")
                continue

            # Establecer unit_price con el precio actual del producto
            if record.unit_price is None and product:
                record.unit_price = product.price

            # Calcular total_price si falta
            if record.total_price is None and record.quantity and record.unit_price:
                record.total_price = (
                    record.quantity * record.unit_price * (1 - (record.discount or 0.0))
                )

            # Establecer descuento default si es None
            if record.discount is None:
                record.discount = 0.0

        db.session.commit()
        print(f"Actualizados {len(incomplete_records)} registros de SaleDetail")


if __name__ == "__main__":
    fill_missing_sale_detail_data()
