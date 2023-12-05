import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, jsonify, session, redirect, url_for
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                         logout_user)

import helpers.connection as db
import helpers.google_api as g_api
import helpers.restaurant as hres
from helpers.auth import (add_user, check_password, check_username,
                          get_user_id, get_username, match_password,
                          user_exists)

import json
from requests.exceptions import HTTPError, RequestException


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


@app.route("/restaurants", methods=['GET', 'POST'])
def show_restaurants():
    try:         
        api_key = os.getenv('GCLOUD_KEY', 
                            '')
        if not api_key:
            app.logger.error("API key is empty")
            return jsonify({'error': 'API key is empty'}), 400
        
        # Default data
        default_data = {
            'place_id': 'ChIJz-VvsdMEdkgR1lQfyxijRMw',
            'name': 'Default: China Town'#,
            #'user_id': 'user_id-2023-london_eye'
        }

        # Handling for POST request
        if request.method == 'POST':
            routes_data = request.get_json() or {}
            place_id = routes_data.get('place_id', default_data['place_id'])
            address = routes_data.get('name', default_data['name'])           
        else:
            # For a GET request, use query parameters
            place_id = request.args.get('place_id', default_data['place_id'])
            address = request.args.get('name', default_data['name'])

        keyword_string, price, dist, open_q = hres.parse_request_parameters()

        #details return to the Jinja
        search_details = {
            'place_id' : place_id,
            'address': address,
            'keyword': keyword_string,
            'price': price,
            'dist': dist,
            'open' : open_q
        }  
        
        lat, lng = hres.fetch_place_details(api_key, place_id)
        if not lat or not lng:
            return 'Failed to retrieve place details', 500        

       # Search nearby restaurants
        nearby_data = hres.search_nearby_restaurants(api_key, lat, lng, keyword_string, dist, price, open_q)
        if 'status' not in nearby_data or nearby_data['status'] != 'OK':
            return 'Failed to retrieve data', 500

        # Process and sort restaurants
        all_restaurants = hres.process_restaurant_data(nearby_data)
        top_restaurants_dict = hres.sort_and_slice_restaurants(all_restaurants)

        # Fetch additional details
        top_restaurants_dict = hres.fetch_additional_details(api_key, top_restaurants_dict)

    except HTTPError as e:
        # This will catch HTTP errors, which occur when HTTP request returned an unsuccessful status code
        app.logger.exception("HTTP Error occurred")
        return jsonify({'error': str(e)}), 500
    except json.JSONDecodeError as e:
        app.logger.exception("JSON Decode Error")
        return jsonify({'error': 'Invalid JSON response'}), 500
    except RequestException as e:
        # This will catch any other exception thrown by the requests library (such as a connection error)
        app.logger.exception("Network-related error occurred")
        return jsonify({'error': str(e)}), 500    
    except Exception as e:    
        app.logger.exception("An unexpected error occurred")
        return jsonify({'error': str(e)}), 500

    # Prepare data for map generation
    restaurant_data = [
        {
            'name': details['name'],
            'lat': details['latitude'],
            'lng': details['longitude'],
            'website_url': details['website'],
            'image_url': details['photo_url'],
            'ratings': details['rating']
        }
        for name, details in top_restaurants_dict.items()
    ]
    
    # Generate map HTML using to_do lat and logn
    map_html = hres.generate_map(restaurant_data, lat, lng, dist) 

    return render_template("restaurants.html", restaurants=top_restaurants_dict, map_html=map_html, search_details=search_details)


