from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Laboratory(Base):
    __tablename__ = "laboratories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, nullable=False, unique=True)

    # Un laboratorio tiene muchos profesores
    professors = relationship("Professor", back_populates="laboratory")


class Professor(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, nullable=False)
    email = Column(String)
    profile_url = Column(String)
    laboratory_id = Column(Integer, ForeignKey("laboratories.id"), nullable=False)

    # Cada profesor pertenece a un laboratorio
    laboratory = relationship("Laboratory", back_populates="professors")
