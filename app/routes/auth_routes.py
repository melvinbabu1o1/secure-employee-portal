from flask import Blueprint, request, jsonify, session, render_template
from app.db import get_db_connection
from app.validators import validate_username, validate_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username', '')
    email = request.form.get('email', '')
    password = request.form.get('password', '')

    # Step A: validate every field before touching the database
    if not validate_username(username):
        return jsonify({"error": "Invalid username. Use 3-20 letters/numbers/underscores."}), 400

    if not validate_email(email):
        return jsonify({"error": "Invalid email format."}), 400

    if len(password) < 10:
        return jsonify({"error": "Password must be at least 10 characters."}), 400

    # Step B: hash the password — never store it in plain text
    password_hash = hash_password(password)

    # Step C: insert into the database using a parameterized query (SQLi-safe)
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"error": "Username or email already exists."}), 409

    conn.close()
    return jsonify({"message": "Registration successful."}), 201

from app.auth import hash_password, verify_password, is_account_locked, record_failed_login, reset_login_attempts
from app.logging_config import security_logger

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    if user is None:
        conn.close()
        security_logger.warning(f"Failed login: unknown username '{username}'")
        return jsonify({"error": "Invalid username or password."}), 401

    if is_account_locked(user['locked_until']):
        conn.close()
        security_logger.warning(f"Login blocked: account locked for user_id={user['id']}")
        return jsonify({"error": "Account locked. Try again later."}), 403

    if not verify_password(password, user['password_hash']):
        record_failed_login(conn, user['id'], user['failed_login_attempts'])
        conn.close()
        security_logger.warning(f"Failed login: wrong password for user_id={user['id']}")
        return jsonify({"error": "Invalid username or password."}), 401

    reset_login_attempts(conn, user['id'])
    conn.close()
    security_logger.info(f"Successful login: user_id={user['id']}")
    session['user_id'] = user['id']
    session['username'] = user['username']
    return jsonify({"message": "Login successful."}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out."}), 200