from typing import List
from fastapi import APIRouter, Depends
from api.department.router import GetDepartments
from api.university.schemas.university import University
from api.utils.auth import get_current_user
from api.utils.db_collection import mongodb

router = APIRouter(
    prefix="/university",
    tags=["university"]
)


@router.post("/api/v1/create", response_model=University)
async def create_university(university: University,current_user:str = Depends(get_current_user)):
    uni = await mongodb["universities"].insert_one(university.dict())
    result = await mongodb["universities"].find_one({"_id": uni.inserted_id})
    return result

@router.get("/api/v1/list", response_model=List[University])
async def get_universities(current_user:str = Depends(get_current_user)):
    universities = await mongodb["universities"].find().to_list(None)
    return universities


@router.get("/api/v1/get-assigned-depart/{uni_id}", response_model=List[GetDepartments])
async def get_assigned_depart(uni_id:str,current_user:str = Depends(get_current_user)):
    """Get assigned departments"""
    universities = await mongodb["departments"].find().to_list(None)
    return universities

