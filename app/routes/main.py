from datetime import datetime

from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from sqlalchemy import func

from app.models import Business, Client, DailyIncome

bp = Blueprint("main", __name__)


@bp.route("/node_modules/<path:filename>")
def node_modules(filename):
    return send_from_directory("../node_modules", filename)


@bp.route("/")
def index():
    return redirect(url_for("client.list_clients"))
