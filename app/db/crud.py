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
