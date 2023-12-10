import json
import os
import secrets
from datetime import timedelta

import requests
from dotenv import load_dotenv
from flask import (Flask, abort, redirect, render_template, request, session,
                   url_for)
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from oauthlib.oauth2 import WebApplicationClient
from requests.exceptions import HTTPError, RequestException

import helpers.favourites as fav
import helpers.places as plc
import helpers.restaurant as hres
from helpers.auth import (User, add_user, check_password, check_username,
                          get_user_id, get_username, match_password,
                          update_user, user_exists)

# Configure app.py
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Get app's secret key so Flask_login can manipulate the session
app.config['SECRET_KEY'] = os.environ.get("SECRETKEY")

# Configure Flask login
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"

# Set cookie expiration
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=31)

# Configure Google OAuth
# to work on MacOS, turn off AirPlay receiver and do $ flask run --host=0.0.0.0
# will only work on localhost
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration")


# Set up OAuth 2 client
client = WebApplicationClient(GOOGLE_CLIENT_ID)


# Define user_loader callback to load user obj from user id in session
@login_manager.user_loader
def load_user(user_id):
    return User(id=user_id, username=get_username(user_id))


# Retrieve Google's provider config
# ADD ERROR HADNLING TO API CALL LATER
def get_google_provider_config():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


# Configure routing
@app.route("/", methods=["GET"])
def index():
    status = request.args.get('status')
    query = request.args.get('query')
    show_alert = (status == "no_results")

    return render_template("index.html", show_alert=show_alert, query=query)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        errors = {}
        exception = None
        username = request.form.get("username").strip()
        password = request.form.get("password")
        repeat_password = request.form.get("repeat_password")

        # Check if issues with username or password supplied
        check_password(password, repeat_password, errors)

        try:
            check_username(username, errors)
        
            if not errors:
                add_user(username, password)
                return redirect("login")
        
        except Exception as db_error:
            exception = db_error

        finally: 
            return render_template("signup.html",
                                   username=username,
                                   errors=errors,
                                   exception=exception)

    return render_template("signup.html")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        errors = {}
        success = False
        password_old = request.form.get("password_old")
        password = request.form.get("password")
        repeat_password = request.form.get("repeat_password")

        # Check old password matches
        if (not match_password(current_user.username, password_old)):
            errors['password_old'] = "Incorrect password"

        # Check validity of new password
        check_password(password, repeat_password, errors)

        if not errors:
            update_user(current_user.id, password)
            success = True

        # Render messages
        return render_template("settings.html", errors=errors, success=success)

    return render_template("settings.html")


@app.route("/OAuth", methods=["GET", "POST"])
def OAuth():
    # Get endpoint for Google login
    google_provider_config = get_google_provider_config()
    auth_endpoint = google_provider_config["authorization_endpoint"]

    # Construct request for Google login
    request_uri = client.prepare_request_uri(
        auth_endpoint,
        redirect_uri=request.base_url+"/callback",
        scope=["openid", "email"])
    return redirect(request_uri)


