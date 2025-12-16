from flask import Blueprint, request, send_file, jsonify
from backend.utils.db_session import DBSession
from backend.utils.db import get_connection
from backend.utils.auth_middleware import login_required
import io
import pandas as pd

export_bp = Blueprint("export_bp", __name__, url_prefix="/api/exportar")


# Helper simple con get_connection (para los GET)
def ejecutar_query(query, params=None):
    """
    Ejecuta una consulta SQL y retorna todas las filas como lista de dicts.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ---------------------------------------------------------
# Atributos dinámicos: helper para obtener nombres válidos
# ---------------------------------------------------------
def get_nombres_atributos_validos():
    """
    Retorna un set con todos los nombres de atributos definidos en la tabla 'atributos'.
    Sirve como whitelist para las columnas dinámicas.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM atributos")
    res = {row[0] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    return res


# ---------------------------------------------------------
# Construcción unificada de filtros (WHERE)
# ---------------------------------------------------------
def construir_where_clause(
        filtros=None,
        filtros_atributos=None,
        base_alias="u",
        master_alias=None,
        interes_master_alias=None,
):
    """
    Construye la cláusula WHERE (sql y params) a partir de:
      - filtros: dict (nombre, mail, telefono, master, interes_master, edicion…)
      - filtros_atributos: lista de dicts {"nombre": "...", "valor": "..."}
    Los 'alias' indican cómo se llaman las tablas en la consulta principal.
    """
    filtros = filtros or {}
    filtros_atributos = filtros_atributos or []

    where_parts = []
    valores = []

    for key, value in filtros.items():
        if value in (None, "", []):
            continue

        k = str(key).lower()

        if k == "nombre":
            where_parts.append(f"{base_alias}.nombreUsuario LIKE %s")
            valores.append(f"%{value}%")

        elif k == "mail":
            where_parts.append(f"{base_alias}.mail LIKE %s")
            valores.append(f"%{value}%")

        elif k in ("telefono", "telefon"):
            where_parts.append(f"{base_alias}.telefon LIKE %s")
            valores.append(f"%{value}%")

        elif k == "estado":
            # Filtro simple por la columna estado de la tabla base
            where_parts.append(f"{base_alias}.estado = %s")
            valores.append(value)

        elif k == "master" and master_alias:
            # Filtra por el master que está cursando
            where_parts.append(f"{master_alias}.nomMaster LIKE %s")
            valores.append(f"%{value}%")

        elif k == "interes_master" and interes_master_alias:
            # Filtra por el master que le interesa
            where_parts.append(f"{interes_master_alias}.nomMaster LIKE %s")
            valores.append(f"%{value}%")

        elif k == "edicion" and master_alias:
            where_parts.append(f"{master_alias}.edicio = %s")
            valores.append(value)

    # Filtros por atributos dinámicos (usando EXISTS para mejor rendimiento)
    for fa in filtros_atributos:
        nombre_attr = fa.get("nombre")
        valor_attr = fa.get("valor")
        if not nombre_attr or not valor_attr:
            continue

        where_parts.append(f"""
            EXISTS (
                SELECT 1 
                FROM valores_atributos va_f
                JOIN atributos a_f ON a_f.idAtributo = va_f.idAtributo
                WHERE va_f.idUsuario = {base_alias}.idUsuario
                AND a_f.nombre = %s
                AND va_f.valor LIKE %s
            )
        """)
        valores.append(nombre_attr)
        valores.append(f"%{valor_attr}%")

    where_sql = ""
    if where_parts:
        where_sql = "WHERE " + " AND ".join(where_parts)

    return where_sql, valores


# ---------------------------------------------------------
# SELECT + FROM según tipo (alumnos / postulados / usuarios / sistema)
# ---------------------------------------------------------
def get_base_query_components(tipo):
    """
    Retorna:
      - select_basico: lista de expresiones SELECT mínimas (sin atributos dinámicos)
      - from_join: cadena con FROM + JOINs
      - group_by: cadena con GROUP BY (o "")
      - alias para construir filtros
    """
    tipo = (tipo or "usuarios").lower()

    if tipo == "sistema":
        # Usuarios del sistema, sin atributos dinámicos
        select_basico = [
            "u.idUsuarioSistema AS idUsuario",
            "u.username AS nombre",
            "'' AS mail",
            "'' AS telefono",
            "CASE WHEN u.activo = 1 THEN 'activo' ELSE 'inactivo' END AS estado",
            "'' AS masters",
            "'' AS intereses",
        ]
        from_join = """
            FROM UserSistema u
        """
        group_by = ""
        base_alias = "u"
        master_alias = None
        interes_master_alias = None
        return select_basico, from_join, group_by, base_alias, master_alias, interes_master_alias


    # Componentes comunes para usuarios, alumnos y postulados
    select_comun = [
        "u.idUsuario AS idUsuario",
        "u.nombreUsuario AS nombre",
        "u.mail AS mail",
        "u.telefon AS telefono",
        # Usamos MAX() para compatibilidad estricta con ONLY_FULL_GROUP_BY
        "MAX(u.estado) AS estado",
    ]

    if tipo == "alumnos":
        # usuario + alumno + relacionusuariomaster + master + atributos
        select_basico = select_comun + [
            "GROUP_CONCAT(DISTINCT m.nomMaster SEPARATOR ', ') AS masters",
            "MIN(al.fecha_matriculacion) AS fecha_matriculacion",
            "'' AS intereses",
        ]
        from_join = """
            FROM usuario u
            INNER JOIN alumno al ON al.idUsuario = u.idUsuario
            LEFT JOIN relacionusuariomaster rum ON rum.idUsuario = u.idUsuario
            LEFT JOIN master m ON m.idMaster = rum.idMaster
            LEFT JOIN valores_atributos va ON va.idUsuario = u.idUsuario
            LEFT JOIN atributos a ON a.idAtributo = va.idAtributo
        """
        group_by = "GROUP BY u.idUsuario"
        base_alias = "u"
        master_alias = "m"
        interes_master_alias = None

    elif tipo == "postulados":
        # usuario + postulado + master (idInteresMaster) + atributos
        select_basico = select_comun + [
            "'' AS masters",
            # MAX() resuelve el error 1055 para pm.nomMaster
            "MAX(pm.nomMaster) AS intereses",
        ]
        from_join = """
            FROM usuario u
            INNER JOIN postulado p ON p.idUsuario = u.idUsuario
            LEFT JOIN master pm ON pm.idMaster = p.idInteresMaster
            LEFT JOIN valores_atributos va ON va.idUsuario = u.idUsuario
            LEFT JOIN atributos a ON a.idAtributo = va.idAtributo
        """
        group_by = "GROUP BY u.idUsuario"
        base_alias = "u"
        master_alias = None
        interes_master_alias = "pm"

    else:  # usuarios genérico (todos)
        # Para evitar JOINs masivos, usamos subconsultas para masters/intereses
        select_basico = select_comun + [
            """
            (
                SELECT GROUP_CONCAT(DISTINCT m.nomMaster SEPARATOR ', ')
                FROM relacionusuariomaster rum
                LEFT JOIN master m ON m.idMaster = rum.idMaster
                WHERE rum.idUsuario = u.idUsuario
            ) AS masters
            """,
            """
            (
                SELECT MAX(pm.nomMaster)
                FROM postulado p
                LEFT JOIN master pm ON pm.idMaster = p.idInteresMaster
                WHERE p.idUsuario = u.idUsuario
            ) AS intereses
            """
        ]
        from_join = """
            FROM usuario u
            LEFT JOIN valores_atributos va ON va.idUsuario = u.idUsuario
            LEFT JOIN atributos a ON a.idAtributo = va.idAtributo
        """
        group_by = "GROUP BY u.idUsuario"
        base_alias = "u"
        master_alias = None
        interes_master_alias = None

    return (
        select_basico,
        from_join,
        group_by,
        base_alias,
        master_alias,
        interes_master_alias,
    )


# ---------------------------------------------------------
# SELECT con columnas personalizadas (incluye atributos)
# ---------------------------------------------------------
def construir_select_columnas(tipo, columnas, valid_attr_names):
    """
    A partir de la lista 'columnas' del frontend, construye:
      - select_list: lista de expresiones SELECT (strings)
      - params_attr: lista de valores para los CASE de atributos dinámicos
    """
    tipo = (tipo or "usuarios").lower()
    columnas = columnas or []

    # Obtener el SELECT básico (incluye masters/intereses/etc. como GROUP_CONCAT/MAX)
    select_basico, _, _, _, _, _ = get_base_query_components(tipo)
    # Convertir a un diccionario para fácil búsqueda por alias
    select_map = {}
    for expr in select_basico:
        # Extraer el alias final (ej. "MAX(u.estado) AS estado" -> "estado")
        parts = expr.split()
        alias = parts[-1]
        select_map[alias.lower()] = expr


    def map_col_fija(col):
        cl = col.lower()

        # Mapeo a columnas básicas del usuario
        if cl in ("id", "idusuario", "id_usuario"):
            return select_map.get("idusuario")

        if cl in ("nombre", "nombreusuario", "nom"):
            return select_map.get("nombre")

        if cl in ("mail", "email", "correo", "correu"):
            return select_map.get("mail")

        if cl in ("telefono", "telefon", "tel"):
            return select_map.get("telefono")

        if cl in ("estado",):
            return select_map.get("estado")

        # ==== ESPECIALES POR TIPO ====

        if cl in ("master", "masters"):
            return select_map.get("masters")

        if cl in ("interes_master", "intereses"):
            return select_map.get("intereses")

        if tipo == "alumnos" and cl in (
                "fecha_matriculacion",
                "fecha_matricula",
                "data_matricula",
        ):
            return select_map.get("fecha_matriculacion")

        return None

    # Si no piden columnas concretas, usamos el SELECT básico
    if not columnas:
        return list(select_basico), []

    select_list = []
    params_attr = []

    for col in columnas:
        # 1) ¿Es un atributo dinámico?
        if col in valid_attr_names:
            # CASE para pivotar el valor del atributo en una columna
            select_list.append(
                f"MAX(CASE WHEN a.nombre = %s THEN va.valor END) AS `{col}`"
            )
            params_attr.append(col)
            continue

        # 2) ¿Es una columna fija conocida?
        expr_fija = map_col_fija(col)
        if expr_fija:
            select_list.append(expr_fija)
            continue

    # Seguridad: si no ha entrado nada, usamos el básico
    if not select_list:
        select_list = list(select_basico)

    return select_list, params_attr


# ---------------------------------------------------------
# Helper para crear DataFrame + Excel en memoria
# ---------------------------------------------------------
def rows_to_excel_response(rows, filename="export.xlsx"):
    """
    Convierte una lista de dicts a un Excel en memoria
    y devuelve la respuesta Flask con send_file.
    """
    df = pd.DataFrame(rows)

    if df.empty:
        df = pd.DataFrame({"info": ["No hay resultados para los filtros aplicados"]})

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )


