import jwt
from functools import wraps
from flask import request, jsonify, current_app


def get_token():
    """Extrae el token del header Authorization."""
    token = request.headers.get("Authorization")
    if not token:
        return None
    return token.replace("Bearer ", "")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token()

        if not token:
            return jsonify({"error": "Token requerido"}), 401

        try:
            decoded = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
            request.user = decoded
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except Exception:
            return jsonify({"error": "Token inválido"}), 401

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token()

        if not token:
            return jsonify({"error": "Token requerido"}), 401

        try:
            decoded = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )

            if decoded.get("rol") != "admin":
                return jsonify({"error": "No autorizado — se requiere rol admin"}), 403

            request.user = decoded

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except Exception:
            return jsonify({"error": "Token inválido"}), 401

        return f(*args, **kwargs)

    return decorated
