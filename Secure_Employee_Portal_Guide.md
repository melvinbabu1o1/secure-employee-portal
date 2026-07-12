# Secure Employee Management Portal — Step-by-Step Build Guide

**Stack:** Python 3.x, Flask, SQLite, bcrypt, Python `logging` module
(Swap Flask→Django or SQLite→MySQL later — the security patterns stay the same.)

---

## Phase 0 — Project Setup

```
secure_employee_portal/
│
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # DB models
│   ├── auth.py              # Centralized authentication logic
│   ├── validators.py        # Input validation engine
│   ├── routes/
│   │   ├── auth_routes.py   # register/login/logout
│   │   └── employee_routes.py
│   ├── templates/           # Jinja2 (auto-escapes → XSS defense)
│   ├── static/
│   └── logging_config.py
│
├── attack_simulation/       # Requirement #10 — separate, isolated
│   ├── sql_injection_test.py
│   ├── xss_test.py
│   ├── brute_force_test.py
│   └── command_injection_test.py
│
├── logs/
│   └── security.log
│
├── requirements.txt
├── config.py
└── run.py
```

Install:
```bash
pip install flask flask-login flask-wtf bcrypt python-dotenv
```

Why Jinja2 templates matter: Flask's default template engine auto-escapes HTML output, which is your first line of defense for Requirement #4.

---

## Phase 1 — Database Design

Keep it simple but realistic:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'employee',
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    full_name TEXT NOT NULL,
    age INTEGER,
    salary REAL,
    phone_number TEXT,
    department TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE password_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    password_hash TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

`password_history` is what enables Requirement #7's "password reuse prevention."

---

## Phase 2 — Input Validation Engine (Requirement #2 & #3)

Build one central `validators.py` — never validate inline in routes.

```python
import re
import unicodedata

def normalize_input(value: str) -> str:
    """Prevent Unicode homoglyph / normalization bypass attacks."""
    if value is None:
        return value
    return unicodedata.normalize('NFKC', value).strip()

def validate_username(username: str) -> bool:
    username = normalize_input(username)
    return bool(re.fullmatch(r'[A-Za-z0-9_]{3,20}', username))

def validate_email(email: str) -> bool:
    email = normalize_input(email)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.fullmatch(pattern, email))

def validate_age(age) -> bool:
    try:
        age = int(age)
        return 18 <= age <= 100
    except (ValueError, TypeError):
        return False

def validate_salary(salary) -> bool:
    try:
        salary = float(salary)
        return 0 < salary <= 10_000_000
    except (ValueError, TypeError):
        return False

def validate_phone(phone: str) -> bool:
    phone = normalize_input(phone)
    return bool(re.fullmatch(r'\+?\d{10,13}', phone))

def validate_department(dept: str) -> bool:
    dept = normalize_input(dept)
    allowed = {'HR', 'Engineering', 'Sales', 'Finance', 'Operations'}
    return dept in allowed
```

