# routes/task_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from models.task import Task
from models.audit_log import AuditLog

task_bp = Blueprint("tasks", __name__)

@task_bp.route("/", methods=["POST"])
@jwt_required()
def create_task():
    current_user = get_jwt_identity()
    data = request.get_json()

    status = data.get("status", "Pending")
    
    new_task = Task(
        user_id=current_user["id"],
        name=data.get("name"),
        description=data.get("description"),
        category=data.get("category"),
        due_date=data.get("due_date"),
        status=status
    )

    # If created as completed, set completed_at
    if status == "Completed":
        new_task.completed_at = datetime.utcnow()

    db.session.add(new_task)
    db.session.commit()

    # Audit log
    log = AuditLog(
        user_id=current_user["id"],
        task_id=new_task.id,
        action="CREATE"
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Task created"}), 201

@task_bp.route("/", methods=["GET"])
@jwt_required()
def list_tasks():
    current_user = get_jwt_identity()
    tasks = Task.query.filter_by(user_id=current_user["id"]).order_by(Task.id.desc()).all()
    result = []
    for t in tasks:
        result.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "due_date": t.due_date,
            "status": t.status,
            "completed_at": t.completed_at
        })
    return jsonify(result), 200

@task_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    current_user = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user["id"]).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    task.name = data.get("name", task.name)
    task.description = data.get("description", task.description)
    task.category = data.get("category", task.category)
    task.due_date = data.get("due_date", task.due_date)

    # Handle completed_at update
    new_status = data.get("status", task.status)
    if new_status == "Completed" and task.status != "Completed":
        task.completed_at = datetime.utcnow()
    elif new_status != "Completed":
        task.completed_at = None

    task.status = new_status

    db.session.commit()

    # Audit log
    log = AuditLog(
        user_id=current_user["id"],
        task_id=task.id,
        action="UPDATE"
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Task updated"}), 200

@task_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    current_user = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=current_user["id"]).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()

    # Audit log
    log = AuditLog(
        user_id=current_user["id"],
        task_id=task.id,
        action="DELETE"
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Task deleted"}), 200
