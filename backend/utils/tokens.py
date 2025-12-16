from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app


def _get_unsubscribe_serializer():
    return URLSafeTimedSerializer(
        secret_key=current_app.config["SECRET_KEY"],
        salt=current_app.config.get("UNSUBSCRIBE_SALT", "unsubscribe-email")
    )


def generar_token_unsubscribe(user_id: int) -> str:
    s = _get_unsubscribe_serializer()
    return s.dumps({"uid": user_id, "scope": "ads"})


def verificar_token_unsubscribe(token: str):
    s = _get_unsubscribe_serializer()
    max_age = current_app.config.get("UNSUBSCRIBE_MAX_AGE", 60 * 60 * 24 * 30)

    try:
        data = s.loads(token, max_age=max_age)
    except SignatureExpired:
        return None, "expired"
    except BadSignature:
        return None, "invalid"

    if data.get("scope") != "ads":
        return None, "invalid"

    return data.get("uid"), None
