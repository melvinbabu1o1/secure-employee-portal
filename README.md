# Secure Employee Management Portal

A Flask-based employee management system built to demonstrate secure coding practices: input validation, output encoding, secure authentication, password security, injection protection, logging & monitoring, and attack simulation testing.

---

## Prerequisites

- Python 3.11+ installed and added to PATH
- Git (optional, if cloning this repo)

---

## Setup

**1. Clone or download this repository, then move into the project folder:**
```powershell
cd secure_employee_portal
```

**2. Create and activate a virtual environment:**
```powershell
python -m venv venv
venv\Scripts\activate
```
> Mac/Linux: `source venv/bin/activate`

**3. Install dependencies:**
```powershell
pip install -r requirements.txt
```

**4. Create a `.env` file** in the project root with:
```
SECRET_KEY=change-this-to-a-random-string
FLASK_ENV=development
```

**5. Initialize the database** (only needed once, or after deleting `employee_portal.db`):
```powershell
python init_db.py
```

---

## Running the App

```powershell
python run.py
```

Open your browser to:
```
http://127.0.0.1:5000
```

You'll land on the login page. Use the **Register** link to create an account, then log in to reach the dashboard, where you can add employees and export employee data.

---

## Project Structure

```
secure_employee_portal/
├── app/
│   ├── __init__.py          Application factory, blueprint registration
│   ├── auth.py               Password hashing, lockout logic
│   ├── validators.py         Input validation engine
│   ├── db.py                 Database connection helper
│   ├── decorators.py         @login_required session guard
│   ├── logging_config.py     Security event logger
│   ├── safe_exec.py          Safe subprocess wrapper (export feature)
│   ├── templates/            Login, register, dashboard pages
│   ├── static/style.css
│   └── routes/
│       ├── auth_routes.py    /register, /login, /logout
│       └── employee_routes.py /employee, /employees, /employees/export
├── attack_simulation/        Standalone attack test scripts (see below)
├── logs/security.log         Security event log (created at runtime)
├── exports/                  Generated exports (created at runtime)
├── config.py
├── init_db.py
└── run.py
```

---

## Running the Attack Simulation Scripts

These scripts test the app's defenses by sending real attack payloads to the running server. **The server must already be running (`python run.py`) in a separate terminal before running any of these.**

Open a **second terminal**, activate the virtual environment there too, then run:

```powershell
venv\Scripts\activate

python attack_simulation\sql_injection_test.py
python attack_simulation\xss_test.py
python attack_simulation\command_injection_test.py
python attack_simulation\unicode_obfuscation_test.py
```

Run `brute_force_test.py` **last**, since it intentionally locks the test account for 15 minutes:
```powershell
python attack_simulation\brute_force_test.py
```

Each script prints the payload sent, the server's response, and whether the attack was blocked.

> **Note:** these scripts only target `http://127.0.0.1:5000` — your own local instance. Never point them at any server you don't own.

---

## Manual Demo (Live in Browser)

For a live walkthrough instead of running scripts, try these directly in the UI:

**1. SQL Injection — on the Login page**
Username: `' OR '1'='1`, any password → rejected with a generic error, not logged in.

**2. Brute Force Lockout — on the Login page**
Enter a wrong password 5 times for a real account → 6th attempt (even with the correct password) is rejected as locked for 15 minutes.

**3. XSS — on the Dashboard, "Add Employee" form**
Full Name: `<script>alert('XSS')</script>` → appears as harmless plain text in the employee table, not an alert popup.

**4. Command Injection — on the Dashboard, "Export" form**
Archive name: `report; rm -rf exports` → rejected immediately with "Invalid archive name."

While demoing, keep `logs/security.log` open in a text editor — it updates in real time as each attempt is logged.

---

## Requirements Coverage

| # | Requirement | Where implemented |
|---|---|---|
| 1 | Secure registration & login | `app/routes/auth_routes.py`, `app/auth.py` |
| 2 | Input validation engine | `app/validators.py` |
| 3 | Unicode/obfuscated input handling | `app/validators.py` (`normalize_input`, ASCII check) |
| 4 | XSS prevention | `html.escape()` in `employee_routes.py` + Jinja2 auto-escaping |
| 5 | SQL injection protection | Parameterized queries throughout `app/db.py` usage |
| 6 | OS command injection prevention | `app/safe_exec.py`, `/employees/export` |
| 7 | Password & identity security | `app/auth.py` (bcrypt, lockout policy) |
| 8 | Centralized authentication | `app/auth.py`, `app/decorators.py` |
| 9 | Logging & monitoring | `app/logging_config.py` |
| 10 | Attack simulation folder | `attack_simulation/` |

---

## Security Notes

- `.env`, `employee_portal.db`, `venv/`, `logs/*.log`, and `exports/` are excluded from version control via `.gitignore` — they contain secrets, credentials, or generated data that should never be committed.
- Passwords are never stored or logged in plain text.
- This project is for educational purposes; before any production use, review session cookie settings in `config.py` (e.g. enable `SESSION_COOKIE_SECURE` once served over HTTPS).
