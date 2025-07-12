from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.user import User
from models.task import Task
from datetime import datetime

admin_bp = Blueprint("admin", __name__)

def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        if not current_user["is_admin"]:
            return jsonify({"error": "Admins only"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

# Existing routes...

@admin_bp.route("/tasks", methods=["GET"])
@admin_required
def list_all_tasks():
    tasks = Task.query.all()
    result = []
    for t in tasks:
        result.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "status": t.status,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "user_id": t.user_id
        })
    return jsonify(result), 200

@admin_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@admin_required
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.json
    task.name = data.get("name", task.name)
    task.description = data.get("description", task.description)
    task.category = data.get("category", task.category)
    task.status = data.get("status", task.status)

    due_date_str = data.get("due_date")
    if due_date_str:
        try:
            task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    db.session.commit()
    return jsonify({"message": "Task updated"}), 200

@admin_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@admin_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"}), 200
