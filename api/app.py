import json
import os
import requests
import secrets
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from dotenv import load_dotenv
from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                         logout_user, current_user)
from requests.exceptions import HTTPError, RequestException
from oauthlib.oauth2 import WebApplicationClient
import helpers.connection as db
import helpers.favourites as fav
import helpers.places as plc
import helpers.restaurant as hres
from helpers.auth import (add_user, check_password, check_username,
                          get_user_id, get_username, match_password,
                          update_user, user_exists)

app = Flask(__name__)
@app.after_request
def set_headers(response):
    response.headers["Referrer-Policy"] = 'no-referrer'
    return response

load_dotenv()
app.config['SECRET_KEY'] = os.environ.get("SECRETKEY")

# Configure Flask login
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"

# Configure Google OAuth
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")


# Set up OAuth 2 client
client = WebApplicationClient(GOOGLE_CLIENT_ID)


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    return User(id=user_id, username=get_username)

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
    print(current_user.is_authenticated)

    return render_template("index.html", show_alert=show_alert, query=query)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if '_user_id' in session:
        return redirect("/")

    if request.method == "POST":
        errors = {}
        username = request.form.get("username").strip()
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


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        errors = {}
        success = False
        password_old = request.form.get("password_old")
        password = request.form.get("password")
        repeat_password = request.form.get("repeat_password")

        if (not match_password(session['username'], password_old)):
            errors['password_old'] = "Incorrect password"

        check_password(password, repeat_password, errors)

        if success:
            update_user(session['_user_id'], password)

        # if errors empty, render success text?
        return render_template("settings.html", errors=errors)
    return render_template("settings.html")

