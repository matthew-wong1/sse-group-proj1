import os

import psycopg as db
from dotenv import load_dotenv
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    # TESTING IF VERCEL WORKS
    load_dotenv()

    conn = db.connect(**{"dbname": os.environ.get("PGDATABASE"),
                         'host': 'db.doc.ic.ac.uk',
                         'port': os.environ.get("PGPORT"),
                         'user': os.environ.get("PGUSER"),
                         'password': os.environ.get("PASSWORD"),
                         'client_encoding': 'utf-8'})

    curs = conn.cursor()

    curs.execute("""SELECT * FROM branch""")
    rec = curs.fetchone()
    # conn.commit()

    conn.close()

    return render_template("index.html", rec=rec)
