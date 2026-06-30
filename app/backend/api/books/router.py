from typing import List
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from api.books.schema.books import Book, GetAllBooks, GetAssignedBooks
from api.utils.auth import get_current_user
from api.utils.db_collection import mongodb
from api.utils.redis_client import cache
router = APIRouter(
    prefix="/book",
    tags=["book"]
)




@router.post("/create")
async def create_book(
    book: Book):
    from api.utils.celery_client import create_book_task

    task = create_book_task.delay(
        book.dict()
    )

    return {
        "message":"Book creation queued",
        "task_id":task.id
    }


@router.post("/api/v1/assign-department",response_model=GetAssignedBooks)
async def assign_to_department(payload:GetAllBooks,current_user:str = Depends(get_current_user)):
    """Assign books to department"""
    if not await mongodb["books"].find_one({"_id": ObjectId(payload.book_id)}):
        raise HTTPException(status_code=404, detail="book does not exist")

    await mongodb["books"].update_one({"_id": ObjectId(payload.book_id)},{"$set": {"department_id": payload.department_id}})
    book = await mongodb["books"].find_one({"_id": ObjectId(payload.book_id)})
    department = await mongodb["departments"].find_one({"_id": ObjectId(payload.department_id)})

    result =  {
        "title": book.get("title"),
        "department": department.get("name")
    }
    return result

@router.get("/list",response_model=List[Book])
@cache(expire=12)
async def get_books():
    result = await mongodb["books"].find().to_list(None)
    for result_info in result:
        result_info['_id'] = str(result_info['_id'])

    return result



