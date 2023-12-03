import os

import psycopg2 as db
from dotenv import load_dotenv


# ADD EXCEPTION HANDLING
def connect_to_db():
    load_dotenv()
    print(os.environ.get("PGDATABASE"))
    conn = db.connect(**{"dbname": os.environ.get("PGDATABASE"),
                         'host': 'db.doc.ic.ac.uk',
                         'port': os.environ.get("PGPORT"),
                         'user': os.environ.get("PGUSER"),
                         'password': os.environ.get("PASSWORD"),
                         'client_encoding': 'utf-8'})
    cursor = conn.cursor()

    return conn, cursor
