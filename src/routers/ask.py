from fastapi import APIRouter

ask_router = APIRouter(tags=["ask"])


@ask_router.post("/ask")
def ask_question():
    return {"answer": "stub"}
