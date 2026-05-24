from fastapi import APIRouter
from pydantic import BaseModel
from filmaura.core.tmdb_client import (
    search_films,
    get_film_by_id,
    enrich_films_parallel
)
from filmaura.core.claude_client import (
    get_film_titles,
    analyze_films,
    get_similar_and_analyze
)

router = APIRouter()

class AuraQuery(BaseModel):
    query: str
    letterboxd_username: str = None

@router.get("/search")
def search(query: str):
    if not query:
        return {"error": "query is required"}
    results = search_films(query)
    return {"results": results}


@router.get("/similar/{tmdb_id}")
def similar(tmdb_id: int):
    # step 1 — get seed film facts from TMDB
    seed = get_film_by_id(tmdb_id)
    if not seed:
        return {"error": "film not found"}

    # step 2 — Claude finds 5 similar films + analyzes them
    similar_films = get_similar_and_analyze(seed)
    if not similar_films:
        return {"results": []}

    # step 3 — TMDB enriches with poster/credits
    # save Claude's aesthetic fields first
    aesthetic_data = {
        film["title"]: {
            k: v for k, v in film.items()
            if k in ["color_palette", "tone", "mood", 
                     "pacing", "aura_match", "letterboxd_slug"]
        }
        for film in similar_films
    }

    # enrich with TMDB facts
    similar_films = enrich_films_parallel(similar_films)

    # restore Claude's aesthetic fields
    for film in similar_films:
        if film["title"] in aesthetic_data:
            film.update(aesthetic_data[film["title"]])

    return {"seed": seed, "results": similar_films}


@router.post("/recommend")
def recommend(body: AuraQuery):
    if not body.query:
        return {"error": "query is required"}

    films = get_film_titles(body.query)
    print(f"Claude picked: {len(films)} films")

    if not films:
        return {"results": []}

    # parallel TMDB enrichment
    films = enrich_films_parallel(films)

    analysis = analyze_films(body.query, films)

    for film in films:
        for result in analysis:
            if result["title"] == film["title"]:
                film.update(result)

    return {"results": films}