from backend.utils.db import get_connection

def registrar_historial(id_usuario, accion, detalle=None):
    """
    Guarda un movimiento en la tabla usuario_historial.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO usuario_historial (idUsuario, accion, detalle)
        VALUES (%s, %s, %s)
    """, (id_usuario, accion, detalle))

    conn.commit()
    cursor.close()
    conn.close()
