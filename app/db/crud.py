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


def get_professor_by_id(db: Session, professor_id: int) -> models.Professor | None:
    return (
        db.query(models.Professor).filter(models.Professor.id == professor_id).first()
    )


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


# ResearchProduct CRUD operations
def create_research_product(
    db: Session, research_product: schemas.ResearchProductCreate
) -> models.ResearchProduct:
    """Crear un producto de investigación para un profesor"""
    db_research_product = models.ResearchProduct(
        professor_id=research_product.professor_id,
        title=research_product.title,
        site=research_product.site,
        year=research_product.year,
    )
    db.add(db_research_product)
    db.commit()
    db.refresh(db_research_product)
    return db_research_product


def get_research_products_by_professor(
    db: Session, professor_id: int
) -> list[models.ResearchProduct]:
    """Obtener todos los productos de investigación de un profesor"""
    return (
        db.query(models.ResearchProduct)
        .filter(models.ResearchProduct.professor_id == professor_id)
        .all()
    )


def get_research_product_by_title_and_professor(
    db: Session, professor_id: int, title: str
) -> models.ResearchProduct | None:
    """Obtener un producto de investigación específico por título y profesor"""
    return (
        db.query(models.ResearchProduct)
        .filter(
            models.ResearchProduct.professor_id == professor_id,
            models.ResearchProduct.title == title,
        )
        .first()
    )


def update_research_product(
    db: Session,
    professor_id: int,
    title: str,
    site: str | None = None,
    year: int | None = None,
) -> bool:
    """Actualizar información de un producto de investigación"""
    # Para evitar problemas de tipado, actualizamos directamente con query
    if site and year:
        rows_affected = (
            db.query(models.ResearchProduct)
            .filter(
                models.ResearchProduct.professor_id == professor_id,
                models.ResearchProduct.title == title,
            )
            .update({"site": site, "year": year})
        )
    elif site:
        rows_affected = (
            db.query(models.ResearchProduct)
            .filter(
                models.ResearchProduct.professor_id == professor_id,
                models.ResearchProduct.title == title,
            )
            .update({"site": site})
        )
    elif year:
        rows_affected = (
            db.query(models.ResearchProduct)
            .filter(
                models.ResearchProduct.professor_id == professor_id,
                models.ResearchProduct.title == title,
            )
            .update({"year": year})
        )
    else:
        return False

    db.commit()
    return rows_affected > 0


def get_research_products_by_year_range(
    db: Session, start_year: int, end_year: int
) -> list[models.ResearchProduct]:
    """Obtener productos de investigación en un rango de años"""
    return (
        db.query(models.ResearchProduct)
        .filter(
            models.ResearchProduct.year >= start_year,
            models.ResearchProduct.year <= end_year,
        )
        .all()
    )


# Thesis CRUD operations
def create_thesis(db: Session, thesis: schemas.ThesisCreate) -> models.Thesis:
    db_thesis = models.Thesis(
        id=thesis.id,
        title=thesis.title,
        student_id=thesis.student_id,
        advisor1_id=thesis.advisor1_id,
        advisor2_id=thesis.advisor2_id,
    )
    db.add(db_thesis)
    db.commit()
    db.refresh(db_thesis)
    return db_thesis


def get_thesis_by_id(db: Session, thesis_id: int) -> models.Thesis | None:
    return db.query(models.Thesis).filter(models.Thesis.id == thesis_id).first()


def get_thesis_by_student_id(db: Session, student_id: int) -> models.Thesis | None:
    return (
        db.query(models.Thesis).filter(models.Thesis.student_id == student_id).first()
    )


def get_theses_by_advisor(db: Session, professor_id: int) -> list[models.Thesis]:
    """Obtiene todas las tesis donde un profesor es asesor (principal o secundario)"""
    return (
        db.query(models.Thesis)
        .filter(
            (models.Thesis.advisor1_id == professor_id)
            | (models.Thesis.advisor2_id == professor_id)
        )
        .all()
    )


