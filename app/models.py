from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CloudResource(Base):
    __tablename__ = "cloud_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    provider: Mapped[str] = mapped_column(String(60), default="AWS")
    resource_type: Mapped[str] = mapped_column(String(60), default="EC2")
    instance_size: Mapped[str] = mapped_column(String(60), default="t3.micro")
    region: Mapped[str] = mapped_column(String(80), default="eu-west-2")
    hourly_cost: Mapped[float] = mapped_column(Float, default=0.0116)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    metrics = relationship("ResourceMetric", back_populates="resource")
    cost_records = relationship("CostRecord", back_populates="resource")
    recommendations = relationship("Recommendation", back_populates="resource")


class ResourceMetric(Base):
    __tablename__ = "resource_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("cloud_resources.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    cpu_percent: Mapped[float] = mapped_column(Float)
    memory_percent: Mapped[float] = mapped_column(Float)
    disk_percent: Mapped[float] = mapped_column(Float)
    network_in_mb: Mapped[float] = mapped_column(Float)
    network_out_mb: Mapped[float] = mapped_column(Float)
    response_time_ms: Mapped[float] = mapped_column(Float, default=120)

    resource = relationship("CloudResource", back_populates="metrics")


class CostRecord(Base):
    __tablename__ = "cost_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("cloud_resources.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    estimated_cost: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")

    resource = relationship("CloudResource", back_populates="cost_records")


class AiPrediction(Base):
    __tablename__ = "ai_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("cloud_resources.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    prediction_type: Mapped[str] = mapped_column(String(80))
    predicted_value: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    details: Mapped[str] = mapped_column(Text, default="")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("cloud_resources.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    category: Mapped[str] = mapped_column(String(60))
    message: Mapped[str] = mapped_column(Text)
    estimated_monthly_saving: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(30), default="open")

    resource = relationship("CloudResource", back_populates="recommendations")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    level: Mapped[str] = mapped_column(String(20), default="INFO")
    message: Mapped[str] = mapped_column(Text)

