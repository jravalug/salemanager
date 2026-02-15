#!/usr/bin/env python
"""
Script para generar un archivo txt con los productos que no tienen materias primas por cada negocio.
"""

import sys
import os
from datetime import datetime

# Agregar la ruta del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Importar modelos
from app.models.product import Product, ProductDetail
from app.models.business import Business

def generate_report():
        # Obtener todos los negocios ordenados por nombre
        businesses = Business.query.order_by(Business.name).all()
        
        # Crear el contenido del reporte
        report_content = []
        report_content.append("=" * 80)
        report_content.append(f"PRODUCTOS SIN MATERIAS PRIMAS")
        report_content.append(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        report_content.append("=" * 80)
        report_content.append("")
        
        total_products_without_materials = 0
        
        # Procesar cada negocio
        for business in businesses:
            # Obtener productos del negocio
            products = Product.query.filter_by(business_id=business.id).order_by(Product.name).all()
            
            # Filtrar productos sin materias primas
            products_without_materials = [
                p for p in products 
                if len(p.raw_materials) == 0
            ]
            
            if products_without_materials:
                total_products_without_materials += len(products_without_materials)
                
                report_content.append(f"NEGOCIO: {business.name}")
                report_content.append(f"ID: {business.id}")
                report_content.append("-" * 80)
                report_content.append(f"Total de productos sin materias primas: {len(products_without_materials)}")
                report_content.append("")
                
                for idx, product in enumerate(products_without_materials, 1):
                    report_content.append(f"  {idx}. {product.name}")
                    report_content.append(f"     ID: {product.id}")
                    report_content.append(f"     SKU: {product.sku if product.sku else 'N/A'}")
                    report_content.append(f"     Categoría: {product.category if product.category else 'N/A'}")
                    report_content.append(f"     Precio: ${product.price:.2f}")
                    report_content.append(f"     Activo: {'Sí' if product.is_active else 'No'}")
                    report_content.append("")
                
                report_content.append("")
        
        # Resumen final
        report_content.append("=" * 80)
        report_content.append(f"RESUMEN TOTAL")
        report_content.append(f"Total de negocios: {len(businesses)}")
        report_content.append(f"Total de productos sin materias primas: {total_products_without_materials}")
        report_content.append("=" * 80)
        
        # Escribir el archivo
        output_file = "productos_sin_materias_primas.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_content))
        
        print(f"✓ Reporte generado correctamente: {output_file}")
        print(f"✓ Total de productos sin materias primas: {total_products_without_materials}")

if __name__ == "__main__":
    generate_report()
