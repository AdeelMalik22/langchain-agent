from typing import List
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from api.books.schema.books import GetAllBooks
from api.department.schema.department import Department, GetDepart, GetDepartments
from api.utils.auth import get_current_user
from api.utils.db_collection import mongodb

router = APIRouter(

    prefix="/department",
    tags=["department"]
)


@router.post("/api/v1/create", response_model=Department)
async def create_department(department: Department,current_user:str = Depends(get_current_user)):
    dept = await mongodb["departments"].insert_one(department.dict())
    result = await mongodb["departments"].find_one({"_id": dept.inserted_id})
    return result

@router.post("/api/v1/assign-university/",response_model=GetDepart)
async def assign_department_to_university(request:GetDepartments,current_user:str = Depends(get_current_user)):
    """Assign department to university"""
    if not await mongodb["departments"].find_one({"_id": ObjectId(request.department_id)}):
        raise HTTPException(status_code=404, detail="department does not exist")

    await mongodb["departments"].update_one({"_id": ObjectId(request.department_id)},{"$set": {"university_id": request.university_id}})
    result = await mongodb["departments"].find_one({"_id": ObjectId(request.department_id)})
    return result

@router.get("/api/v1", response_model=List[Department])
async def get_departments(current_user:str = Depends(get_current_user)):
    response =  await mongodb["departments"].find().to_list(None)
    return response


@router.get("/get-assigned-books/{depart_id}", response_model=List[GetAllBooks])
async def get_department_assigned_books(depart_id: str,current_user:str = Depends(get_current_user)):
    """Get assigned books to specific department"""
    result = await mongodb["books"].find({"department_id":str(depart_id)}).to_list(None)
    return result