from datetime import datetime
from flask import Blueprint, jsonify, request
from app_helpers import get_current_user
from models import db, Event

api_bp = Blueprint("api", __name__, url_prefix="/api")


def event_json(event):
    return {
        "id": event.id, "title": event.title, "description": event.description,
        "location": event.location, "category": event.category,
        "starts_at": event.starts_at.isoformat(), "ends_at": event.ends_at.isoformat() if event.ends_at else None,
        "capacity": event.capacity, "registrations": len(event.registrations),
        "available_spots": event.available_spots
    }


def can_manage():
    user = get_current_user()
    return bool(user and user.role in ("admin", "organizer"))


@api_bp.get("/events")
def api_events():
    events = Event.query.order_by(Event.starts_at.asc()).all()
    return jsonify({"items": [event_json(e) for e in events], "count": len(events)}), 200


@api_bp.get("/events/<int:event_id>")
def api_event_detail(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Evento não encontrado."}), 404
    return jsonify(event_json(event)), 200


@api_bp.post("/events")
def api_event_create():
    if not can_manage():
        return jsonify({"error": "Autenticação e perfil organizador/admin necessários."}), 403
    data = request.get_json(silent=True) or {}
    try:
        starts_at = datetime.fromisoformat(data["starts_at"])
        ends_at = datetime.fromisoformat(data["ends_at"]) if data.get("ends_at") else None
        capacity = int(data.get("capacity", 0))
        if capacity < 0 or (ends_at and ends_at < starts_at):
            raise ValueError()
        required = ["title", "description", "location"]
        if any(not str(data.get(k, "")).strip() for k in required):
            raise KeyError()
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "JSON inválido. Informe title, description, location e starts_at em ISO 8601."}), 400
    event = Event(title=data["title"].strip(), description=data["description"].strip(),
                  location=data["location"].strip(), starts_at=starts_at, ends_at=ends_at,
                  capacity=capacity, category=data.get("category", "Acadêmico"),
                  created_by_id=get_current_user().id)
    db.session.add(event)
    db.session.commit()
    return jsonify(event_json(event)), 201


@api_bp.put("/events/<int:event_id>")
def api_event_update(event_id):
    if not can_manage():
        return jsonify({"error": "Autenticação e perfil organizador/admin necessários."}), 403
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Evento não encontrado."}), 404
    data = request.get_json(silent=True) or {}
    try:
        starts_at = datetime.fromisoformat(data["starts_at"]) if data.get("starts_at") else event.starts_at
        ends_at = datetime.fromisoformat(data["ends_at"]) if data.get("ends_at") else None
        capacity = int(data.get("capacity", event.capacity))
        if capacity < 0 or (ends_at and ends_at < starts_at):
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"error": "Data ou capacidade inválida."}), 400
    for field in ("title", "description", "location", "category"):
        if field in data and str(data[field]).strip():
            setattr(event, field, str(data[field]).strip())
    event.starts_at, event.ends_at, event.capacity = starts_at, ends_at, capacity
    db.session.commit()
    return jsonify(event_json(event)), 200


@api_bp.delete("/events/<int:event_id>")
def api_event_delete(event_id):
    if not can_manage():
        return jsonify({"error": "Autenticação e perfil organizador/admin necessários."}), 403
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Evento não encontrado."}), 404
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Evento excluído."}), 200
