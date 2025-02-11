from . import db  # Importar la instancia de db desde __init__.py


class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # Nombre del negocio
    description = db.Column(db.String(255))  # Descripción opcional del negocio
    logo = db.Column(db.String(255))  # Ruta del archivo del logo
    products = db.relationship(
        "Product", backref="business", lazy=True
    )  # Relacion de Productos
    sales = db.relationship("Sale", backref="business", lazy=True)  # Relacion de Ventas


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


class SaleProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sale.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship("Product", back_populates="sale_products")
    sale = db.relationship("Sale", back_populates="products")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    business_id = db.Column(
        db.Integer, db.ForeignKey("business.id"), nullable=False
    )  # Asociación con el negocio
    sale_products = db.relationship("SaleProduct", back_populates="product")


# Función para cargar datos iniciales de arquitecto
def load_initial_data_arquitecto():
    """Carga los productos iniciales en la base de datos si no existen."""
    initial_products = [
        {"name": "AGUA", "price": 200.00},
        {"name": "ALBONDIGAS DE CERDO", "price": 1500.00},
        {"name": "ARROZ BLANCO", "price": 300.00},
        {"name": "ARROZ CON CERDO", "price": 650.00},
        {"name": "ARROZ CON CHICHARRON", "price": 500.00},
        {"name": "ARROZ CON POLLO", "price": 650.00},
        {"name": "ARROZ CON TOCINETA", "price": 650.00},
        {"name": "ARROZ CON VEGETALES", "price": 750.00},
        {"name": "ARROZ CONGRIS", "price": 550.00},
        {"name": "ARROZ FRITO", "price": 1000.00},
        {"name": "ARROZ PILAF", "price": 500.00},
        {"name": "ARROZ SALTEADO", "price": 750.00},
        {"name": "BISTEC DE CERDO EMPANADO", "price": 1500.00},
        {"name": "BISTEC DE CERDO GRILLE", "price": 1300.00},
        {"name": "BISTEC DE CERDO LIONESA", "price": 1400.00},
        {"name": "BISTEC URUGUALLO", "price": 1700.00},
        {"name": "CERVEZA BUCANERO", "price": 310.00},
        {"name": "CERVEZA CACIQUE", "price": 310.00},
        {"name": "CERVEZA CALATRAVA", "price": 280.00},
        {"name": "CERVEZA HOLLANDIA", "price": 280.00},
        {"name": "CERVEZA UNLAGUER", "price": 280.00},
        {"name": "CERVEZA WIDWIL", "price": 280.00},
        {"name": "CHICHARRITA", "price": 320.00},
        {"name": "CHULETA AHUMADA", "price": 1450.00},
        {"name": "CIGARRO POPULAR VERDE", "price": 350.00},
        {"name": "CIGARRO ROTMAN ROJO", "price": 350.00},
        {"name": "CROQUETAS", "price": 750.00},
        {"name": "ENSALADA MIXTA", "price": 250.00},
        {"name": "ENSALADA TOMATE", "price": 300.00},
        {"name": "ENTREMES DE JQ", "price": 900.00},
        {"name": "ESPAGUETTI DE JAMON", "price": 850.00},
        {"name": "ESPAGUETTI JQ", "price": 850.00},
        {"name": "ESPAGUETTI NAPOLITANO", "price": 700.00},
        {"name": "ESPERLAN DE PESCADO", "price": 1300.00},
        {"name": "ESPERLAN DE POLLO", "price": 1200.00},
        {"name": "ESTOFADO DE CARNERO", "price": 1200.00},
        {"name": "FAJITAS DE POLLO", "price": 1200.00},
        {"name": "FILETE CANCILLER", "price": 1350.00},
        {"name": "FILETE DE PESCADO FRITO", "price": 1000.00},
        {"name": "FRICASE CARNERO", "price": 1300.00},
        {"name": "FRICASE CERDO", "price": 1450.00},
        {"name": "HAMBURGUESA ESPECIAL CERDO", "price": 1500.00},
        {"name": "JUGO", "price": 260.00},
        {"name": "KERMATO", "price": 550.00},
        {"name": "LONJAS DE CARNERO EN SALSA", "price": 1200.00},
        {"name": "MALTA BUCANERO", "price": 300.00},
        {"name": "MALTA MORENA", "price": 250.00},
        {"name": "MASA DE CERDO FRITA", "price": 1450.00},
        {"name": "PLATANO MADURO FRITO", "price": 300.00},
        {"name": "POLLO A LA CORDON BLUE", "price": 1500.00},
        {"name": "POLLO ASADO", "price": 1100.00},
        {"name": "POLLO FRITO", "price": 1100.00},
        {"name": "REFRESCO", "price": 270.00},
        {"name": "SOPA DE POLLO", "price": 500.00},
        {"name": "TOSTON NATURAL", "price": 350.00},
        {"name": "TOSTON RELLENO JQ", "price": 450.00},
    ]

    business = Business.query.filter_by(name="La Casa del Arquitecto").first()
    if not business:
        business = Business(
            name="La Casa del Arquitecto",
            description="Restaurante la Casa del Arquitecto",
        )
        db.session.add(business)
        db.session.commit()

    for product_data in initial_products:
        product = Product.query.filter_by(
            name=product_data["name"], business_id=1
        ).first()
        if not product:
            new_product = Product(
                name=product_data["name"],
                price=product_data["price"],
                business_id=business.id,
            )
            db.session.add(new_product)
    db.session.commit()


