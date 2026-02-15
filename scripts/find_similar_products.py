#!/usr/bin/env python
"""
Script para encontrar productos con nombre similar en un negocio específico.
Uso: python find_similar_products.py <business_id> <product_id> [similarity_threshold]

Ejemplo: python find_similar_products.py 2 62
"""

import sys
import os
from difflib import SequenceMatcher
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# Configuración de la base de datos
DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/business.db'
engine = create_engine(DATABASE_URI, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Definir modelos (simplificado)
class Business(Base):
    __tablename__ = 'business'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    products = relationship('Product', back_populates='business')

class Sale(Base):
    __tablename__ = 'sale'
    id = Column(Integer, primary_key=True)
    sale_number = Column(String(3), nullable=False)
    date = Column(String, nullable=False)
    business_id = Column(Integer, ForeignKey('business.id'), nullable=False)
    sale_details = relationship('SaleDetail', back_populates='sale')

class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    sku = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True)
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    business_id = Column(Integer, ForeignKey('business.id'), nullable=False)
    business = relationship('Business', back_populates='products')
    raw_materials = relationship('ProductDetail', back_populates='product')

class ProductDetail(Base):
    __tablename__ = 'product_detail'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    raw_material_id = Column(Integer, ForeignKey('inventory_item.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    product = relationship('Product', back_populates='raw_materials')

class SaleDetail(Base):
    __tablename__ = 'sale_detail'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sale.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)
    sale = relationship('Sale', back_populates='sale_details')

def calculate_similarity(str1, str2):
    """Calcula el porcentaje de similitud entre dos strings"""
    ratio = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    return round(ratio * 100, 2)

def find_similar_products(business_id, product_id, similarity_threshold=40):
    """
    Encuentra productos con nombre similar en un negocio específico
    
    Args:
        business_id: ID del negocio
        product_id: ID del producto de referencia
        similarity_threshold: Umbral de similitud en porcentaje (0-100)
    """
    session = Session()
    try:
        # Validar que el negocio existe
        business = session.query(Business).filter_by(id=business_id).first()
        if not business:
            print(f"❌ Error: Negocio con ID {business_id} no encontrado")
            return
        
        # Obtener el producto de referencia
        reference_product = session.query(Product).filter_by(
            id=product_id,
            business_id=business_id
        ).first()
        
        if not reference_product:
            print(f"❌ Error: Producto con ID {product_id} no encontrado en el negocio {business.name}")
            return
        
        # Obtener todos los productos del negocio
        all_products = session.query(Product).filter_by(business_id=business_id).order_by(Product.name).all()
        
        # Encontrar productos similares
        similar_products = []
        for product in all_products:
            if product.id != reference_product.id:  # Excluir el producto de referencia
                # Solo considerar productos que tengan materias primas asociadas
                if len(product.raw_materials) > 0:
                    similarity = calculate_similarity(reference_product.name, product.name)
                    if similarity >= similarity_threshold:
                        similar_products.append({
                            'product': product,
                            'similarity': similarity,
                            'raw_materials_count': len(product.raw_materials)
                        })
        
        # Ordenar por similitud (mayor a menor)
        similar_products.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Mostrar resultados
        print("\n" + "=" * 100)
        print("PRODUCTOS CON NOMBRE SIMILAR")
        print("=" * 100)
        print(f"Negocio: {business.name} (ID: {business_id})")
        print(f"Producto de referencia: {reference_product.name} (ID: {product_id})")
        print(f"Categoría: {reference_product.category if reference_product.category else 'N/A'}")
        print(f"Precio: ${reference_product.price:.2f}")
        print(f"Umbral de similitud: {similarity_threshold}%")
        print("=" * 100)
        print("")
        
        if similar_products:
            print(f"Se encontraron {len(similar_products)} producto(s) similar(es) CON materias primas asociadas:\n")
            for idx, item in enumerate(similar_products, 1):
                product = item['product']
                similarity = item['similarity']
                raw_materials_count = item['raw_materials_count']
                
                print(f"{idx}. {product.name}")
                print(f"   ID: {product.id}")
                print(f"   SKU: {product.sku if product.sku else 'N/A'}")
                print(f"   Categoría: {product.category if product.category else 'N/A'}")
                print(f"   Precio: ${product.price:.2f}")
                print(f"   Activo: {'Sí' if product.is_active else 'No'}")
                print(f"   Similitud: {similarity}%")
                print(f"   Materias primas: {raw_materials_count}")
                print("")
            
            # Preguntar cuál producto seleccionar
            print("=" * 100)
            user_choice = input(f"\n¿Cuál producto deseas seleccionar? (1-{len(similar_products)}, o 0 para cancelar): ").strip()
            
            try:
                choice_idx = int(user_choice) - 1
                if user_choice == "0":
                    print("\n✓ Operación cancelada")
                    print("=" * 100)
                    return
                
                if 0 <= choice_idx < len(similar_products):
                    selected_item = similar_products[choice_idx]
                    selected_product = selected_item['product']
                    
                    # Confirmar la sustitución
                    print("\n" + "=" * 100)
                    print("SUSTITUCIÓN DE PRODUCTOS EN ÓRDENES")
                    print("=" * 100)
                    print(f"Producto Original: {reference_product.name} (ID: {reference_product.id})")
                    print(f"Producto de Sustitución: {selected_product.name} (ID: {selected_product.id})")
                    print("=" * 100)
                    print()
                    
                    confirm = input("¿Deseas continuar con la sustitución? (s/n): ").strip().lower()
                    
                    if confirm == 's':
                        # Buscar todas las órdenes que contienen el producto original
                        orders_to_update = session.query(SaleDetail).filter_by(
                            product_id=reference_product.id
                        ).all()
                        
                        if orders_to_update:
                            print(f"\n✓ Se encontraron {len(orders_to_update)} línea(s) de orden para actualizar...")
                            
                            # Crear respaldo de cambios
                            changes_log = []
                            
                            # Actualizar las órdenes
                            for sale_detail in orders_to_update:
                                changes_log.append({
                                    'sale_id': sale_detail.sale_id,
                                    'old_product_id': reference_product.id,
                                    'old_product_name': reference_product.name,
                                    'new_product_id': selected_product.id,
                                    'new_product_name': selected_product.name,
                                    'quantity': sale_detail.quantity
                                })
                                sale_detail.product_id = selected_product.id
                            
                            # Confirmar cambios en BD
                            session.commit()
                            
                            print("\n" + "=" * 100)
                            print("CAMBIOS REALIZADOS")
                            print("=" * 100)
                            print(f"Total de líneas actualizadas: {len(changes_log)}\n")
                            
                            for log in changes_log:
                                print(f"Orden ID: {log['sale_id']}")
                                print(f"  De: {log['old_product_name']} (ID: {log['old_product_id']}) → A: {log['new_product_name']} (ID: {log['new_product_id']})")
                                print(f"  Cantidad: {log['quantity']}")
                                print("")
                            
                            print("=" * 100)
                            print("✓ ¡Sustitución completada exitosamente!")
                            print("=" * 100)
                        else:
                            print(f"\n⚠ No se encontraron órdenes asociadas al producto {reference_product.name} (ID: {reference_product.id})")
                    else:
                        print("\n✓ Operación cancelada")
                else:
                    print(f"\n❌ Error: Selecciona un número entre 1 y {len(similar_products)}")
            except ValueError:
                print("\n❌ Error: Por favor ingresa un número válido")
        else:
            print(f"No se encontraron productos similares CON materias primas asociadas con un umbral de similitud >= {similarity_threshold}%")
        
        print("=" * 100)
        
    except Exception as e:
        print(f"❌ Error al buscar productos similares: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    print("\n" + "=" * 100)
    print("BUSCAR PRODUCTOS CON NOMBRE SIMILAR")
    print("=" * 100)
    print()
    
    try:
        # Solicitar datos al usuario
        print("Por favor ingresa los siguientes datos:\n")
        
        business_id_input = input("ID del negocio: ").strip()
        if not business_id_input:
            print("❌ Error: El ID del negocio es requerido")
            sys.exit(1)
        business_id = int(business_id_input)
        
        product_id_input = input("ID del producto: ").strip()
        if not product_id_input:
            print("❌ Error: El ID del producto es requerido")
            sys.exit(1)
        product_id = int(product_id_input)
        
        similarity_threshold_input = input("Umbral de similitud (0-100, por defecto 40): ").strip()
        if similarity_threshold_input:
            similarity_threshold = int(similarity_threshold_input)
        else:
            similarity_threshold = 40
        
        if not (0 <= similarity_threshold <= 100):
            print("❌ Error: El umbral de similitud debe estar entre 0 y 100")
            sys.exit(1)
        
        print()
        find_similar_products(business_id, product_id, similarity_threshold)
    except ValueError:
        print("❌ Error: Los valores ingresados deben ser números enteros")
        sys.exit(1)
