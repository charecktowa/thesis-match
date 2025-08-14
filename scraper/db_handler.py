# is this really necessary? idk
import os
import sys

# Asegurar que el root del proyecto esté en sys.path para poder importar app.*
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

#

from app.db.database import SessionLocal, engine
from app.db import models, schemas, crud


# TODO: Add logging


def init_db():
    models.Base.metadata.create_all(bind=engine)


def save_laboratory_data(lab_name: str, lab_id: int, professors: list) -> None:
    db = SessionLocal()

    try:
        # Verify if it exists
        existing_lab = crud.get_laboratory_by_id(db, lab_id)

        if not existing_lab:
            # Create new laboratory
            lab_schema = schemas.LaboratoryCreate(name=lab_name, id=lab_id)
            lab_model = models.Laboratory(id=lab_schema.id, name=lab_schema.name)
            db.add(lab_model)
            db.commit()
        else:
            print("Laboratory already exists in the database.")

        for professor in professors:
            if not professor.get("id"):
                print(
                    f"Skipping professor without ID: {professor.get('name', 'Unknown')}"
                )
                continue

            # Verify if it exists
            existing_prof = (
                db.query(models.Professor)
                .filter(models.Professor.id == professor["id"])
                .first()
            )

            if not existing_prof:
                # Create new professor - mapear campos directamente
                prof_model = models.Professor(
                    id=professor["id"],
                    name=professor["name"],
                    email=professor.get("email"),
                    profile_url=professor.get("profile_url", ""),
                    laboratory_id=professor.get("laboratory_id", lab_id),
                )
                db.add(prof_model)
                print(f"Added professor: {professor['name']}")
            else:
                print(f"Professor already exists in the database: {existing_prof.name}")

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.close()


def get_lab_stats():
    db = SessionLocal()

    try:
        labs_count = db.query(models.Laboratory).count()
        profs_count = db.query(models.Professor).count()
        students_count = db.query(models.Student).count()
        print(f"Laboratories count: {labs_count}")
        print(f"Professors count: {profs_count}")
        print(f"Students count: {students_count}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()


def get_all_labs_id():
    """Obtiene todos los IDs de laboratorios existentes"""
    db = SessionLocal()
    try:
        labs = db.query(models.Laboratory.id).all()
        return [lab.id for lab in labs]
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        db.close()


def save_student_data(students: list, lab_id: int) -> None:
    """
    Guarda estudiantes y sus asociaciones con laboratorios

    Args:
        students: Lista de diccionarios con datos de estudiantes
        lab_id: ID del laboratorio
    """
    db = SessionLocal()

    try:
        for student_data in students:
            if not student_data.get("id"):
                print(
                    f"Skipping student without ID: {student_data.get('nombre', 'Unknown')}"
                )
                continue

            # Verificar si el estudiante ya existe
            existing_student = (
                db.query(models.Student)
                .filter(models.Student.id == student_data["id"])
                .first()
            )

            if not existing_student:
                # Convertir formato para que coincida con el schema
                student_formatted = {
                    "id": student_data["id"],
                    "name": student_data["nombre"],  # cambiar 'nombre' por 'name'
                    "email": student_data.get("correo"),  # cambiar 'correo' por 'email'
                    "profile_url": student_data.get(
                        "pagina", ""
                    ),  # cambiar 'pagina' por 'profile_url'
                }

                # Crear nuevo estudiante
                student_model = models.Student(
                    id=student_formatted["id"],
                    name=student_formatted["name"],
                    email=student_formatted.get("email"),
                    profile_url=student_formatted.get("profile_url", ""),
                )
                db.add(student_model)
                db.commit()
                db.refresh(student_model)
                print(f"Added student: {student_formatted['name']}")
                existing_student = student_model
            else:
                print(f"Student already exists: {existing_student.name}")

            # Agregar asociación con laboratorio usando CRUD
            from app.db import crud

            success = crud.add_student_to_laboratory(db, student_data["id"], lab_id)

            if success:
                print(
                    f"Associated student {existing_student.name} with laboratory {lab_id}"
                )

    except Exception as e:
        db.rollback()
        print(f"An error occurred saving students: {e}")
    finally:
        db.close()
