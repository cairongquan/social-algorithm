from fastapi import APIRouter
from app.api.v1 import auth, articles, tags, uploads, endpoints, social, topology

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(articles.router, prefix="/articles", tags=["articles"])
router.include_router(tags.router, prefix="/tags", tags=["tags"])
router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
router.include_router(endpoints.router, prefix="/endpoints", tags=["endpoints"])
router.include_router(social.router, prefix="/social", tags=["social"])
router.include_router(topology.router, prefix="/topology", tags=["topology"])
