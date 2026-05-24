import os
import asyncio
import httpx

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"


def search_films(query: str) -> list:
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "include_adult": False,
    }

    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        films = []
        for film in data.get("results", []):
            if film.get("vote_count", 0) < 50:
                continue
            films.append({
                "title": film["title"],
                "year": film["release_date"][:4] if film.get("release_date") else "unknown",
                "poster_url": POSTER_BASE_URL + film["poster_path"] if film.get("poster_path") else None,
                "tmdb_id": film["id"],
                "vote_count": film["vote_count"],
                "overview": film.get("overview", "")
            })
        return films[:8]

    except httpx.HTTPError as e:
        print(f"TMDB search error: {e}")
        return []


async def enrich_film_async(client: httpx.AsyncClient, title: str, year: int) -> dict:
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "year": year,
        "include_adult": False,
    }

    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])

        if not results:
            return {}

        film = results[0]
        return {
            "tmdb_id": film["id"],
            "poster_url": POSTER_BASE_URL + film["poster_path"] if film.get("poster_path") else None,
            "overview": film.get("overview", ""),
            "vote_average": film.get("vote_average", None),
        }

    except httpx.HTTPError as e:
        print(f"TMDB enrich error for {title}: {e}")
        return {}


def get_film_by_id(tmdb_id: int) -> dict:
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY}

    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            film = response.json()

        credits = get_credits_sync(tmdb_id)

        return {
            "tmdb_id": film["id"],
            "title": film["title"],
            "year": film["release_date"][:4] if film.get("release_date") else "unknown",
            "poster_url": POSTER_BASE_URL + film["poster_path"] if film.get("poster_path") else None,
            "overview": film.get("overview", ""),
            "vote_average": film.get("vote_average", None),
            "director": credits.get("director", "unknown"),
            "cast": credits.get("cast", [])
        }

    except httpx.HTTPError as e:
        print(f"TMDB get_film_by_id error: {e}")
        return {}


def get_credits_sync(tmdb_id: int) -> dict:
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits"
    params = {"api_key": TMDB_API_KEY}

    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        crew = data.get("crew", [])
        cast = data.get("cast", [])

        director = next(
            (member["name"] for member in crew if member["job"] == "Director"),
            "unknown"
        )
        top_cast = [member["name"] for member in cast[:4]]

        return {"director": director, "cast": top_cast}

    except httpx.HTTPError as e:
        print(f"TMDB credits error: {e}")
        return {}


async def enrich_film_with_credits_async(title: str, year: int) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        facts = await enrich_film_async(client, title, year)
        
        if not facts.get("tmdb_id"):
            return facts
            
        credits = await get_credits_async(client, facts["tmdb_id"])
        return {**facts, **credits}


def enrich_films_parallel(films: list) -> list:
    async def run():
        async with httpx.AsyncClient(timeout=10) as client:
            tasks = [
                asyncio.gather(
                    enrich_film_async(client, film["title"], film["year"]),
                )
                for film in films
            ]
            results = await asyncio.gather(*tasks)
            
            credit_tasks = []
            enriched = [r[0] for r in results]
            for facts in enriched:
                if facts.get("tmdb_id"):
                    credit_tasks.append(get_credits_async(client, facts["tmdb_id"]))
                else:
                    credit_tasks.append(asyncio.sleep(0))

            credits = await asyncio.gather(*credit_tasks)
            
            for i, film in enumerate(films):
                film.update(enriched[i])
                if isinstance(credits[i], dict):
                    film.update(credits[i])
            
            return films

    return asyncio.run(run())

async def get_credits_async(client: httpx.AsyncClient, tmdb_id: int) -> dict:
    if not tmdb_id:
        return {}
    
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits"
    params = {"api_key": TMDB_API_KEY}

    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        crew = data.get("crew", [])
        cast = data.get("cast", [])

        director = next(
            (member["name"] for member in crew if member["job"] == "Director"),
            "unknown"
        )
        top_cast = [member["name"] for member in cast[:4]]

        return {"director": director, "cast": top_cast}

    except httpx.HTTPError as e:
        print(f"TMDB credits async error for {tmdb_id}: {e}")
        return {}