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
        print(f"Laboratories count: {labs_count}")
        print(f"Professors count: {profs_count}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
