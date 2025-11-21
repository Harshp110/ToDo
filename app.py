from flask import (
    Flask, render_template, request, redirect, send_file,
    flash, url_for, jsonify, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from collections import Counter
from openpyxl import Workbook
import pathlib, os, io, json

# -----------------------------------------------------
# INITIAL SETUP
# -----------------------------------------------------
BASE_DIR = pathlib.Path(__file__).parent.resolve()
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".txt"}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "replace-with-your-secret")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

# -----------------------------------------------------
# DATABASE CONFIG
# -----------------------------------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------------------------------
# MODELS
# -----------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    todos = db.relationship("Todo", backref="owner", cascade="all,delete", lazy=True)

class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default="Medium")
    category = db.Column(db.String(50), default="General")
    due_date = db.Column(db.String(20), nullable=True)
    position = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Reminders
    reminder_time = db.Column(db.DateTime, nullable=True)
    reminder_minutes_before = db.Column(db.Integer, default=0)

    # Kanban
    status = db.Column(db.String(20), default="todo")  # todo, inprogress, done

    attachments = db.relationship("Attachment", backref="todo", cascade="all,delete", lazy=True)
    subtasks = db.relationship("Subtask", backref="todo", cascade="all,delete", lazy="dynamic")

class Subtask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    todo_id = db.Column(db.Integer, db.ForeignKey("todo.sno"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    todo_id = db.Column(db.Integer, db.ForeignKey("todo.sno"), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    mimetype = db.Column(db.String(100), nullable=True)

# -----------------------------------------------------
# LOGIN MANAGER
# -----------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------------------------------
# CREATE DB TABLES
# -----------------------------------------------------
with app.app_context():
    db.create_all()

# -----------------------------------------------------
# HELPERS
# -----------------------------------------------------
def allowed_file(filename):
    return pathlib.Path(filename).suffix.lower() in ALLOWED_EXT

def simple_summary(text, max_chars=200):
    if not text:
        return ""
    text = " ".join(text.split())
    return text[:max_chars] + ("..." if len(text) > max_chars else "")

# Optional OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
try:
    if OPENAI_API_KEY:
        import openai
        openai.api_key = OPENAI_API_KEY
except Exception:
    openai = None

# -----------------------------------------------------
# ROUTES
# -----------------------------------------------------

# --------------------- Dashboard ---------------------
# -----------------------------------------------------
# DASHBOARD ROUTE
# -----------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    # all todos for current user
    todos = Todo.query.filter_by(user_id=current_user.id).all()

    total = len(todos)
    completed = sum(1 for t in todos if t.completed)
    pending = total - completed

    # category counts
    by_cat = Counter(t.category for t in todos)

    # priority counts
    by_prio = Counter(t.priority for t in todos)

    # completed in last 7 days
    today = datetime.utcnow().date()
    last7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
    completed_by_day = {d.isoformat(): 0 for d in last7}

    for t in todos:
        if t.completed and t.date_created:
            d = t.date_created.date().isoformat()
            if d in completed_by_day:
                completed_by_day[d] += 1

    # Kanban columns
    todo_col = [t for t in todos if t.status == "todo"]
    inprog_col = [t for t in todos if t.status == "inprogress"]
    done_col = [t for t in todos if t.status == "done"]

    return render_template(
        "dashboard.html",
        total=total,
        completed=completed,
        pending=pending,
        by_cat=by_cat,
        by_prio=by_prio,
        completed_by_day=completed_by_day,
        todo_col=todo_col,
        inprog_col=inprog_col,
        done_col=done_col,
    )



# ------------------- Uploads -------------------------
@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/attach/<int:sno>", methods=["POST"])
@login_required
def attach_file(sno):
    todo = Todo.query.get_or_404(sno)
    if todo.user_id != current_user.id:
        flash("Not allowed", "danger")
        return redirect("/")

    f = request.files.get("file")
    if not f:
        flash("No file", "warning")
        return redirect("/")

    if allowed_file(f.filename):
        filename = secure_filename(f.filename)
        final = f"{todo.sno}_{int(datetime.utcnow().timestamp())}_{filename}"
        f.save(UPLOAD_FOLDER / final)

        db.session.add(Attachment(todo_id=sno, filename=final, mimetype=f.mimetype))
        db.session.commit()

        flash("Uploaded", "success")
    else:
        flash("File type not allowed", "danger")

    return redirect("/")

@app.route("/delete_attach/<int:id>")
@login_required
def delete_attach(id):
    at = Attachment.query.get_or_404(id)
    if at.todo.user_id != current_user.id:
        return redirect("/")

    try:
        (UPLOAD_FOLDER / at.filename).unlink()
    except:
        pass

    db.session.delete(at)
    db.session.commit()
    return redirect("/")

# ------------------- OpenAI Summaries -----------------
@app.route("/ai/summarize", methods=["POST"])
@login_required
def ai_summarize():
    text = (request.json or {}).get("text", "")
    if OPENAI_API_KEY and openai:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Summarize:\n{text}"}],
                max_tokens=120
            )
            return jsonify({"summary": response["choices"][0]["message"]["content"]})
        except Exception:
            pass

    return jsonify({"summary": simple_summary(text)})

# ------------------- Auth -----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("User exists", "warning")
            return redirect("/signup")

        db.session.add(User(username=username, password=generate_password_hash(password)))
        db.session.commit()

        flash("Created. Login now.", "success")
        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect("/")

        flash("Invalid credentials", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ------------------- Home / Add Todo ------------------
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        desc = request.form.get("desc", "").strip()
        priority = request.form.get("priority", "Medium")
        category = request.form.get("category", "General")
        due_date = request.form.get("due_date")
        reminder_raw = request.form.get("reminder_time")

        reminder_time = None
        if reminder_raw:
            try:
                reminder_time = datetime.fromisoformat(reminder_raw)
            except:
                pass

        max_pos = db.session.query(db.func.max(Todo.position)).filter_by(user_id=current_user.id).scalar()
        pos = (max_pos + 1) if max_pos else 0

        todo = Todo(
            title=title, desc=desc, priority=priority, category=category,
            due_date=due_date, reminder_time=reminder_time,
            user_id=current_user.id, position=pos
        )
        db.session.add(todo)
        db.session.commit()

        return redirect("/")

    todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.position.desc()).all()
    categories = sorted({t.category for t in todos} | {"General", "Work", "Study", "Personal", "Urgent"})

    return render_template("index.html", allTodo=todos, categories=categories)

# ------------------- Delete Todo ----------------------
@app.route("/delete/<int:sno>")
@login_required
def delete(sno):
    todo = Todo.query.get_or_404(sno)
    if todo.user_id != current_user.id:
        return redirect("/")

    for a in todo.attachments:
        try: (UPLOAD_FOLDER / a.filename).unlink()
        except: pass

    db.session.delete(todo)
    db.session.commit()

    return redirect("/")

# ------------------- Update Todo ----------------------
@app.route("/update/<int:sno>", methods=["GET", "POST"])
@login_required
def update(sno):
    todo = Todo.query.get_or_404(sno)
    if todo.user_id != current_user.id:
        return redirect("/")

    if request.method == "POST":
        todo.title = request.form.get("title", todo.title)
        todo.desc = request.form.get("desc", todo.desc)
        todo.priority = request.form.get("priority", todo.priority)
        todo.category = request.form.get("category", todo.category)
        todo.due_date = request.form.get("due_date", todo.due_date)

        rt = request.form.get("reminder_time")
        try:
            todo.reminder_time = datetime.fromisoformat(rt) if rt else None
        except:
            todo.reminder_time = None

        db.session.commit()
        return redirect("/")

    return render_template("update.html", todo=todo)

# ------------------- Toggle Complete ------------------
@app.route("/toggle/<int:sno>", methods=["POST"])
@login_required
def toggle(sno):
    todo = Todo.query.get_or_404(sno)
    if todo.user_id != current_user.id:
        return ("", 403)
    todo.completed = not todo.completed
    db.session.commit()
    return ("", 204)

# ------------------- Reorder List ---------------------
@app.route("/reorder", methods=["POST"])
@login_required
def reorder():
    order = request.get_json().get("order", [])
    for i, sno in enumerate(order):
        todo = Todo.query.get(int(sno))
        if todo and todo.user_id == current_user.id:
            todo.position = len(order) - i
    db.session.commit()
    return ("", 204)

# ------------------- Subtasks -------------------------
@app.route("/subtask/add/<int:sno>", methods=["POST"])
@login_required
def add_subtask(sno):
    title = request.form.get("subtask_title", "").strip()
    todo = Todo.query.get_or_404(sno)

    if todo.user_id != current_user.id:
        return redirect("/")

    db.session.add(Subtask(todo_id=sno, title=title))
    db.session.commit()
    return redirect("/")

@app.route("/subtask/toggle/<int:id>", methods=["POST"])
@login_required
def toggle_subtask(id):
    st = Subtask.query.get_or_404(id)
    if st.todo.user_id != current_user.id:
        return ("", 403)

    st.done = not st.done
    db.session.commit()
    return ("", 204)

@app.route("/subtask/delete/<int:id>")
@login_required
def delete_subtask(id):
    st = Subtask.query.get_or_404(id)
    if st.todo.user_id != current_user.id:
        return redirect("/")
    db.session.delete(st)
    db.session.commit()
    return redirect("/")

# ------------------- Kanban Update --------------------
@app.route("/kanban/update", methods=["POST"])
@login_required
def kanban_update():
    data = request.get_json()
    sno = data.get("sno")
    todo = Todo.query.get_or_404(sno)

    if todo.user_id != current_user.id:
        return ("", 403)

    todo.status = data.get("status", todo.status)
    todo.position = data.get("position", todo.position)
    db.session.commit()

    return ("", 204)

# ------------------- Dashboard API --------------------
@app.route("/api/stats")
@login_required
def api_stats():
    todos = Todo.query.filter_by(user_id=current_user.id).all()

    by_priority = Counter(t.priority for t in todos)
    by_category = Counter(t.category for t in todos)
    completion = {"done": sum(t.completed for t in todos),
                  "todo": sum(not t.completed for t in todos)}

    return jsonify({
        "by_priority": dict(by_priority),
        "by_category": dict(by_category),
        "completion": completion
    })

# ------------------- Export Excel ---------------------
@app.route("/export")
@login_required
def export_xlsx():
    todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.position.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.append(["Sno", "Title", "Description", "Priority", "Category", "Due Date", "Completed", "Created"])

    for t in todos:
        ws.append([
            t.sno, t.title, t.desc, t.priority, t.category,
            t.due_date or "", str(t.completed),
            t.date_created.strftime("%Y-%m-%d %H:%M:%S")
        ])

    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)

    return send_file(
        bio,
        download_name=f"todos_{current_user.username}.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# -----------------------------------------------------
# RUN APP
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