@app.route("/OAuth", methods=["GET", "POST"])
def OAuth():
    # Get endpoint for Google login
    google_provider_config = get_google_provider_config()
    auth_endpoint = google_provider_config["authorization_endpoint"]

    # Construct request for Google login 
    request_uri = client.prepare_request_uri(auth_endpoint, redirect_uri = request.base_url + "/callback", scope=["openid", "email"])
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
    login_user(user)

    # Log in the user
    login_user(user)

    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if '_user_id' in session:
        return redirect("/")

    errors = {}
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")

        if (not user_exists(username) or
           (user_exists and not match_password(username, password))):
            errors['login'] = 'Incorrect username or password'
            return render_template("login.html",
                                   username=username,
                                   errors=errors,
                                   GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID)

        user = User(id=get_user_id(username), username=username)
        login_user(user)
        session['username'] = username
        return redirect("/")

    else:
        return render_template("login.html", GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect("/")


@app.route("/restaurants", methods=["GET", "POST"])
def show_restaurants():
    try:
        api_key = os.environ.get("GCLOUD_KEY")
        if not api_key:
            app.logger.error("API key is empty")
            return jsonify({"error": "API key is empty"}), 400

        # Default data
        default_data = {
            "place_id": "ChIJz-VvsdMEdkgR1lQfyxijRMw",
            "name": "Default: China Town",
            "location": "London",
            "date": "2023-01-01",
        }
        # Note default data wont be required in real
        if request.method == "POST":
            routes_data = request.get_json() or {}
            place_id = routes_data.get("place_id", default_data["place_id"])
            name = routes_data.get("name", default_data["name"])
            # location of the search e.g. London
            location = routes_data.get("location", default_data["location"])
            date = routes_data.get("date", default_data["date"])
        else:
            # For a GET request, use query parameters
            # Get request shouldnt happen?
            place_id = request.args.get("place_id", default_data["place_id"])
            name = request.args.get("name", default_data["name"])
            location = request.args.get("location", default_data["location"])
            date = request.args.get("date", default_data["date"])

        keyword_string, price, dist, open_q = hres.parse_request_parameters()

        # details return to the Jinja
        search_details = {
            "name": name,
            "keyword": keyword_string,
            "price": price,
            "dist": dist,
            "open": open_q,
        }

        lat, lng = hres.fetch_place_details(api_key, place_id)
        if not lat or not lng:
            return "Failed to retrieve place details", 500

        # Search nearby restaurants
        nearby_data = hres.search_nearby_restaurants(
            api_key, lat, lng, keyword_string, dist, price, open_q
        )
        if "status" not in nearby_data or nearby_data["status"] != "OK":
            return "Failed to retrieve data", 500

        # Process and sort restaurants
        all_restaurants = hres.process_restaurant_data(nearby_data)
        top_restaurants_dict = hres.sort_and_slice_restaurants(
            all_restaurants
        )

        # Fetch additional details
        # date and location of original search added to all for database
        top_restaurants_dict = hres.fetch_additional_details(
            api_key, top_restaurants_dict, date, location
        )

        # this will update the bool value for if heart should be red or not.
        top_restaurants_dict = hres.is_restaurant_saved(top_restaurants_dict)

    except HTTPError as e:
        # This will catch HTTP errors, which occur when HTTP request
        # returned an unsuccessful status code
        app.logger.exception("HTTP Error occurred")
        return jsonify({"error": str(e)}), 500
    except json.JSONDecodeError:
        app.logger.exception("JSON Decode Error")
        return jsonify({"error": "No restaurants found in the radius :("}), 500
    except RequestException:
        # This will catch any other exception thrown by
        # the requests library (such as a connection error)
        app.logger.exception("Network-related error occurred")
        return jsonify({"error": "Please check your internet connection"}), 500
    except Exception as e:
        app.logger.exception("An unexpected error occurred")
        return jsonify({"error": str(e)}), 500

    # Prepare data for map generation
    restaurant_data = [
        {
            "name": details["name"],
            "lat": details["latitude"],
            "lng": details["longitude"],
            "website_url": details["website"],
            "image_url": details["photo_url"],
            "ratings": details["rating"],
        }
        for name, details in top_restaurants_dict.items()
    ]

    # Generate map HTML using to_do lat and logn
    map_html = hres.generate_map(restaurant_data, lat, lng, dist)
    return render_template(
        "restaurants.html",
        restaurants=top_restaurants_dict,
        map_html=map_html,
        search_details=search_details,
        to_do_coords=[lng, lat],
        lat_long=restaurant_data,
        mapbox_key=os.environ.get("MAPBOX_KEY")
    )


@app.route("/save-restaurant", methods=["POST"])
def save_restaurant():
    if '_user_id' not in session:
        return redirect(url_for("login"))
    conn = None
    cursor = None
    try:
        if request.args:
            data = plc.get_place_details(request.args.get('placeid'),
                                         request.args.get('date'),
                                         request.args.get('location'),
                                         os.environ.get("GCLOUD_KEY"))
            if isinstance(data.get('photo_reference'), list):
                data['photo_reference'] = data['photo_reference'][0]
        else:
            # data will be from the JS passing the dictionary of info
            data = request.json
        conn, cursor = db.connect_to_db()
        # Step 1: Check if the row exists for place_id
        # Check if the row exists using EXISTS
        check_query = """
            SELECT EXISTS(
                SELECT 1 FROM places
                WHERE placeid = %s
            )
        """
        cursor.execute(check_query, (data["place_id"],))
        exists = cursor.fetchone()[0]

        # Step 2: Update or Insert based on the check
        if exists:
            # Update
            update_query = """
                UPDATE places
                SET name = %s, ratings = %s, rating_count = %s,
                search_link = %s, photo_reference = %s,
                editorial_summary = %s, type = %s
                WHERE placeid = %s
            """
            cursor.execute(
                update_query,
                (
                    data["name"],
                    data["ratings"],
                    data["rating_count"],
                    data["search_link"],
                    data["photo_reference"],
                    data["editorial_summary"],
                    "restaurant",
                    data["place_id"],
                ),
            )
        else:
            # Insert
            insert_query = """
                INSERT INTO places (placeid, name, ratings,
                rating_count, search_link, photo_reference,
                editorial_summary, type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (
                    data["place_id"],
                    data["name"],
                    data["ratings"],
                    data["rating_count"],
                    data["search_link"],
                    data["photo_reference"],
                    data["editorial_summary"],
                    "restaurant",
                ),
            )

        # TEMP userid BEING USED!
        userid = session["_user_id"]

        # userid = "tp4646"\
        # Insert into placesadded table
        # this table will be unique so no need for a check
        insert_query = """
            INSERT INTO placesadded (userid, location, date, placeid)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(
            insert_query,
            (
                userid,
                data["location"],
                data["date"],
                data["place_id"],
            ),
        )

        conn.commit()

    except Exception as e:
        print(e)
        return {"status": "error", "message": str(e)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return {"status": "success"}


@app.route("/delete-restaurant", methods=["POST"])
def delete_restaurant():
    conn = None
    cursor = None
    if '_user_id' not in session:
        # User is not logged in, redirect to login page
        return redirect(url_for("login"))
    if request.args:
        data = plc.get_place_details(request.args.get('placeid'),
                                     request.args.get('date'),
                                     request.args.get('location'),
                                     os.environ.get("GCLOUD_KEY"))
        if isinstance(data.get('photo_reference'), list):
            data['photo_reference'] = data['photo_reference'][0]
    else:
        data = request.json
    # Retrieve user_id from session
    userid = session["_user_id"]
    # userid = "tp4646"

    try:
        conn, cursor = db.connect_to_db()

        # Delete the entry from the second table
        sql_delete_table2 = (
            "DELETE FROM placesadded WHERE userid"
            " = %s AND location = %s "
            "AND date = %s AND placeid = %s"
        )
        cursor.execute(
            sql_delete_table2,
            (userid, data["location"], data["date"], data["place_id"]),
        )

        # Check if no users have place_id in placesadded table
        sql_check = (
            "SELECT EXISTS (SELECT 1 FROM placesadded WHERE placeid = %s)"
        )
        cursor.execute(sql_check, (data["place_id"],))
        # Check if any row exists in table2 with the given place_id
        exists = cursor.fetchone()[0]

        # If place_id is not in the placesadded table i.e. user table
        if not exists:
            sql_delete_table1 = "DELETE FROM places WHERE placeid = %s"
            cursor.execute(sql_delete_table1, (data["place_id"],))

        conn.commit()

    except Exception as e:
        conn.rollback()  # Rollback the transaction in case of an error
        # logging.error(e) Log the error
        return {"status": "error", "message": str(e)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return {
        "status": "success",
        "message": "Operation completed successfully",
    }


@app.route("/favourites", methods=["GET"])
@login_required
def favourites():
    try:
        favr = fav.get_favourites(session["_user_id"])
        fav_json = {'data': favr}
        return render_template("favourites.html",
                               fav_json=json.dumps(fav_json), fav=favr)
    # renders empty if extraction from database fails
    except Exception:
        return render_template("favourites.html",
                               fav_json={}, fav={})  # modified


@app.route("/favourites/opt", methods=["POST"])
def favourites_optimize():
    return fav.get_route(request.get_json(), os.environ.get("GCLOUD_KEY"))


@app.route("/favourites/save", methods=["POST"])
def favourites_save():
    return fav.save_favourites_order(session["_user_id"], request.get_json())


@app.route("/places", methods=["GET"])
def get_places():
    location = request.args.get('location')
    date = request.args.get('date')
    if ((location is None) | (date is None)):
        return redirect(url_for('index', status="no_results", query=location))
    places = plc.get_places(location, date, os.environ.get("GCLOUD_KEY"))
    cname = plc.get_cname(places[0], os.environ.get("GCLOUD_KEY"))
    if ((len(places) == 0) | (cname["country_name"] == '')):
        return redirect(url_for('index', status="no_results", query=location))
    cinfo_all = {**plc.get_cinfo(cname["country_name"]),
                 **plc.get_weather(places[0]["longlat"], date),
                 "name": plc.fuzzy_match(location, cname)}
    return render_template("places.html",
                           places=places,
                           cinfo=cinfo_all)


@app.route("/places/details", methods=["GET"])
def get_place_details():
    return plc.get_place_details(request.args.get('placeid'),
                                 request.args.get('date'),
                                 request.args.get('location'),
                                 os.environ.get("GCLOUD_KEY"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404
