from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    home_team: Mapped[str] = mapped_column(String, nullable=False)
    home_flag: Mapped[str] = mapped_column(String, nullable=False)
    away_team: Mapped[str] = mapped_column(String, nullable=False)
    away_flag: Mapped[str] = mapped_column(String, nullable=False)
    venue_name: Mapped[str] = mapped_column(String, nullable=False)
    venue_address: Mapped[str] = mapped_column(String, nullable=False)
    organizer: Mapped[str] = mapped_column(String, nullable=False)
    kickoff_iso: Mapped[str] = mapped_column(String, nullable=False)
    match_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    invite_link: Mapped[str] = mapped_column(String, nullable=False)
    calendar_link: Mapped[str] = mapped_column(String, nullable=False)
    maps_link: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="future")
    recap_event_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    competition: Mapped[str] = mapped_column(String, default="")
    venue_distance: Mapped[str] = mapped_column(String, default="")
    amenities: Mapped[str] = mapped_column(String, default="[]")  # JSON array of [icon, label] pairs

    registrations: Mapped[list["RegistrationModel"]] = relationship(back_populates="event")
    predictions: Mapped[list["PredictionModel"]] = relationship(back_populates="event")
    photos: Mapped[list["PhotoModel"]] = relationship(back_populates="event")


class RegistrationModel(Base):
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String, ForeignKey("events.id"), nullable=False)
    user_name: Mapped[str] = mapped_column(String, default="")
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    checked_in: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped["EventModel"] = relationship(back_populates="registrations")


class PredictionModel(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String, ForeignKey("events.id"), nullable=False)
    user_name: Mapped[str] = mapped_column(String, default="")
    home_score: Mapped[int] = mapped_column(Integer, nullable=False)
    away_score: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    event: Mapped["EventModel"] = relationship(back_populates="predictions")


class PhotoModel(Base):
    __tablename__ = "photos"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, ForeignKey("events.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    uploader_id: Mapped[str] = mapped_column(String, default="")
    uploader_name: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    event: Mapped["EventModel"] = relationship(back_populates="photos")
