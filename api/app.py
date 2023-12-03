import json
import ssl
import urllib.parse
import urllib.request

from flask import Flask, redirect, render_template, request

from helpers.auth import (add_user, check_password, check_username,
                          match_password, user_exists)

app = Flask(__name__)


def get_coordinates(destination, api_key):
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json?'

    # Setup SSL context to ignore SSL certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Prepare parameters for the API request
    params = {'address': destination, 'key': api_key}

    # Construct and make the API request
    url = base_url + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, context=ctx) as response:
            json_data = json.loads(response.read().decode())
    except Exception as e:
        print(f'get_coordinates: Error retrieving data = {e}')
        return None, None

    # Check if the API response is valid
    if json_data.get('status') != 'OK':
        print('get_coordinates(): Error bad response')
        return None, None

    coordinates = json_data['results'][0]['geometry']['location']
    return coordinates['lat'], coordinates['lng']


def get_restaurants(latitude, longitude, dist, price, open_now, api_key):
    base_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'

    # Setup SSL context to ignore SSL certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Construct parameters for the Places API request
    params = {
        'location': f'{latitude},{longitude}',
        'radius': dist,
        'keyword': 'restaurant',
        'key': api_key
    }
    if price:
        params['maxprice'] = price
    if open_now:
        params['opennow'] = 'true'

    # Construct the Places API request URL
    url = base_url + urllib.parse.urlencode(params)

    # Make the Places API request
    try:
        with urllib.request.urlopen(url, context=ctx) as response:
            json_data = json.loads(response.read().decode())
    except Exception as e:
        print(f'get_restaurants(): Error retrieving data = {e}')
        return None, None

    # Check if the Places API response is valid
    if json_data.get('status') != 'OK':
        print('get_restaurants(): Error bad response')
        return None

    # Process and print restaurants (greater that 4* and more than 30 reviews)
    restaurants = {}
    for result in json_data['results']:
        rating = result.get('rating', 0)
        user_ratings_total = result.get('user_ratings_total', 0)

        if rating > 4 and user_ratings_total > 20:
            name = result['name']
            lat = result['geometry']['location']['lat']
            lng = result['geometry']['location']['lng']
            restaurants[name] = {
                "latitude": lat,
                "longitude": lng,
                "rating": rating,
                "num_user_ratings": user_ratings_total
            }

    return restaurants


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
    lat, lng = get_coordinates(request_data["destination"], api_key)

    if lat is not None and lng is not None:
        center = (lat, lng)
        restaurants = get_restaurants(lat, lng, 1000, None, True, api_key)

    return render_template("restaurants.html",
                           restaurants=restaurants, center=center)


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        errors = {}
        username = request.form.get("username")
        password = request.form.get("password")
        repeat_password = request.form.get("repeat_password")

        # Check if fields empty
        check_username(username, errors)
        check_password(password, repeat_password, errors)

        if not errors:
            add_user(username, password)
            return redirect("login")
        return render_template("signup.html", username=username, errors=errors)
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    errors = {}
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if (user_exists(username) or not match_password(username, password)):
            errors['login'] = 'Incorrect username or password'
            return render_template("login.html",
                                   username=username,
                                   errors=errors)

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    return redirect("/")
