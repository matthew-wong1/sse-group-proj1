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


def get_user_id(username):
    conn, cursor = connect_to_db()

    cursor.execute("""SELECT id
        FROM users
        WHERE username=%s""", [username])
    rec = cursor.fetchone()

    conn.close()

    return rec[0]


def get_username(user_id):
    conn, cursor = connect_to_db()

    cursor.execute("""SELECT username
        FROM users
        WHERE id=%s""", [user_id])
    rec = cursor.fetchone()

    conn.close()

    return rec[0]


# Check if password is valid (matches requirements and confirmation password)
def check_password(password, another_password, errors):
    if not password:
        errors['password'] = 'Please enter a password'
    elif len(password) < 8:
        errors['password'] = 'Your password must be at least 8 characters long'

    if password != another_password:
        errors['confirmation'] = 'Passwords do not match'


def match_password(username, password):
    conn, cursor = connect_to_db()

    cursor.execute("""SELECT password
        FROM users
        WHERE username=%s""", [username])
    rec = cursor.fetchone()

    conn.close()

    return bcrypt.checkpw(password.encode('utf-8'), rec[0].encode('utf-8'))


def salt_and_hash(password):
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(bytes, salt)
    return hash.decode('utf-8')


def add_user(username, password):
    hash = salt_and_hash(password)
    params = (username, hash)

    conn, cursor = connect_to_db()

    cursor.execute("""INSERT
        INTO users (username, password)
        VALUES (%s, %s)""", params)
    conn.commit()

    conn.close()


def update_user(user_id, password):
    hash = salt_and_hash(password)
    conn, cursor = connect_to_db()
    params = (hash, user_id)

    cursor.execute("""UPDATE users
        SET password=%s
        WHERE id=%s""", params)
    conn.commit()

    conn.close
