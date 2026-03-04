from typing import List
from sqlalchemy import func

from app.forms import ProductForm
from app.models import Product, ProductDetail, InventoryItem, Sale, SaleDetail
from app.extensions import db
from app.repositories.product_repository import ProductRepository
from app.utils.slug_utils import get_business_by_slugs


class ProductService:
    """
    Servicio para manejar las operaciones relacionadas con el modelo Product.
    """

    def __init__(self):
        self.repository = ProductRepository()

    def get_all_products(self, business_id: int) -> List[Product]:
        """
        Obtiene todos los productos asociados a un negocio específico.

        :param business_id: Id del negocio.
        :return: Lista de productos ordenados por nombre.
        """
        return self.repository.get_all_products(business_id=business_id)

    def get_product_by_id(self, business_id, product_id):
        """
        Obtiene un producto por su Id, verificando que pertenezca a un negocio específico.

        :param business_id: Id del negocio al que debe pertenecer el producto.
        :param product_id: Id del producto.
        :return: Objeto Product si existe y pertenece al negocio, None en caso contrario.
        """
        return self.repository.get_product_by_id(
            business_id=business_id, product_id=product_id
        )

    def get_full_product(self, business_id, product_id):
        """
        Obtiene un producto específico que pertenece a un negocio dado,
        incluyendo sus materias primas asociadas.

        :param business_id: Id del negocio al que pertenece el producto.
        :param product_id: Id del producto a buscar.
        :return: Objeto Product si existe y pertenece al negocio, None en caso contrario.
        """
        return self.repository.get_product_with_raw_materials(
            business_id=business_id, product_id=product_id
        )

    def create_product(self, business_id, form):
        """
        Crea un nuevo producto asociado a un negocio.

        :param business_id: Id del negocio al que pertenece el producto.
        :param form: Campos y valores para crear el producto.
        :return: El objeto Product recién creado.
        """
        # Convertir el formulario en un diccionario
        data = {
            "name": form.name.data,
            "price": form.price.data,
            "instructions": form.instructions.data,
            "description": form.description.data,
            "category": form.category.data,
            "sku": form.sku.data,
            "is_active": form.is_active.data,
            "is_batch_prepared": form.is_batch_prepared.data,
            "batch_size": form.batch_size.data,
        }
        return self.repository.create_product(business_id, **data)

    def update_product(self, product, form):
        """
        Actualiza un producto existente.

        :param product: Objeto Product a actualizar.
        :param form: Campos y valores a actualizar.
        :return: El objeto Product actualizado.
        """
        # Convertir el formulario en un diccionario
        data = {
            "name": form.name.data,
            "price": form.price.data,
            "instructions": form.instructions.data,
            "description": form.description.data,
            "category": form.category.data,
            "sku": form.sku.data,
            "is_active": form.is_active.data,
            "is_batch_prepared": form.is_batch_prepared.data,
            "batch_size": form.batch_size.data,
        }

        return self.repository.update_product(product, **data)

    def add_raw_material(self, product_id, raw_material_id, quantity):
        """
        Agrega una materia prima a un producto.

        :param product_id: Id del producto.
        :param raw_material_id: Id de la materia prima.
        :param quantity: Cantidad de la materia prima.
        :return: La relación ProductDetail creada.
        """
        return self.repository.add_product_detail(product_id, raw_material_id, quantity)

    def update_raw_material(self, product_id, raw_material_id, quantity):
        """
        Actualiza la cantidad de una materia prima asociada a un producto.

        :param product_id: Id del producto.
        :param raw_material_id: Id de la materia prima.
        :param quantity: Cantidad de la materia prima.
        :return: La relación ProductDetail actualizada.
        """
        return self.repository.update_product_detail(
            product_id, raw_material_id, quantity
        )

    def remove_raw_material(self, product_id, raw_material_id):
        """
        Elimina una materia prima asociada a un producto.

        :param product_id: Id del producto.
        :param raw_material_id: Id de la materia prima.
        """
        return self.repository.remove_product_detail(product_id, raw_material_id)

    def remove_raw_material_with_name(
        self, product_id: int, raw_material_id: int
    ) -> str:
        raw_material = InventoryItem.query.get(raw_material_id)
        if not raw_material:
            raise ValueError("La materia prima seleccionada no existe.")

        self.remove_raw_material(product_id=product_id, raw_material_id=raw_material.id)
        return raw_material.name

    def get_products_api_data(self, client_slug: str, business_slug: str):
        business = get_business_by_slugs(client_slug, business_slug)
        if not business:
            return []

        products = Product.query.filter(Product.business_id == business.id).all()
        return [
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "category": product.category,
            }
            for product in products
        ]

    def get_product_list_stats(self, business_id: int, products_list: List[Product]):
        categories = sorted(
            {
                product.category
                for product in products_list
                if getattr(product, "category", None)
            }
        )

        sale_stats = {}
        product_ids = [product.id for product in products_list]
        if not product_ids:
            return categories, sale_stats

        rows = (
            db.session.query(
                SaleDetail.product_id,
                func.coalesce(func.sum(SaleDetail.quantity), 0).label("total_sold"),
                func.count(func.distinct(SaleDetail.sale_id)).label("orders_count"),
                func.max(Sale.date).label("last_sale_date"),
            )
            .join(Sale, Sale.id == SaleDetail.sale_id)
            .filter(Sale.business_id == business_id)
            .filter(SaleDetail.product_id.in_(product_ids))
            .group_by(SaleDetail.product_id)
            .all()
        )

        for product_id, total_sold, orders_count, last_date in rows:
            sale_stats[product_id] = {
                "total_sold": int(total_sold) if total_sold is not None else 0,
                "orders_count": int(orders_count) if orders_count is not None else 0,
                "last_sale_date": last_date,
            }

        pd_rows = (
            db.session.query(
                ProductDetail.product_id,
                ProductDetail.raw_material_id,
                ProductDetail.quantity.label("qty_per_product"),
                InventoryItem.name.label("raw_name"),
                InventoryItem.unit.label("raw_unit"),
            )
            .join(InventoryItem, InventoryItem.id == ProductDetail.raw_material_id)
            .filter(ProductDetail.product_id.in_(product_ids))
            .all()
        )

        raw_map = {}
        for product_id, raw_id, qty_per_product, raw_name, raw_unit in pd_rows:
            raw_map.setdefault(product_id, []).append(
                {
                    "raw_id": raw_id,
                    "raw_name": raw_name,
                    "raw_unit": raw_unit,
                    "qty_per_product": qty_per_product,
                }
            )

        for product_id in product_ids:
            stats = sale_stats.get(
                product_id,
                {"total_sold": 0, "orders_count": 0, "last_sale_date": None},
            )
            total_sold = stats.get("total_sold", 0)
            materials = []

            for material in raw_map.get(product_id, []):
                try:
                    used_total = float(material["qty_per_product"]) * float(total_sold)
                except Exception:
                    used_total = 0

                materials.append(
                    {
                        "raw_id": material["raw_id"],
                        "raw_name": material["raw_name"],
                        "raw_unit": material["raw_unit"],
                        "qty_per_product": material["qty_per_product"],
                        "used_total": used_total,
                    }
                )

            if product_id in sale_stats:
                sale_stats[product_id]["raw_materials"] = materials
            else:
                sale_stats[product_id] = {
                    "total_sold": 0,
                    "orders_count": 0,
                    "last_sale_date": None,
                    "raw_materials": materials,
                }

        return categories, sale_stats
