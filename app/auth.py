import bcrypt
from datetime import datetime, timedelta, timezone

MAX_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=15)

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

def verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def is_account_locked(locked_until_str) -> bool:
    if not locked_until_str:
        return False
    locked_until = datetime.fromisoformat(locked_until_str)
    return locked_until > datetime.now(timezone.utc)

def record_failed_login(conn, user_id, current_attempts):
    new_attempts = current_attempts + 1
    if new_attempts >= MAX_ATTEMPTS:
        locked_until = (datetime.now(timezone.utc) + LOCK_DURATION).isoformat()
        conn.execute(
            "UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE id = ?",
            (new_attempts, locked_until, user_id)
        )
    else:
        conn.execute(
            "UPDATE users SET failed_login_attempts = ? WHERE id = ?",
            (new_attempts, user_id)
        )
    conn.commit()

def reset_login_attempts(conn, user_id):
    conn.execute(
        "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?",
        (user_id,)
    )
    conn.commit()
    
import re

def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 10:
        return False, "Password must be at least 10 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Include at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Include at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Include at least one digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Include at least one special character"
    return True, "OK"

# def check_password_reuse(user_id, new_password, db_session, PasswordHistory, last_n=5):
#     history = db_session.query(PasswordHistory)\
#         .filter_by(user_id=user_id)\
#         .order_by(PasswordHistory.changed_at.desc())\
#         .limit(last_n).all()
#     for record in history:
#         if bcrypt.checkpw(new_password.encode(), record.password_hash):
#             return False  # reused
#     return True

