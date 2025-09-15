from typing import List

from app.forms import ProductForm
from app.models import Product, ProductDetail, InventoryItem
from app.extensions import db
from app.repositories.product_repository import ProductRepository


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
