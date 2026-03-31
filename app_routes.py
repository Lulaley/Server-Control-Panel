from flask import Blueprint, render_template, jsonify, request, redirect
from app_utils import _get_machine_info
from app_config import logger

routes_bp = Blueprint('routes_bp', __name__)

@routes_bp.route("/about", methods=["GET"])
def about():
    return render_template("about.html")

@routes_bp.route("/_ping", methods=["GET"])
def _ping():
    return "ok", 200

@routes_bp.route('/api/machine', methods=['GET'])
def api_machine():
    info = _get_machine_info()
    if info is None:
        return jsonify({"error": "server_error"}), 500
    return jsonify(info)

@routes_bp.app_errorhandler(404)
def not_found_error(e):
    logger.warning("404 error: %s for path %s", e, request.path)
    if request.path in ['/signup', '/reset-password']:
        return redirect('/login')
    return "Page not found", 404

@routes_bp.app_errorhandler(500)
def internal_server_error(e):
    logger.error("Internal server error: %s", e)
    logger.error("Request path: %s", request.path)
    logger.error("Request method: %s", request.method)
    logger.error("Traceback: %s", e, exc_info=True)
    return "Internal server error - check logs for details", 500
