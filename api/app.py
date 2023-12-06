import json
import os

from dotenv import load_dotenv
from flask import (Flask, jsonify, redirect, render_template, request, session,
                   url_for)
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                         logout_user)
from requests.exceptions import HTTPError, RequestException

import helpers.connection as db
import helpers.restaurant as hres
from helpers.auth import (add_user, check_password, check_username,
                          get_user_id, get_username, match_password,
                          user_exists)

app = Flask(__name__)

load_dotenv()
app.config['SECRET_KEY'] = os.environ.get("SECRETKEY")

# Configure Flask login
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    return User(id=user_id, username=get_username)


# Configure routing
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/things-to-do", methods=["POST"])
def things_to_do():
    request_data = {
        "destination": request.form.get("destination"),
        "date": request.form.get("date"),
    }
    return request_data


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

        user = User(id=get_user_id(username), username=username)
        login_user(user)
        print(session)
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/test')
@login_required
def test():
    return ("Hello")


@app.route("/restaurants", methods=["GET", "POST"])
def show_restaurants():
    try:
        api_key = os.getenv("GCLOUD_KEY", "")
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
        # example dictionary from the post.
        # {"location":"London", "placeid": "placeid01",
        #  "name":"London Eye", "date": "2023-01-01"}

        # Handling for POST request
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
        return jsonify({"error": "Invalid JSON response"}), 500
    except RequestException as e:
        # This will catch any other exception thrown by
        # the requests library (such as a connection error)
        app.logger.exception("Network-related error occurred")
        return jsonify({"error": str(e)}), 500
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
    )


@app.route("/save-restaurant", methods=["POST"])
def save_restaurant():
    if '_user_id' not in session:
        return redirect(url_for("login"))
    conn = None
    cursor = None
    try:
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
            # userid = "tp4646"

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
