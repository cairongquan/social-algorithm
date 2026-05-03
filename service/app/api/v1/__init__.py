"""V1 版本 API 路由聚合。"""

from fastapi import APIRouter
from app.api.v1 import auth, articles, tags, uploads, endpoints, social, topology, admin

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(articles.router, prefix="/articles", tags=["articles"])
router.include_router(tags.router, prefix="/tags", tags=["tags"])
router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
router.include_router(endpoints.router, prefix="/endpoints", tags=["endpoints"])
router.include_router(social.router, prefix="/social", tags=["social"])
router.include_router(topology.router, prefix="/topology", tags=["topology"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
