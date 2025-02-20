from app.extensions import db


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=False
    )  # Asociación con el negocio

    # Relación con materias primas
    sale_products = db.relationship("SaleProduct", back_populates="product")
    raw_materials = db.relationship("ProductRawMaterial", back_populates="product")
