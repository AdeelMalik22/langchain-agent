from typing import Optional

from pydantic import BaseModel


class Department(BaseModel):
    name: str


class GetDepart(Department):
    university_id: str


class GetDepartments(BaseModel):
    department_id : str
    university_id: str | None = None
