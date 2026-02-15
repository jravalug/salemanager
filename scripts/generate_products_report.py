#!/usr/bin/env python
"""
Script independiente para generar un archivo txt con los productos que no tienen materias primas.
Conecta directamente a SQLAlchemy sin cargar la aplicación Flask.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

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

class Sale(Base):
    __tablename__ = 'sale'
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('business.id'), nullable=False)
    date = Column(String, nullable=False)
    sale_detail = relationship('SaleDetail', back_populates='sale')

class SaleDetail(Base):
    __tablename__ = 'sale_detail'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sale.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    sale = relationship('Sale', back_populates='sale_detail')

def generate_report():
    session = Session()
    try:
        # Obtener todos los negocios ordenados por nombre
        businesses = session.query(Business).order_by(Business.name).all()
        
        # Crear el contenido del reporte
        report_content = []
        report_content.append("=" * 80)
        report_content.append("PRODUCTOS SIN MATERIAS PRIMAS")
        report_content.append("(Categorías: Comida, Postre, Coctelería)")
        report_content.append(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        report_content.append("=" * 80)
        report_content.append("")
        
        total_products_without_materials = 0
        businesses_with_products_without_materials = 0
        
        # Procesar cada negocio
        for business in businesses:
            # Obtener productos del negocio
            products = session.query(Product).filter_by(business_id=business.id).order_by(Product.name).all()
            
            # Filtrar productos sin materias primas y con categorías específicas
            products_without_materials = [
                p for p in products 
                if len(p.raw_materials) == 0 and p.category in ['comida', 'postre', 'cocteleria']
            ]
            
            # Enriquecer con información de órdenes y ordenar por cantidad de órdenes (menor a mayor)
            products_with_orders = []
            for product in products_without_materials:
                sale_details = session.query(SaleDetail).filter_by(product_id=product.id).all()
                sale_ids = [str(sd.sale_id) for sd in sale_details]
                unique_sale_ids = list(set(sale_ids))
                unique_sale_ids.sort(key=int)
                
                products_with_orders.append({
                    'product': product,
                    'orders_count': len(sale_ids),
                    'unique_orders': len(unique_sale_ids),
                    'unique_sale_ids': unique_sale_ids
                })
            
            # Ordenar por número de órdenes únicas (de menor a mayor)
            products_with_orders.sort(key=lambda x: x['unique_orders'])
            
            if products_with_orders:
                businesses_with_products_without_materials += 1
                total_products_without_materials += len(products_with_orders)
                
                report_content.append(f"NEGOCIO: {business.name}")
                report_content.append(f"ID: {business.id}")
                report_content.append("-" * 80)
                report_content.append(f"Total de productos sin materias primas: {len(products_with_orders)}")
                report_content.append("")
                
                for idx, item in enumerate(products_with_orders, 1):
                    product = item['product']
                    unique_sale_ids = item['unique_sale_ids']
                    orders_count = item['orders_count']
                    unique_orders = item['unique_orders']
                    
                    report_content.append(f"  {idx}. {product.name}")
                    report_content.append(f"     ID: {product.id}")
                    report_content.append(f"     SKU: {product.sku if product.sku else 'N/A'}")
                    report_content.append(f"     Categoría: {product.category if product.category else 'N/A'}")
                    report_content.append(f"     Precio: ${product.price:.2f}")
                    report_content.append(f"     Activo: {'Sí' if product.is_active else 'No'}")
                    report_content.append(f"     Veces vendido: {orders_count}")
                    report_content.append(f"     Órdenes únicas: {unique_orders}")
                    
                    if unique_sale_ids:
                        report_content.append(f"     IDs de órdenes: {', '.join(unique_sale_ids)}")
                    report_content.append("")
                
                report_content.append("")
        
        # Resumen final
        report_content.append("=" * 80)
        report_content.append("RESUMEN TOTAL")
        report_content.append(f"Total de negocios: {len(businesses)}")
        report_content.append(f"Negocios con productos sin materias primas: {businesses_with_products_without_materials}")
        report_content.append(f"Total de productos sin materias primas: {total_products_without_materials}")
        report_content.append("=" * 80)
        
        # Escribir el archivo
        output_file = "productos_sin_materias_primas.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_content))
        
        print(f"✓ Reporte generado correctamente: {output_file}")
        print(f"✓ Total de productos sin materias primas: {total_products_without_materials}")
        print(f"✓ En {businesses_with_products_without_materials} negocio(s)")
        
    except Exception as e:
        print(f"❌ Error al generar el reporte: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    generate_report()
