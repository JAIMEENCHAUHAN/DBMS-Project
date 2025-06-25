from flask import Flask, render_template_string
import psycopg2
import base64
import imghdr

app = Flask(__name__)

# PostgreSQL connection
DB_CONFIG = {
    'dbname': '202301469',
    'user': '202301469',
    'password': 'Neel10102005',
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
