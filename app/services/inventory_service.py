from app import db
from app.models import InventoryItem
from app.utils.slug_utils import get_business_by_slugs


class InventoryService:
    @staticmethod
    def resolve_business(client_slug: str, business_slug: str):
        business = get_business_by_slugs(client_slug, business_slug)
        if not business:
            raise ValueError("Negocio no encontrado")
        return business

    @staticmethod
    def get_all_items():
        return InventoryItem.query.order_by(InventoryItem.name).all()

    @staticmethod
    def create_item(name: str, unit: str):
        new_item = InventoryItem(name=name, unit=unit)
        db.session.add(new_item)
        db.session.commit()
        return new_item

    @staticmethod
    def update_item(inventory_item_id: int, name: str, unit: str):
        inventory_item = InventoryItem.query.get_or_404(inventory_item_id)
        inventory_item.name = name
        inventory_item.unit = unit
        db.session.commit()
        return inventory_item
