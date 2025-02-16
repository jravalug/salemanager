from app.extensions import db


class SaleProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sale.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship("Product", back_populates="sale_products")
    sale = db.relationship("Sale", back_populates="products")
