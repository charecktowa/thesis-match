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
    "/students/",
    response_model=list[schemas.StudentWithAcademicInfo],
    tags=["students"],
)
async def read_students(db: Session = Depends(get_db)):
    """Obtiene todos los estudiantes con información académica y de tesis"""
    students = crud.get_students_with_academic_info(db)

    # Convertir las filas de la consulta a esquemas
    result = []
    for student in students:
        result.append(
            schemas.StudentWithAcademicInfo(
                id=student[0],  # student.id
                name=student[1],  # student.name
                email=student[2],  # student.email
                profile_url=student[3],  # student.profile_url
                program=student[4],  # academic_program.program
                status=student[5],  # academic_program.status
                thesis_title=student[6],  # academic_program.thesis_title
                thesis_url=student[7],  # academic_program.thesis_url
            )
        )

    return result


@router.get(
    "/students/{student_id}",
    response_model=schemas.StudentWithAcademicInfo,
    tags=["students"],
)
async def read_student(student_id: int, db: Session = Depends(get_db)):
    """Obtiene un estudiante específico con información académica y de tesis"""
    student = crud.get_student_with_academic_info(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    return schemas.StudentWithAcademicInfo(
        id=student[0],  # student.id
        name=student[1],  # student.name
        email=student[2],  # student.email
        profile_url=student[3],  # student.profile_url
        program=student[4],  # academic_program.program
        status=student[5],  # academic_program.status
        thesis_title=student[6],  # academic_program.thesis_title
        thesis_url=student[7],  # academic_program.thesis_url
    )


@router.get(
    "/students/{student_id}/laboratories",
    response_model=schemas.StudentWithLaboratories,
    tags=["students"],
)
async def read_student_laboratories(student_id: int, db: Session = Depends(get_db)):
    """Obtiene los laboratorios asociados a un estudiante específico"""
    student = crud.get_student_with_laboratories(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    # Convertir los laboratorios
    laboratories = []
    for lab in student.laboratories:
        laboratories.append(schemas.LaboratoryRead(id=lab.id, name=lab.name))

    return schemas.StudentWithLaboratories(
        id=student.id,
        name=student.name,
        email=student.email,
        profile_url=student.profile_url,
        laboratories=laboratories,
    )


@router.get(
    "/students/{student_id}/thesis",
    response_model=schemas.StudentWithThesis,
    tags=["students"],
)
async def read_student_thesis(student_id: int, db: Session = Depends(get_db)):
    """Obtiene la tesis y programas académicos de un estudiante específico"""
    student = crud.get_student_with_thesis(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    # Convertir la tesis si existe
    thesis = None
    if student.thesis:
        thesis = schemas.ThesisRead(
            id=student.thesis.id,
            title=student.thesis.title,
            student_id=student.thesis.student_id,
            advisor1_id=student.thesis.advisor1_id,
            advisor2_id=student.thesis.advisor2_id,
        )

    # Convertir los programas académicos
    academic_programs = []
    for program in student.academic_programs:
        academic_programs.append(
            schemas.AcademicProgramRead(
                id=program.id,
                student_id=program.student_id,
                program=program.program,
                status=program.status,
                thesis_title=program.thesis_title,
                thesis_url=program.thesis_url,
            )
        )

    return schemas.StudentWithThesis(
        id=student.id,
        name=student.name,
        email=student.email,
        profile_url=student.profile_url,
        thesis=thesis,
        academic_programs=academic_programs,
    )


@router.get(
    "/students/program/{program}",
    response_model=List[schemas.StudentWithAcademicInfo],
    tags=["students"],
)
async def read_students_by_program(program: str, db: Session = Depends(get_db)):
    """Obtiene estudiantes por programa académico específico"""
    students = crud.get_students_by_program(db, program)

    # Convertir las filas de la consulta a esquemas
    result = []
    for student in students:
        result.append(
            schemas.StudentWithAcademicInfo(
                id=student[0],  # student.id
                name=student[1],  # student.name
                email=student[2],  # student.email
                profile_url=student[3],  # student.profile_url
                program=student[4],  # academic_program.program
                status=student[5],  # academic_program.status
                thesis_title=student[6],  # academic_program.thesis_title
                thesis_url=student[7],  # academic_program.thesis_url
            )
        )

    return result


@router.get(
    "/students/status/{status}",
    response_model=list[schemas.StudentWithAcademicInfo],
    tags=["students"],
)
async def read_students_by_status(status: str, db: Session = Depends(get_db)):
    """Obtiene estudiantes por estatus académico específico"""
    students = crud.get_students_by_status(db, status)

    # Convertir las filas de la consulta a esquemas
    result = []
    for student in students:
        result.append(
            schemas.StudentWithAcademicInfo(
                id=student[0],  # student.id
                name=student[1],  # student.name
                email=student[2],  # student.email
                profile_url=student[3],  # student.profile_url
                program=student[4],  # academic_program.program
                status=student[5],  # academic_program.status
                thesis_title=student[6],  # academic_program.thesis_title
                thesis_url=student[7],  # academic_program.thesis_url
            )
        )

    return result