@app.route("/OAuth/callback", methods=["GET", "POST"])
def callback():
    # Get Google's Auth code
    auth_code = request.args.get("code")

    google_provider_config = get_google_provider_config()
    token_endpoint = google_provider_config["token_endpoint"]

    # Prepare request for tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=auth_code
    )

    # Send request for tokens
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
    )

    # Parse tokens
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Get User information
    userinfo_endpoint = google_provider_config["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # Parse response from userinfo
    email = userinfo_response.json()["email"]
    # Throw error if email not avialable

    # Check if user already exists
    if not user_exists(email):
        RAND_PASSWORD_LENGTH = 32
        rand_password = secrets.token_urlsafe(RAND_PASSWORD_LENGTH)
        add_user(email, rand_password)

    # Create a user object
    user = User(id=get_user_id(email), username=email)

    # Log in the user
    login_user(user)

    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        errors = {}
        username = request.form.get("username").strip()
        password = request.form.get("password")

        if (not user_exists(username) or
           (user_exists and not match_password(username, password))):
            errors['login'] = 'Incorrect username or password'
            return render_template("login.html",
                                   username=username,
                                   errors=errors)

        user = User(id=get_user_id(username), username=username)
        login_user(user)
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect("/")


@app.route("/restaurants", methods=["GET", "POST"])
def show_restaurants():
    try:
        api_key = hres.get_api_key_or_error()
        request_data = hres.get_request_data()
        search_details = hres.get_search_details(request_data)
        lat, lng = hres.get_lat_lng_or_error(api_key, request_data['place_id'])
        nearby_data = hres.get_nearby_data_or_error(api_key,
                                                    lat, lng, search_details)
        top_restaurants_dict = hres.process_and_sort_restaurants(
            nearby_data)
        top_restaurants_dict = hres.fetch_and_update_restaurant_details(
            api_key, top_restaurants_dict, request_data)
        restaurant_data = hres.prepare_restaurant_data_for_map(
            top_restaurants_dict)
        map_html = hres.generate_map_html(
            restaurant_data, lat, lng, search_details['dist'])
        return render_template(
            "restaurants.html",
            restaurants=top_restaurants_dict,
            map_html=map_html,
            search_details=search_details,
            to_do_coords=[lng, lat],
            lat_long=restaurant_data,
            mapbox_key=os.environ.get("MAPBOX_KEY")
        )
    except (HTTPError, RequestException, Exception) as e:
        return hres.handle_error(e)


@app.route('/restaurant-not-found')
def some_endpoint():
    return render_template('restaurant-not-found.html'), 404


@app.route("/save-restaurant", methods=["POST"])
def save_restaurant():
    if not current_user.is_authenticated:
        abort(401, description="User not logged in")

    # Get data from request and user_id from session
    data = request.json
    user_id = current_user.id

    # Call the helper function to handle restaurant data saving
    result = hres.save_restaurant_data(user_id, data)

    return result


@app.route("/delete-restaurant", methods=["POST"])
def delete_restaurant():
    if not current_user.is_authenticated:
        abort(401, description="User not logged in")

    # Get data from request and user_id from session
    data = request.json
    user_id = current_user.id

    # Call the helper function to handle places data deletion
    result = hres.delete_restaurant_data(user_id, data)

    return result


@app.route("/places/delete-places", methods=["POST"])
def delete_places():
    if not current_user.is_authenticated:
        abort(401, description="User not logged in")
    # Get data from request and user_id from session
    request_data = request.get_json()
    user_id = current_user.id
    # Call the helper function to handle places data deletion
    result = hres.delete_restaurant_data(user_id, request_data)

    return result


@app.route("/places/save-places", methods=["POST"])
def save_places():
    if not current_user.is_authenticated:
        abort(401, description="User not logged in")
    # Get data from request and user_id from session
    request_data = request.get_json()
    user_id = current_user.id
    # Call the helper function to handle places data saving
    data = plc.get_place_details(request_data["place_id"],
                                 request_data["date"],
                                 request_data["location"],
                                 os.environ.get("GCLOUD_KEY"))
    data['photo_reference'] = data['photo_reference'][0]
    result = hres.save_restaurant_data(user_id, data)
    return result


@app.route("/favourites", methods=["GET"])
@login_required
def favourites():
    try:
        favr = fav.get_favourites(current_user.id)
        fav_json = {'data': favr}
        return render_template("favourites.html",
                               fav_json=json.dumps(fav_json), fav=favr)
    # renders empty if extraction from database fails
    except Exception:
        return render_template("favourites.html",
                               fav_json={}, fav={})  # modified


@app.route("/favourites/opt", methods=["POST"])
def favourites_optimize():
    # get optimized path
    return fav.get_route(request.get_json(), os.environ.get("GCLOUD_KEY"))


@app.route("/favourites/save", methods=["POST"])
def favourites_save():
    # retrieved saved places route order
    return fav.save_favourites_order(current_user.id, request.get_json())


@app.route("/places", methods=["GET"])
def get_places():
    location = request.args.get('location')
    date = request.args.get('date')
    # if no proper arguments provided
    if ((location is None) | (date is None)):
        return redirect(url_for('index', status="no_results", query=location))
    # retrieved searched places
    places = plc.get_places(location, date, os.environ.get("GCLOUD_KEY"))
    # retrieved country name
    cname = plc.get_cname(places[0], os.environ.get("GCLOUD_KEY"))
    # if no search found provided
    if ((len(places) == 0) | (cname["country_name"] == '')):
        return redirect(url_for('index', status="no_results", query=location))
    # get country information, weather info
    cinfo_all = {**plc.get_cinfo(cname["country_name"]),
                 **plc.get_weather(places[0]["longlat"], date),
                 "name": plc.fuzzy_match(location, cname)}
    return render_template("places.html",
                           places=places,
                           cinfo=cinfo_all)


@app.route("/places/details", methods=["GET"])
def get_place_details():
    # get the details of a chosen place
    return plc.get_place_details(request.args.get('placeid'),
                                 request.args.get('date'),
                                 request.args.get('location'),
                                 os.environ.get("GCLOUD_KEY"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404
