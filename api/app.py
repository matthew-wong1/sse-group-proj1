import json
import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                         logout_user)
from requests.exceptions import HTTPError, RequestException

import helpers.connection as db
import helpers.favourites as fav
import helpers.places as plc
import helpers.restaurant as hres
from helpers.auth import (add_user, check_password, check_username,
                          get_user_id, get_username, match_password,
                          update_user, user_exists)

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
@app.route("/", methods=["GET"])
def index():
    status = request.args.get('status')
    query = request.args.get('query')
    show_alert = (status == "no_results")

    return render_template("index.html", show_alert=show_alert, query=query)


@app.route("/signup", methods=["GET", "POST"])
def signup():

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
                                   errors=errors)

        user = User(id=get_user_id(username), username=username)
        login_user(user)
        session['username'] = username
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
def favourites():
    favr = fav.get_favourites()
    fav_json = {'data': favr}
    return render_template("favourites.html",
                           fav_json=json.dumps(fav_json), fav=favr)


@app.route("/favourites/opt", methods=["POST"])
def favourites_optimize():
    return fav.get_route(request.get_json(), os.environ.get("GCLOUD_KEY"))


@app.route("/favourites/save", methods=["POST"])
def favourites_save():
    return fav.save_favourites_order(request.get_json())


@app.route("/places", methods=["GET"])
def get_places():
    location = request.args.get('location')
    date = request.args.get('date')
    print("imhere")
    places = plc.get_places(location, date, os.environ.get("GCLOUD_KEY"))
    if len(places) == 0:
        return redirect(url_for('index', status="no_results", query=location))

    cname = plc.get_cname(places[0], os.environ.get("GCLOUD_KEY"))
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
