# backend/utils/db_session.py
from backend.utils.db import get_connection


class DBSession:
    """
    Context manager per gestionar connexió + cursor dict + commit/rollback.

    Ús:
        with DBSession() as db:
            db.execute("SELECT ...", (..,))
            rows = db.fetchall()
    """

    def __enter__(self):
        self.conn = get_connection()
        # cursor dict per defecte
        self.cursor = self.conn.cursor(dictionary=True)
        return self.cursor

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
        finally:
            self.cursor.close()
            self.conn.close()
