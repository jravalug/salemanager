from . import db  # Importar la instancia de db desde __init__.py

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # Nombre del local
    description = db.Column(db.String(255))  # Descripción opcional del local

    # Relaciones
    items = db.relationship('Item', backref='location', lazy=True)
    orders = db.relationship('Order', backref='location', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)  # Asociación con el local

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)  # Asociación con el local

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    order = db.relationship('Order', backref=db.backref('items', lazy=True))
    item = db.relationship('Item', backref=db.backref('orders', lazy=True))

# Función para cargar datos iniciales
def load_initial_data():
    """Carga los items iniciales en la base de datos si no existen."""
    initial_items = [
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

    for item_data in initial_items:
        item = Item.query.filter_by(name=item_data["name"]).first()
        if not item:
            new_item = Item(name=item_data["name"], price=item_data["price"])
            db.session.add(new_item)
    db.session.commit()