# models/audit_log.py

from app import db

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # e.g., CREATE, UPDATE, DELETE
    details = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<AuditLog {self.action} TaskID={self.task_id}>"
