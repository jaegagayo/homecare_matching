from fastapi import APIRouter

router = APIRouter()

@router.get("/recommend")
def recommend_matching():
    return {
        "status": "ok",
        "service": "homecare-matching",
        "version": "1.0.0"
    }
