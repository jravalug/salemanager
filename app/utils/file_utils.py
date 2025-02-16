import os
from werkzeug.utils import secure_filename
from flask import current_app, flash

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    """
    Verifica si el archivo tiene una extensión permitida.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def handle_logo_upload(logo_file):
    """
    Maneja la subida de un archivo de logo.
    """
    if logo_file and allowed_file(logo_file.filename):
        filename = secure_filename(logo_file.filename)
        logo_path = os.path.join("images", "logos", filename)
        full_path = os.path.join(
            current_app.root_path, "static", "images", "logos", filename
        )
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            logo_file.save(full_path)
            return logo_path
        except Exception as e:
            flash(f"Error al guardar el logo: {str(e)}", "error")
            return None
    else:
        flash(
            "Formato de archivo no permitido. Sube una imagen (PNG, JPG, JPEG, GIF).",
            "error",
        )
        return None
