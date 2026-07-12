from flask import Flask, session, redirect, url_for
from config import Config
from app.routes.auth_routes import auth_bp
from app.routes.employee_routes import employee_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)

    @app.route('/')
    def home():
        if 'user_id' in session:
            return redirect(url_for('employee.dashboard'))
        return redirect(url_for('auth.login'))

    return app