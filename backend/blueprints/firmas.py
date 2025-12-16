from flask import Blueprint, request, jsonify
from backend.utils.db import get_connection
from backend.utils.auth_middleware import login_required

firma_bp = Blueprint("firma_bp", __name__, url_prefix="/api")


# =========================================================
# GET /api/firmas
# Devuelve todas las firmas activas (globales)
# =========================================================
@firma_bp.route("/firmas", methods=["GET"])
@login_required
def get_firmas():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT idFirma, nombre, html, es_defecto
        FROM firmas_email
        WHERE activa = 1
        ORDER BY es_defecto DESC, nombre
    """)

    firmas = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(firmas), 200


# POST /api/firmas
# Crear firma global (solo admin)
@firma_bp.route("/firmas", methods=["POST"])
@login_required
def crear_firma():
    user = request.user
    if user.get("rol") != "admin":
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json() or {}
    nombre = data.get("nombre")
    html = data.get("html")
    es_defecto = int(data.get("es_defecto", 0))

    if not nombre or not html:
        return jsonify({"error": "Faltan campos"}), 400

    conn = get_connection()
    cur = conn.cursor()

    # Si esta firma es por defecto → quitar defecto a las demás
    if es_defecto:
        cur.execute("""
            UPDATE firmas_email
            SET es_defecto = 0
        """)

    cur.execute("""
        INSERT INTO firmas_email (nombre, html, es_defecto, activa)
        VALUES (%s, %s, %s, 1)
    """, (nombre, html, es_defecto))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok"}), 201


# DELETE /api/firmas/<idFirma>
# Desactivar firma (soft delete, solo admin)
@firma_bp.route("/firmas/<int:id_firma>", methods=["DELETE"])
@login_required
def eliminar_firma(id_firma):
    user = request.user
    if user.get("rol") != "admin":
        return jsonify({"error": "No autorizado"}), 403

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE firmas_email
        SET activa = 0,
            es_defecto = 0
        WHERE idFirma = %s
    """, (id_firma,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok"}), 200
