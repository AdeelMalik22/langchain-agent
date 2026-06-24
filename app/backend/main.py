
from fastapi import FastAPI


from api.user.router import router as user_routers
from api.books.router import router as books_routers
from api.university.router import router as university_routers
from api.department.router import router as department_routers
app = FastAPI()
app.include_router(user_routers)
app.include_router(books_routers)
app.include_router(university_routers)
app.include_router(department_routers)