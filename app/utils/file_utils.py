import os
from flask import current_app, flash
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
LOGO_RELATIVE_DIR = os.path.join("images", "logos")


def _build_logo_paths(filename: str) -> tuple[str, str]:
    """Construye ruta relativa pública y ruta absoluta de guardado del logo."""
    logo_path = os.path.join(LOGO_RELATIVE_DIR, filename)
    full_path = os.path.join(
        current_app.root_path, "static", LOGO_RELATIVE_DIR, filename
    )
    return logo_path, full_path


def allowed_file(filename: str) -> bool:
    """Verifica si el archivo tiene una extensión permitida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def handle_logo_upload(logo_file):
    """Guarda el logo subido y devuelve su ruta pública relativa, o `None`."""
    if not logo_file or logo_file.filename == "":
        return None

    if not allowed_file(logo_file.filename):
        flash(
            "Formato de archivo no permitido. Sube una imagen (PNG, JPG, JPEG, GIF).",
            "error",
        )
        return None

    filename = secure_filename(logo_file.filename)
    logo_path, full_path = _build_logo_paths(filename)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        logo_file.save(full_path)
        return logo_path
    except Exception as e:
        flash(f"Error al guardar el logo: {str(e)}", "error")
        return None
