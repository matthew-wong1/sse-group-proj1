import os

import psycopg2 as db
from dotenv import load_dotenv


# Connects to the postgres database, returning a tuple
# of the connection and the cursor
def connect_to_db():
    load_dotenv()

    conn = db.connect(**{"dbname": os.environ.get("PGDATABASE"),
                         'host': 'db.doc.ic.ac.uk',
                         'port': os.environ.get("PGPORT"),
                         'user': os.environ.get("PGUSER"),
                         'password': os.environ.get("PASSWORD"),
                         'client_encoding': 'utf-8'})
    cursor = conn.cursor()

    return conn, cursor
