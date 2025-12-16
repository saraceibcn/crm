from flask import Blueprint, jsonify
from backend.utils.db import get_connection
from backend.utils.auth_middleware import admin_required, login_required

masters_bp = Blueprint("masters_bp", __name__, url_prefix="/api")

@masters_bp.route("/masters", methods=["GET"])
@login_required
def obtener_masters():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                idMaster,
                nomMaster AS nombre,
                edicio AS edicion
            FROM master
            ORDER BY nomMaster ASC, edicio ASC
        """)
        masters = cursor.fetchall()

        cursor.close()
        conn.close()
        return jsonify(masters)

    except Exception as e:
        print("❌ ERROR MASTERS:", e)
        return jsonify({"error": str(e)}), 500
