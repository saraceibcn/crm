from flask import Blueprint, request, jsonify
from backend.utils.db import get_connection
from backend.utils.auth_middleware import admin_required
import bcrypt

users_sistema_bp = Blueprint("users_sistema_bp", __name__, url_prefix="/api")


# OBTENER USUARIOS DEL SISTEMA
@users_sistema_bp.route("/users", methods=["GET"])
@admin_required
def get_users_sistema():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT idUsuarioSistema, username, rol, activo
        FROM usuario_sistema
    """)

    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data), 200



# CREAR USUARIO DEL SISTEMA
@users_sistema_bp.route("/users", methods=["POST"])
@admin_required
def crear_usuario_sistema():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")
    rol = data.get("rol", "normal")
    activo = data.get("activo", True)

    if not username or not password:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuario_sistema (username, password_hash, rol, activo)
            VALUES (%s, %s, %s, %s)
        """, (username, password_hash, rol, activo))

        conn.commit()
        return jsonify({"mensaje": "Usuario creado correctamente"}), 201

    except Exception as e:
        print("ERROR creando usuario:", e)
        return jsonify({"error": "Error al crear usuario"}), 500

    finally:
        cursor.close()
        conn.close()


# EDITAR USUARIO DEL SISTEMA
@users_sistema_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def editar_usuario_sistema(user_id):
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")
    rol = data.get("rol")
    activo = data.get("activo")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if password:
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()
            cursor.execute("""
                UPDATE usuario_sistema
                SET username=%s, password_hash=%s, rol=%s, activo=%s
                WHERE idUsuarioSistema=%s
            """, (username, password_hash, rol, activo, user_id))
        else:
            cursor.execute("""
                UPDATE usuario_sistema
                SET username=%s, rol=%s, activo=%s
                WHERE idUsuarioSistema=%s
            """, (username, rol, activo, user_id))

        conn.commit()
        return jsonify({"mensaje": "Usuario actualizado correctamente"}), 200

    except Exception as e:
        print("ERROR editando usuario:", e)
        return jsonify({"error": "Error al editar usuario"}), 500

    finally:
        cursor.close()
        conn.close()
