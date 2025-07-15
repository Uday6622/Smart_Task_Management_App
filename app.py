from flask import Flask, render_template, redirect, url_for, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from extensions import db, jwt
from datetime import datetime, timedelta

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

    from models import user, task, audit_log
    from models.user import User
    from models.task import Task

    from routes.auth_routes import auth_bp
    from routes.task_routes import task_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(task_bp, url_prefix="/api/tasks")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            if not email or not password:
                return render_template("login.html", message="Email and password are required.")

            user = User.query.filter_by(email=email).first()
            if not user or not check_password_hash(user.password_hash, password):
                return render_template("login.html", message="Invalid credentials.")

            if not user.is_active:
                return render_template("login.html", message="Your account is deactivated.")

            session["user_id"] = user.id
            session["username"] = user.username
            session["is_admin"] = user.is_admin

            if user.is_admin:
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("dashboard"))

        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")

            if not username or not email or not password:
                return render_template("register.html", message="All fields are required.")

            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            if existing_user:
                return render_template("register.html", message="Username or email already exists.")

            hashed_password = generate_password_hash(password)

            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password,
                is_admin=False,
                is_active=True
            )
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/dashboard")
    def dashboard():
        if "user_id" not in session:
            return redirect(url_for("login"))

        tasks = Task.query.filter_by(user_id=session["user_id"]).order_by(Task.id.desc()).all()

        today = datetime.utcnow().date()

        tasks_due_today = [
            t for t in tasks
            if t.due_date is not None and t.due_date.date() == today
        ]

        upcoming_tasks = [
            t for t in tasks
            if t.due_date is not None and t.due_date.date() > today
        ]

        category_counts = {}
        for t in tasks:
            if t.category:
                category_counts[t.category] = category_counts.get(t.category, 0) + 1
        popular_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        popular_categories_data = {
        "labels": [c[0] for c in popular_categories],
        "counts": [c[1] for c in popular_categories]
        }
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        labels = [d.strftime("%Y-%m-%d") for d in last_7_days]
        counts = []
        for day in last_7_days:
            count = sum(
                1 for t in tasks
                if t.status == "Completed" and t.due_date is not None and t.due_date.date() == day
            )
            counts.append(count)

        completed_tasks_data = {
            "labels": labels,
            "counts": counts
        }

        return render_template(
            "dashboard.html",
            tasks=tasks,
            tasks_due_today=tasks_due_today,
            upcoming_tasks=upcoming_tasks,
            popular_categories=popular_categories,
            popular_categories_data=popular_categories_data, 
            completed_tasks_data=completed_tasks_data,
            username=session.get("username")
        )

    @app.route("/create-task", methods=["GET", "POST"])
    def create_task():
        if "user_id" not in session:
            return redirect(url_for("login"))

        if request.method == "POST":
            name = request.form.get("name")
            description = request.form.get("description")
            category = request.form.get("category")
            due_date_str = request.form.get("due_date")
            status = request.form.get("status")

            if not name:
                return render_template("create_task.html", message="Task name is required.")

            parsed_due_date = None
            if due_date_str:
                try:
                    parsed_due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                except ValueError:
                    return render_template("create_task.html", message="Invalid due date format. Use YYYY-MM-DD.")

            new_task = Task(
                user_id=session["user_id"],
                name=name,
                description=description,
                category=category,
                due_date=parsed_due_date,
                status=status or "Pending"
            )
            db.session.add(new_task)
            db.session.commit()

            return redirect(url_for("dashboard"))

        return render_template("create_task.html")

    @app.route("/update-task/<int:task_id>", methods=["GET", "POST"])
    def update_task(task_id):
        if "user_id" not in session:
            return redirect(url_for("login"))

        task = Task.query.get_or_404(task_id)

        if task.user_id != session["user_id"]:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            task.name = request.form.get("name")
            task.description = request.form.get("description")
            task.category = request.form.get("category")
            status = request.form.get("status")

            due_date_str = request.form.get("due_date")
            if due_date_str:
                try:
                    task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                except ValueError:
                    return render_template("edit_task.html", task=task, message="Invalid date format.")
            else:
                task.due_date = None

            task.status = status or "Pending"

            db.session.commit()
            return redirect(url_for("dashboard"))

        return render_template("edit_task.html", task=task)

    @app.route("/delete-task/<int:task_id>", methods=["POST"])
    def delete_task(task_id):
        if "user_id" not in session:
            return redirect(url_for("login"))

        task = Task.query.get_or_404(task_id)

        if task.user_id != session["user_id"]:
            return redirect(url_for("dashboard"))

        db.session.delete(task)
        db.session.commit()
        return redirect(url_for("dashboard"))

    @app.route("/admin")
    def admin_dashboard():
        if not session.get("is_admin"):
            return redirect(url_for("dashboard"))

        users = User.query.all()
        tasks_by_user = {u.id: Task.query.filter_by(user_id=u.id).order_by(Task.due_date).all() for u in users}

        # Compute number of users with at least one task in each status
        status_user_counts = {
            "Pending": 0,
            "In Progress": 0,
            "Completed": 0
        }
        for u in users:
            user_tasks = tasks_by_user[u.id]
            user_statuses = set()
            for t in user_tasks:
                if t.status:
                    user_statuses.add(t.status)
            for status in user_statuses:
                if status in status_user_counts:
                    status_user_counts[status] += 1

        user_task_status_data = {
            "labels": list(status_user_counts.keys()),
            "counts": list(status_user_counts.values())
        }

        return render_template(
            "admin_dashboard.html",
            users=users,
            tasks_by_user=tasks_by_user,
            user_task_status_data=user_task_status_data
        )


    @app.route("/admin/create-task/<int:user_id>", methods=["GET", "POST"])
    def admin_create_task(user_id):
        if not session.get("is_admin"):
            return redirect(url_for("dashboard"))

        user = User.query.get_or_404(user_id)

        if request.method == "POST":
            name = request.form.get("name")
            description = request.form.get("description")
            category = request.form.get("category")
            due_date_str = request.form.get("due_date")
            status = request.form.get("status")

            if not name:
                return render_template("admin_create_task.html", user=user, message="Task name is required.", now=datetime.utcnow())

            parsed_due_date = None
            if due_date_str:
                try:
                    parsed_due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                except ValueError:
                    return render_template("admin_create_task.html", user=user, message="Invalid date format.", now=datetime.utcnow())

            new_task = Task(
                user_id=user.id,
                name=name,
                description=description,
                category=category,
                due_date=parsed_due_date,
                status=status or "Pending"
            )
            db.session.add(new_task)
            db.session.commit()

            return redirect(url_for("admin_dashboard"))

        upcoming_tasks = (
            Task.query.filter(
                Task.user_id == user.id,
                Task.due_date != None,
                Task.due_date >= datetime.utcnow()
            )
            .order_by(Task.due_date)
            .all()
        )

        return render_template("admin_create_task.html", user=user, upcoming_tasks=upcoming_tasks, now=datetime.utcnow())


    @app.route("/admin/update-task/<int:task_id>", methods=["GET", "POST"])
    def admin_update_task(task_id):
        if not session.get("is_admin"):
            return redirect(url_for("dashboard"))

        task = Task.query.get_or_404(task_id)

        if request.method == "POST":
            task.name = request.form.get("name")
            task.description = request.form.get("description")
            task.category = request.form.get("category")
            status = request.form.get("status")

            due_date_str = request.form.get("due_date")
            if due_date_str:
                try:
                    task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                except ValueError:
                    return render_template("edit_task.html", task=task, message="Invalid date format.")
            else:
                task.due_date = None

            task.status = status or "Pending"

            db.session.commit()
            return redirect(url_for("admin_dashboard"))

        return render_template("edit_task.html", task=task)


    @app.route("/admin/delete-task/<int:task_id>", methods=["POST"])
    def admin_delete_task(task_id):
        if not session.get("is_admin"):
            return redirect(url_for("dashboard"))

        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))


    @app.route("/toggle-user-status/<int:user_id>", methods=["POST"])
    def toggle_user_status(user_id):
        if not session.get("is_admin"):
            return redirect(url_for("dashboard"))

        user = User.query.get_or_404(user_id)
        if user.is_admin:
            return redirect(url_for("admin_dashboard"))

        user.is_active = not user.is_active
        db.session.commit()
        return redirect(url_for("admin_dashboard"))


    @app.route("/delete-user/<int:user_id>", methods=["POST"])
    def delete_user(user_id):
        if not session.get("is_admin"):
            return redirect(url_for("dashboard"))

        user = User.query.get_or_404(user_id)
        if user.is_admin:
            return redirect(url_for("admin_dashboard"))

        db.session.delete(user)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))


    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))
    import io
    from flask import send_file
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib import colors

    @app.route("/admin/export/users/pdf")
    def export_users_pdf():
        if not session.get("is_admin"):
            return redirect(url_for("dashboard"))

        users = User.query.all()

        output = io.BytesIO()
        doc = SimpleDocTemplate(output)
        data = [["ID", "Username", "Email", "Is Admin", "Is Active", "Created At"]]
        for u in users:
            data.append([
                str(u.id),
                u.username,
                u.email,
                str(u.is_admin),
                str(u.is_active),
                u.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])

        table = Table(data)
        style = TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0,0), (-1,0), 12),
            ("BACKGROUND", (0,1), (-1,-1), colors.beige),
        ])
        table.setStyle(style)
        elements = [table]
        doc.build(elements)
        output.seek(0)

        return send_file(
            output,
            download_name="users.pdf",
            as_attachment=True,
            mimetype="application/pdf"
        )


    @app.route("/error")
    def error():
        return render_template("error.html", message="Something went wrong.")
    return app

if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        from models.user import User
        if not User.query.filter_by(email="admin@example.com").first():
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=generate_password_hash("admin123"),
                is_admin=True,
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Default admin created: admin@example.com / admin123")

    app.run(host="0.0.0.0", port=5000, debug=True)
