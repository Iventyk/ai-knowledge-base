from fastapi import APIRouter

router = APIRouter(tags=["ask"])


@router.post("/ask")
def ask_question():
    return {"answer": "stub"}
