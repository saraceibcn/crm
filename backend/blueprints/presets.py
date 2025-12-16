from flask import Blueprint, request, jsonify
from backend.utils.db_session import DBSession
from backend.utils.auth_middleware import login_required
import json

presets_bp = Blueprint("presets_bp", __name__, url_prefix="/api/presets")


# GET — Cargar presets del usuario (por tipo opcional)
@presets_bp.route("/", methods=["GET"])
@login_required
def obtener_presets():
    user_id = request.user["id"]
    tipo = request.args.get("tipo")  # alumnos / potenciales / todos / sistema

    try:
        query = """
            SELECT idPreset, nombre, tipo, filtros, filtrosAtributos
            FROM preset_filtros
            WHERE idUsuarioSistema = %s
        """
        valores = [user_id]

        if tipo:
            query += " AND tipo = %s"
            valores.append(tipo)

        with DBSession() as db:
            db.execute(query, valores)
            presets = db.fetchall()

        return jsonify(presets), 200

    except Exception as e:
        print("❌ ERROR /presets GET:", e)
        return jsonify({"error": "Error obteniendo presets"}), 500



# POST — Crear preset
@presets_bp.route("/", methods=["POST"])
@login_required
def crear_preset():
    try:
        data = request.get_json() or {}
        user_id = request.user["id"]

        nombre = data.get("nombre")
        tipo = data.get("tipo")
        filtros = data.get("filtros", {})
        filtros_atributos = data.get("filtrosAtributos", [])

        if not nombre or not tipo:
            return jsonify({"error": "Nombre y tipo son obligatorios"}), 400

        with DBSession() as db:
            db.execute(
                """
                INSERT INTO preset_filtros (
                    idUsuarioSistema, nombre, tipo, filtros, filtrosAtributos
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    nombre,
                    tipo,
                    json.dumps(filtros),
                    json.dumps(filtros_atributos),
                ),
            )

        return jsonify({"mensaje": "Preset guardado"}), 201

    except Exception as e:
        print("❌ ERROR /presets POST:", e)
        return jsonify({"error": "Error guardando preset"}), 500



# DELETE — Eliminar un preset
@presets_bp.route("/<int:idPreset>", methods=["DELETE"])
@login_required
def eliminar_preset(idPreset):
    user_id = request.user["id"]

    try:
        with DBSession() as db:
            db.execute(
                """
                DELETE FROM preset_filtros
                WHERE idPreset = %s AND idUsuarioSistema = %s
                """,
                (idPreset, user_id),
            )

        return jsonify({"mensaje": "Preset eliminado"}), 200

    except Exception as e:
        print("❌ ERROR /presets DELETE:", e)
        return jsonify({"error": "Error eliminando preset"}), 500
