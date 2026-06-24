from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status

from api.utils.db_collection import mongodb
from api.utils.hash_password import SECRET_KEY, ALGORITHM, pwd_context

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status

security = HTTPBearer()


async def authenticate_user(username: str, password: str):
    """Authenticate a user"""
    user = await mongodb["users"].find_one({"username": username})
    if not user or not pwd_context.verify(password, user["password"]):
        return False
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
