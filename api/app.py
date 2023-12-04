import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                         logout_user)

import helpers.connection as db
import helpers.google_api as g_api
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


@app.route("/restaurants", methods=["POST"])
def restaurants():
    # Parse data from form
    request_data = {
        "destination": request.form.get("destination"),
        "date": request.form.get("date"),
    }

    load_dotenv()
    api_key = os.environ.get("GCLOUD_KEY")
    lat, lng = g_api.get_coordinates(request_data["destination"], api_key)

    if lat is not None and lng is not None:
        center = (lat, lng)
        restaurants = g_api.get_restaurants(lat, lng, 1000,
                                            None, True, api_key)

    # restaurants = db.is_restaurant_saved(restaurants)
    print(restaurants)

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


@app.route('/save-restaurant', methods=['POST'])
def save_restaurant():
    try:
        data = request.json
        conn, cursor = db.connect_to_db()

        sql = """INSERT INTO restaurants (name, latitude, longitude,
                                          rating, num_ratings)
                 VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (data['name'], data['latitude'], data['longitude'],
                             data['rating'], data['num_user_ratings']))

        conn.commit()

    except Exception as e:
        print(e)
        return {'status': 'error', 'message': str(e)}

    finally:
        cursor.close()
        conn.close()

    return {'status': 'success'}


@app.route('/delete-restaurant', methods=['POST'])
def delete_restaurant():
    data = request.json
    name = data['name']

    try:
        conn, cursor = db.connect_to_db()
        cursor.execute("DELETE FROM restaurants WHERE name = %s", (name,))
        conn.commit()
    except Exception as e:
        print(e)
        return {'status': 'error', 'message': str(e)}
    finally:
        cursor.close()
        conn.close()

    return {'status': 'success'}
