from flask import Blueprint, render_template, session, jsonify, request
from werkzeug.security import generate_password_hash
from utils.users import load_pending, save_pending, save_user_record, load_users, save_users_dict, load_reset_requests, save_reset_requests
admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin/pending")
def admin_pending_page():
    if session.get("role") != "admin":
        return "forbidden", 403
    return render_template("admin_pending.html")

@admin_bp.route("/admin/users")
def admin_users_page():
    if session.get("role") != "admin":
        return "forbidden", 403
    return render_template("admin_users.html")

@admin_bp.route("/admin/reset-requests")
def admin_reset_requests_page():
    if session.get("role") != "admin":
        return "forbidden", 403
    return render_template("admin_reset_requests.html")

# API endpoints
@admin_bp.route("/api/admin/pending_users")
def api_admin_pending_list():
    if session.get("role") != "admin":
        return jsonify({"error":"forbidden"}), 403
    pending = load_pending()
    out = [{"username": p.get("username"), "role": p.get("role")} for p in pending]
    return jsonify({"pending": out})

@admin_bp.route("/api/admin/pending_users/<username>/approve", methods=["POST"])
def api_admin_pending_approve(username):
    if session.get("role") != "admin":
        return jsonify({"error":"forbidden"}), 403
    pending = load_pending()
    match = next((p for p in pending if p.get("username")==username), None)
    if not match:
        return jsonify({"error":"not_found"}), 404
    ok = save_user_record(match)
    if not ok:
        return jsonify({"error":"user_exists_or_write_failed"}), 500
    pending = [p for p in pending if p.get("username")!=username]
    save_pending(pending)
    return jsonify({"status":"approved"})

@admin_bp.route("/api/admin/pending_users/<username>/reject", methods=["POST"])
def api_admin_pending_reject(username):
    if session.get("role") != "admin":
        return jsonify({"error":"forbidden"}), 403
    pending = load_pending()
    if not any(p.get("username")==username for p in pending):
        return jsonify({"error":"not_found"}), 404
    pending = [p for p in pending if p.get("username")!=username]
    save_pending(pending)
    return jsonify({"status":"rejected"})

@admin_bp.route("/api/admin/users")
def api_admin_users_list():
    if session.get("role") != "admin":
        return jsonify({"error": "forbidden"}), 403
    users = load_users()
    out = [{"username": u.get("username"), "role": u.get("role")} for u in users.values()]
    return jsonify({"users": out})

@admin_bp.route("/api/admin/users/<username>/role", methods=["POST"])
def api_admin_user_set_role(username):
    if session.get("role") != "admin":
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json() or {}
    new_role = data.get("role")
    if new_role not in ("admin", "manager", "user"):
        return jsonify({"error": "invalid_role"}), 400
    users = load_users()
    if username not in users:
        return jsonify({"error": "not_found"}), 404
    users[username]["role"] = new_role
    if not save_users_dict(users):
        return jsonify({"error": "write_failed"}), 500
    return jsonify({"status": "ok"})

@admin_bp.route("/api/admin/users/<username>", methods=["DELETE"])
def api_admin_user_delete(username):
    if session.get("role") != "admin":
        return jsonify({"error": "forbidden"}), 403
    current = session.get("user")
    if username == current:
        return jsonify({"error": "cannot_delete_self"}), 400
    users = load_users()
    if username not in users:
        return jsonify({"error": "not_found"}), 404
    admin_count = sum(1 for u in users.values() if u.get("role") == "admin")
    if users[username].get("role") == "admin" and admin_count <= 1:
        return jsonify({"error": "cannot_delete_last_admin"}), 400
    users.pop(username, None)
    if not save_users_dict(users):
        return jsonify({"error": "write_failed"}), 500
    return jsonify({"status": "deleted"})

@admin_bp.route("/api/admin/reset_requests")
def api_admin_reset_requests_list():
    if session.get("role") != "admin":
        return jsonify({"error": "forbidden"}), 403
    reset_requests = load_reset_requests()
    out = [{"username": r.get("username")} for r in reset_requests]
    return jsonify({"reset_requests": out})

@admin_bp.route("/api/admin/reset_requests/<username>/approve", methods=["POST"])
def api_admin_reset_approve(username):
    if session.get("role") != "admin":
        return jsonify({"error": "forbidden"}), 403
    reset_requests = load_reset_requests()
    if not any(r.get("username") == username for r in reset_requests):
        return jsonify({"error": "not_found"}), 404
    users = load_users()
    if username not in users:
        return jsonify({"error": "user_not_found"}), 404
    default_password = "azertyuiop*97"
    users[username]["password"] = generate_password_hash(default_password)
    if not save_users_dict(users):
        return jsonify({"error": "write_failed"}), 500
    reset_requests = [r for r in reset_requests if r.get("username") != username]
    save_reset_requests(reset_requests)
    return jsonify({"status": "approved", "new_password": default_password})

@admin_bp.route("/api/admin/reset_requests/<username>/reject", methods=["POST"])
def api_admin_reset_reject(username):
    if session.get("role") != "admin":
        return jsonify({"error": "forbidden"}), 403
    reset_requests = load_reset_requests()
    if not any(r.get("username") == username for r in reset_requests):
        return jsonify({"error": "not_found"}), 404
    reset_requests = [r for r in reset_requests if r.get("username") != username]
    save_reset_requests(reset_requests)
    return jsonify({"status": "rejected"})
