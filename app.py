import os
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, User, Event, Registration
from controllers.event_controller import events_bp
from controllers.api_controller import api_bp

load_dotenv()

app = Flask(__name__)
os.makedirs(app.instance_path, exist_ok=True)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///eventos.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Alguns provedores entregam postgres://; SQLAlchemy atual espera postgresql://.
if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres://"):
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"].replace("postgres://", "postgresql+psycopg://", 1)
elif app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql://"):
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"].replace("postgresql://", "postgresql+psycopg://", 1)

db.init_app(app)
app.register_blueprint(events_bp)
app.register_blueprint(api_bp)


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


@app.context_processor
def inject_user():
    return {"logged_user": current_user()}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Faça login para acessar essa página.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Faça login para continuar.", "warning")
                return redirect(url_for("login"))
            if user.role not in roles:
                flash("Você não tem permissão para realizar essa ação.", "danger")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.get("/")
def index():
    events = Event.query.filter(Event.starts_at >= datetime.now()).order_by(Event.starts_at.asc()).limit(6).all()
    return render_template("index.html", events=events)


@app.get("/login")
def login():
    if current_user():
        return redirect(url_for("index"))
    return render_template("login.html")


@app.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash("E-mail ou senha inválidos.", "danger")
        return render_template("login.html"), 401
    if not user.active:
        flash("Esta conta está desativada. Procure a coordenação.", "warning")
        return render_template("login.html"), 403
    session.clear()
    session["user_id"] = user.id
    flash(f"Bem-vindo(a), {user.name}!", "success")
    destination = request.args.get("next")
    return redirect(destination if destination and destination.startswith("/") else url_for("index"))


@app.get("/cadastro")
def register():
    return render_template("register.html")


@app.post("/cadastro")
def register_post():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if len(name) < 3 or "@" not in email or len(password) < 8:
        flash("Informe nome válido, e-mail válido e senha com pelo menos 8 caracteres.", "danger")
        return render_template("register.html"), 400
    if User.query.filter_by(email=email).first():
        flash("Já existe uma conta com esse e-mail.", "warning")
        return render_template("register.html"), 409
    user = User(name=name, email=email, password_hash=generate_password_hash(password), role="student")
    db.session.add(user)
    db.session.commit()
    flash("Cadastro realizado! Agora entre com sua conta.", "success")
    return redirect(url_for("login"))


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("index"))


@app.get("/painel")
@login_required
def dashboard():
    user = current_user()
    if user.role in ("admin", "organizer"):
        events = Event.query.order_by(Event.starts_at.desc()).all()
        registrations = Registration.query.join(Event).order_by(Registration.created_at.desc()).limit(10).all()
    else:
        events = [r.event for r in Registration.query.filter_by(user_id=user.id).all()]
        registrations = []
    return render_template("dashboard.html", events=events, registrations=registrations)


@app.cli.command("init-db")
def init_db():
    """Cria as tabelas do banco."""
    db.create_all()
    print("Tabelas criadas.")


@app.cli.command("create-admin")
def create_admin():
    """Cria um administrador inicial: informe ADMIN_NAME, ADMIN_EMAIL e ADMIN_PASSWORD no ambiente."""
    name = os.getenv("ADMIN_NAME", "Administrador")
    email = os.getenv("ADMIN_EMAIL", "admin@fatec.local").lower()
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        print("Defina ADMIN_PASSWORD antes de executar flask create-admin.")
        return
    if User.query.filter_by(email=email).first():
        print("Já existe um usuário com esse e-mail.")
        return
    db.session.add(User(name=name, email=email, password_hash=generate_password_hash(password), role="admin"))
    db.session.commit()
    print(f"Administrador {email} criado.")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1", host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
