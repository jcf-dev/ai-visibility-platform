from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database import Base


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="pending")  # pending, running, completed, failed
    notes = Column(String, nullable=True)

    brands = relationship("Brand", back_populates="run", cascade="all, delete-orphan")
    prompts = relationship("Prompt", back_populates="run", cascade="all, delete-orphan")
    responses = relationship(
        "Response", back_populates="run", cascade="all, delete-orphan"
    )


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"))
    name = Column(String, index=True)

    run = relationship("Run", back_populates="brands")
    mentions = relationship("ResponseBrandMention", back_populates="brand")


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"))
    text = Column(Text)

    run = relationship("Run", back_populates="prompts")
    responses = relationship("Response", back_populates="prompt")


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"))
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    model = Column(String)
    latency_ms = Column(Float)
    raw_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    error = Column(Text, nullable=True)  # To store error message if failed

    run = relationship("Run", back_populates="responses")
    prompt = relationship("Prompt", back_populates="responses")
    mentions = relationship(
        "ResponseBrandMention", back_populates="response", cascade="all, delete-orphan"
    )


class ResponseBrandMention(Base):
    __tablename__ = "response_brand_mentions"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("responses.id"))
    brand_id = Column(Integer, ForeignKey("brands.id"))
    mentioned = Column(Boolean, default=False)
    position_index = Column(Integer, nullable=True)  # -1 or null if not found

    response = relationship("Response", back_populates="mentions")
    brand = relationship("Brand", back_populates="mentions")
