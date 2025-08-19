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
        students = (
            db.query(models.Student)
            .filter(
                models.Student.profile_url.isnot(None), models.Student.profile_url != ""
            )
            .all()
        )
        return [student.profile_url for student in students]
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


def get_all_professors_ids():
    """Obtiene todos los IDs de profesores existentes"""
    db = SessionLocal()
    try:
        professor_ids = db.query(models.Professor.id).all()
        return [professor_id[0] for professor_id in professor_ids]
    except Exception as e:
        print(f"Error getting professor IDs: {e}")
        return []
    finally:
        db.close()


def save_research_product_data(professor_id: int, product_data: dict) -> None:
    """
    Guarda información de un producto de investigación para un profesor

    Args:
        professor_id: ID del profesor
        product_data: Dict con keys: 'title', 'site', 'year'
    """
    db = SessionLocal()

    try:
        # Verificar si el profesor existe
        professor_exists = (
            db.query(models.Professor)
            .filter(models.Professor.id == professor_id)
            .first()
        )

        if not professor_exists:
            print(f"Professor {professor_id} not found")
            return

        # Verificar si ya existe este producto para el profesor
        existing_product = crud.get_research_product_by_title_and_professor(
            db, professor_id, product_data["title"]
        )

        if existing_product:
            # Actualizar información existente
            success = crud.update_research_product(
                db,
                professor_id,
                product_data["title"],
                product_data.get("site"),
                product_data.get("year"),
            )
            if success:
                print(
                    f"Updated research product '{product_data['title']}' for professor {professor_id}"
                )
        else:
            # Crear nuevo producto de investigación
            research_product_model = models.ResearchProduct(
                professor_id=professor_id,
                title=product_data["title"],
                site=product_data["site"],
                year=product_data["year"],
            )

            db.add(research_product_model)
            db.commit()
            print(
                f"Created research product '{product_data['title']}' for professor {professor_id}"
            )

    except Exception as e:
        db.rollback()
        print(f"Error saving research product for professor {professor_id}: {e}")
    finally:
        db.close()


def save_multiple_research_products(professor_id: int, products_list: list) -> None:
    """
    Guarda múltiples productos de investigación para un profesor

    Args:
        professor_id: ID del profesor
        products_list: Lista de diccionarios con información de productos
    """
    print(f"Saving {len(products_list)} research products for professor {professor_id}")

    for product_data in products_list:
        save_research_product_data(professor_id, product_data)


def get_research_product_stats() -> None:
    """Mostrar estadísticas de productos de investigación"""
    db = SessionLocal()

    try:
        total_products = db.query(models.ResearchProduct).count()

        # Contar productos por años recientes
        from sqlalchemy import func

        recent_products = (
            db.query(models.ResearchProduct.year, func.count(models.ResearchProduct.id))
            .filter(models.ResearchProduct.year >= 2020)
            .group_by(models.ResearchProduct.year)
            .order_by(models.ResearchProduct.year.desc())
            .all()
        )

        # Contar profesores con productos
        professors_with_products = (
            db.query(models.ResearchProduct.professor_id).distinct().count()
        )

        print("\nResearch Product Statistics:")
        print(f"   Total products: {total_products}")
        print(f"   Professors with products: {professors_with_products}")
        print("   Recent years:")
        for year, count in recent_products:
            print(f"     - {year}: {count} products")

    except Exception as e:
        print(f"Error getting research product stats: {e}")
    finally:
        db.close()


