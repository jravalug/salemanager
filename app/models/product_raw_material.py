from app.extensions import db


class ProductRawMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    raw_material_id = db.Column(
        db.Integer, db.ForeignKey("raw_material.id"), nullable=False
    )
    quantity = db.Column(
        db.Float, nullable=False
    )  # Cantidad de materia prima necesaria

    # Relaciones
    product = db.relationship("Product", backref="raw_materials")
    raw_material = db.relationship("RawMaterial", backref="products")
