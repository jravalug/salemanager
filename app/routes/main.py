from flask import (
    Blueprint,
    redirect,
    send_from_directory,
    url_for,
)

bp = Blueprint("main", __name__)


@bp.route("/node_modules/<path:filename>")
def node_modules(filename):
    return send_from_directory("../node_modules", filename)


@bp.route("/")
def index():
    return redirect(url_for("client.list_clients"))
