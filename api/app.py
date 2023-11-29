# import os
import google_api
# import psycopg2 as db
# from dotenv import load_dotenv
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
    # # TESTING IF VERCEL WORKS
    # # load_dotenv()
    # conn = db.connect(**{"dbname": os.environ.get("PGDATABASE"),
    #                      'host': 'db.doc.ic.ac.uk',
    #                      'port': os.environ.get("PGPORT"),
    #                      'user': os.environ.get("PGUSER"),
    #                      'password': os.environ.get("PASSWORD"),
    #                      'client_encoding': 'utf-8'})
    # curs = conn.cursor()
    #
    # curs.execute("""SELECT * FROM branch""")
    # rec = curs.fetchone()
    # # conn.commit()
    #
    # conn.close()
    #
    # return render_template("index.html", rec=rec)

    return render_template("index.html")


@app.route("/restaurants", methods=["POST"])
def restaurants():
    # Parse data from form
    request_data = {
        "destination": request.form.get("destination"),
        "check_in_date": request.form.get("check_in_date"),
        "check_out_date": request.form.get("check_out_date"),
        "guests": request.form.get("guests")
    }

    api_key = 'AIzaSyD4WDNlgnhFpI3O2idkfNBZk2l1dpVLVYQ'
    lat, lng = google_api.get_coordinates(request_data["destination"], api_key)

    if lat is not None and lng is not None:
        center = (lat, lng)
        restaurants = google_api.get_restaurants(lat, lng, 1000,
                                                 None, True, api_key)

    return render_template("restaurants.html",
                           restaurants=restaurants, center=center)
