# backend/blueprints/postulados.py
from flask import Blueprint, request, jsonify
from backend.utils.db_session import DBSession
from backend.utils.query_helpers import (
    aplicar_filtros_basicos,
    aplicar_filtros_atributos,
    cargar_atributos,
)
from backend.utils.logger import registrar_historial
from backend.utils.auth_middleware import login_required

postulados_bp = Blueprint("postulados_bp", __name__, url_prefix="/api")


@postulados_bp.route("/postulados", methods=["GET"])
@login_required
def listar_postulados():
    """
    Solo POSTULADOS, con:
      - máster de interés (nomMaster) en 'master'
      - filtros normales + dinámicos
      - atributos dinámicos en 'atributos'
    """
    try:
        params = request.args.to_dict()

        mapa = {
            "nombre":  "u.nombreUsuario LIKE %s",
            "telefono": "u.telefon LIKE %s",
            "mail":    "u.mail LIKE %s",
            "master":  "m.nomMaster = %s",
            "interes_master": "m.nomMaster = %s",
            "edicion": "m.edicio = %s",
        }

        filtros, valores = aplicar_filtros_basicos(params, mapa)
        filtros, valores = aplicar_filtros_atributos(
            params,
            filtros,
            valores,
            claves_reservadas=set(mapa.keys()),
        )

        query = """
            SELECT 
                u.idUsuario AS id,
                u.nombreUsuario AS nombre,
                u.mail,
                u.telefon AS telefono,
                GROUP_CONCAT(DISTINCT m.nomMaster SEPARATOR ', ') AS master
            FROM postulado p
            JOIN usuario u ON u.idUsuario = p.idUsuario
            JOIN master  m ON m.idMaster = p.idInteresMaster
            WHERE 1 = 1
        """

        if filtros:
            query += " AND " + " AND ".join(filtros)

        query += """
            GROUP BY u.idUsuario, u.nombreUsuario, u.mail, u.telefon
            ORDER BY u.nombreUsuario ASC
        """

        with DBSession() as db:
            db.execute(query, valores)
            rows = db.fetchall()

            if not rows:
                return jsonify([]), 200

            ids = [r["id"] for r in rows]
            attrs = cargar_atributos(db, ids)

            for r in rows:
                r["atributos"] = attrs.get(r["id"], {})

        return jsonify(rows), 200

    except Exception as e:
        print("❌ ERROR /postulados GET:", e)
        return jsonify({"error": str(e)}), 500

# CREAR POSTULADO
@postulados_bp.route("/postulados", methods=["POST"])
@login_required
def crear_postulado():
    """
    Crea un usuario con estado 'postulado' + entrada en tabla postulado.
    El máster se guarda por id, pero en el historial NO se muestra la edición.
    """
    try:
        data = request.json or {}

        nombre = (data.get("nombreUsuario") or data.get("nombre") or "").strip()
        mail = (data.get("mail") or "").strip()
        telefono = (data.get("telefon") or data.get("telefono") or "").strip()
        id_master = data.get("idMaster")

        if not all([nombre, mail, telefono, id_master]):
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        with DBSession() as db:
            # Usuario base
            db.execute(
                """
                INSERT INTO usuario (nombreUsuario, mail, telefon, estado)
                VALUES (%s, %s, %s, 'postulado')
                """,
                (nombre, mail, telefono),
            )
            id_usuario = db.lastrowid

            # Postulado
            db.execute(
                """
                INSERT INTO postulado (idUsuario, idInteresMaster, fecha_interes)
                VALUES (%s, %s, NOW())
                """,
                (id_usuario, id_master),
            )

            # Nombre del máster (sin edición)
            db.execute(
                "SELECT nomMaster FROM master WHERE idMaster = %s",
                (id_master,),
            )
            row = db.fetchone()
            nombre_master = row["nomMaster"] if row else str(id_master)

        detalle = f"Alta de potencial con interés en máster {nombre_master}"
        registrar_historial(id_usuario, "Postulado creado", detalle)

        return jsonify({"mensaje": "Postulado creado correctamente", "id": id_usuario}), 201

    except Exception as e:
        print("❌ ERROR /postulados POST:", e)
        return jsonify({"error": str(e)}), 500
