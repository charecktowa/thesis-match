from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import crud, schemas
from app.db.database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "/professors/",
    response_model=list[schemas.ProfessorWithLaboratory],
    tags=["professors"],
)
async def read_professors(db: Session = Depends(get_db)):
    """Obtiene todos los profesores con información de su laboratorio"""
    professors = crud.get_professors_with_laboratory(db)

    # Convertir las filas de la consulta a esquemas
    result = []
    for prof in professors:
        result.append(
            schemas.ProfessorWithLaboratory(
                id=prof[0],  # prof.id
                name=prof[1],  # prof.name
                email=prof[2],  # prof.email
                profile_url=prof[3],  # prof.profile_url
                laboratory_id=prof[4],  # prof.laboratory_id
                laboratory_name=prof[5],  # prof.laboratory_name
            )
        )

    return result


@router.get(
    "/professors/{professor_id}",
    response_model=schemas.ProfessorWithLaboratory,
    tags=["professors"],
)
async def read_professor(professor_id: int, db: Session = Depends(get_db)):
    """Obtiene un profesor específico con información de su laboratorio"""
    professor = crud.get_professor_with_laboratory(db, professor_id)

    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found")

    return schemas.ProfessorWithLaboratory(
        id=professor[0],  # professor.id
        name=professor[1],  # professor.name
        email=professor[2],  # professor.email
        profile_url=professor[3],  # professor.profile_url
        laboratory_id=professor[4],  # professor.laboratory_id
        laboratory_name=professor[5],  # professor.laboratory_name
    )


@router.get(
    "/professors/{professor_id}/research",
    response_model=schemas.ProfessorResearch,
    tags=["professors"],
)
async def read_professor_research(professor_id: int, db: Session = Depends(get_db)):
    """Obtiene la información de investigación de un profesor específico"""
    professor = crud.get_professor_with_research(db, professor_id)

    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found")

    # Convertir los productos de investigación manualmente
    research_products = []
    for product in professor.research_products:
        research_products.append(
            schemas.ResearchProductRead(
                id=product.id,
                professor_id=product.professor_id,
                title=product.title,
                site=product.site,
                year=product.year,
            )
        )

    return schemas.ProfessorResearch(
        id=professor.id,
        name=professor.name,
        email=professor.email,
        profile_url=professor.profile_url,
        research_products=research_products,
    )


@router.get(
    "/professors/{professor_id}/thesis",
    response_model=schemas.ProfessorTheses,
    tags=["professors"],
)
async def read_professor_theses(professor_id: int, db: Session = Depends(get_db)):
    """Obtiene las tesis asesoradas por un profesor específico"""
    professor = crud.get_professor_with_theses(db, professor_id)

    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found")

    # Convertir las tesis asesoradas manualmente
    advised_theses = []

    # Tesis como asesor principal
    for thesis in professor.advised_theses_primary:
        advised_theses.append(
            schemas.ThesisRead(
                id=thesis.id,
                title=thesis.title,
                student_id=thesis.student_id,
                advisor1_id=thesis.advisor1_id,
                advisor2_id=thesis.advisor2_id,
            )
        )

    # Tesis como asesor secundario
    for thesis in professor.advised_theses_secondary:
        advised_theses.append(
            schemas.ThesisRead(
                id=thesis.id,
                title=thesis.title,
                student_id=thesis.student_id,
                advisor1_id=thesis.advisor1_id,
                advisor2_id=thesis.advisor2_id,
            )
        )

    return schemas.ProfessorTheses(
        id=professor.id,
        name=professor.name,
        email=professor.email,
        profile_url=professor.profile_url,
        advised_theses=advised_theses,
    )
