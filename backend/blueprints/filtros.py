from flask import Blueprint, request, jsonify
from backend.utils.db_session import DBSession
from backend.utils.auth_middleware import login_required

filtros_bp = Blueprint("filtros_bp", __name__, url_prefix="/api")


@filtros_bp.route("/ediciones", methods=["GET"])
@login_required
def obtener_ediciones():
    try:
        with DBSession() as db:
            db.execute("SELECT DISTINCT edicio FROM master ORDER BY edicio")
            rows = db.fetchall()

        ediciones = [row["edicio"] for row in rows]
        return jsonify(ediciones), 200

    except Exception as e:
        print("❌ ERROR /ediciones:", e)
        return jsonify({"error": "Error obteniendo ediciones"}), 500


@filtros_bp.route("/atributos-list", methods=["GET"])
@login_required
def obtener_atributos():
    try:
        with DBSession() as db:
            db.execute("SELECT nombre FROM atributos ORDER BY nombre")
            rows = db.fetchall()

        atributos = [row["nombre"] for row in rows]
        return jsonify(atributos), 200

    except Exception as e:
        print("❌ ERROR /atributos-list:", e)
        return jsonify({"error": "Error obteniendo atributos dinámicos"}), 500


@filtros_bp.route("/atributos", methods=["POST"])
@login_required
def crear_atributo():
    try:
        data = request.get_json() or {}
        nombre = data.get("nombre")

        if not nombre:
            return jsonify({"error": "Nombre obligatorio"}), 400

        with DBSession() as db:
            db.execute(
                "INSERT INTO atributos (nombre) VALUES (%s)",
                (nombre,),
            )

        return jsonify({"mensaje": "Atributo creado"}), 201

    except Exception as e:
        print("❌ ERROR /atributos POST:", e)
        return jsonify({"error": "Error creando atributo"}), 500
