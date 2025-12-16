# backend/utils/query_helpers.py

def aplicar_filtros_basicos(params, mapa_condiciones):
    """
    Construeix la llista de condicions SQL i els valors
    a partir d'un dict de paràmetres i un mapa de claus → condicions.
    """
    filtros = []
    valores = []

    for key, cond in mapa_condiciones.items():
        raw = params.get(key)
        if not raw:
            continue

        valor = raw.strip()
        if not valor:
            continue

        if "LIKE" in cond:
            valores.append(f"%{valor}%")
        else:
            valores.append(valor)

        filtros.append(cond)

    return filtros, valores


def aplicar_filtros_atributos(params, filtros_actuales, valores_actuales, claves_reservadas=None):
    """
    Afegeix filtres EXISTS sobre valores_atributos per qualsevol clau
    que no estigui a 'claves_reservadas'.
    """
    claves_reservadas = claves_reservadas or set()

    filtros = list(filtros_actuales)
    valores = list(valores_actuales)

    cond_exists = """
        EXISTS (
            SELECT 1
            FROM valores_atributos va
            JOIN atributos a ON a.idAtributo = va.idAtributo
            WHERE va.idUsuario = u.idUsuario
              AND a.nombre = %s
              AND va.valor LIKE %s
        )
    """

    for key, raw in params.items():
        if key in claves_reservadas:
            continue
        if not raw:
            continue

        valor = raw.strip()
        if not valor:
            continue

        filtros.append(cond_exists)
        valores.append(key)
        valores.append(f"%{valor}%")

    return filtros, valores


def cargar_atributos(cursor, ids_usuarios):
    """
    Retorna un dict:
        { idUsuario: { nombreAtributo: valor, ... }, ... }

    Un sol SELECT per tots els usuaris.
    """
    if not ids_usuarios:
        return {}

    placeholders = ", ".join(["%s"] * len(ids_usuarios))

    cursor.execute(f"""
        SELECT 
            va.idUsuario,
            a.nombre AS atributo,
            va.valor
        FROM valores_atributos va
        JOIN atributos a ON a.idAtributo = va.idAtributo
        WHERE va.idUsuario IN ({placeholders})
    """, ids_usuarios)

    mapa = {}
    for row in cursor.fetchall():
        uid = row["idUsuario"]
        attr = row["atributo"]
        val = row["valor"]
        if uid not in mapa:
            mapa[uid] = {}
        mapa[uid][attr] = val

    return mapa
