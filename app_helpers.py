from functools import wraps
from flask import flash, redirect, session, url_for
from models import db, User


def get_current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            flash("Faça login para acessar essa página.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash("Faça login para continuar.", "warning")
                return redirect(url_for("login"))
            if user.role not in roles:
                flash("Acesso permitido apenas a organizadores e administradores.", "danger")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator
