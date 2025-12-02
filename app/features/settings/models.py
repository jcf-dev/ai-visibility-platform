from sqlalchemy import Column, String
from app.infrastructure.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    provider = Column(String, primary_key=True, index=True)
    api_key = Column(String, nullable=False)
