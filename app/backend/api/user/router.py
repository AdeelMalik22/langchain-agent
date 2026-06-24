from typing import List
from bson import ObjectId
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from api.user.schema.users import User, GetUserRole, GetAssignedUser, GetUserDetails, CreateUserRole, \
    AssignUserUni, LoginRequest
from fastapi import APIRouter, HTTPException, Depends

from api.utils.auth import authenticate_user, get_current_user
from api.utils.db_collection import mongodb
from api.utils.hash_password import  create_access_token, get_password_hash
from api.utils.kafka_producer import send_kafka_log

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@router.post("/api/v1/login")
async def login(login_data: LoginRequest):
    """Generate Access Token"""
    print(login_data)
    user = await authenticate_user(login_data.username, login_data.password)
    if not user:
        send_kafka_log("login failed", {"username": login_data.username})

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    send_kafka_log("user login", {"username": login_data.username})


    token_data = {"sub": user["username"]}
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/api/v1/create-user", response_model=User)
async def create_user(user:User , current_user:str = Depends(get_current_user)):
    """Create new user with a check to see if the user is already registered"""
    existing_user = await mongodb["users"].find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username taken")
    existing_user_email = await mongodb["users"].find_one({"email":user.email})
    if existing_user_email:
        raise HTTPException(status_code=400, detail="Email taken")

    # Hashing password
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password

    users = await mongodb["users"].insert_one(user_dict)
    result = await mongodb["users"].find_one({"_id": users.inserted_id})
    return result

@router.post("/api/v1/create-user-role/", response_model=GetUserRole)
async def create_user_role(payload:CreateUserRole,current_user:str= Depends(get_current_user)):
    """Assign Role to a user"""
    if not await mongodb["users"].find_one({"_id":ObjectId(payload.user_id)}):
        raise HTTPException(status_code=404, detail="User does not exist")

    await mongodb["users"].update_one({"_id":ObjectId(payload.user_id)},{"$set": {"role": payload.role.lower()}})

    updated_user = await mongodb["users"].find_one({"_id":ObjectId(payload.user_id)})
    return updated_user

@router.get("/api/v1/get-users-wrt-roles", response_model=GetUserRole)
async def get_users(role: str , current_user:str= Depends(get_current_user)):
    """Get users with specific role"""
    user =  await mongodb["users"].find_one({"role" : role.lower()})
    return user

@router.get("/api/v1/get-all-users", response_model=List[GetUserRole])
async def get_users( current_user:str= Depends(get_current_user)):
    user =  await mongodb["users"].find().to_list(None)
    return user

@router.post("/api/v1/assign-uni&depart/{uni_id}/{depart_id}", response_model=AssignUserUni)
async def assign_uni_and_department(request:GetAssignedUser,user : str = Depends(get_current_user)):
    """Assign uni and department to a user"""
    if not await mongodb["users"].find_one({"_id":ObjectId(request.user_id)}):

        raise HTTPException(status_code=404, detail="User does not exist")
    await mongodb["users"].update_one({"_id":ObjectId(request.user_id) },{"$set": {"university_id": request.university_id,"department_id": request.department_id}})
    result  = await mongodb["users"].find_one({"_id": ObjectId(request.user_id)})

    return result


@router.get("/api/v1/user-details", response_model=GetUserDetails)
async def user_details(user_id:str,user: str = Depends(get_current_user)):
    """Get user details"""
    user_data = await mongodb["users"].find_one({"_id": ObjectId(user_id)})
    if not user_data:
        raise HTTPException(status_code=404, detail="User does not exist")

    if user_data.get("university_id"):
        university = await mongodb["universities"].find_one({"_id": ObjectId(user_data["university_id"])})
        if user_data.get("department_id"):
            department = await mongodb["departments"].find_one({"_id": ObjectId(user_data["department_id"])})

            if department.get("_id"):
                books = await mongodb["books"].find({"department_id": str(user_data["department_id"])}).to_list(None)

                result = {
                    "username": user_data["username"],
                    "university": university.get("name"),
                    "department": department.get("name"),
                    "books": books
                }
                return result
    return None
