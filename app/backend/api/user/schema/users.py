from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    username: str
    password: str
    age: int
    email: str
    class Config:
        from_attributes = True

class CreateUserRole(BaseModel):
    user_id: str
    role: str
    class Config:
        from_attributes = True


class GetUserRole(User):
    university_id: str | None = None
    department_id: str | None = None
    role: str | None = None


class AssignUserUni(User):
    university_id: str
    department_id: str

class GetAssignedUser(BaseModel):
    user_id : str
    university_id: str | None = None
    department_id: str | None = None


class Book(BaseModel):
    title: str

class GetUserDetails(BaseModel):
    username: str
    university :str
    department : str
    books : list[Book]


class LoginRequest(BaseModel):
    username: str
    password: str
