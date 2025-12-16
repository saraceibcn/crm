from flask import Blueprint, request, jsonify, current_app
import jwt
import datetime
import bcrypt
from backend.utils.db import get_connection

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api")


# ============================
# GENERAR TOKEN UNIFICADO
# ============================
def generar_token(usuario):
    payload = {
        "id": usuario["idUsuarioSistema"],
        "username": usuario["username"],
        "email": usuario["email"],        # <--- IMPORTANT
        "rol": usuario["rol"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }

    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
    return token


# LOGIN ÚNIC
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Usuario y contraseña requeridos"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT idUsuarioSistema, username, password_hash, rol, email
        FROM usuario_sistema
        WHERE username = %s
    """, (username,))

    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return jsonify({"error": "Contraseña incorrecta"}), 401

    token = generar_token(user)

    print(">>> LOGIN EJECUTADO (blueprints/auth.py) <<<")

    return jsonify({
        "mensaje": "Login correcto",
        "token": token,
        "rol": user["rol"]
    }), 200
