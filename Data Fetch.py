import requests
import psycopg2

# OMDb API Key
api_key = "bd01652d"

# Movie titles
movie_titles = [
    "Inception", "The Shawshank Redemption", "The Godfather", "The Godfather Part II",
    "Schindler's List", "12 Angry Men", "Spirited Away", "The Dark Knight",
    "Dilwale Dulhania Le Jayenge", "The Green Mile", "Parasite", "Pulp Fiction",
    "Your Name.", "The Lord of the Rings: The Return of the King", "Forrest Gump",
    "The Good, the Bad and the Ugly", "GoodFellas", "Seven Samurai", "Interstellar",
    "Grave of the Fireflies", "Life Is Beautiful", "Fight Club", "Cinema Paradiso",
    "City of God", "Psycho", "My Name Is Khan", "12th Fail", "3 Idiots",
    "Like Stars on Earth", "Dangal", "Period. End of Sentence.", "Sanam Teri Kasam",
    "Bajrangi Bhaijaan", "PK", "Kabhi Khushi Kabhie Gham", "Drishyam", "Black",
    "Andhadhun", "Chhichhore", "Mom", "Zindagi Na Milegi Dobara", "Hichki",
    "Barfi!", "Article 15", "Devdas", "Tumbbad", "Kuch Kuch Hota Hai", "Talvar",
    "Gangubai Kathiawadi"
]

# Connect to database
conn = psycopg2.connect(
    dbname="202301469",
    user="202301469",
    password="",
    host="10.100.71.21",
    port="5432"
)
cursor = conn.cursor()
cursor.execute('SET search_path TO "MovieMania";')

for title in movie_titles:
    url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()

    if data.get("Response") == "False":
        print(f"Movie not found on OMDb: {title}")
        continue

    # Get movie_id from local DB
    cursor.execute("SELECT movie_id FROM movie WHERE title = %s", (data.get("Title"),))
    result = cursor.fetchone()
    if not result:
        print(f"Movie not found in database: {title}")
        continue

    movie_id = result[0]

    # Get cast from OMDb (comma-separated)
    cast_list = data.get("Actors", "").split(", ")
    
    for full_name in cast_list:
        if not full_name.strip():
            continue

        # Check if actor already exists
        cursor.execute("SELECT cast_id FROM cast_members WHERE full_name = %s", (full_name,))
        result = cursor.fetchone()
        if result:
            cast_id = result[0]
        else:
            cursor.execute("INSERT INTO cast_members (full_name) VALUES (%s) RETURNING cast_id", (full_name,))
            cast_id = cursor.fetchone()[0]

        # Insert into movie_cast
        cursor.execute("""
            INSERT INTO movie_cast (movie_id, cast_id, role)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (movie_id, cast_id, "Unknown"))

    print(f"Inserted cast for: {title}")

# Finalize
conn.commit()
cursor.close()
conn.close()


############################################################################################################################################

import requests
import psycopg2

# OMDb API Key
api_key = "bd01652d"

# Movie titles
movie_titles = [
    "Inception", "The Shawshank Redemption", "The Godfather", "The Godfather Part II",
    "Schindler's List", "12 Angry Men", "Spirited Away", "The Dark Knight",
    "Dilwale Dulhania Le Jayenge", "The Green Mile", "Parasite", "Pulp Fiction",
    "Your Name.", "The Lord of the Rings: The Return of the King", "Forrest Gump",
    "The Good, the Bad and the Ugly", "GoodFellas", "Seven Samurai", "Interstellar",
    "Grave of the Fireflies", "Life Is Beautiful", "Fight Club", "Cinema Paradiso",
    "City of God", "Psycho", "My Name Is Khan", "12th Fail", "3 Idiots",
    "Like Stars on Earth", "Dangal", "Period. End of Sentence.", "Sanam Teri Kasam",
    "Bajrangi Bhaijaan", "PK", "Kabhi Khushi Kabhie Gham", "Drishyam", "Black",
    "Andhadhun", "Chhichhore", "Mom", "Zindagi Na Milegi Dobara", "Hichki",
    "Barfi!", "Article 15", "Devdas", "Tumbbad", "Kuch Kuch Hota Hai", "Talvar",
    "Gangubai Kathiawadi"
]

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="202301469",
    user="202301469",
    password="",
    host="10.100.71.21",
    port="5432"
)
cursor = conn.cursor()
cursor.execute('SET search_path TO "MovieMania";')

for title in movie_titles:
    url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()

    if data.get("Response") == "False":
        print(f"Movie not found on OMDb: {title}")
        continue

    # Get movie_id from DB
    cursor.execute("SELECT movie_id FROM movie WHERE title = %s", (data.get("Title"),))
    result = cursor.fetchone()
    if not result:
        print(f"Movie not found in database: {title}")
        continue

    movie_id = result[0]

    # Only fetch Director and Writer
    cast_data = {
        "Director": data.get("Director", "").split(", "),
        "Writer": data.get("Writer", "").split(", ")
    }

    for role, people in cast_data.items():
        for full_name in people:
            full_name = full_name.strip()
            if not full_name or full_name.lower() in ["n/a", "unknown"]:
                continue

            # Add to cast_members if not exists
            cursor.execute("SELECT cast_id FROM cast_members WHERE full_name = %s", (full_name,))
            result = cursor.fetchone()
            if result:
                cast_id = result[0]
            else:
                cursor.execute("INSERT INTO cast_members (full_name) VALUES (%s) RETURNING cast_id", (full_name,))
                cast_id = cursor.fetchone()[0]

            # Avoid duplicates in movie_cast
            cursor.execute("""
                SELECT 1 FROM movie_cast WHERE movie_id = %s AND cast_id = %s AND role = %s
            """, (movie_id, cast_id, role))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute("""
                    INSERT INTO movie_cast (movie_id, cast_id, role)
                    VALUES (%s, %s, %s)
                """, (movie_id, cast_id, role))

    print(f"Inserted director and writer for: {title}")

# Finalize
conn.commit()
cursor.close()
conn.close()


############################################################################################################################################


from flask import Flask, render_template_string
import psycopg2
import base64
import imghdr

app = Flask(__name__)

# PostgreSQL connection
DB_CONFIG = {
    'dbname': '202301469',
    'user': '202301469',
    'password': '',
    'host': '10.100.71.21',
    'port': 5432
}

@app.route("/posters")
def show_posters():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, poster FROM "MovieMania".movie_posters
        WHERE poster IS NOT NULL
    """)
    posters = cursor.fetchall()
    cursor.close()
    conn.close()

    poster_html = ""
    seen_titles = set()
    for title, poster_data in posters:
        if title in seen_titles:
            continue
        seen_titles.add(title)
        img_type = imghdr.what(None, h=poster_data)
        if not img_type:
            continue
        base64_img = base64.b64encode(poster_data).decode('utf-8')
        poster_html += f"""
            <div style="margin: 20px; text-align: center;">
                <h3>{title}</h3>
                <img src="data:image/{img_type};base64,{base64_img}" width="200"/>
            </div>
        """

    html_template = f"""
    <html>
    <head><title>Movie Posters</title></head>
    <body style="font-family: Arial; display: flex; flex-wrap: wrap;">
        {poster_html}
    </body>
    </html>
    """
    return render_template_string(html_template)

if __name__ == "__main__":
    app.run(debug=True)

############################################################################################################################################

import requests
import psycopg2

# Replace with your values
TMDB_API_KEY = "17339813e83f42442368f91d683c7132"
DB_CONFIG = {
    'dbname': '202301469',
    'user': '202301469',
    'password': '',
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

