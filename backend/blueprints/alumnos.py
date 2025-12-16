# backend/blueprints/alumnos.py
from flask import Blueprint, request, jsonify
from backend.utils.db_session import DBSession
from backend.utils.query_helpers import (
    aplicar_filtros_basicos,
    aplicar_filtros_atributos,
    cargar_atributos,
)
from backend.utils.logger import registrar_historial
from backend.utils.auth_middleware import admin_required, login_required

alumnos_bp = Blueprint("alumnos_bp", __name__, url_prefix="/api")


@alumnos_bp.route("/alumnos", methods=["GET"])
@login_required
def listar_alumnos():
    """
    Lista alumnos (estado = 'alumno') con:
      - masters cursando (nomMaster — edicio) en 'master'
      - filtros normales + atributos dinámicos
      - 'atributos' en el JSON (mapa nombre_attr -> valor)
    """
    try:
        params = request.args.to_dict()

        mapa = {
            "nombre":  "u.nombreUsuario LIKE %s",
            "telefono": "u.telefon LIKE %s",
            "mail":    "u.mail LIKE %s",
            "master":  "m.nomMaster = %s",
            "edicion": "m.edicio   = %s",
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
                GROUP_CONCAT(
                    DISTINCT CONCAT(m.nomMaster, ' — ', m.edicio)
                    SEPARATOR ', '
                ) AS master
            FROM usuario u
            LEFT JOIN relacionusuariomaster rum 
                ON rum.idUsuario = u.idUsuario
            LEFT JOIN master m 
                ON m.idMaster = rum.idMaster
            WHERE u.estado = 'alumno'
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

            for u in rows:
                u["atributos"] = attrs.get(u["id"], {})

        return jsonify(rows), 200

    except Exception as e:
        print("❌ ERROR /alumnos GET:", e)
        return jsonify({"error": str(e)}), 500

@alumnos_bp.route("/alumnos", methods=["POST"])
@admin_required
def crear_alumno():
    try:
        data = request.json or {}

        nombre = data.get("nombre")
        mail = data.get("mail")
        telefono = data.get("telefono")
        id_master = data.get("idMaster")

        if not all([nombre, mail, telefono, id_master]):
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        with DBSession() as db:
            # Crear usuario base como alumno
            db.execute(
                """
                INSERT INTO usuario (nombreUsuario, mail, telefon, estado)
                VALUES (%s, %s, %s, 'alumno')
                """,
                (nombre, mail, telefono),
            )
            id_usuario = db.lastrowid

            # Crear entrada en tabla alumno
            db.execute(
                """
                INSERT INTO alumno (idUsuario, fecha_matriculacion)
                VALUES (%s, NOW())
                """,
                (id_usuario,),
            )

            # Relación con máster cursado
            db.execute(
                """
                INSERT INTO relacionusuariomaster (idUsuario, idMaster)
                VALUES (%s, %s)
                """,
                (id_usuario, id_master),
            )

            # nombre máster + edición para historial
            db.execute(
                "SELECT nomMaster, edicio FROM master WHERE idMaster = %s",
                (id_master,),
            )
            m = db.fetchone()

        nombre_master = m["nomMaster"] if m else str(id_master)
        edicion_master = m["edicio"] if m else None

        detalle = f"Alta de alumno en máster {nombre_master}"
        if edicion_master:
            detalle += f" — Ed. {edicion_master}"
        registrar_historial(id_usuario, "Alumno creado", detalle)

        return jsonify({"mensaje": "Alumno creado correctamente", "id": id_usuario}), 201

    except Exception as e:
        print("❌ ERROR /alumnos POST:", e)
        return jsonify({"error": str(e)}), 500
