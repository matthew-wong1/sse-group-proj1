import os

import psycopg2 as db
from dotenv import load_dotenv


# ADD EXCEPTION HANDLING
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


def is_restaurant_saved(restaurants):
    try:
        conn, cursor = connect_to_db()
        cursor.execute("SELECT name FROM restaurants")
        saved_restaurants_records = cursor.fetchall()
        conn.commit()
    except Exception as e:
        print(e)
        return restaurants
    finally:
        cursor.close()
        conn.close()

    # Convert the list of tuples to a set for faster lookup
    saved_restaurants = set(record[0] for record in saved_restaurants_records)

    # Update each restaurant's data with the saved status
    for restaurant_name, details in restaurants.items():
        details['is_saved'] = restaurant_name in saved_restaurants
        restaurants[restaurant_name] = details

    return restaurants
