import sqlite3

def get_db_connection():
    conn = sqlite3.connect('employee_portal.db')
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn