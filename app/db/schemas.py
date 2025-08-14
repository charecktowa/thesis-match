from pydantic import BaseModel


# Laboratory
class LaboratoryCreate(BaseModel):
    id: int
    name: str


class LaboratoryRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# Professor
class ProfessorCreate(BaseModel):
    id: int
    name: str
    email: str | None
    profile_url: str


class ProfessorRead(BaseModel):
    id: int
    name: str
    email: str | None
    profile_url: str
    laboratory_id: int

    class Config:
        from_attributes = True
