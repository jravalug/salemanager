from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from .models import Order, MenuItem
from . import db

bp = Blueprint('orders', __name__)

@bp.route('/')
def index():
    menu_items = MenuItem.query.all()
    return render_template('index.html', menu_items=menu_items)

@bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    new_order = Order(customer_name=data['customer_name'], items=data['items'])
    db.session.add(new_order)
    db.session.commit()
    return jsonify({'message': 'Order created', 'order_id': new_order.id}), 201

@bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({'id': order.id, 'customer_name': order.customer_name, 'items': order.items})

@bp.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.get_json()
    order = Order.query.get_or_404(order_id)
    order.customer_name = data['customer_name']
    order.items = data['items']
    db.session.commit()
    return jsonify({'message': 'Order updated'})

@bp.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({'message': 'Order deleted'})

@bp.route('/menu_items', methods=['POST'])
def create_menu_item():
    data = request.form
    new_item = MenuItem(name=data['name'], price=data['price'])
    db.session.add(new_item)
    db.session.commit()
    return redirect(url_for('orders.index'))

@bp.route('/menu_items/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    return jsonify({'id': item.id, 'name': item.name, 'price': item.price})

@bp.route('/menu_items/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    data = request.form
    item = MenuItem.query.get_or_404(item_id)
    item.name = data['name']
    item.price = data['price']
    db.session.commit()
    return redirect(url_for('orders.index'))

@bp.route('/menu_items/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('orders.index'))