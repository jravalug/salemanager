from app import db
from app.models import Business, InventoryItem
from app.utils.slug_utils import get_business_by_slugs


class InventoryService:
    @staticmethod
    def resolve_business(client_slug: str, business_slug: str) -> Business:
        """Resuelve y valida el negocio a partir de slugs de cliente y negocio."""
        business = get_business_by_slugs(client_slug, business_slug)
        if not business:
            raise ValueError("Negocio no encontrado")
        return business

    @staticmethod
    def _get_item_or_404(inventory_item_id: int) -> InventoryItem:
        """Obtiene un item de inventario o lanza 404 si no existe."""
        return InventoryItem.query.get_or_404(inventory_item_id)

    @staticmethod
    def get_all_items() -> list[InventoryItem]:
        """Devuelve todos los items de inventario ordenados por nombre."""
        return InventoryItem.query.order_by(InventoryItem.name).all()

    @staticmethod
    def create_item(name: str, unit: str):
        """Crea y persiste un nuevo item de inventario."""
        new_item = InventoryItem(name=name, unit=unit)
        db.session.add(new_item)
        db.session.commit()
        return new_item

    @staticmethod
    def update_item(inventory_item_id: int, name: str, unit: str):
        """Actualiza nombre y unidad de un item de inventario existente."""
        inventory_item = InventoryService._get_item_or_404(inventory_item_id)
        inventory_item.name = name
        inventory_item.unit = unit
        db.session.commit()
        return inventory_item