# Función para cargar datos iniciales de solar
def load_initial_data_solar():
    """Carga los productos iniciales en la base de datos si no existen."""
    initial_products = [
        {"name": "AGREGO CEBOLLA", "price": 350.00},
        {"name": "AGREGO LIMON", "price": 200.00},
        {"name": "AGUA", "price": 250.00},
        {"name": "AJIACO CAMAGÜEYANO", "price": 150.00},
        {"name": "ARROZ FRITO", "price": 405.00},
        {"name": "ARROZ BLANCO", "price": 125.00},
        {"name": "ARROZ CON POLLO", "price": 440.00},
        {"name": "ARROZ IMPERIAL", "price": 950.00},
        {"name": "ARROZ MOROS Y CRISTIANO", "price": 165.00},
        {"name": "BATIDO FRUTA BOMBBA", "price": 190.00},
        {"name": "BATIDO MAMEY", "price": 190.00},
        {"name": "BISTEC DE CERDO GRILLET", "price": 975.00},
        {"name": "BISTEC DE CERDO URUGUAYO", "price": 1350.00},
        {"name": "BISTEC DE POLLO GRILLET", "price": 975.00},
        {"name": "BISTEC DE RES", "price": 850.00},
        {"name": "BONIATO FRITO", "price": 500.00},
        {"name": "CAFÉ EXPRESO", "price": 100.00},
        {"name": "CERVEZA", "price": 300.00},
        {"name": "CHICHARRITAS", "price": 500.00},
        {"name": "CHILINDRON DE CARNERO", "price": 1095.00},
        {"name": "ENSALADA MIXTA", "price": 350.00},
        {"name": "ENSALADA TOMATE", "price": 500.00},
        {"name": "FILETE DE PESCADO", "price": 975.00},
        {"name": "FRIJOLES NEGROS", "price": 500.00},
        {"name": "FUFU DE PLATANO", "price": 250.00},
        {"name": "JABA", "price": 10.00},
        {"name": "JUGO CAJA", "price": 300.00},
        {"name": "JUGO FRUTA BOMBA", "price": 155.00},
        {"name": "JUGO GUALLABA", "price": 155.00},
        {"name": "JUGO MAMEY", "price": 155.00},
        {"name": "JUGO TOMATE", "price": 240.00},
        {"name": "LIMONADA FRAPE", "price": 250.00},
        {"name": "MALTA", "price": 300.00},
        {"name": "MASA DE CERDO", "price": 975.00},
        {"name": "MATA JIBARO", "price": 315.00},
        {"name": "MICHELADA", "price": 540.00},
        {"name": "PAELLA", "price": 1500.00},
        {"name": "PAPA FRITAS", "price": 500.00},
        {"name": "PASTA NATURAL (ESPAGUETI)", "price": 440.00},
        {"name": "PESCADO FRITO", "price": 975.00},
        {"name": "PIERNA DE CERDO AZADA", "price": 1625.00},
        {"name": "PIÑA COLADA", "price": 250.00},
        {"name": "PLATANO MADURO FRITO", "price": 500.00},
        {"name": "POLLO FRITO", "price": 815.00},
        {"name": "POLLO GORDONBLUE", "price": 1315.00},
        {"name": "POZUELO", "price": 90.00},
        {"name": "PUDIN", "price": 390.00},
        {"name": "REFRESCO LATA", "price": 300.00},
        {"name": "ROPA VIEJA", "price": 850.00},
        {"name": "SOPA DE PESCADO", "price": 440.00},
        {"name": "SOPA DE POLLO", "price": 440.00},
        {"name": "SOPA DE VEGETALES", "price": 190.00},
        {"name": "SPAG JAMÓN Y QUESO", "price": 575.00},
        {"name": "TAMAL EN HOJAS", "price": 250.00},
        {"name": "TOSTONES DE PLATANO VERDE", "price": 500.00},
        {"name": "TOSTONES RELLENOS", "price": 475.00},
        {"name": "YUCA CON MOJO", "price": 500.00},
    ]

    business = Business.query.filter_by(name="El Solar").first()
    if not business:
        business = Business(name="El Solar", description="Restaurante el Solar")
        db.session.add(business)
        db.session.commit()

    for product_data in initial_products:
        product = Product.query.filter_by(
            name=product_data["name"], business_id=2
        ).first()
        if not product:
            new_product = Product(
                name=product_data["name"],
                price=product_data["price"],
                business_id=business.id,
            )
            db.session.add(new_product)
    db.session.commit()
