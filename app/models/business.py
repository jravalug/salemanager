from app.extensions import db


class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # Nombre del negocio
    description = db.Column(db.String(255))  # Descripción opcional del negocio
    logo = db.Column(db.String(255))  # Ruta del archivo del logo
    products = db.relationship(
        "Product", backref="business", lazy=True
    )  # Relacion de Productos
    sales = db.relationship("Sale", backref="business", lazy=True)  # Relacion de Ventas

    def __repr__(self):
        return f"<Business {self.name}>"
