import os

import psycopg2 as db
from dotenv import load_dotenv
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    # TESTING IF VERCEL WORKS
    load_dotenv()

    conn = db.connect(**{"dbname": os.environ.get("pgdatabase"),
                         'host': 'db.doc.ic.ac.uk',
                         'port': os.environ.get("pgport"),
                         'user': os.environ.get("pguser"),
                         'password': os.environ.get("password"),
                         'client_encoding': 'utf-8'})

    print(os.environ.get("pgport"))
    curs = conn.cursor()

    curs.execute("""SELECT * FROM branch""")
    rec = curs.fetchone()
    # conn.commit()

    conn.close()

    return render_template("index.html", rec=rec)
