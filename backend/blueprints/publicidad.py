from flask import Blueprint, request
from backend.utils.db import get_connection
from backend.utils.tokens import verificar_token_unsubscribe

publicidad_bp = Blueprint("publicidad_bp", __name__, url_prefix="/api/publicidad")

@publicidad_bp.route("/unsubscribe", methods=["GET"])
def unsubscribe():
    token = request.args.get("token", "")

    user_id, error = verificar_token_unsubscribe(token)
    if error:
        return "<h2>Enlace no válido o caducado</h2>", 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuario SET publicidad = 0 WHERE idUsuario = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return """
        <h2>Te has dado de baja correctamente</h2>
        <p>No recibirás más publicidad.</p>
    """
