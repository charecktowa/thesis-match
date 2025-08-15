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


def update_student_status(db: Session, student_id: int, new_status: str) -> bool:
    """Actualiza el status de un estudiante"""
    student = get_student_by_id(db, student_id)
    if not student:
        return False

    # Para evitar problemas de tipado, actualizamos directamente con query
    db.query(models.Student).filter(models.Student.id == student_id).update(
        {"status": new_status}
    )
    db.commit()
    return True


# AcademicProgram CRUD operations
def create_academic_program(
    db: Session, academic_program: schemas.AcademicProgramCreate
) -> models.AcademicProgram:
    """Crear un programa académico para un estudiante"""
    db_academic_program = models.AcademicProgram(
        student_id=academic_program.student_id,
        program=academic_program.program,
        status=academic_program.status,
        thesis_title=academic_program.thesis_title,
        thesis_url=academic_program.thesis_url,
    )
    db.add(db_academic_program)
    db.commit()
    db.refresh(db_academic_program)
    return db_academic_program


def get_academic_programs_by_student(
    db: Session, student_id: int
) -> list[models.AcademicProgram]:
    """Obtener todos los programas académicos de un estudiante"""
    return (
        db.query(models.AcademicProgram)
        .filter(models.AcademicProgram.student_id == student_id)
        .all()
    )


def get_academic_program_by_student_and_program(
    db: Session, student_id: int, program: str
) -> models.AcademicProgram | None:
    """Obtener un programa académico específico de un estudiante"""
    return (
        db.query(models.AcademicProgram)
        .filter(
            models.AcademicProgram.student_id == student_id,
            models.AcademicProgram.program == program,
        )
        .first()
    )


def update_academic_program_thesis(
    db: Session,
    student_id: int,
    program: str,
    thesis_title: str,
    thesis_url: str | None = None,
) -> bool:
    """Actualizar información de tesis de un programa académico"""
    update_data = {"thesis_title": thesis_title}
    if thesis_url:
        update_data["thesis_url"] = thesis_url

    rows_affected = (
        db.query(models.AcademicProgram)
        .filter(
            models.AcademicProgram.student_id == student_id,
            models.AcademicProgram.program == program,
        )
        .update(update_data)
    )

    db.commit()
    return rows_affected > 0


def get_students_by_program_and_status(
    db: Session, program: str, status: str
) -> list[models.Student]:
    """Obtener estudiantes por programa y estatus"""
    return (
        db.query(models.Student)
        .join(models.AcademicProgram)
        .filter(
            models.AcademicProgram.program == program,
            models.AcademicProgram.status == status,
        )
        .all()
    )


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
