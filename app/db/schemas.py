from enum import Enum
from pydantic import BaseModel


class Program(str, Enum):
    MCC = "Maestría en Ciencias de la Computación"
    MCIC = "Maestría en Ciencias en Ingeniería de Cómputo"
    DCC = "Doctorado en Ciencias de la Computación"


# Laboratory
class LaboratoryCreate(BaseModel):
    id: int
    name: str


class LaboratoryRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class BasePerson(BaseModel):
    id: int
    name: str
    email: str | None = None
    profile_url: str | None = None


# Professor
class ProfessorCreate(BasePerson):
    laboratory_id: int | None = None


class ProfessorRead(BasePerson):
    laboratory_id: int

    class Config:
        from_attributes = True


# Student
class StudentCreate(BasePerson):
    pass  # Solo necesita los campos de BasePerson


class StudentRead(BasePerson):
    laboratories: list[LaboratoryRead] = []

    class Config:
        from_attributes = True


# AcademicProgram
class AcademicProgramCreate(BaseModel):
    student_id: int
    program: str  # MCC, MCIC, DCC
    status: str  # inscrito, graduado, egresado
    thesis_title: str | None = None
    thesis_url: str | None = None


class AcademicProgramRead(BaseModel):
    id: int
    student_id: int
    program: str
    status: str
    thesis_title: str | None = None
    thesis_url: str | None = None

    class Config:
        from_attributes = True


# ResearchProduct
class ResearchProductCreate(BaseModel):
    professor_id: int
    title: str
    site: str  # Descripción/Revista donde se publicó
    year: int


class ResearchProductRead(BaseModel):
    id: int
    professor_id: int
    title: str
    site: str
    year: int

    class Config:
        from_attributes = True


# Para asociaciones Student-Laboratory
class StudentLaboratoryAssociation(BaseModel):
    student_id: int
    laboratory_id: int


# Thesis
class ThesisCreate(BaseModel):
    id: int
    title: str
    student_id: int
    advisor1_id: int
    advisor2_id: int | None = None


class ThesisRead(BaseModel):
    id: int
    title: str
    student_id: int
    advisor1_id: int
    advisor2_id: int | None = None

    class Config:
        from_attributes = True
