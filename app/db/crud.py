from sqlalchemy.orm import Session

from . import models, schemas


def create_laboratory(
    db: Session, laboratory: schemas.LaboratoryCreate
) -> models.Laboratory:
    db_laboratory = models.Laboratory(name=laboratory.name)
    db.add(db_laboratory)
    db.commit()
    db.refresh(db_laboratory)
    return db_laboratory


def get_laboratory_by_name(db: Session, name: str) -> models.Laboratory | None:
    return db.query(models.Laboratory).filter(models.Laboratory.name == name).first()


def get_laboratory_by_id(db: Session, laboratory_id: int) -> models.Laboratory | None:
    return (
        db.query(models.Laboratory)
        .filter(models.Laboratory.id == laboratory_id)
        .first()
    )


def create_professor(
    db: Session, professor: schemas.ProfessorCreate
) -> models.Professor:
    db_professor = models.Professor(
        name=professor.name,
        email=professor.email,
        profile_url=professor.profile_url,
        laboratory_id=professor.laboratory_id,
    )
    db.add(db_professor)
    db.commit()
    db.refresh(db_professor)
    return db_professor


def get_professor_by_email(db: Session, email: str) -> models.Professor | None:
    return db.query(models.Professor).filter(models.Professor.email == email).first()


def get_professors_by_lab_name(db: Session, lab_name: str) -> list[models.Professor]:
    return (
        db.query(models.Professor)
        .filter(models.Professor.laboratory.has(name=lab_name))
        .all()
    )


# Student CRUD operations
def create_student(db: Session, student: schemas.StudentCreate) -> models.Student:
    db_student = models.Student(
        id=student.id,
        name=student.name,
        email=student.email,
        profile_url=student.profile_url,
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def get_student_by_id(db: Session, student_id: int) -> models.Student | None:
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_student_by_email(db: Session, email: str) -> models.Student | None:
    return db.query(models.Student).filter(models.Student.email == email).first()


def add_student_to_laboratory(db: Session, student_id: int, laboratory_id: int) -> bool:
    """Asocia un estudiante con un laboratorio"""

    # Verificar que el estudiante existe
    student = get_student_by_id(db, student_id)
    if not student:
        print(f"Student {student_id} not found")
        return False

    # Verificar que el laboratorio existe
    laboratory = get_laboratory_by_id(db, laboratory_id)
    if not laboratory:
        print(f"Laboratory {laboratory_id} not found")
        return False

    # Verificar que no exceda el límite de 2 laboratorios
    if len(student.laboratories) >= 2:
        print(f"Student {student_id} already belongs to 2 laboratories")
        return False

    # Verificar que la asociación no exista ya
    if laboratory in student.laboratories:
        print(
            f"Student {student_id} already associated with laboratory {laboratory_id}"
        )
        return False

    # Crear la asociación
    student.laboratories.append(laboratory)
    db.commit()
    return True


def get_students_by_laboratory(db: Session, laboratory_id: int) -> list[models.Student]:
    """Obtiene todos los estudiantes de un laboratorio específico"""
    return (
        db.query(models.Student)
        .join(models.student_laboratory_association)
        .filter(models.student_laboratory_association.c.laboratory_id == laboratory_id)
        .all()
    )


def get_laboratories_by_student(
    db: Session, student_id: int
) -> list[models.Laboratory]:
    """Obtiene todos los laboratorios de un estudiante específico"""
    return (
        db.query(models.Laboratory)
        .join(models.student_laboratory_association)
        .filter(models.student_laboratory_association.c.student_id == student_id)
        .all()
    )