@app.route('/save-restaurant', methods=['POST'])
def save_restaurant():
    return {'status': 'success'}
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        data = request.json
        user_info = session['user_id']  # Retrieve user_id from session
        username, location_query, date = user_info.split('-')  # Splitting the string

        conn, cursor = db.connect_to_db()

        # Step 1: Check if the row exists
        check_query = "SELECT COUNT(*) FROM table1 WHERE place_id = %s"
        cursor.execute(check_query, (data['place_id'],))
        count = cursor.fetchone()[0]

        # Step 2: Update or Insert based on the check
        if count > 0:
            # Update
            update_query = """
                UPDATE table1
                SET name = %s, ratings = %s, rating_count = %s, search_link = %s, photo_reference = %s, editorial_summary = %s
                WHERE place_id = %s
            """
            cursor.execute(update_query, (data['name'], data['ratings'], data['rating_count'], data['search_link'], data['photo_reference'], data['editorial_summary'], data['place_id']))
        else:
            # Insert
            insert_query = """
                INSERT INTO table1 (place_id, name, ratings, rating_count, search_link, photo_reference, editorial_summary)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (data['place_id'], data['name'], data['ratings'], data['rating_count'], data['search_link'], data['photo_reference'], data['editorial_summary']))

        # # Will this change the auto increment count.
        # # Insert/update data in the first table
        # sql_table1 = """
        #     INSERT INTO table1 (place_id, name, ratings, rating_count, search_link, photo_reference, editorial_summary)
        #     VALUES (%s, %s, %s, %s, %s, %s, %s)
        #     ON DUPLICATE KEY UPDATE 
        #     name=VALUES(name), ratings=VALUES(ratings), rating_count=VALUES(rating_count),
        #     search_link=VALUES(search_link), photo_reference=VALUES(photo_reference), editorial_summary=VALUES(editorial_summary)
        # """
        # cursor.execute(sql_table1, (data['place_id'], data['name'], data['ratings'], 
        #                             data['rating_count'], data['search_link'], 
        #                             data['photo_reference'], data['editorial_summary']))
        # # Insert/update data in the second table
        # sql_table2 = """
        #     INSERT INTO table2 (Username, location_query, date, place_id)
        #     VALUES (%s, %s, %s, %s)
        #     ON DUPLICATE KEY UPDATE 
        #     location_query=VALUES(location_query), date=VALUES(date)
        # """
        # cursor.execute(sql_table2, (username, location_query, date, data['place_id']))

        # Step 1: Check if the row exists
        # Or could use: "SELECT EXISTS(SELECT 1 FROM table2 WHERE Username = %s AND place_id = %s)"
        # instead of count have exists and then if exists = update, else insert.
        check_query = "SELECT COUNT(*) FROM table2 WHERE Username = %s AND place_id = %s"
        cursor.execute(check_query, (data['Username'], data['place_id']))
        count = cursor.fetchone()[0]

        # Step 2: Update or Insert based on the check
        #   IS THE USERNAME AND DATE A UNIQUE COMBO/THE COMBO WE WANT?
        if count > 0:
            # Update
            update_query = """
                UPDATE table2
                SET location_query = %s, date = %s
                WHERE Username = %s AND place_id = %s
            """
            cursor.execute(update_query, (data['location_query'], data['date'], data['Username'], data['place_id']))
        else:
            # Insert
            insert_query = """
                INSERT INTO table2 (Username, location_query, date, place_id)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (data['Username'], data['location_query'], data['date'], data['place_id']))

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
    return {'status': 'success'}
    if 'user_id' not in session:
        # User is not logged in, redirect to login page
        return redirect(url_for('login'))

    data = request.json
    user_info = session['user_id']  # Retrieve user_id from session
    username, location_query, date = user_info.split('-')  # Splitting the string

    try:
        conn, cursor = db.connect_to_db()

        # Delete the entry from the second table
        sql_delete_table2 = "DELETE FROM table2 WHERE Username = %s AND location_query = %s AND date = %s AND place_id = %s"
        cursor.execute(sql_delete_table2, (username, location_query, date, data['place_id']))

        # Check if there are no more references to the place_id in the second table before deleting from the first table
        sql_check = "SELECT COUNT(*) FROM table2 WHERE place_id = %s"
        cursor.execute(sql_check, (data['place_id'],))
        #no more rows in table2 with place_id reference.
        if cursor.fetchone()[0] == 0:
            # Delete the entry from the first table if no more references are found
            sql_delete_table1 = "DELETE FROM table1 WHERE place_id = %s"
            cursor.execute(sql_delete_table1, (data['place_id'],))

        conn.commit()

    except Exception as e:
        conn.rollback()  # Rollback the transaction in case of an error
        logging.error(e)  # Log the error
        return {'status': 'error', 'message': str(e)}

    finally:
        cursor.close()
        conn.close()

    return {'status': 'success', 'message': 'Operation completed successfully'}

# @app.route("/restaurants", methods=["POST"])
# def restaurants():
#     # Parse data from form
#     request_data = {
#         "destination": request.form.get("destination"),
#         "date": request.form.get("date"),
#     }

#     load_dotenv()
#     api_key = os.environ.get("GCLOUD_KEY")
#     lat, lng = g_api.get_coordinates(request_data["destination"], api_key)

#     if lat is not None and lng is not None:
#         center = (lat, lng)
#         restaurants = g_api.get_restaurants(lat, lng, 1000,
#                                             None, True, api_key)

#     # restaurants = db.is_restaurant_saved(restaurants)
#     print(restaurants)

#     return render_template("restaurants.html",
#                            restaurants=restaurants, center=center)