**Key ideas the examiner will look for:**
- Whitelisting over blacklisting (allow known-good patterns, don't try to block "bad" ones)
- `unicodedata.normalize()` before any regex check — stops obfuscated/Unicode bypass payloads
- Reject-by-default: if validation fails, don't try to "clean" the input — reject it

---

## Phase 3 — Secure Registration & Login (Requirement #1, #8)

### Centralized auth logic (`auth.py`)
```python
import bcrypt
from datetime import datetime, timedelta

MAX_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=15)

def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

def verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def is_account_locked(user) -> bool:
    return user.locked_until and user.locked_until > datetime.utcnow()

def record_failed_login(user, db_session):
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= MAX_ATTEMPTS:
        user.locked_until = datetime.utcnow() + LOCK_DURATION
    db_session.commit()

def reset_login_attempts(user, db_session):
    user.failed_login_attempts = 0
    user.locked_until = None
    db_session.commit()
```

### Password policy (Requirement #7)
```python
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

def check_password_reuse(user_id, new_password, db_session, PasswordHistory, last_n=5):
    history = db_session.query(PasswordHistory)\
        .filter_by(user_id=user_id)\
        .order_by(PasswordHistory.changed_at.desc())\
        .limit(last_n).all()
    for record in history:
        if bcrypt.checkpw(new_password.encode(), record.password_hash):
            return False  # reused
    return True
```

Use `Flask-Login` for session management — it handles secure session cookies, `login_required` decorators, and logout invalidation correctly out of the box, rather than rolling your own.

Session cookie hardening in `config.py`:
```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 1800  # 30 min
```

---

## Phase 4 — SQL Injection Protection (Requirement #5)

Never string-format SQL. Use parameterized queries always — with raw SQLite or with an ORM (SQLAlchemy).

```python
# NEVER do this:
# cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")

# Always do this:
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

If using SQLAlchemy ORM, parameterization is automatic as long as you don't use `.execute(f"...")` or `text()` with string interpolation.

---

## Phase 5 — XSS Protection (Requirement #4)

Two layers:

1. **Auto-escaping templates** — Jinja2 does this by default. Never use `| safe` on user input.
2. **Contextual output encoding** for cases outside templates (e.g., JSON API responses, JS contexts):

```python
import html

def safe_render(user_input: str) -> str:
    return html.escape(user_input, quote=True)
```

3. **Content-Security-Policy header** as defense-in-depth:
```python
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response
```

---

## Phase 6 — OS Command Injection Prevention (Requirement #6)

If the portal ever needs to shell out (e.g., generating a report file), avoid `os.system()` entirely:

```python
import subprocess
import shlex

# NEVER: os.system(f"convert {filename} output.pdf")

# Safe: no shell=True, arguments passed as a list (no shell parsing)
def safe_convert(filename: str, output: str):
    allowed_chars = re.fullmatch(r'[\w\-.]+', filename)
    if not allowed_chars:
        raise ValueError("Invalid filename")
    subprocess.run(["convert", filename, output], check=True, timeout=10)
```

Key rule: `shell=False` (the default when you pass a list), validate/whitelist any filename or argument before it touches subprocess.

---

## Phase 7 — Logging & Monitoring (Requirement #9)

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger('security')
    handler = RotatingFileHandler('logs/security.log', maxBytes=1_000_000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

security_logger = setup_logger()

# Usage across the app:
security_logger.warning(f"Failed login attempt for username={username} from IP={request.remote_addr}")
security_logger.critical(f"Possible SQLi payload blocked: {payload} from IP={request.remote_addr}")
security_logger.warning(f"Account locked due to brute force: user_id={user.id}")
```

Log **events, not secrets** — never log passwords, tokens, or full session IDs.

---

## Phase 8 — Attack Simulation Folder (Requirement #10)

These scripts test **your own local instance only** — never point them at anything you don't own.

```python
# attack_simulation/sql_injection_test.py
import requests

TARGET = "http://localhost:5000/login"
PAYLOADS = [
    "' OR '1'='1",
    "admin'--",
    "' UNION SELECT NULL,NULL,NULL--",
]

for payload in PAYLOADS:
    r = requests.post(TARGET, data={"username": payload, "password": "x"})
    print(f"Payload: {payload} -> Status: {r.status_code}, Blocked: {'error' in r.text.lower()}")
```

```python
# attack_simulation/brute_force_test.py
import requests, time

TARGET = "http://localhost:5000/login"
for i in range(10):
    r = requests.post(TARGET, data={"username": "testuser", "password": f"wrongpass{i}"})
    print(f"Attempt {i+1}: {r.status_code}")
    if "locked" in r.text.lower():
        print("Account lockout triggered — brute force protection working.")
        break
    time.sleep(0.5)
```

Build similar scripts for `xss_test.py` (submit `<script>alert(1)</script>` into feedback fields and confirm it's rendered as escaped text, not executed) and `command_injection_test.py` (submit shell metacharacters like `; rm -rf /` and confirm they're rejected by input validation).

Document results in a short table: payload → expected block → actual result.

---

## Phase 9 — Testing Checklist Before Submission

| Test | How to verify |
|---|---|
| SQLi blocked | Run `sql_injection_test.py`, confirm no auth bypass |
| XSS blocked | Submit script tags in feedback form, confirm escaped in rendered HTML |
| Command injection blocked | Attempt shell metacharacters in any subprocess-touching field |
| Brute force lockout | 5+ failed logins → account locked |
| Password reuse blocked | Try reusing last password on change |
| Logging works | Trigger a failed login, check `logs/security.log` |
| Session security | Inspect cookies in browser dev tools — `HttpOnly`, `Secure` flags set |
| Unicode bypass | Try homoglyph username (e.g., Cyrillic 'а' vs Latin 'a') |

---

## Suggested Timeline

1. **Day 1–2:** Project scaffold, DB models, validators.py
2. **Day 3–4:** Registration/login/auth.py + password policy
3. **Day 5:** Employee CRUD routes with input validation wired in
4. **Day 6:** XSS defenses + security headers
5. **Day 7:** Logging module + wire logging calls into all routes
6. **Day 8:** Attack simulation scripts + run and document results
7. **Day 9:** Testing pass using the checklist above
8. **Day 10:** Write up a short report (architecture diagram + how each requirement was met) — most rubrics expect this alongside code

---

## Notes
- If your rubric wants Django instead: `Flask-Login` → `Django's built-in auth`, and you get CSRF protection, ORM parameterization, and template auto-escaping for free — less code to write.
- For MySQL instead of SQLite: swap the connection layer only; all validation/auth/logging code above is unchanged.
