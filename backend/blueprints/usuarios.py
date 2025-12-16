# backend/blueprints/usuarios.py
from flask import Blueprint, request, jsonify
from backend.utils.db_session import DBSession
from backend.utils.auth_middleware import login_required
from backend.utils.query_helpers import (
    aplicar_filtros_basicos,
    aplicar_filtros_atributos,
    cargar_atributos,
)

usuarios_bp = Blueprint("usuarios_bp", __name__, url_prefix="/api")


@usuarios_bp.route("/usuarios", methods=["GET"])
@login_required
def listar_usuarios():
    """
    Lista todos los usuarios (alumnos + postulados + otros) con:
      - masters (relacionusuariomaster)
      - intereses (postulado)
      - filtros básicos + dinámicos (atributos)
      - atributos dinámicos en 'atributos'
    """
    try:
        params = request.args.to_dict()

        mapa = {
            "nombre": "u.nombreUsuario LIKE %s",
            "telefono": "u.telefon LIKE %s",
            "mail":    "u.mail LIKE %s",
            "master":  "m.nomMaster = %s",
            "edicion": "m.edicio = %s",
            "interes_master": "m2.nomMaster = %s",
            "estado": "u.estado = %s",
            "publicidad": "u.publicidad = %s",
        }

        filtros, valores = aplicar_filtros_basicos(params, mapa)
        filtros, valores = aplicar_filtros_atributos(
            params,
            filtros,
            valores,
            claves_reservadas=set(mapa.keys()),
        )

        query = """
            SELECT 
                u.idUsuario AS id,
                u.nombreUsuario AS nombre,
                u.mail,
                u.telefon AS telefono,
                u.estado,
                GROUP_CONCAT(DISTINCT m.nomMaster SEPARATOR ', ')  AS masters,
                GROUP_CONCAT(DISTINCT m2.nomMaster SEPARATOR ', ') AS intereses
            FROM usuario u
            LEFT JOIN relacionusuariomaster rum ON rum.idUsuario = u.idUsuario
            LEFT JOIN master m                  ON m.idMaster   = rum.idMaster
            LEFT JOIN postulado p               ON p.idUsuario  = u.idUsuario
            LEFT JOIN master m2                 ON m2.idMaster  = p.idInteresMaster
            WHERE 1 = 1
        """

        if filtros:
            query += " AND " + " AND ".join(filtros)

        query += """
            GROUP BY u.idUsuario, u.nombreUsuario, u.mail, u.telefon, u.estado
            ORDER BY u.nombreUsuario ASC
        """

        with DBSession() as db:
            db.execute(query, valores)
            rows = db.fetchall()

            if not rows:
                return jsonify([]), 200

            ids = [r["id"] for r in rows]
            attrs = cargar_atributos(db, ids)

            for r in rows:
                r["atributos"] = attrs.get(r["id"], {})

        return jsonify(rows), 200

    except Exception as e:
        print("❌ ERROR /usuarios GET:", e)
        return jsonify({"error": str(e)}), 500



# CREAR USUARIO GENÉRICO
@usuarios_bp.route("/usuarios", methods=["POST"])
@login_required
def crear_usuario():
    """
    Crea un usuario "genérico".
    Normalmente se crean:
      - alumnos por /alumnos
      - postulados por /postulados
    Esto sirve si en algún punto usas /usuarios con POST.
    """
    try:
        data = request.json or {}

        nombre = (data.get("nombreUsuario") or data.get("nombre") or "").strip()
        mail = (data.get("mail") or "").strip()
        telefono = (data.get("telefon") or data.get("telefono") or "").strip()
        estado = (data.get("estado") or "otro").strip()

        if not nombre:
            return jsonify({"error": "Falta el nombre"}), 400

        with DBSession() as db:
            db.execute(
                """
                INSERT INTO usuario (nombreUsuario, mail, telefon, estado)
                VALUES (%s, %s, %s, %s)
                """,
                (nombre, mail, telefono, estado),
            )
            id_usuario = db.lastrowid

        return jsonify({"mensaje": "Usuario creado correctamente", "id": id_usuario}), 201

    except Exception as e:
        print("❌ ERROR /usuarios POST:", e)
        return jsonify({"error": str(e)}), 500



# EDITAR USUARIO (FormEditarUsuario)
@usuarios_bp.route("/usuarios/<int:id_usuario>", methods=["PUT"])
@login_required
def editar_usuario(id_usuario):
    """
    Actualiza:
      - nombre, mail, telefono del usuario
      - atributos dinámicos (sustituye por lo que llega)
    El frontend envía:
      {
        nombre: string,
        mail: string,
        telefono: string,
        atributos: { clave: valor, ... }
      }
    """
    try:
        data = request.json or {}

        nombre = (data.get("nombre") or "").strip()
        mail = (data.get("mail") or "").strip()
        telefono = (data.get("telefono") or "").strip()
        atributos = data.get("atributos", {}) or {}

        with DBSession() as db:
            # Comprobar que existe
            db.execute(
                "SELECT idUsuario FROM usuario WHERE idUsuario = %s",
                (id_usuario,),
            )
            existe = db.fetchone()
            if not existe:
                return jsonify({"error": "Usuario no encontrado"}), 404

            # Actualizar datos básicos
            db.execute(
                """
                UPDATE usuario
                SET nombreUsuario = %s,
                    mail          = %s,
                    telefon       = %s,
                    publicidad    = %s
                WHERE idUsuario = %s
                """,
                (nombre, mail, telefono,data.get("publicidad", 1), id_usuario),
            )

            # Atributos dinámicos: borro y re-inserto
            db.execute(
                "DELETE FROM valores_atributos WHERE idUsuario = %s",
                (id_usuario,),
            )

            if atributos:
                db.execute("SELECT idAtributo, nombre FROM atributos")
                filas_attr = db.fetchall()
                mapa_attr = {f["nombre"]: f["idAtributo"] for f in filas_attr}

                for nombre_attr, valor in atributos.items():
                    valor = (valor or "").strip()
                    if not valor:
                        continue
                    id_attr = mapa_attr.get(nombre_attr)
                    if not id_attr:
                        # si no existe el atributo, lo ignoramos
                        continue

                    db.execute(
                        """
                        INSERT INTO valores_atributos (idUsuario, idAtributo, valor)
                        VALUES (%s, %s, %s)
                        """,
                        (id_usuario, id_attr, valor),
                    )

        return jsonify({"mensaje": "Usuario actualizado correctamente"}), 200

    except Exception as e:
        print("❌ ERROR /usuarios PUT:", e)
        return jsonify({"error": str(e)}), 500