# ---------------------------------------------------------
# Mapeo de tipos del frontend al interno
# ---------------------------------------------------------
def map_tipo_front_to_internal(tipo_front):
    tipo_front = (tipo_front or "").lower().strip()
    if tipo_front == "potenciales":
        return "postulados", "potenciales.xlsx"
    elif tipo_front == "alumnos":
        return "alumnos", "alumnos.xlsx"
    elif tipo_front in ("usuarios", "todos"):
        return "usuarios", "usuarios.xlsx"
    elif tipo_front == "sistema":
        return "sistema", "sistema.xlsx"
    return None, None


# =========================================================
#               ENDPOINTS GET BÁSICOS
# =========================================================
# Se mantienen, pero ahora usan MAX(u.estado) de los helpers
@export_bp.route("/alumnos", methods=["GET"])
@login_required
def exportar_alumnos():
    filtros = {
        "nombre": request.args.get("nombre"),
        "mail": request.args.get("mail"),
        "telefono": request.args.get("telefono"),
        "master": request.args.get("master"),
        "edicion": request.args.get("edicion"),
        "estado": request.args.get("estado"),
    }

    (
        select_basico,
        from_join,
        group_by,
        base_alias,
        master_alias,
        interes_master_alias,
    ) = get_base_query_components("alumnos")

    where_sql, valores = construir_where_clause(
        filtros=filtros,
        filtros_atributos=None,
        base_alias=base_alias,
        master_alias=master_alias,
        interes_master_alias=interes_master_alias,
    )

    query = f"""
        SELECT
            {", ".join(select_basico)}
        {from_join}
        {where_sql}
        {group_by}
        ORDER BY u.nombreUsuario
    """

    rows = ejecutar_query(query, valores)
    return rows_to_excel_response(rows, filename="alumnos.xlsx")


