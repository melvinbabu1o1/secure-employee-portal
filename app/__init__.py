from flask import Flask
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
        return "Secure Employee Portal — setup successful."

    return app