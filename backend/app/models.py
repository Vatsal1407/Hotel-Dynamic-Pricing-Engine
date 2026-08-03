"""SQLAlchemy ORM models."""
from sqlalchemy import Column, Integer, Float, DateTime, JSON
from sqlalchemy.sql import func

from .db import Base


class PricingRequest(Base):
    """Logs each pricing recommendation for the history dashboard."""

    __tablename__ = "pricing_requests"

    id                     = Column(Integer, primary_key=True, index=True)
    created_at             = Column(DateTime(timezone=True), server_default=func.now())
    input_payload          = Column(JSON, nullable=False)
    recommended_price      = Column(Float)
    expected_revenue       = Column(Float)
    cancellation_probability = Column(Float)
    occupancy_rate         = Column(Float)
