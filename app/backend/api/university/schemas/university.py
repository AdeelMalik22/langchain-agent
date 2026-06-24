from typing import Optional

from pydantic import BaseModel

class University(BaseModel):
    name:str

class GetDepartUni(BaseModel):
    department_id:str

class GetDepartUniResponse(University):
    department_id: Optional[str] = None