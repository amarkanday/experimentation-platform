# Results and analysis endpoints
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_results():
    return {"message": "Results Endpoint"}
