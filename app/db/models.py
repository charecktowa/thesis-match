from sqlalchemy import Column, Integer, String, ForeignKey, Table
from pgvector.sqlalchemy import Vector
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

    # Un profesor puede tener muchos productos de investigación
    research_products = relationship(
        "ResearchProduct", back_populates="professor", cascade="all, delete-orphan"
    )

    # Un profesor puede ser asesor principal en muchas tesis
    advised_theses_primary = relationship(
        "Thesis", foreign_keys="Thesis.advisor1_id", back_populates="advisor1"
    )

    # Un profesor puede ser asesor secundario en muchas tesis
    advised_theses_secondary = relationship(
        "Thesis", foreign_keys="Thesis.advisor2_id", back_populates="advisor2"
    )


class ResearchProduct(Base):
    """
    Papers and conferences (title, site and year)

    A professor can have many research products.
    """

    __tablename__ = "research_products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    site = Column(String, nullable=False)
    year = Column(Integer, nullable=False)

    embedding = Column(Vector(1024), nullable=True)

    # Cada producto de investigación pertenece a un profesor
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=False)
    professor = relationship("Professor", back_populates="research_products")


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

    # Un estudiante puede tener una tesis
    thesis = relationship("Thesis", back_populates="student", uselist=False)


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


class Thesis(Base):
    """
    Thesis information with advisors

    A thesis belongs to one student and has 1-2 advisors (professors).
    """

    __tablename__ = "theses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    title = Column(String, nullable=False)

    embedding = Column(Vector(1024), nullable=True)

    # Foreign key to student
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    # Foreign keys to advisors (professors)
    advisor1_id = Column(Integer, ForeignKey("professors.id"), nullable=False)
    advisor2_id = Column(
        Integer, ForeignKey("professors.id"), nullable=True
    )  # Optional second advisor

    # Relationships
    student = relationship("Student", back_populates="thesis")
    advisor1 = relationship(
        "Professor", foreign_keys=[advisor1_id], back_populates="advised_theses_primary"
    )
    advisor2 = relationship(
        "Professor",
        foreign_keys=[advisor2_id],
        back_populates="advised_theses_secondary",
    )
