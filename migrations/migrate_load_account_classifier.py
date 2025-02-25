from app import create_app, db
from app.models import db, ACAccount, ACSubAccount, ACElement

# Datos del plan de cuentas (extraídos de tu tabla)
account_classifier = {
    "800": {
        "name": "Gastos de Operaciones",
        "subaccounts": {
            "11": {
                "name": "Materias Primas y Materiales",
                "elements": {
                    "01": "Alimento",
                    "02": "Materiales de la Construcción",
                    "03": "Vestuario y Lencería",
                    "04": "Materiales para la Enseñanza",
                    "05": "Medicamentos y Materiales Afines",
                    "06": "Materiales y Artículos de Consumo",
                    "07": "Libros y Revistas",
                    "08": "Útiles y Herramientas",
                    "09": "Partes y Piezas de Repuestos",
                    "10": "Otros Inventarios",
                    "11": "Equipos de Protección Personal",
                },
            },
            "20": {
                "name": "Mercancía para la Venta",
                "elements": {
                    "01": "Confituras",
                    "02": "Bebidas y Licores",
                    "03": "Cigarros y Tabacos",
                    "04": "Misceláneas",
                    "05": "Material de Oficina",
                },
            },
            "30": {
                "name": "Combustible",
                "elements": {
                    "01": "Gas",
                    "02": "Combustibles",
                    "03": "Lubricantes y Aceites",
                    "04": "Leña",
                    "05": "Carbón",
                },
            },
            "40": {
                "name": "Energía Eléctrica",
                "elements": {
                    "01": "Energía Eléctrica",
                    "02": "Otras formas de energía",
                },
            },
            "80": {
                "name": "Otros Gastos Monetarios y Financieros",
                "elements": {
                    "01": "Viáticos Nacionales",
                    "02": "Prestación a Trabajadores",
                    "03": "Estipendio a Estudiantes",
                    "04": "Otros Servicios de Mantenimiento y Reparaciones Corrientes",
                    "06": "Otros Servicios Contratados",
                    "07": "Servicios Profesionales",
                    "08": "Otros Gastos",
                    "09": "Intereses y Comisiones Bancarias",
                    "10": "Servicio de Mantenimiento y Reparación Constructivo",
                },
            },
        },
    }
}


def load_account_classifier():
    """
    Carga el plan de cuentas en las tablas Account, SubAccount y Element.
    """

    app = create_app()  # Crea la aplicación Flask
    with app.app_context():
        try:
            # Iterar sobre las cuentas principales
            for account_code, account_data in account_classifier.items():
                # Crear la cuenta principal
                account = ACAccount(
                    code=account_code,
                    name=account_data["name"],
                )
                db.session.add(account)

                # Iterar sobre las partidas de la cuenta
                for subaccount_code, subaccount_data in account_data[
                    "subaccounts"
                ].items():
                    subaccount = ACSubAccount(
                        account_code=account_code,
                        code=subaccount_code,
                        name=subaccount_data["name"],
                    )
                    db.session.add(subaccount)

                    # Iterar sobre los elementos de la partida
                    for element_code, element_name in subaccount_data[
                        "elements"
                    ].items():
                        element = ACElement(
                            subaccount_code=subaccount_code,
                            code=element_code,
                            name=element_name,
                        )
                        db.session.add(element)

            # Confirmar los cambios en la base de datos
            db.session.commit()
            print("Plan de cuentas cargado exitosamente.")
        except Exception as e:
            # En caso de error, revertir los cambios
            db.session.rollback()
            print(f"Error al cargar el plan de cuentas: {e}")


if __name__ == "__main__":
    # Ejecutar el script para cargar el plan de cuentas
    load_account_classifier()
