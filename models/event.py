from datetime import datetime
from . import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(160), nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False, index=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    capacity = db.Column(db.Integer, nullable=False, default=0)  # 0 = sem limite informado
    category = db.Column(db.String(80), nullable=False, default="Acadêmico")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    creator = db.relationship("User", back_populates="events_created")
    registrations = db.relationship("Registration", back_populates="event", cascade="all, delete-orphan")

    @property
    def available_spots(self):
        if self.capacity <= 0:
            return None
        return max(0, self.capacity - len(self.registrations))
