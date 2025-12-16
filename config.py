import os

class Config:
    # ---------------------------
    # Base de datos
    # ---------------------------
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '02coord*')
    DB_NAME = os.getenv('DB_NAME', 'crm_db')

    # ---------------------------
    # Seguridad / Tokens
    # ---------------------------
    # Mejor leerla de entorno y tener un fallback solo en local
    SECRET_KEY = os.getenv('SECRET_KEY', 'super_secret_key_change_this')

    # Dominio público donde se usará el enlace de baja
    # Ejemplo en .env:
    # PUBLIC_BASE_URL=https://mi-crm.com
    PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', 'http://localhost:5000')

    # Config extra para los tokens de desuscripción
    UNSUBSCRIBE_SALT = os.getenv('UNSUBSCRIBE_SALT', 'unsubscribe-email')
    # Tiempo máximo que el enlace de baja es válido (30 días)
    UNSUBSCRIBE_MAX_AGE = int(os.getenv('UNSUBSCRIBE_MAX_AGE', 60 * 60 * 24 * 30))

    # ---------------------------
    # Email (Flask-Mail / SMTP)
    # ---------------------------
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = os.getenv('MAIL_USERNAME')  # tu cuenta de envío, ej: notificaciones@tuapp.com
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # app password o contraseña

    # Remitente por defecto de los correos
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5000")