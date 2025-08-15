from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship

from .database import Base

# Tabla intermedia para la relación muchos-a-muchos Student-Laboratory
student_laboratory_association = Table(
    "student_laboratories",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("laboratory_id", Integer, ForeignKey("laboratories.id"), primary_key=True),
)


class Laboratory(Base):
    __tablename__ = "laboratories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, nullable=False, unique=True)

    # Un laboratorio tiene muchos profesores
    professors = relationship("Professor", back_populates="laboratory")

    # Un laboratorio tiene muchos estudiantes (many-to-many)
    students = relationship(
        "Student",
        secondary=student_laboratory_association,
        back_populates="laboratories",
    )


# Professor and Student will inherint from here
class BasePerson(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    profile_url = Column(String)


class Professor(BasePerson):
    __tablename__ = "professors"

    laboratory_id = Column(Integer, ForeignKey("laboratories.id"), nullable=False)

    # Cada profesor pertenece a un laboratorio
    laboratory = relationship("Laboratory", back_populates="professors")


class Student(BasePerson):
    __tablename__ = "students"

    # Un estudiante puede pertenecer a varios laboratorios (many-to-many)
    laboratories = relationship(
        "Laboratory",
        secondary=student_laboratory_association,
        back_populates="students",
    )

    # --- Nueva relación (One-to-Many) ---
    # Un estudiante puede tener varios programas académicos asociados.
    # `cascade` asegura que si borras un estudiante, sus registros académicos también se borren.
    academic_programs = relationship(
        "AcademicProgram", back_populates="student", cascade="all, delete-orphan"
    )


#
class AcademicProgram(Base):
    __tablename__ = "academic_programs"

    id = Column(Integer, primary_key=True, index=True)
    program = Column(String, nullable=False)
    status = Column(String, nullable=False)
    thesis_title = Column(String, nullable=True)
    thesis_url = Column(String, nullable=True)

    # Cada registro de programa pertenece a un solo estudiante.
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    # Permite acceder al objeto Student desde un AcademicProgram (ej: my_program.student)
    student = relationship("Student", back_populates="academic_programs")
