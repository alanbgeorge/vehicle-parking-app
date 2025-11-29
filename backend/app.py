# backend/app.py

from flask import Flask
from flask_cors import CORS

from config import Config
from extensions import db, bcrypt, init_redis_a   # ✅ import init_redis_a

# import all blueprints
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.parking_routes import parking_bp
from routes.booking_routes import booking_bp
from routes.export_routes import export_bp        # ✅ NEW import


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # allow frontend (Vue) to call this API later
    CORS(app)

    # initialise extensions (database, bcrypt, redis)
    db.init_app(app)
    bcrypt.init_app(app)
    init_redis_a(app)      # ✅ initialise Redis

    # register all blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(parking_bp, url_prefix="/parking")
    app.register_blueprint(booking_bp, url_prefix="/parking")
    app.register_blueprint(export_bp)             # ✅ export routes (already have /api/exports prefix)

    # simple test route
    @app.route("/")
    def home():
        return {"message": "Vehicle Parking System backend is running"}

    return app


if __name__ == "__main__":
    app = create_app()

    # create tables in the database if they do not exist
    with app.app_context():
        db.create_all()

    # start the development server
    app.run(debug=True)
