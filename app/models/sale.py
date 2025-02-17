from sqlalchemy import event
from app.extensions import db


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(3), nullable=False)
    date = db.Column(db.Date, nullable=False)
    business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=False
    )  # Asociación con el negocio
    products = db.relationship("SaleProduct", back_populates="sale")

    __table_args__ = (
        db.UniqueConstraint(
            "business_id",
            "sale_number",
            "date",
            name="unique_sale_per_business_per_date",
        ),
    )

    def __repr__(self):
        return f"Sale #{self.sale_number} - Business: {self.business.name} - Date: {self.date}"


# Evento para generar el sale_number antes de insertar una nueva venta
@event.listens_for(Sale, "before_insert")
def generate_sale_number(mapper, connection, target):
    # Obtener la fecha y el business_id de la venta
    sale_date = target.date
    business_id = target.business_id

    # Consultar la última venta del mismo día y negocio
    last_sale = (
        Sale.query.filter(Sale.business_id == business_id, Sale.date == sale_date)
        .order_by(Sale.sale_number.desc())
        .first()
    )

    # Generar el siguiente sale_number
    if last_sale:
        last_number = int(last_sale.sale_number)
        target.sale_number = f"{last_number + 1:03}"  # Incrementar y formatear
    else:
        target.sale_number = "001"  # Primera venta del día
