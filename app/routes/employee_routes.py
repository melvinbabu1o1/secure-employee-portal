import csv
import os
from flask import Blueprint, request, jsonify, session, send_file, render_template, redirect, url_for
from app.db import get_db_connection
from app.decorators import login_required
from app.validators import validate_age, validate_salary, validate_phone, validate_department, validate_export_filename
from app.safe_exec import safe_compress_file
from app.logging_config import security_logger
import html

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/employee', methods=['POST'])
@login_required
def create_employee():
    full_name = request.form.get('full_name', '').strip()
    age = request.form.get('age', '')
    salary = request.form.get('salary', '')
    phone = request.form.get('phone', '')
    department = request.form.get('department', '')

    if not full_name or len(full_name) > 100:
        return jsonify({"error": "Full name is required and must be under 100 characters."}), 400
    if not validate_age(age):
        return jsonify({"error": "Age must be between 18 and 100."}), 400
    if not validate_salary(salary):
        return jsonify({"error": "Invalid salary."}), 400
    if not validate_phone(phone):
        return jsonify({"error": "Phone number must be 10-13 digits."}), 400
    if not validate_department(department):
        return jsonify({"error": "Invalid department."}), 400

    # Contextual output encoding: escape before storing, so it's always
    # safe no matter where it's later rendered (Requirement #4)
    safe_full_name = html.escape(full_name)

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO employees (user_id, full_name, age, salary, phone_number, department) VALUES (?, ?, ?, ?, ?, ?)",
        (session['user_id'], safe_full_name, age, salary, phone, department)
    )
    conn.commit()
    conn.close()

    security_logger.info(f"Employee record created by user_id={session['user_id']}")
    return jsonify({"message": "Employee record created."}), 201


@employee_bp.route('/employees', methods=['GET'])
@login_required
def list_employees():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM employees WHERE user_id = ?", (session['user_id'],)).fetchall()
    conn.close()

    employees = [dict(row) for row in rows]
    return jsonify(employees), 200

@employee_bp.route('/employees/export', methods=['POST'])
@login_required
def export_employees():
    archive_name = request.form.get('archive_name', '')

    if not validate_export_filename(archive_name):
        return jsonify({"error": "Invalid archive name. Use only letters, numbers, - and _, max 50 chars."}), 400

    os.makedirs('exports', exist_ok=True)

    # Step 1: generate CSV using Python's csv module — no subprocess involved here,
    # this part carries no command injection risk at all
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM employees WHERE user_id = ?", (session['user_id'],)).fetchall()
    conn.close()

    csv_path = f"exports/employees_{session['user_id']}.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'full_name', 'age', 'salary', 'phone_number', 'department', 'created_at'])
        for row in rows:
            writer.writerow([row['id'], row['full_name'], row['age'], row['salary'],
                              row['phone_number'], row['department'], row['created_at']])

    # Step 2: compress it via subprocess, using the user-supplied (validated) archive name
    result, archive_path = safe_compress_file(csv_path, archive_name)

    if result.returncode != 0:
        security_logger.warning(f"Export compression failed for user_id={session['user_id']}: {result.stderr}")
        return jsonify({"error": "Export failed."}), 500

    security_logger.info(f"Employee export created by user_id={session['user_id']}: {archive_path}")
    return jsonify({"message": "Export created.", "file": archive_path}), 201


@employee_bp.route('/employees/download/<archive_name>', methods=['GET'])
@login_required
def download_export(archive_name):
    if not validate_export_filename(archive_name):
        return jsonify({"error": "Invalid archive name."}), 400

    archive_path = f"exports/{archive_name}.tar.gz"
    if not os.path.exists(archive_path):
        return jsonify({"error": "File not found."}), 404

    return send_file(archive_path, as_attachment=True)

@employee_bp.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')