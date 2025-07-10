from extensions import db  # ✅ Import the shared db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    google_id = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    tasks = db.relationship("Task", backref="user", cascade="all, delete", lazy=True)
    audit_logs = db.relationship("AuditLog", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"