def update_thesis_advisor2(db: Session, thesis_id: int, advisor2_id: int) -> bool:
    """Actualizar el asesor secundario de una tesis"""
    rows_affected = (
        db.query(models.Thesis)
        .filter(models.Thesis.id == thesis_id)
        .update({"advisor2_id": advisor2_id})
    )
    db.commit()
    return rows_affected > 0


# Professor additional CRUD operations for complex queries
def get_professors_with_laboratory(db: Session):
    """Obtiene todos los profesores con información de su laboratorio"""
    return (
        db.query(
            models.Professor.id,
            models.Professor.name,
            models.Professor.email,
            models.Professor.profile_url,
            models.Professor.laboratory_id,
            models.Laboratory.name.label("laboratory_name"),
        )
        .join(models.Laboratory)
        .all()
    )


def get_professor_with_laboratory(db: Session, professor_id: int):
    """Obtiene un profesor específico con información de su laboratorio"""
    result = (
        db.query(
            models.Professor.id,
            models.Professor.name,
            models.Professor.email,
            models.Professor.profile_url,
            models.Professor.laboratory_id,
            models.Laboratory.name.label("laboratory_name"),
        )
        .join(models.Laboratory)
        .filter(models.Professor.id == professor_id)
        .first()
    )
    return result


def get_professor_with_research(
    db: Session, professor_id: int
) -> models.Professor | None:
    """Obtiene un profesor con todos sus productos de investigación"""
    return (
        db.query(models.Professor).filter(models.Professor.id == professor_id).first()
    )


def get_professor_with_theses(
    db: Session, professor_id: int
) -> models.Professor | None:
    """Obtiene un profesor con todas las tesis que ha asesorado"""
    return (
        db.query(models.Professor).filter(models.Professor.id == professor_id).first()
    )


# Student additional CRUD operations for complex queries
def get_students_with_academic_info(db: Session):
    """Obtiene todos los estudiantes con información académica y de tesis"""
    return (
        db.query(
            models.Student.id,
            models.Student.name,
            models.Student.email,
            models.Student.profile_url,
            models.AcademicProgram.program,
            models.AcademicProgram.status,
            models.AcademicProgram.thesis_title,
            models.AcademicProgram.thesis_url,
        )
        .join(models.AcademicProgram)
        .join(models.Thesis)
        .all()
    )


def get_student_with_academic_info(db: Session, student_id: int):
    """Obtiene un estudiante específico con información académica y de tesis"""
    return (
        db.query(
            models.Student.id,
            models.Student.name,
            models.Student.email,
            models.Student.profile_url,
            models.AcademicProgram.program,
            models.AcademicProgram.status,
            models.AcademicProgram.thesis_title,
            models.AcademicProgram.thesis_url,
        )
        .join(models.AcademicProgram)
        .join(models.Thesis)
        .filter(models.Student.id == student_id)
        .first()
    )


def get_student_with_laboratories(
    db: Session, student_id: int
) -> models.Student | None:
    """Obtiene un estudiante con todos sus laboratorios"""
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_student_with_thesis(db: Session, student_id: int) -> models.Student | None:
    """Obtiene un estudiante con su tesis y programas académicos"""
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_students_by_program(db: Session, program: str):
    """Obtiene estudiantes por programa académico"""
    return (
        db.query(
            models.Student.id,
            models.Student.name,
            models.Student.email,
            models.Student.profile_url,
            models.AcademicProgram.program,
            models.AcademicProgram.status,
            models.AcademicProgram.thesis_title,
            models.AcademicProgram.thesis_url,
        )
        .join(models.AcademicProgram)
        .filter(models.AcademicProgram.program == program)
        .all()
    )


def get_students_by_status(db: Session, status: str):
    """Obtiene estudiantes por estatus académico"""
    return (
        db.query(
            models.Student.id,
            models.Student.name,
            models.Student.email,
            models.Student.profile_url,
            models.AcademicProgram.program,
            models.AcademicProgram.status,
            models.AcademicProgram.thesis_title,
            models.AcademicProgram.thesis_url,
        )
        .join(models.AcademicProgram)
        .filter(models.AcademicProgram.status == status)
        .all()
    )
