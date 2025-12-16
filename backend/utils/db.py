# backend/utils/db.py
import os
import mysql.connector
import mysql.connector.pooling

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "crm_db"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "connection_timeout": 10,
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
}

_pool = None


def _init_pool():
    """Inicialitza el pool de connexions només una vegada."""
    global _pool
    if _pool is not None:
        return

    print("🔧 Inicializando pool MySQL:", {
        "host": DB_CONFIG["host"],
        "user": DB_CONFIG["user"],
        "db": DB_CONFIG["database"],
    })

    _pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="crm_pool",
        pool_size=int(os.getenv("DB_POOL_SIZE", "15")),  # una mica més alt
        pool_reset_session=True,
        **DB_CONFIG,
    )


def get_connection():
    """Retorna una connexió des del pool."""
    global _pool
    if _pool is None:
        _init_pool()

    conn = _pool.get_connection()

    # 👇 Debug lleuger (pots comentar-lo si molesta)
    print("CONECTANDO A BD:", {
        "host": DB_CONFIG["host"],
        "user": DB_CONFIG["user"],
        "db": DB_CONFIG["database"],
    })

    return conn
