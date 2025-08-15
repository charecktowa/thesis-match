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


def create_fake_laboratory():
    """Ya que hay alumnos egresados y que no pertenecen a ningun laboratorio, se crea un laboratorio ficticio."""
    db = SessionLocal()
    try:
        fake_lab = models.Laboratory(id=999, name="Laboratorio Egresados")
        db.add(fake_lab)
        db.commit()
        print("Created fake laboratory: Laboratorio Egresados")
    except Exception as e:
        db.rollback()
        print(f"An error occurred while creating fake laboratory: {e}")
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


def get_all_student_profile_urls() -> list:
    """Obtiene todas las URLs de perfil de estudiantes existentes"""
    db = SessionLocal()
    try:
        students = db.query(models.Student).all()
        return [student.profile_url for student in students if student.profile_url]
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        db.close()


def save_academic_program_data(student_id: int, program_data: dict) -> None:
    """
    Guarda información de un programa académico para un estudiante

    Args:
        student_id: ID del estudiante
        program_data: Dict con keys: 'programa', 'status', 'tesis_titulo', 'tesis_url'
    """
    db = SessionLocal()

    try:
        # Verificar si el estudiante existe
        from app.db import crud

        student = crud.get_student_by_id(db, student_id)
        if not student:
            print(f"Student {student_id} not found")
            return

        # Verificar si ya existe este programa para el estudiante
        existing_program = crud.get_academic_program_by_student_and_program(
            db, student_id, program_data["programa"]
        )

        if existing_program:
            # Actualizar información existente usando query directa
            db.query(models.AcademicProgram).filter(
                models.AcademicProgram.student_id == student_id,
                models.AcademicProgram.program == program_data["programa"],
            ).update(
                {
                    "status": program_data["status"],
                    "thesis_title": program_data.get("tesis_titulo"),
                    "thesis_url": program_data.get("tesis_url"),
                }
            )
            db.commit()
            print(
                f"Updated {program_data['programa']} program for student {student_id}"
            )
        else:
            # Crear nuevo programa académico
            academic_program_model = models.AcademicProgram(
                student_id=student_id,
                program=program_data["programa"],
                status=program_data["status"],
                thesis_title=program_data.get("tesis_titulo"),
                thesis_url=program_data.get("tesis_url"),
            )

            db.add(academic_program_model)
            db.commit()
            print(
                f"Created {program_data['programa']} program for student {student_id}"
            )

    except Exception as e:
        db.rollback()
        print(f"Error saving academic program for student {student_id}: {e}")
    finally:
        db.close()


def save_multiple_academic_programs(student_id: int, programs_list: list) -> None:
    """
    Guarda múltiples programas académicos para un estudiante

    Args:
        student_id: ID del estudiante
        programs_list: Lista de diccionarios con información de programas
    """
    print(f"Saving {len(programs_list)} academic programs for student {student_id}")

    for program_data in programs_list:
        save_academic_program_data(student_id, program_data)


def get_academic_program_stats() -> None:
    """Mostrar estadísticas de programas académicos"""
    db = SessionLocal()

    try:
        total_programs = db.query(models.AcademicProgram).count()

        # Contar por programa
        mcc_count = (
            db.query(models.AcademicProgram)
            .filter(models.AcademicProgram.program == "MCC")
            .count()
        )
        mcic_count = (
            db.query(models.AcademicProgram)
            .filter(models.AcademicProgram.program == "MCIC")
            .count()
        )
        dcc_count = (
            db.query(models.AcademicProgram)
            .filter(models.AcademicProgram.program == "DCC")
            .count()
        )

        # Contar por status
        inscrito_count = (
            db.query(models.AcademicProgram)
            .filter(models.AcademicProgram.status == "inscrito")
            .count()
        )
        graduado_count = (
            db.query(models.AcademicProgram)
            .filter(models.AcademicProgram.status == "graduado")
            .count()
        )
        egresado_count = (
            db.query(models.AcademicProgram)
            .filter(models.AcademicProgram.status == "egresado")
            .count()
        )

        # Contar programas con tesis
        with_thesis = (
            db.query(models.AcademicProgram)
            .filter(models.AcademicProgram.thesis_title.isnot(None))
            .count()
        )

        print("\nAcademic Program Statistics:")
        print(f"   Total programs: {total_programs}")
        print("   By program:")
        print(f"     - MCC: {mcc_count}")
        print(f"     - MCIC: {mcic_count}")
        print(f"     - DCC: {dcc_count}")
        print("   By status:")
        print(f"     - Inscrito: {inscrito_count}")
        print(f"     - Graduado: {graduado_count}")
        print(f"     - Egresado: {egresado_count}")
        print(f"   With thesis: {with_thesis}")

    except Exception as e:
        print(f"Error getting academic program stats: {e}")
    finally:
        db.close()


def get_all_student_ids():
    """Obtiene todos los IDs de estudiantes existentes"""
    db = SessionLocal()
    try:
        student_ids = db.query(models.Student.id).all()
        return [student_id[0] for student_id in student_ids]
    except Exception as e:
        print(f"Error getting student IDs: {e}")
        return []
    finally:
        db.close()
