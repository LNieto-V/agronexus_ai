from fastapi import APIRouter

router = APIRouter(tags=["system"])

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
