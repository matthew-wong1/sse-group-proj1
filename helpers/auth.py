import bcrypt

from helpers.connection import connect_to_db


def check_username(username, errors):
    if not username:
        errors['username'] = 'Please enter a username'
    elif user_exists(username):
        errors['username'] = 'Username already taken'


def user_exists(username):
    conn, cursor = connect_to_db()

    cursor.execute("""SELECT username FROM users""")
    rec = cursor.fetchone()

    conn.close()

    return username in rec


# Check if password is valid (matches requirements and confirmation password)
def check_password(password, errors):
    if not password:
        errors['password'] = 'Please enter a password'
    elif len(password) < 8:
        errors['password'] = 'Your password must be at least 8 characters long'


def check_repeat(password, repeat_password, errors):
    if password != repeat_password:
        errors['repeat_password'] = 'Passwords do not match'


def salt_and_hash(password):
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(bytes, salt)


def add_user(username, password):
    hash = salt_and_hash(password)
    params = (username, hash)

    conn, cursor = connect_to_db()

    cursor.execute("""INSERT
        INTO users (username, password)
        VALUES (%s, %s)""", params)
    conn.commit()
