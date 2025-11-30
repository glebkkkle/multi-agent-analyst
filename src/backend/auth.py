# src/backend/auth.py
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from src.multi_agent_analyst.db.db_core import conn  

# JWT CONFIG
SECRET_KEY = "RANDKEY123"  # env var in prod
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login_raw")  # token URL = your login endpoint

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: int
    thread_id: str
    exp: Optional[int] = None

class CurrentUser(BaseModel):
    id: int
    email: str
    thread_id: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        thread_id: str = payload.get("thread_id")

        if user_id is None or thread_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return TokenData(user_id=user_id, thread_id=thread_id, exp=payload.get("exp"))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

# DB helper: load user
def get_user_by_id(user_id: int) -> Optional[CurrentUser]:
    cur = conn.cursor()
    cur.execute("SELECT id, email, thread_id FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    uid, email, thread_id = row
    return CurrentUser(id=uid, email=email, thread_id=thread_id)

# FastAPI dependency
async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    token_data = decode_access_token(token)
    user = get_user_by_id(token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if user.thread_id != token_data.thread_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token thread mismatch",
        )
    return user
