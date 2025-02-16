from flask import Blueprint, send_from_directory, render_template

bp = Blueprint("main", __name__)


@bp.route("/node_modules/<path:filename>")
def node_modules(filename):
    return send_from_directory("../node_modules", filename)


@bp.route("/")
def index():
    return render_template("index.html")
