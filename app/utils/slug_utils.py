from app.models import Business, Client


def get_client_by_slug(client_slug: str) -> Client | None:
    """Busca un cliente por `slug` recorriendo clientes ordenados por creación."""
    clients = Client.query.order_by(Client.id.asc()).all()
    return next((item for item in clients if item.slug == client_slug), None)


def get_business_by_slugs(client_slug: str, business_slug: str) -> Business | None:
    """Resuelve un negocio por `client_slug` y `business_slug` dentro del mismo cliente."""
    client = get_client_by_slug(client_slug)
    if not client:
        return None
    businesses = Business.query.filter_by(client_id=client.id).all()
    return next((item for item in businesses if item.slug == business_slug), None)
