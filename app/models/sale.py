from app.extensions import db


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=False
    )  # Asociación con el negocio
    products = db.relationship("SaleProduct", back_populates="sale")

    __table_args__ = (
        db.UniqueConstraint(
            "business_id",
            "sale_number",
            "year",
            name="unique_sale_per_business_per_year",
        ),
    )

    def __repr__(self):
        return f"Sale #{self.sale_number} - Business: {self.business.name} - Year: {self.year} - Date: {self.date}"
