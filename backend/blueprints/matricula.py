from flask import Blueprint, request, jsonify
from backend.utils.db import get_connection
from backend.utils.auth_middleware import admin_required, login_required

matricula_bp = Blueprint("matricula_bp", __name__, url_prefix="/api")


@matricula_bp.route("/matricular", methods=["POST"])
@login_required
def matricular():
    """
    Matricula 1 o més usuaris a un màster concret:
      - comprova si ja està relacionat amb el màster
      - canvia estado = 'alumno'
      - crea registre a 'alumno' si no existeix
      - crea relació a relacionusuariomaster
      - esborra el postulado només per aquell màster
    """
    try:
        data = request.json or {}
        ids = data.get("ids", [])
        idMaster = data.get("idMaster")

        if not ids or not idMaster:
            return jsonify({"error": "Faltan parámetros"}), 400

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        nuevos_matriculados = []
        ya_matriculados = []

        for idUsuario in ids:

            # Comprovar si ja està matriculat en aquest màster
            cursor.execute("""
                SELECT 1 FROM relacionusuariomaster
                WHERE idUsuario = %s AND idMaster = %s
            """, (idUsuario, idMaster))

            if cursor.fetchone():
                ya_matriculados.append(idUsuario)
                continue

            # Passar a estado 'alumno'
            cursor.execute("""
                UPDATE usuario
                SET estado = 'alumno'
                WHERE idUsuario = %s
            """, (idUsuario,))

            # Crear entrada a 'alumno' si no existeix
            cursor.execute("""
                SELECT 1 FROM alumno WHERE idUsuario = %s
            """, (idUsuario,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO alumno (idUsuario, fecha_matriculacion)
                    VALUES (%s, NOW())
                """, (idUsuario,))

            # Relació usuari-màster
            cursor.execute("""
                INSERT INTO relacionusuariomaster (idUsuario, idMaster)
                VALUES (%s, %s)
            """, (idUsuario, idMaster))

            # Esborrar l'interès només d'aquest màster
            cursor.execute("""
                DELETE FROM postulado
                WHERE idUsuario = %s AND idInteresMaster = %s
            """, (idUsuario, idMaster))

            nuevos_matriculados.append(idUsuario)

        conn.commit()
        cursor.close()
        conn.close()

        if nuevos_matriculados and ya_matriculados:
            return jsonify({
                "mensaje": "Matriculación completada parcialmente.",
                "nuevos": nuevos_matriculados,
                "ya_matriculados": ya_matriculados
            }), 200

        if not nuevos_matriculados and ya_matriculados:
            return jsonify({
                "error": "Todos los usuarios ya estaban matriculados en este máster.",
                "ya_matriculados": ya_matriculados
            }), 400

        return jsonify({
            "mensaje": "Matriculación completada correctamente.",
            "nuevos": nuevos_matriculados
        }), 200

    except Exception as e:
        print("❌ ERROR matricular:", e)
        return jsonify({"error": str(e)}), 500
