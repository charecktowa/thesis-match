from enum import Enum
from pydantic import BaseModel


class Program(str, Enum):
    MCC = "Maestría en Ciencias de la Computación"
    MCIC = "Maestría en Ciencias en Ingeniería de Cómputo"
    DCC = "Doctorado en Ciencias de la Computación"


# Laboratory
class LaboratoryCreate(BaseModel):
    id: int
    name: str


class LaboratoryRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class BasePerson(BaseModel):
    id: int
    name: str
    email: str | None = None
    profile_url: str | None = None


# Professor
class ProfessorCreate(BasePerson):
    laboratory_id: int | None = None


class ProfessorRead(BasePerson):
    laboratory_id: int

    class Config:
        from_attributes = True


# Student
class StudentCreate(BasePerson):
    pass  # Solo necesita los campos de BasePerson


class StudentRead(BasePerson):
    laboratories: list[LaboratoryRead] = []

    class Config:
        from_attributes = True


# AcademicProgram
class AcademicProgramCreate(BaseModel):
    student_id: int
    program: str  # MCC, MCIC, DCC
    status: str  # inscrito, graduado, egresado
    thesis_title: str | None = None
    thesis_url: str | None = None


class AcademicProgramRead(BaseModel):
    id: int
    student_id: int
    program: str
    status: str
    thesis_title: str | None = None
    thesis_url: str | None = None

    class Config:
        from_attributes = True


# ResearchProduct
class ResearchProductCreate(BaseModel):
    professor_id: int
    title: str
    site: str  # Descripción/Revista donde se publicó
    year: int


class ResearchProductRead(BaseModel):
    id: int
    professor_id: int
    title: str
    site: str
    year: int

    class Config:
        from_attributes = True


# Para asociaciones Student-Laboratory
class StudentLaboratoryAssociation(BaseModel):
    student_id: int
    laboratory_id: int


# Thesis
class ThesisCreate(BaseModel):
    id: int
    title: str
    student_id: int
    advisor1_id: int
    advisor2_id: int | None = None


class ThesisRead(BaseModel):
    id: int
    title: str
    student_id: int
    advisor1_id: int
    advisor2_id: int | None = None

    class Config:
        from_attributes = True


# Esquemas para respuestas complejas de professor endpoints
class ProfessorWithLaboratory(BaseModel):
    id: int
    name: str
    email: str | None = None
    profile_url: str | None = None
    laboratory_id: int
    laboratory_name: str


class ProfessorResearch(BaseModel):
    id: int
    name: str
    email: str | None = None
    profile_url: str | None = None
    research_products: list[ResearchProductRead] = []


class ProfessorTheses(BaseModel):
    id: int
    name: str
    email: str | None = None
    profile_url: str | None = None
    advised_theses: list[ThesisRead] = []


# Esquemas para respuestas complejas de student endpoints
class StudentWithAcademicInfo(BaseModel):
    id: int
    name: str
    email: str | None = None
    profile_url: str | None = None
    program: str
    status: str
    thesis_title: str | None = None
    thesis_url: str | None = None


class StudentWithLaboratories(BaseModel):
    id: int
    name: str
    email: str | None = None
    profile_url: str | None = None
    laboratories: list[LaboratoryRead] = []


class StudentWithThesis(BaseModel):
    id: int
    name: str
    email: str | None = None
    profile_url: str | None = None
    thesis: ThesisRead | None = None
    academic_programs: list[AcademicProgramRead] = []


# Esquemas para sistema de recomendaciones
class RecommendationRequest(BaseModel):
    query: str
    k: int = 10
    include_theses: bool = True
    include_research_products: bool = True


class ThesisRecommendation(BaseModel):
    id: int
    title: str
    student_id: int
    student_name: str
    advisor1_name: str
    advisor2_name: str | None = None
    similarity_score: float


class ResearchProductRecommendation(BaseModel):
    id: int
    title: str
    site: str
    year: int
    professor_id: int
    professor_name: str
    laboratory_name: str
    similarity_score: float


class RecommendationResponse(BaseModel):
    query: str
    theses: list[ThesisRecommendation] = []
    research_products: list[ResearchProductRecommendation] = []
    total_results: int


class SimilaritySearchRequest(BaseModel):
    thesis_id: int | None = None
    research_product_id: int | None = None
    k: int = 10
    search_type: str = "both"  # "theses", "research_products", "both"


class ClusterAnalysisRequest(BaseModel):
    entity_type: str  # "theses" or "research_products"
    n_clusters: int = 5
    min_year: int | None = None
    max_year: int | None = None


class ClusterResult(BaseModel):
    cluster_id: int
    items: list[dict]  # Contains either theses or research products
    cluster_center: list[float]
    cluster_size: int


class ClusterAnalysisResponse(BaseModel):
    entity_type: str
    clusters: list[ClusterResult]
    total_items: int
