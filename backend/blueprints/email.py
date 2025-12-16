from flask import Blueprint, request, jsonify
from backend.utils.auth_middleware import login_required
from backend.utils.email import enviar_correo_html, wrap_email_html

email_bp = Blueprint("email_bp", __name__, url_prefix="/api")

@email_bp.route("/enviar-email", methods=["POST"])
@login_required
def enviar_email():
    data = request.get_json() or {}

    asunto = data.get("asunto")
    contenido = data.get("contenido")
    destinatarios = data.get("destinatarios")
    bcc = data.get("bcc", [])

    if not asunto or not contenido or not destinatarios:
        return jsonify({"error": "Faltan campos"}), 400

    if not isinstance(destinatarios, list):
        return jsonify({"error": "destinatarios debe ser lista"}), 400

    user = request.user
    print("DEBUG USER TOKEN:", user)

    remitente_email = user.get("email") or "tecnico@ceibcn.com"
    remitente_nombre = user.get("username") or "CRM"

    enviados = 0

    for dest in destinatarios:
        enviar_correo_html(
            destino=dest,
            asunto=asunto,
            cuerpo_html=contenido,
            remitente_email=remitente_email,
            remitente_nombre=remitente_nombre,
            bcc_list=bcc
        )
        enviados += 1

    return jsonify({"status": "ok", "mensaje": f"Correos enviados: {enviados}"}), 200
