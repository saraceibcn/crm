from flask import Blueprint, jsonify
from backend.utils.db_session import DBSession
from backend.utils.auth_middleware import login_required

usuario_detalle_bp = Blueprint("usuario_detalle_bp", __name__, url_prefix="/api")


@usuario_detalle_bp.route('/usuario/<int:id>', methods=['GET'])
@login_required
def obtener_usuario(id):
    """
    Detall d'un usuari:
      - dades bàsiques
      - masters cursando (nom + edicio)
      - masters_interes (nom SENSE duplicar els que ja cursa)
      - atributs dinàmics
    """
    try:
        with DBSession() as db:
            # Dades bàsiques
            db.execute("""
                SELECT 
                    u.idUsuario AS id,
                    u.nombreUsuario AS nombre,
                    u.mail,
                    u.telefon AS telefono,
                    u.estado,
                    u.publicidad
                FROM usuario u
                WHERE u.idUsuario = %s
            """, (id,))
            user = db.fetchone()
            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404

            # Masters cursant
            db.execute("""
                SELECT m.nomMaster AS nombre, m.edicio AS edicion
                FROM relacionusuariomaster rum
                JOIN master m ON m.idMaster = rum.idMaster
                WHERE rum.idUsuario = %s
                ORDER BY m.nomMaster, m.edicio
            """, (id,))
            user["masters_cursando"] = db.fetchall()

            # Interesos (nom, sense edició, exclosos els que ja cursa)
            db.execute("""
                SELECT DISTINCT m.nomMaster AS nombre
                FROM postulado p
                JOIN master m ON m.idMaster = p.idInteresMaster
                WHERE p.idUsuario = %s
                  AND p.idInteresMaster NOT IN (
                        SELECT idMaster
                        FROM relacionusuariomaster
                        WHERE idUsuario = %s
                  )
                ORDER BY m.nomMaster
            """, (id, id))
            user["masters_interes"] = db.fetchall()

            # Atributs dinàmics
            db.execute("""
                SELECT a.nombre AS atributo, va.valor
                FROM valores_atributos va
                JOIN atributos a ON a.idAtributo = va.idAtributo
                WHERE va.idUsuario = %s
            """, (id,))
            attrs = db.fetchall()
            user["atributos"] = {a["atributo"]: a["valor"] for a in attrs}

        return jsonify(user), 200

    except Exception as e:
        print("❌ ERROR en /usuario/<id> [GET]:", e)
        return jsonify({"error": str(e)}), 500


@usuario_detalle_bp.route('/usuario/<int:id>', methods=['DELETE'])
@login_required
def eliminar_usuario(id):
    """
    Elimina completament un usuari i totes les seves relacions.
    """
    try:
        with DBSession() as db:
            # Comprovar existència
            db.execute("SELECT 1 FROM usuario WHERE idUsuario = %s", (id,))
            if not db.fetchone():
                return jsonify({"error": "Usuario no encontrado"}), 404

            # Esborrar dependències
            queries = [
                "DELETE FROM postulado WHERE idUsuario = %s",
                "DELETE FROM relacionusuariomaster WHERE idUsuario = %s",
                "DELETE FROM alumno WHERE idUsuario = %s",
                "DELETE FROM valores_atributos WHERE idUsuario = %s",
                "DELETE FROM usuario_historial WHERE idUsuario = %s",
                "DELETE FROM usuario WHERE idUsuario = %s",
            ]
            for q in queries:
                db.execute(q, (id,))

        # Si arribem aquí, el commit ja s'ha fet
        return jsonify({"mensaje": "Usuario eliminado correctamente"}), 200

    except Exception as e:
        print("❌ ERROR en /usuario/<id> [DELETE]:", e)
        return jsonify({"error": str(e)}), 500
