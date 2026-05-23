from fastapi import APIRouter
from filmaura.core.tmdb_client import search_films

router = APIRouter()

@router.get("/search")
def search(query: str):
    if not query:
        return {"error": "query is required"}
    results = search_films(query)
    return {"results": results}