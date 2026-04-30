import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlite3 import Connection
from uuid import uuid4

from app.core.database import get_db
from app.api.v1.auth import get_current_user

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    filename = file.filename
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # 保存文件
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 记录到数据库
    cursor = db.cursor()
    upload_id = str(uuid4())
    cursor.execute(
        "INSERT INTO uploads (id, filename, filepath, uploaded_by) VALUES (?, ?, ?, ?)",
        (upload_id, filename, filepath, user["user_id"])
    )
    db.commit()
    
    # 返回可访问的URL和base64（用于TinyMCE）
    import base64
    with open(filepath, "rb") as f:
        file_content = f.read()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
    
    return {
        "filename": filename,
        "url": f"/api/v1/uploads/{filename}",
        "base64": f"data:{file.content_type};base64,{file_base64}"
    }

@router.get("/{filename}")
async def get_file(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath)

@router.get("")
async def list_uploads(
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM uploads WHERE uploaded_by = ? ORDER BY created_at DESC", 
                   (user["user_id"],))
    return [{"id": row["id"], "filename": row["filename"], "url": f"/api/v1/uploads/{row['filename']}"} 
            for row in cursor.fetchall()]
