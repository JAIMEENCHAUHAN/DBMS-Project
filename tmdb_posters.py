import requests
import psycopg2

# Replace with your values
TMDB_API_KEY = "17339813e83f42442368f91d683c7132"
DB_CONFIG = {
    'dbname': '202301469',
    'user': '202301469',
    'password': 'Neel10102005',
    'host': '10.100.71.21',
    'port': 5432
}

IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

def get_tmdb_poster(title):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get("results")
        if results:
            poster_path = results[0].get("poster_path")
            return IMAGE_BASE_URL + poster_path if poster_path else None
    return None

def sync_movie_posters():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Step 1: Fetch id and title from movie table
    cursor.execute('SELECT movie_id, title FROM "MovieMania".movie')
    movies = cursor.fetchall()

    for movie_id, title in movies:
        poster_url = get_tmdb_poster(title)
        if poster_url:
            cursor.execute("""
                INSERT INTO "MovieMania".movie_posters (id, title, poster)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE 
                SET title = EXCLUDED.title,
                    poster = EXCLUDED.poster;
            """, (movie_id, title, poster_url))
            print(f"✅ Poster added/updated for: {title}")
        else:
            print(f"❌ Poster not found for: {title}")

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    sync_movie_posters()
