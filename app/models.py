from . import db

# Definimos la tabla de asociación
order_items = db.Table('order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('menu_item_id', db.Integer, db.ForeignKey('menu_items.id'), primary_key=True)
)

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Relación Many-to-Many con MenuItem
    items = db.relationship('MenuItem', secondary=order_items, backref=db.backref('orders', lazy='dynamic'), lazy='dynamic')

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

