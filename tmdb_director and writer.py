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
    password="Neel10102005",
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
