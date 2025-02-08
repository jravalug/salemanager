from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Location, Item, Order, OrderItem
from datetime import datetime
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    monthly_totals = {}
    total_general = 0
    orders = Order.query.all()
    for order in orders:
        month = order.date.strftime('%Y-%m')
        total = sum(item.item.price * item.quantity for item in order.items)
        monthly_totals[month] = monthly_totals.get(month, 0) + total
        total_general += total

    months = list(monthly_totals.keys())
    totals = list(monthly_totals.values())
    plt.figure(figsize=(8, 4))
    plt.bar(months, totals, color='skyblue')
    plt.title('Desempeño Mensual')
    plt.xlabel('Mes')
    plt.ylabel('Total Acumulado')
    chart_path = os.path.join('app', 'static', 'chart.png')
    plt.savefig(chart_path)
    plt.close()

    return render_template('index.html', monthly_totals=monthly_totals, total_general=total_general, chart_path=chart_path)

@bp.route('/locations', methods=['GET', 'POST'])
def locations():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        new_location = Location(name=name, description=description)
        db.session.add(new_location)
        db.session.commit()
        flash('Local agregado correctamente', 'success')
        return redirect(url_for('main.locations'))
    
    locations_list = Location.query.all()
    return render_template('locations.html', locations=locations_list)

@bp.route('/items', methods=['GET', 'POST'])
def items():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        new_item = Item(name=name, price=price)
        db.session.add(new_item)
        db.session.commit()
        flash('Item agregado correctamente', 'success')
        return redirect(url_for('main.items'))
    
    items_list = Item.query.all()
    return render_template('items.html', items=items_list)

@bp.route('/items/<int:item_id>', methods=['POST'])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    item.name = request.form['name']
    item.price = float(request.form['price'])
    db.session.commit()
    flash('Item actualizado correctamente', 'success')
    return redirect(url_for('main.items'))

@bp.route('/orders', methods=['GET', 'POST'])
def orders():
    if request.method == 'POST':
        order_number = request.form['order_number']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        new_order = Order(order_number=order_number, date=date)
        db.session.add(new_order)
        db.session.commit()
        flash('Orden creada correctamente', 'success')
        return redirect(url_for('main.add_order_items', order_id=new_order.id))

    # Obtener todas las órdenes
    all_orders = Order.query.order_by(Order.date.desc()).all()

    # Agrupar órdenes por mes y fecha
    orders_by_months = defaultdict(lambda: defaultdict(lambda: {"total_items": 0, "total_income": 0, "orders": []}))
    month_totals = defaultdict(float)

    for order in all_orders:
        month_key = order.date.strftime('%Y-%m')
        date_key = order.date.strftime('%Y-%m-%d')

        # Calcular totales por orden
        total_items = sum(item.quantity for item in order.items)
        total_income = sum(item.item.price * item.quantity for item in order.items)

        # Agregar datos a la estructura
        orders_by_months[month_key][date_key]["total_items"] += total_items
        orders_by_months[month_key][date_key]["total_income"] += total_income
        orders_by_months[month_key][date_key]["orders"].append(order)

        # Acumular totales por mes
        month_totals[month_key] += total_income

    # Convertir defaultdict a diccionarios regulares para Jinja2
    orders_by_months = {month: dict(dates) for month, dates in orders_by_months.items()}
    month_totals = dict(month_totals)

    return render_template('orders.html', orders_by_months=orders_by_months, month_totals=month_totals)

@bp.route('/orders/<int:order_id>/add_items', methods=['GET', 'POST'])
def add_order_items(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        item_id = int(request.form['item_id'])
        quantity = int(request.form['quantity'])
        order_item = OrderItem(order_id=order.id, item_id=item_id, quantity=quantity)
        db.session.add(order_item)
        db.session.commit()
        flash('Item agregado a la orden', 'success')
        return redirect(url_for('main.add_order_items', order_id=order.id))
    
    items_list = Item.query.all()
    return render_template('add_order.html', order=order, items=items_list)

@bp.route('/orders/<int:order_id>')
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    total = sum(item.item.price * item.quantity for item in order.items)
    return render_template('order_details.html', order=order, total=total)