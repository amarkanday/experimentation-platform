# Experiment assignment endpoints
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_assignments():
    return {"message": "Assignments Endpoint"}