@export_bp.route("/postulados", methods=["GET"])
@login_required
def exportar_postulados():
    filtros = {
        "nombre": request.args.get("nombre"),
        "mail": request.args.get("mail"),
        "telefono": request.args.get("telefono"),
        "interes_master": request.args.get("interes_master"),
        "estado": request.args.get("estado"),
    }

    (
        select_basico,
        from_join,
        group_by,
        base_alias,
        master_alias,
        interes_master_alias,
    ) = get_base_query_components("postulados")

    where_sql, valores = construir_where_clause(
        filtros=filtros,
        filtros_atributos=None,
        base_alias=base_alias,
        master_alias=master_alias,
        interes_master_alias=interes_master_alias,
    )

    query = f"""
        SELECT
            {", ".join(select_basico)}
        {from_join}
        {where_sql}
        {group_by}
        ORDER BY u.nombreUsuario
    """

    rows = ejecutar_query(query, valores)
    return rows_to_excel_response(rows, filename="postulados.xlsx")


@export_bp.route("/usuarios", methods=["GET"])
@login_required
def exportar_usuarios():
    filtros = {
        "nombre": request.args.get("nombre"),
        "mail": request.args.get("mail"),
        "telefono": request.args.get("telefono"),
        "estado": request.args.get("estado"),
    }

    (
        select_basico,
        from_join,
        group_by,
        base_alias,
        master_alias,
        interes_master_alias,
    ) = get_base_query_components("usuarios")

    where_sql, valores = construir_where_clause(
        filtros=filtros,
        filtros_atributos=None,
        base_alias=base_alias,
        master_alias=master_alias,
        interes_master_alias=interes_master_alias,
    )

    query = f"""
        SELECT
            {", ".join(select_basico)}
        {from_join}
        {where_sql}
        {group_by}
        ORDER BY u.nombreUsuario
    """

    rows = ejecutar_query(query, valores)
    return rows_to_excel_response(rows, filename="usuarios.xlsx")


