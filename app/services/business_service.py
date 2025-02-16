from app.models import Business
from app.extensions import db


def create_business(name, description, logo_path=None):
    """
    Crea un nuevo negocio en la base de datos.
    """
    new_business = Business(name=name, description=description, logo=logo_path)
    db.session.add(new_business)
    db.session.commit()
    return new_business


def update_business(business, name, description, logo_path=None):
    """
    Actualiza un negocio existente en la base de datos.
    """
    business.name = name
    business.description = description
    if logo_path:
        business.logo = logo_path
    db.session.commit()
    return business
