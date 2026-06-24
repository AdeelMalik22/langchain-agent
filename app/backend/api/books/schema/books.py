from pydantic import BaseModel


class Book(BaseModel):
    title: str
    author: str
    published_date: str | None = None

class GetAssignedBooks(BaseModel):
    title: str
    department : str

class GetAllBooks(BaseModel):
    book_id: str
    department_id : str | None = None