# =========================================================
#               ENDPOINT POST UNIFICADO (Refactorizado)
# =========================================================
@export_bp.route("/excel", methods=["POST"])
@login_required
def exportar_excel():
    try:
        data = request.get_json() or {}

        tipo_front = data.get("tipo")
        filtros = data.get("filtros", {})
        filtros_atributos = data.get("filtrosAtributos", [])
        columnas_seleccionadas = data.get("columnas", [])

        print("📥 TIPO RECIBIDO DESDE FRONT:", tipo_front)

        # 1. MAPEO Y VALIDACIÓN DE TIPOS
        tipo, filename = map_tipo_front_to_internal(tipo_front)

        if not tipo:
            return jsonify({"error": f"Tipo no válido: {tipo_front}"}), 400

        # 2. OBTENER COMPONENTES BASE Y ATRIBUTOS VÁLIDOS
        valid_attr_names = get_nombres_atributos_validos()

        (
            select_basico,
            from_join,
            group_by,
            base_alias,
            master_alias,
            interes_master_alias,
        ) = get_base_query_components(tipo)

        # Columna para ORDER BY (usa 'username' para sistema, 'nombreUsuario' para el resto)
        if tipo == "sistema":
            order_by_col = f"{base_alias}.username"
        else:
            order_by_col = f"{base_alias}.nombreUsuario"


        # 3. CONSTRUIR SELECT (incluye el pivotado de atributos)
        select_list, params_attr = construir_select_columnas(
            tipo, columnas_seleccionadas, valid_attr_names
        )

        # 4. CONSTRUIR WHERE (filtros fijos y de atributos)
        where_sql, valores_filtros = construir_where_clause(
            filtros=filtros,
            filtros_atributos=filtros_atributos,
            base_alias=base_alias,
            master_alias=master_alias,
            interes_master_alias=interes_master_alias,
        )

        # 5. ENSAMBLAR QUERY Y PARÁMETROS
        query = f"""
            SELECT
                {", ".join(select_list)}
            {from_join}
            {where_sql}
            {group_by}
            ORDER BY {order_by_col}
        """
        params = params_attr + valores_filtros

        print("🔍 QUERY FINAL EXPORT:", query)
        print("🔍 PARAMS:", params)

        # 6. EJECUTAR QUERY
        with DBSession() as db:
            db.execute(query, params)
            rows = db.fetchall()

        # 7. EXPORTAR EXCEL
        # El DataFrame se crea directamente con las 'rows' resultantes de la
        # consulta unificada, que ya incluye todos los atributos y campos.
        return rows_to_excel_response(rows, filename=filename)

    except Exception as e:
        print("❌ ERROR exportar_excel:", e)
        return jsonify({"error": "Error generando Excel"}), 500