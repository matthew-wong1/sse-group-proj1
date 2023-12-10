import bcrypt
import psycopg2
import requests
import json
from flask_login import UserMixin

from helpers.connection import connect_to_db

GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration")

# User class
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username


# Retrieve Google's provider config
# ADD ERROR HADNLING TO API CALL LATER
def get_google_provider_config():
    try:
        return requests.get(GOOGLE_DISCOVERY_URL).json()
    except (Exception) as google_api_error:
        raise google_api_error


# Sign-up check to see if the username is valid
def check_username(username, errors):
    if not username:
        errors['username'] = 'Please enter a username'
    elif user_exists(username):
        errors['username'] = 'Username already taken'


# Checks if a given username already exists in the table of users
def user_exists(username):
    conn = None
    cursor = None
    result = None
    try: 
        conn, cursor = connect_to_db()

        cursor.execute("""SELECT username
                        FROM users
                        WHERE username=%s""", [username])
        result = cursor.fetchone()
    except (Exception, psycopg2.Error) as db_error:
        raise db_error

    finally:
        if conn:
            cursor.close()
            conn.close()

    return result is not None
    


# Gets the id of a user from their username
def get_user_id(username):
    conn = None
    cursor = None
    result = None

    try:
        conn, cursor = connect_to_db()

        cursor.execute("""SELECT id
            FROM users
            WHERE username=%s""", [username])
        result = cursor.fetchone()

    except (Exception, psycopg2.Error) as db_error:
        raise db_error

    finally:
        if conn:
            cursor.close()
            conn.close()

    return result[0]


# Gets the username of a user from their id
def get_username(user_id):
    conn = None
    cursor = None
    result = None

    try:
        conn, cursor = connect_to_db()

        cursor.execute("""SELECT username
            FROM users
            WHERE id=%s""", [user_id])
        result = cursor.fetchone()

    except (Exception, psycopg2.Error) as db_error:
        raise db_error
    
    finally:
        if conn:
            cursor.close()
            conn.close()

    return result[0]


# Check if password is valid (matches requirements and confirmation password)
def check_password(password, another_password, errors):
    if not password:
        errors['password'] = 'Please enter a password'
    elif len(password) < 8:
        errors['password'] = 'Your password must be at least 8 characters long'

    if password != another_password:
        errors['confirmation'] = 'Passwords do not match'


# Checks if the provided password matches the one stored in the database
# for the specified username
def match_password(username, password):
    conn = None
    cursor = None
    result = None

    try:
        conn, cursor = connect_to_db()

        cursor.execute("""SELECT password
            FROM users
            WHERE username=%s""", [username])
        result = cursor.fetchone()

    except (Exception, psycopg2.Error) as db_error:
        raise db_error
    
    finally:
        if conn:
            cursor.close()
            conn.close()

    return bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8'))


# Salts and hashes a password
def salt_and_hash(password):
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(bytes, salt)
    return hash.decode('utf-8')


# Adds a user to the database
def add_user(username, password):
    hash = salt_and_hash(password)
    params = (username, hash)

    conn = None
    cursor = None

    try:
        conn, cursor = connect_to_db()

        cursor.execute("""INSERT
            INTO users (username, password)
            VALUES (%s, %s)""", params)

    except (Exception, psycopg2.Error) as db_error:
        raise db_error
    else:
        if (cursor.rowcount == 1):
            conn.commit()
    finally:
        if conn:
            cursor.close()
            conn.close()


# Updates a user's password
def update_user(user_id, password):
    hash = salt_and_hash(password)
    params = (hash, user_id)

    conn = None
    cursor = None

    try:
        conn, cursor = connect_to_db()
        

        cursor.execute("""UPDATE users
            SET password=%s
            WHERE id=%s""", params)
        

    except (Exception, psycopg2.Error) as db_error:
        raise db_error
    else:
        if (cursor.rowcount == 1):
            conn.commit()
    finally:
        if conn:
            cursor.close()
            conn.close()
