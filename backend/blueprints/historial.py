from flask import Blueprint, jsonify
from backend.utils.db import get_connection
from backend.utils.auth_middleware import admin_required, login_required

historial_bp = Blueprint("historial_bp", __name__, url_prefix="/api")


@historial_bp.route("/usuario/<int:id>/historial", methods=["GET"])
@login_required
def obtener_historial(id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT accion, detalle, fecha
            FROM usuario_historial
            WHERE idUsuario = %s
            ORDER BY fecha DESC
        """, (id,))

        registros = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(registros), 200

    except Exception as e:
        print("❌ ERROR historial:", e)
        return jsonify({"error": str(e)}), 500
