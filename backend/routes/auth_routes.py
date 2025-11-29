from flask import Blueprint, request, jsonify
from extensions import db, bcrypt
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"message": "Name, email and password are required"}), 400

    # check if email already exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"message": "Email already registered"}), 400

    # hash password
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    #  decide role based on email
    # if email is admin@parking.com -> ADMIN, else USER
    role_value = "ADMIN" if email == "admin@parking.com" else "USER"

    user = User(
        name=name,
        email=email,
        password=password_hash,  # we store hashed password
        role=role_value
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Invalid email or password"}), 401

    # For simplicity we just return user details (no JWT for now)
    return jsonify(
        {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            },
        }
    ), 200
