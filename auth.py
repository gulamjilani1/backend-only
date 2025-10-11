from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import User

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password required"}), 400

    user = User.get_or_none(User.username == data["username"])
    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    login_user(user)
    return jsonify({"message": "Login successful", "user_id": user.id})

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"})

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password required"}), 400

    if User.get_or_none(User.username == data["username"]):
        return jsonify({"error": "Username already exists"}), 400

    hashed_pw = generate_password_hash(data["password"])
    user = User.create(username=data["username"], password=hashed_pw)
    return jsonify({"message": "User registered successfully", "user_id": user.id})
