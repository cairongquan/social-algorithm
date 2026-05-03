"""示例端点集合。"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
async def read_example():
    return {"message": "Hello from API v1"}