def save_thesis_data(thesis_data: dict) -> None:
    """
    Guarda información de una tesis

    Args:
        thesis_data: Dict con keys: 'id', 'title', 'student_id', 'advisor1_id', 'advisor2_id'
    """
    db = SessionLocal()

    try:
        # Verificar si la tesis ya existe
        existing_thesis = crud.get_thesis_by_id(db, thesis_data["id"])

        if existing_thesis:
            print(f"Thesis {thesis_data['id']} already exists")
            return

        # Verificar que el estudiante existe
        student_exists = crud.get_student_by_id(db, thesis_data["student_id"])
        if not student_exists:
            print(f"Student {thesis_data['student_id']} not found")
            return

        # Verificar que el asesor principal existe
        advisor1_exists = crud.get_professor_by_id(db, thesis_data["advisor1_id"])
        if not advisor1_exists:
            print(f"Advisor1 {thesis_data['advisor1_id']} not found")
            return

        # Verificar que el asesor secundario existe (si se proporciona)
        if thesis_data.get("advisor2_id"):
            advisor2_exists = crud.get_professor_by_id(db, thesis_data["advisor2_id"])
            if not advisor2_exists:
                print(f"Advisor2 {thesis_data['advisor2_id']} not found")
                return

        # Crear nueva tesis
        thesis_create = schemas.ThesisCreate(**thesis_data)
        crud.create_thesis(db, thesis_create)

        print(f"Created thesis '{thesis_data['title']}' (ID: {thesis_data['id']})")

    except Exception as e:
        db.rollback()
        print(f"Error saving thesis {thesis_data.get('id', 'unknown')}: {e}")
    finally:
        db.close()


def save_multiple_theses(theses_list: list) -> None:
    """
    Guarda múltiples tesis consolidando asesores cuando es necesario

    Args:
        theses_list: Lista de diccionarios con información de tesis
    """
    print(f"Processing {len(theses_list)} theses for consolidation...")

    # Diccionario para consolidar tesis por ID
    consolidated_theses = {}

    for thesis_data in theses_list:
        thesis_id = thesis_data["id"]

        if thesis_id in consolidated_theses:
            # Tesis ya existe, consolidar asesores
            existing_thesis = consolidated_theses[thesis_id]

            # Si esta entrada tiene advisor1_id y la existente no
            if thesis_data.get("advisor1_id") and not existing_thesis.get(
                "advisor1_id"
            ):
                existing_thesis["advisor1_id"] = thesis_data["advisor1_id"]

            # Si esta entrada tiene advisor2_id y la existente no
            if thesis_data.get("advisor2_id") and not existing_thesis.get(
                "advisor2_id"
            ):
                existing_thesis["advisor2_id"] = thesis_data["advisor2_id"]

        else:
            # Nueva tesis
            consolidated_theses[thesis_id] = thesis_data.copy()

    # Asegurar que todas las tesis tengan al menos advisor1_id
    valid_theses = []
    for thesis_data in consolidated_theses.values():
        if not thesis_data.get("advisor1_id") and thesis_data.get("advisor2_id"):
            # Promover advisor2 a advisor1
            thesis_data["advisor1_id"] = thesis_data["advisor2_id"]
            thesis_data["advisor2_id"] = None

        if thesis_data.get("advisor1_id"):  # Solo guardar si tiene al menos un asesor
            valid_theses.append(thesis_data)

    print(f"Consolidated to {len(valid_theses)} valid theses")

    # Guardar las tesis consolidadas
    for thesis_data in valid_theses:
        save_thesis_data(thesis_data)


def get_thesis_stats() -> None:
    """Mostrar estadísticas de tesis"""
    db = SessionLocal()

    try:
        total_theses = db.query(models.Thesis).count()

        # Contar tesis con dos asesores
        theses_with_two_advisors = (
            db.query(models.Thesis)
            .filter(models.Thesis.advisor2_id.isnot(None))
            .count()
        )

        # Contar por asesor principal (top 5)
        from sqlalchemy import func

        top_advisors = (
            db.query(
                models.Professor.name,
                func.count(models.Thesis.id).label("thesis_count"),
            )
            .join(models.Thesis, models.Professor.id == models.Thesis.advisor1_id)
            .group_by(models.Professor.id, models.Professor.name)
            .order_by(func.count(models.Thesis.id).desc())
            .limit(5)
            .all()
        )

        print("\nThesis Statistics:")
        print(f"   Total theses: {total_theses}")
        print(f"   Theses with two advisors: {theses_with_two_advisors}")
        print("   Top advisors (as primary):")
        for advisor_name, count in top_advisors:
            print(f"     - {advisor_name}: {count} theses")

    except Exception as e:
        print(f"Error getting thesis stats: {e}")
    finally:
        db.close()
