import os
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"

def search_films(query: str):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "include_adult": False,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from TMDb: {e}")
        return []


    films = []
    for film in data.get("results", []):
        if film.get("vote_count", 0) < 50:
            continue
        films.append({
            "title": film["title"],
            "overview": film.get("overview", ""),
            "year": film["release_date"][:4] if film.get("release_date") else "unknown",
            "poster_url": POSTER_BASE_URL + film["poster_path"] if film.get("poster_path") else None,
            "tmdb_id": film["id"],
            "vote_count": film["vote_count"]
        })
    return films[:8]