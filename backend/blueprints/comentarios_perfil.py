from flask import Blueprint, request, jsonify
from backend.utils.db_session import DBSession
from backend.utils.auth_middleware import login_required
from backend.utils.db import get_connection

comentarios_bp = Blueprint("comentarios_bp", __name__, url_prefix="/api/comentarios")


# CREAR COMENTARIO
@comentarios_bp.route("/crear", methods=["POST"])
@login_required
def crear_comentario():
    data = request.json

    idUsuario = data.get("idUsuario")
    comentario = data.get("comentario")
    idUsuarioSistema = request.user.get("id")

    if not idUsuario or not comentario:
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            INSERT INTO comentarios_perfil (idUsuario, idUsuarioSistema, comentario)
            VALUES (%s, %s, %s)
            """,
            (idUsuario, idUsuarioSistema, comentario)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Comentario guardado"}), 200

    except Exception as e:
        print("ERROR COMENTARIOS:", str(e))
        return jsonify({"error": str(e)}), 500


# OBTENER COMENTARIOS DE UN PERFIL
@comentarios_bp.route("/usuario/<int:idUsuario>", methods=["GET"])
@login_required
def obtener_comentarios(idUsuario):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT 
                c.idComentario,
                c.comentario,
                c.fecha,
                u.username AS autorNombre,
                u.rol AS autorRol
            FROM comentarios_perfil c
            JOIN usuario_sistema u
                ON u.idUsuarioSistema = c.idUsuarioSistema
            WHERE c.idUsuario = %s
            ORDER BY c.fecha DESC
            """,
            (idUsuario,)
        )

        comentarios = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify(comentarios), 200

    except Exception as e:
        print("ERROR OBTENER_COMENTARIOS:", str(e))
        return jsonify({"error": str(e)}), 500


# EDITAR COMENTARIO
@comentarios_bp.route("/<int:idComentario>", methods=["PUT"])
@login_required
def editar_comentario(idComentario):
    data = request.json
    nuevo_texto = data.get("comentario")
    idUsuarioSistema = request.user.get("id")

    if not nuevo_texto:
        return jsonify({"error": "Comentario vacío"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Comprobar que el comentario es del usuario actual
        cursor.execute(
            "SELECT idUsuarioSistema FROM comentarios_perfil WHERE idComentario = %s",
            (idComentario,)
        )
        fila = cursor.fetchone()

        if not fila:
            return jsonify({"error": "Comentario no encontrado"}), 404

        if fila["idUsuarioSistema"] != idUsuarioSistema:
            return jsonify({"error": "No autorizado"}), 403

        # Actualizar comentario
        cursor.execute(
            """
            UPDATE comentarios_perfil
            SET comentario = %s
            WHERE idComentario = %s
            """,
            (nuevo_texto, idComentario)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Comentario actualizado"}), 200

    except Exception as e:
        print("ERROR EDITAR:", str(e))
        return jsonify({"error": str(e)}), 500


# ELIMINAR COMENTARIO
@comentarios_bp.route("/<int:idComentario>", methods=["DELETE"])
@login_required
def eliminar_comentario(idComentario):
    idUsuarioSistema = request.user.get("id")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Comprobar autor
        cursor.execute(
            "SELECT idUsuarioSistema FROM comentarios_perfil WHERE idComentario = %s",
            (idComentario,)
        )
        fila = cursor.fetchone()

        if not fila:
            return jsonify({"error": "Comentario no encontrado"}), 404

        if fila["idUsuarioSistema"] != idUsuarioSistema:
            return jsonify({"error": "No autorizado"}), 403

        cursor.execute(
            "DELETE FROM comentarios_perfil WHERE idComentario = %s",
            (idComentario,)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Comentario eliminado"}), 200

    except Exception as e:
        print("ERROR ELIMINAR:", str(e))
        return jsonify({"error": str(e)}), 500
