# models/task.py

from app import db

class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(
    db.Enum("Pending", "In Progress", "Completed"),
    default="Pending",
    nullable=False
)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    audit_logs = db.relationship("AuditLog", backref="task", lazy=True)

    def __repr__(self):
        return f"<Task {self.name}>"
