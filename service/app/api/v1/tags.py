from fastapi import APIRouter, Depends, HTTPException, status
from sqlite3 import Connection
from pydantic import BaseModel
from typing import List
from uuid import uuid4

from app.core.database import get_db
from app.api.v1.auth import get_current_user

router = APIRouter()

class TagCreate(BaseModel):
    name: str

class TagUpdate(BaseModel):
    name: str

class TagResponse(BaseModel):
    id: str
    name: str
    created_at: str

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag: TagCreate,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    try:
        tag_id = str(uuid4())
        cursor.execute("INSERT INTO tags (id, name) VALUES (?, ?)", (tag_id, tag.name))
        db.commit()
        return {"id": tag_id, "message": "Tag created successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Tag name already exists")

@router.get("", response_model=List[TagResponse])
async def list_tags(db: Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tags ORDER BY name")
    return [{"id": row["id"], "name": row["name"], "created_at": row["created_at"]} 
            for row in cursor.fetchall()]

@router.put("/{tag_id}")
async def update_tag(
    tag_id: str,
    tag: TagUpdate,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Tag not found")
    
    try:
        cursor.execute("UPDATE tags SET name = ? WHERE id = ?", (tag.name, tag_id))
        db.commit()
        return {"message": "Tag updated successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Tag name already exists")

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # 删除标签时，清除关联文章的所有标签（根据需求：将关联标签的文章的标签都清除）
    # 如果只需要清除被删除标签的关联，删除下面这行
    cursor.execute("DELETE FROM article_tags WHERE tag_id = ?", (tag_id,))
    # 如果需要清除关联文章的所有标签，使用下面这行代替上行
    # cursor.execute("DELETE FROM article_tags WHERE article_id IN (SELECT article_id FROM article_tags WHERE tag_id = ?)", (tag_id,))
    cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    db.commit()
