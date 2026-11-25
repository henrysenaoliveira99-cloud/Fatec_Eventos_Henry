from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from app_helpers import get_current_user, login_required, roles_required
from models import db, Event, Registration

events_bp = Blueprint("events", __name__)


def parse_datetime(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        return None


@events_bp.get("/eventos")
def event_list():
    search = request.args.get("q", "").strip()
    query = Event.query
    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
    events = query.order_by(Event.starts_at.asc()).all()
    return render_template("events.html", events=events, search=search)


@events_bp.get("/eventos/<int:event_id>")
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    user = get_current_user()
    registered = bool(user and Registration.query.filter_by(user_id=user.id, event_id=event.id).first())
    return render_template("event_detail.html", event=event, registered=registered)


@events_bp.route("/eventos/novo", methods=["GET", "POST"])
@roles_required("admin", "organizer")
def event_create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        starts_at = parse_datetime(request.form.get("starts_at"))
        ends_at = parse_datetime(request.form.get("ends_at")) if request.form.get("ends_at") else None
        try:
            capacity = int(request.form.get("capacity", "0"))
            if capacity < 0:
                raise ValueError()
        except ValueError:
            capacity = -1
        category = request.form.get("category", "Acadêmico").strip() or "Acadêmico"
        if not title or not description or not location or not starts_at or capacity < 0:
            flash("Preencha os campos obrigatórios e informe uma capacidade válida.", "danger")
            return render_template("event_form.html", event=None), 400
        if ends_at and ends_at < starts_at:
            flash("O término não pode ser anterior ao início.", "danger")
            return render_template("event_form.html", event=None), 400
        event = Event(title=title, description=description, location=location, starts_at=starts_at,
                      ends_at=ends_at, capacity=capacity, category=category, created_by_id=get_current_user().id)
        db.session.add(event)
        db.session.commit()
        flash("Evento cadastrado com sucesso!", "success")
        return redirect(url_for("events.event_detail", event_id=event.id))
    return render_template("event_form.html", event=None)


@events_bp.route("/eventos/<int:event_id>/editar", methods=["GET", "POST"])
@roles_required("admin", "organizer")
def event_edit(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == "POST":
        starts_at = parse_datetime(request.form.get("starts_at"))
        ends_at = parse_datetime(request.form.get("ends_at")) if request.form.get("ends_at") else None
        try:
            capacity = int(request.form.get("capacity", "0"))
            if capacity < 0:
                raise ValueError()
        except ValueError:
            capacity = -1
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        if not title or not description or not location or not starts_at or capacity < 0 or (ends_at and ends_at < starts_at):
            flash("Revise os campos: há informações inválidas.", "danger")
            return render_template("event_form.html", event=event), 400
        event.title, event.description, event.location = title, description, location
        event.starts_at, event.ends_at, event.capacity = starts_at, ends_at, capacity
        event.category = request.form.get("category", "Acadêmico").strip() or "Acadêmico"
        db.session.commit()
        flash("Evento atualizado.", "success")
        return redirect(url_for("events.event_detail", event_id=event.id))
    return render_template("event_form.html", event=event)


@events_bp.post("/eventos/<int:event_id>/excluir")
@roles_required("admin", "organizer")
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Evento excluído.", "info")
    return redirect(url_for("events.event_list"))


@events_bp.post("/eventos/<int:event_id>/inscrever")
@login_required
def event_register(event_id):
    event = Event.query.get_or_404(event_id)
    user = get_current_user()
    if Registration.query.filter_by(user_id=user.id, event_id=event.id).first():
        flash("Você já está inscrito neste evento.", "info")
    elif event.starts_at < datetime.now():
        flash("As inscrições para este evento não estão disponíveis.", "warning")
    elif event.capacity > 0 and event.available_spots <= 0:
        flash("As vagas deste evento estão esgotadas.", "danger")
    else:
        db.session.add(Registration(user_id=user.id, event_id=event.id))
        db.session.commit()
        flash("Inscrição realizada com sucesso!", "success")
    return redirect(url_for("events.event_detail", event_id=event.id))


@events_bp.post("/eventos/<int:event_id>/cancelar-inscricao")
@login_required
def event_unregister(event_id):
    event = Event.query.get_or_404(event_id)
    registration = Registration.query.filter_by(user_id=get_current_user().id, event_id=event.id).first()
    if registration:
        db.session.delete(registration)
        db.session.commit()
        flash("Sua inscrição foi cancelada.", "info")
    return redirect(url_for("events.event_detail", event_id=event.id))
