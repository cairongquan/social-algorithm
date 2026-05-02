import os
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlite3 import Connection
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, decode_token

router = APIRouter()
security = HTTPBearer()

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfileResponse(BaseModel):
    user_id: str
    username: str
    is_admin: bool = False
    avatar_url: str | None = None


class UserProfileUpdate(BaseModel):
    username: str | None = None
    password: str | None = None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return payload


def require_admin(user: dict = Depends(get_current_user), db: Connection = Depends(get_db)) -> dict:
    cursor = db.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user["user_id"],))
    row = cursor.fetchone()
    if not row or not bool(row["is_admin"]):
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    return user


def get_current_user_row(user_payload: dict, db: Connection) -> dict:
    cursor = db.cursor()
    cursor.execute("SELECT id, username, is_admin, avatar_url FROM users WHERE id = ?", (user_payload["user_id"],))
    user_row = cursor.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="用户不存在")
    return dict(user_row)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    password_hash = hash_password(user.password)
    user_id = str(uuid4())
    cursor.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, user.username, password_hash)
    )
    db.commit()
    return {"message": "User created successfully"}

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, username, password_hash, is_admin FROM users WHERE username = ?", (user.username,))
    row = cursor.fetchone()
    
    if not row or not verify_password(user.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": row["username"], "user_id": row["id"], "is_admin": bool(row["is_admin"])})
    return {"access_token": access_token}


@router.get("/me", response_model=UserProfileResponse)
async def get_me(user: dict = Depends(get_current_user), db: Connection = Depends(get_db)):
    user_row = get_current_user_row(user, db)
    return {
        "user_id": user_row["id"],
        "username": user_row["username"],
        "is_admin": bool(user_row["is_admin"]),
        "avatar_url": user_row["avatar_url"]
    }


@router.put("/me")
async def update_me(
    payload: UserProfileUpdate,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    user_row = get_current_user_row(user, db)
    cursor = db.cursor()

    next_username = user_row["username"]
    if payload.username is not None and payload.username.strip() != "":
        next_username = payload.username.strip()
        cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (next_username, user_row["id"]))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")

    updates = []
    params: list[str] = []

    if next_username != user_row["username"]:
        updates.append("username = ?")
        params.append(next_username)

    if payload.password is not None and payload.password.strip() != "":
        updates.append("password_hash = ?")
        params.append(hash_password(payload.password.strip()))

    if updates:
        params.append(user_row["id"])
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()

    new_token = create_access_token(data={"sub": next_username, "user_id": user_row["id"], "is_admin": bool(user_row["is_admin"])})
    return {
        "message": "更新成功",
        "access_token": new_token,
        "user": {
            "user_id": user_row["id"],
            "username": next_username,
            "avatar_url": user_row["avatar_url"]
        }
    }


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1] or ".png"
    safe_name = f"avatar_{user['user_id']}_{uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, safe_name)

    with open(filepath, "wb") as out:
        out.write(await file.read())

    avatar_url = f"/api/v1/uploads/{safe_name}"
    cursor = db.cursor()
    cursor.execute("UPDATE users SET avatar_url = ? WHERE id = ?", (avatar_url, user["user_id"]))
    db.commit()

    return {"avatar_url": avatar_url}
