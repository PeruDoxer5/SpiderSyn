from flask import Flask, jsonify, request
import sqlite3
from datetime import datetime, timedelta
import secrets
from collections import Counter
import math
import hashlib
import secrets
import time
import os
from flask_cors import CORS, cross_origin

DB_PATH = "multiplataforma.db"
HIST_DB_PATH = "historial.db"
COMPRAS_DB_PATH = "compras.db"
KEYS_DB_PATH = "keys.db"

app = Flask(__name__)

# -------------------------
# Utils
# -------------------------
def generate_unique_token() -> str:
    # 64 chars hex (SHA-256). Mezcla tiempo (ns) + entropía criptográfica
    seed = f"{time.time_ns()}:{secrets.token_hex(32)}".encode("utf-8")
    return hashlib.sha256(seed).hexdigest()

def now_utc() -> datetime:
    return datetime.utcnow().replace(microsecond=0)

def now_iso() -> str:
    return now_utc().isoformat() + "Z"

def parse_iso(dt_str: str) -> datetime:
    # Acepta "YYYY-mm-ddTHH:MM:SSZ" o sin 'Z'
    s = dt_str.strip()
    if s.endswith("Z"):
        s = s[:-1]
    return datetime.fromisoformat(s)

def get_conn(db_path=DB_PATH):
    return sqlite3.connect(db_path, check_same_thread=False)

def init_main_db():
    conn = get_conn(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id_tg TEXT PRIMARY KEY,
            rol_tg TEXT DEFAULT 'FREE',
            fecha_register_tg TEXT,

            creditos INTEGER DEFAULT 5,
            plan TEXT DEFAULT 'FREE',
            estado TEXT DEFAULT 'ACTIVO',
            fecha_caducidad TEXT,

            register_web INTEGER DEFAULT 0,   -- FALSE por defecto
            register_wsp INTEGER DEFAULT 0,   -- FALSE por defecto

            token_api_web TEXT UNIQUE,
            user_web TEXT,
            pass_web TEXT,
            rol_web TEXT DEFAULT 'FREE',
            fecha_register_web TEXT,

            token_api_wsp TEXT UNIQUE,
            number_wsp TEXT,
            rol_wsp TEXT DEFAULT 'FREE',
            fecha_register_wsp TEXT,

            antispam INTEGER DEFAULT 60
        );
        """
    )
    conn.commit()
    conn.close()

def init_keys_db():
    conn = get_conn(KEYS_DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        key TEXT PRIMARY KEY,
        tipo TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        usos INTEGER NOT NULL,
        creador_id INTEGER NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS redemptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        fecha_canje TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (key) REFERENCES keys(key)
    )
    """)

    conn.commit()
    conn.close()    

def init_hist_db():
    conn = get_conn(HIST_DB_PATH)
    cur = conn.cursor()
    # ¿Existe la tabla?
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historial';")
    exists = cur.fetchone() is not None

    if not exists:
        # Crear con el esquema nuevo (ID autoincremental y CHECK de plataforma)
        cur.execute(
            """
            CREATE TABLE historial (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_TG TEXT,
                consulta TEXT,
                valor TEXT,
                fecha TEXT,
                plataforma TEXT NOT NULL CHECK (plataforma IN ('TG','WEB','WSP'))
            );
            """
        )
        conn.commit()
        conn.close()
        return

    # Si existe, revisamos columnas; si estaba con ID_TG como PK, migramos.
    cur.execute("PRAGMA table_info(historial);")
    cols = [(r[1], r[5]) for r in cur.fetchall()]  # (name, pk)
    col_names = [c[0] for c in cols]
    # Esquema deseado:
    desired = ["ID", "ID_TG", "consulta", "valor", "fecha", "plataforma"]

    def needs_migration() -> bool:
        # Si no coincide EXACTO o si ID_TG es PK, migramos
        if col_names == desired and any(pk == 1 for (name, pk) in cols if name == "ID"):
            return False
        # Caso típico viejo: PK en ID_TG
        if "ID_TG" in col_names and any(pk == 1 for (name, pk) in cols if name == "ID_TG"):
            return True
        # Cualquier otra diferencia de esquema -> migrar por seguridad
        return True

    if needs_migration():
        # Crear tabla nueva, copiar datos, renombrar
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS historial_new (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_TG TEXT,
                consulta TEXT,
                valor TEXT,
                fecha TEXT,
                plataforma TEXT NOT NULL CHECK (plataforma IN ('TG','WEB','WSP'))
            );
            """
        )
        # Copiar lo que exista, normalizando plataforma a 'TG' si no cumple
        if "plataforma" in col_names:
            cur.execute(
                """
                INSERT INTO historial_new (ID_TG, consulta, valor, fecha, plataforma)
                SELECT 
                    COALESCE(ID_TG, ''), 
                    COALESCE(consulta, ''), 
                    COALESCE(valor, ''), 
                    COALESCE(fecha, ''), 
                    CASE WHEN plataforma IN ('TG','WEB','WSP') THEN plataforma ELSE 'TG' END
                FROM historial;
                """
            )
        else:
            # Tabla antigua sin 'plataforma'
            cur.execute(
                """
                INSERT INTO historial_new (ID_TG, consulta, valor, fecha, plataforma)
                SELECT 
                    COALESCE(ID_TG, ''), 
                    COALESCE(consulta, ''), 
                    COALESCE(valor, ''), 
                    COALESCE(fecha, ''), 
                    'TG'
                FROM historial;
                """
            )
        cur.execute("DROP TABLE historial;")
        cur.execute("ALTER TABLE historial_new RENAME TO historial;")
        conn.commit()

    conn.close()

def init_compras_db():
    conn = get_conn(COMPRAS_DB_PATH)
    cur = conn.cursor()

    # Ver si existe y si el esquema coincide
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compras';")
    exists = cur.fetchone() is not None

    recreate = False
    if exists:
        cur.execute("PRAGMA table_info(compras);")
        cols = [r[1] for r in cur.fetchall()]
        desired = ["ID_TG", "VENDEDOR", "FECHA", "COMPRO"]
        if cols != desired:
            recreate = True
    else:
        recreate = True

    if recreate:
        # ⚠️ Recrea (DROP + CREATE) — destruye datos previos si existen
        cur.execute("DROP TABLE IF EXISTS compras;")
        cur.execute(
            """
            CREATE TABLE compras (
                ID_TG TEXT PRIMARY KEY,
                VENDEDOR TEXT,
                FECHA TEXT,
                COMPRO TEXT
            );
            """
        )
        conn.commit()

    conn.close()

# -------------------------
# DB helpers
# -------------------------
def get_user_by_id(id_tg):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id_tg = ?", (id_tg,))
    row = cur.fetchone()
    conn.close()
    return row

def get_user_by_web_token(token):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE token_api_web = ?", (token,))
    row = cur.fetchone()
    conn.close()
    return row

def update_user_profile(user_id, credits, days_valid):
    """Actualiza los créditos y días válidos del usuario en su perfil en multplatatforma.db."""
    conn = sqlite3.connect("multiplataforma.db")  # Conectar a la base de datos de clientes
    cursor = conn.cursor()

    # Actualizar los créditos y días válidos del usuario
    cursor.execute("""
        UPDATE usuarios
        SET creditos = creditos + ?, fecha_caducidad = ?
        WHERE id_tg = ?
    """, (credits, days_valid, user_id))

    conn.commit()
    conn.close()

def get_user_by_wsp_token(token):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE token_api_wsp = ?", (token,))
    row = cur.fetchone()
    conn.close()
    return row

def create_user(id_tg):
    ts = now_iso()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO usuarios (
            id_tg, rol_tg, fecha_register_tg,
            creditos, plan, estado, fecha_caducidad,
            register_web, register_wsp,
            token_api_web, user_web, pass_web, rol_web, fecha_register_web,
            token_api_wsp, number_wsp, rol_wsp, fecha_register_wsp,
            antispam
        ) VALUES (
            ?, 'FREE', ?,
            5, 'FREE', 'ACTIVO', NULL,
            0, 0,
            NULL, NULL, NULL, 'FREE', NULL,
            NULL, NULL, 'FREE', NULL,
            60
        )
        """,
        (id_tg, ts),
    )
    conn.commit()
    conn.close()

def row_info_payload(row: sqlite3.Row):
    return {
        "ID_TG": row["id_tg"],
        "ROL_TG": row["rol_tg"],
        "FECHA_REGISTER_TG": row["fecha_register_tg"],
        "CREDITOS": row["creditos"],
        "PLAN": row["plan"],
        "ESTADO": row["estado"],
        "FECHA DE CADUCIDAD": row["fecha_caducidad"],
        "REGISTER_WEB": bool(row["register_web"]),
        "REGISTER_WSP": bool(row["register_wsp"]),
        "ROL_WEB": row["rol_web"],
        "ROL_WSP": row["rol_wsp"],
        "ANTISPAM": row["antispam"],
    }

# -------------------------
# Endpoints existentes resumidos (con mensajes)
# -------------------------

@app.route("/register", methods=["GET"])
def register():
    id_tg = request.args.get("ID_TG")
    if not id_tg:
        return jsonify({"status": "error", "exists": False, "message": "Falta el parámetro ID_TG"}), 400
    row = get_user_by_id(id_tg)
    if row:
        return jsonify({"status": "error", "exists": True, "message": "El usuario ya está registrado"}), 423
    create_user(id_tg)
    return jsonify({"status": "ok", "exists": False, "message": "Usuario registrado correctamente"}), 200

@app.route("/tg_info", methods=["GET"])
def tg_info():
    id_tg = request.args.get("ID_TG")
    if not id_tg:
        return jsonify({"status": "error", "message": "Falta el parámetro ID_TG"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    data = row_info_payload(row)
    return jsonify({"status": "ok", "message": "Información obtenida correctamente", "data": data}), 200

@app.route("/create_token_web", methods=["GET"])
def create_token_web():
    id_tg = request.args.get("ID_TG")
    if not id_tg:
        return jsonify({"status": "error", "message": "Falta el parámetro ID_TG"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    if row["token_api_web"] is not None:
        return jsonify({"status": "error", "message": "Ya existe un token WEB para este usuario"}), 423
    token = generate_unique_token()
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET token_api_web = ? WHERE id_tg = ?", (token, id_tg))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": "Token WEB creado correctamente"}), 200

@app.route("/create_token_wsp", methods=["GET"])
def create_token_wsp():
    id_tg = request.args.get("ID_TG")
    if not id_tg:
        return jsonify({"status": "error", "message": "Falta el parámetro ID_TG"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    if row["token_api_wsp"] is not None:
        return jsonify({"status": "error", "message": "Ya existe un token WSP para este usuario"}), 423
    token = generate_unique_token()
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET token_api_wsp = ? WHERE id_tg = ?", (token, id_tg))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": "Token WSP creado correctamente"}), 200

@app.route("/info_token_web", methods=["GET"])
def info_token_web():
    id_tg = request.args.get("ID_TG")
    if not id_tg:
        return jsonify({"status": "error", "message": "Falta el parámetro ID_TG"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    token = row["token_api_web"]
    if not token:
        return jsonify({"status": "error", "message": "Token WEB no encontrado para este usuario"}), 404
    return jsonify({"status": "ok", "message": "Token WEB obtenido correctamente", "TOKEN_API_WEB": token}), 200

@app.route("/info_token_wsp", methods=["GET"])
def info_token_wsp():
    id_tg = request.args.get("ID_TG")
    if not id_tg:
        return jsonify({"status": "error", "message": "Falta el parámetro ID_TG"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    token = row["token_api_wsp"]
    if not token:
        return jsonify({"status": "error", "message": "Token WSP no encontrado para este usuario"}), 404
    return jsonify({"status": "ok", "message": "Token WSP obtenido correctamente", "TOKEN_API_WSP": token}), 200

@app.route("/info_web", methods=["GET"])
def info_web():
    token = request.args.get("token")
    if not token:
        return jsonify({"status": "error", "message": "Falta el parámetro token"}), 400
    row = get_user_by_web_token(token)
    if not row:
        return jsonify({"status": "error", "message": "Token WEB no válido o usuario no encontrado"}), 404
    data = {
        "TOKEN_API_WEB": token,
        "ID_TG": row["id_tg"],
        "CREDITOS": row["creditos"],
        "PLAN": row["plan"],
        "ESTADO": row["estado"],
        "FECHA DE CADUCIDAD": row["fecha_caducidad"],
        "REGISTER_WEB": bool(row["register_web"]),
        "REGISTER_WSP": bool(row["register_wsp"]),
        "ROL_WEB": row["rol_web"],
        "FECHA_REGISTER_WEB": row["fecha_register_web"],
        "ANTISPAM": row["antispam"],
    }
    return jsonify({"status": "ok", "message": "Información WEB obtenida correctamente", "data": data}), 200

@app.route("/info_wsp", methods=["GET"])
def info_wsp():
    token = request.args.get("token")
    if not token:
        return jsonify({"status": "error", "message": "Falta el parámetro token"}), 400
    row = get_user_by_wsp_token(token)
    if not row:
        return jsonify({"status": "error", "message": "Token WSP no válido o usuario no encontrado"}), 404
    data = {
        "TOKEN_API_WSP": token,
        "ID_TG": row["id_tg"],
        "CREDITOS": row["creditos"],
        "PLAN": row["plan"],
        "ESTADO": row["estado"],
        "FECHA DE CADUCIDAD": row["fecha_caducidad"],
        "REGISTER_WEB": bool(row["register_web"]),
        "REGISTER_WSP": bool(row["register_wsp"]),
        "NUMBER_WSP": row["number_wsp"],
        "ROL_WSP": row["rol_wsp"],
        "FECHA_REGISTER_WSP": row["fecha_register_wsp"],
        "ANTISPAM": row["antispam"],
    }
    return jsonify({"status": "ok", "message": "Información WSP obtenida correctamente", "data": data}), 200

# -------------------------
# Activación WEB/WSP
# -------------------------
@app.route("/activate_wsp", methods=["GET"])
def activate_wsp():
    token = request.args.get("token")
    number_wsp = request.args.get("number_wsp")
    if not token or not number_wsp:
        return jsonify({"status": "error", "message": "Faltan parámetros: token y number_wsp son requeridos"}), 400
    row = get_user_by_wsp_token(token)
    if not row:
        return jsonify({"status": "error", "message": "Token WSP no válido o usuario no encontrado"}), 404
    if bool(row["register_wsp"]):
        return jsonify({"status": "error", "message": "WSP ya se encuentra activado para este usuario"}), 423
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET register_wsp = 1, number_wsp = ?, fecha_register_wsp = ? WHERE token_api_wsp = ?",
                (number_wsp, now_iso(), token))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": "WSP activado correctamente"}), 200

@app.route("/activate_web", methods=["GET"])
def activate_web():
    token = request.args.get("token")
    user = request.args.get("user")
    password = request.args.get("pass")
    if not token or not user or not password:
        return jsonify({"status": "error", "message": "Faltan parámetros: token, user y pass son requeridos"}), 400
    row = get_user_by_web_token(token)
    if not row:
        return jsonify({"status": "error", "message": "Token WEB no válido o usuario no encontrado"}), 404
    if bool(row["register_web"]):
        return jsonify({"status": "error", "message": "WEB ya se encuentra activado para este usuario"}), 423
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET register_web = 1, user_web = ?, pass_web = ?, fecha_register_web = ? WHERE token_api_web = ?",
                (user, password, now_iso(), token))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": "WEB activado correctamente"}), 200

# -------------------------
# Créditos (/cred) y Suscripción (/sub)
# -------------------------
@app.route("/cred", methods=["GET"])
def cred():
    id_tg = request.args.get("ID_TG")
    oper = (request.args.get("operacion") or "").strip().lower()
    cantidad_raw = request.args.get("cantidad")
    if not id_tg or not oper or cantidad_raw is None:
        return jsonify({"status": "error", "message": "Parámetros requeridos: ID_TG, operacion, cantidad"}), 400
    try:
        cantidad = int(cantidad_raw)
        if cantidad < 0:
            raise ValueError()
    except ValueError:
        return jsonify({"status": "error", "message": "cantidad debe ser un entero no negativo"}), 400

    if oper not in ("igualar", "sumar", "restar"):
        return jsonify({"status": "error", "message": "operacion debe ser igualar, sumar o restar"}), 400

    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

    current = int(row["creditos"] or 0)
    if oper == "igualar":
        new_val = cantidad
    elif oper == "sumar":
        new_val = current + cantidad
    else:  # restar
        new_val = max(0, current - cantidad)

    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET creditos = ? WHERE id_tg = ?", (new_val, id_tg))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": f"Créditos {oper} => {new_val}", "CREDITOS": new_val}), 200

@app.route("/sub", methods=["GET"])
def sub():
    id_tg = request.args.get("ID_TG")
    oper = (request.args.get("operacion") or "").strip().lower()
    cantidad_raw = request.args.get("cantidad")
    if not id_tg or not oper or cantidad_raw is None:
        return jsonify({"status": "error", "message": "Parámetros requeridos: ID_TG, operacion, cantidad"}), 400
    try:
        dias = int(cantidad_raw)
        if dias < 0:
            raise ValueError()
    except ValueError:
        return jsonify({"status": "error", "message": "cantidad debe ser un entero no negativo (días)"}), 400

    if oper not in ("igualar", "sumar", "restar"):
        return jsonify({"status": "error", "message": "operacion debe ser igualar, sumar o restar"}), 400

    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

    now = now_utc()
    fcad = row["fecha_caducidad"]
    # Reglas especiales:
    if fcad is None or str(fcad).strip() == "":
        if oper in ("sumar", "igualar"):
            new_dt = now + timedelta(days=dias)
        else:  # restar desde NULL no tiene sentido
            return jsonify({"status": "error", "message": "No se puede restar días: la fecha de caducidad está vacía"}), 400
    else:
        try:
            current_dt = parse_iso(fcad)
        except Exception:
            current_dt = now  # si hay formato inesperado, normalizamos
        if current_dt < now:
            # Si ya venció: igualar a ahora + dias (sin importar la operación)
            new_dt = now + timedelta(days=dias)
        else:
            if oper == "igualar":
                new_dt = now + timedelta(days=dias)
            elif oper == "sumar":
                new_dt = current_dt + timedelta(days=dias)
            else:  # restar
                new_dt = current_dt - timedelta(days=dias)

    new_iso = new_dt.replace(microsecond=0).isoformat() + "Z"
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET fecha_caducidad = ? WHERE id_tg = ?", (new_iso, id_tg))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": f"Fecha de caducidad {oper}", "FECHA_DE_CADUCIDAD": new_iso}), 200

# -------------------------
# Plan y Roles
# -------------------------
PLANES_VALIDOS = {"PREMIUM", "STANDARD", "BASICO", "FREE"}
ROLES_VALIDOS = {"FREE", "CLIENTE", "SELLER", "CO-FUNDADOR", "FUNDADOR"}

@app.route("/plan", methods=["GET"])
def set_plan():
    id_tg = request.args.get("ID_TG")
    plan = (request.args.get("plan") or "").upper()
    if not id_tg or not plan:
        return jsonify({"status": "error", "message": "Parámetros requeridos: ID_TG, plan"}), 400
    if plan not in PLANES_VALIDOS:
        return jsonify({"status": "error", "message": f"plan inválido. Opciones: {', '.join(PLANES_VALIDOS)}"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET plan = ? WHERE id_tg = ?", (plan, id_tg))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": f"Plan actualizado a {plan}"}), 200

@app.route("/rol_wsp", methods=["GET"])
def set_rol_wsp():
    id_tg = request.args.get("ID_TG")
    rol = (request.args.get("rol") or "").upper()
    if not id_tg or not rol:
        return jsonify({"status": "error", "message": "Parámetros requeridos: ID_TG, rol"}), 400
    if rol not in ROLES_VALIDOS:
        return jsonify({"status": "error", "message": f"rol inválido. Opciones: {', '.join(ROLES_VALIDOS)}"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET rol_wsp = ? WHERE id_tg = ?", (rol, id_tg))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": f"ROL_WSP actualizado a {rol}"}), 200

@app.route("/rol_web", methods=["GET"])
def set_rol_web():
    id_tg = request.args.get("ID_TG")
    rol = (request.args.get("rol") or "").upper()
    if not id_tg or not rol:
        return jsonify({"status": "error", "message": "Parámetros requeridos: ID_TG, rol"}), 400
    if rol not in ROLES_VALIDOS:
        return jsonify({"status": "error", "message": f"rol inválido. Opciones: {', '.join(ROLES_VALIDOS)}"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET rol_web = ? WHERE id_tg = ?", (rol, id_tg))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": f"ROL_WEB actualizado a {rol}"}), 200

@app.route("/rol_tg", methods=["GET"])
def set_rol_tg():
    id_tg = request.args.get("ID_TG")
    rol = (request.args.get("rol") or "").upper()
    if not id_tg or not rol:
        return jsonify({"status": "error", "message": "Parámetros requeridos: ID_TG, rol"}), 400
    if rol not in ROLES_VALIDOS:
        return jsonify({"status": "error", "message": f"rol inválido. Opciones: {', '.join(ROLES_VALIDOS)}"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET rol_tg = ? WHERE id_tg = ?", (rol, id_tg))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": f"ROL_TG actualizado a {rol}"}), 200

# -------------------------
# Antispam
# -------------------------
@app.route("/antispam", methods=["GET"])
def set_antispam():
    id_tg = request.args.get("ID_TG")
    val_raw = request.args.get("valor")
    if not id_tg or val_raw is None:
        return jsonify({"status": "error", "message": "Parámetros requeridos: ID_TG, valor"}), 400
    try:
        val = int(val_raw)
        if val < 0:
            raise ValueError()
    except ValueError:
        return jsonify({"status": "error", "message": "valor debe ser un entero no negativo"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET antispam = ? WHERE id_tg = ?", (val, id_tg))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": f"ANTISPAM actualizado a {val}", "ANTISPAM": val}), 200

# -------------------------
# Compras e Historial
# -------------------------
@app.route("/compras", methods=["GET"])
def compras():
    # Ahora ID_TG es el identificador del cliente
    id_tg = request.args.get("ID_TG")
    id_vendedor = request.args.get("ID_VENDEDOR")
    cantidad = request.args.get("CANTIDAD")  # p.ej. "DIAS:30" o "CREDITOS:100" o un número

    if not id_tg or not id_vendedor or not cantidad:
        return jsonify({
            "status": "error",
            "message": "Parámetros requeridos: ID_TG, ID_VENDEDOR, CANTIDAD"
        }), 400

    # Validar que el cliente exista en usuarios
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario (ID_TG) no encontrado"}), 404

    fecha = now_iso()  # fecha automática

    # Guardar/actualizar compra del usuario (REPLACE por PK ID_TG)
    conn = get_conn(COMPRAS_DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO compras (ID_TG, VENDEDOR, FECHA, COMPRO)
        VALUES (?, ?, ?, ?)
        """,
        (id_tg, id_vendedor, fecha, cantidad)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "message": "Compra registrada",
        "FECHA": fecha
    }), 200

@app.route("/historial", methods=["GET"])
def historial():
    # Requeridos
    id_tg = request.args.get("ID_TG")
    consulta = request.args.get("CONSULTA")
    valor = request.args.get("VALOR")
    plataforma = (request.args.get("PLATAFORMA") or "").upper().strip()

    if not id_tg or not consulta or not valor or not plataforma:
        return jsonify({
            "status": "error",
            "message": "Parámetros requeridos: ID_TG, CONSULTA, VALOR, PLATAFORMA"
        }), 400

    if plataforma not in {"TG", "WEB", "WSP"}:
        return jsonify({
            "status": "error",
            "message": "PLATAFORMA inválida. Valores permitidos: TG, WEB, WSP"
        }), 400

    # Validar que el usuario exista
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario (ID_TG) no encontrado"}), 404

    fecha = now_iso()  # fecha automática en servidor

    # INSERT simple (NO REPLACE) para no sobrescribir registros anteriores
    conn = get_conn(HIST_DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO historial (ID_TG, consulta, valor, fecha, plataforma) VALUES (?, ?, ?, ?, ?)",
        (id_tg, consulta, valor, fecha, plataforma)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok",
        "message": "Historial registrado",
        "FECHA": fecha
    }), 200


# -------------------------
# Reset y Estado
# -------------------------
@app.route("/reset", methods=["GET"])
def reset_user():
    id_tg = request.args.get("ID_TG")
    if not id_tg:
        return jsonify({"status": "error", "message": "Falta el parámetro ID_TG"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        """
        UPDATE usuarios
        SET plan='FREE',
            rol_tg='FREE',
            rol_web='FREE',
            rol_wsp='FREE',
            creditos=5,
            fecha_caducidad=NULL,
            antispam=60,
            estado='ACTIVO'
        WHERE id_tg = ?
        """,
        (id_tg,)
    )
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": "Usuario reseteado a valores por defecto"}), 200

@app.route("/estado", methods=["GET"])
def estado():
    id_tg = request.args.get("ID_TG")
    valor = (request.args.get("valor") or "").upper()
    if not id_tg or not valor:
        return jsonify({"status": "error", "message": "Parámetros requeridos: ID_TG, valor"}), 400
    if valor not in {"ACTIVO", "BANEADO"}:
        return jsonify({"status": "error", "message": "valor inválido. Opciones: ACTIVO, BANEADO"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE usuarios SET estado = ? WHERE id_tg = ?", (valor, id_tg))
    conn.commit(); conn.close()
    return jsonify({"status": "ok", "message": f"Estado actualizado a {valor}"}), 200

def _safe_parse_date(s: str):
    if not s:
        return None
    try:
        ds = s.strip()
        if ds.endswith("Z"):
            ds = ds[:-1]
        return datetime.fromisoformat(ds)
    except Exception:
        return None

@app.route("/estadisticas", methods=["GET"])
def estadisticas():
    try:
        # --------- HISTORIAL: conteos hoy / globales y tops ----------
        today = now_utc().date()

        # Leer historial
        h_conn = get_conn(HIST_DB_PATH)
        h_conn.row_factory = sqlite3.Row
        h_cur = h_conn.cursor()
        h_cur.execute("SELECT ID_TG, consulta, fecha FROM historial;")
        h_rows = h_cur.fetchall()
        h_conn.close()

        consultas_globales = 0
        consultas_hoy = 0
        top_cmd_global = Counter()
        top_cmd_hoy = Counter()
        top_user_global = Counter()
        top_user_hoy = Counter()

        for r in h_rows:
            consultas_globales += 1
            consulta = (r["consulta"] or "").strip()
            uid = (r["ID_TG"] or "").strip()
            top_cmd_global[consulta] += 1
            top_user_global[uid] += 1

            d = _safe_parse_date(r["fecha"])
            if d and d.date() == today:
                consultas_hoy += 1
                top_cmd_hoy[consulta] += 1
                top_user_hoy[uid] += 1

        # Top lists
        top20_cmd_hoy = [{"consulta": k, "total": v} for k, v in top_cmd_hoy.most_common(20)]
        top30_user_hoy = [{"ID_TG": k, "total": v} for k, v in top_user_hoy.most_common(30)]
        top30_cmd_global = [{"consulta": k, "total": v} for k, v in top_cmd_global.most_common(30)]
        top30_user_global = [{"ID_TG": k, "total": v} for k, v in top_user_global.most_common(30)]

        # --------- USUARIOS: créditos, planes y días ----------
        u_conn = get_conn(DB_PATH)
        u_conn.row_factory = sqlite3.Row
        u_cur = u_conn.cursor()
        u_cur.execute("SELECT id_tg, creditos, plan, fecha_caducidad FROM usuarios;")
        users = u_cur.fetchall()
        u_conn.close()

        total_users = len(users)
        creditos_totales = 0
        inactivos_5 = 0              # creditos == 5
        creditos_cero = 0            # creditos == 0
        cinco_o_1k = 0               # creditos == 5 OR creditos == 1000 (interpretación literal del ejemplo)
        mas_1k = 0                   # creditos > 1000
        mas_5 = 0                    # creditos > 5

        planes_count = Counter()

        # Días (suscripción)
        now_dt = now_utc()
        con_plan_activo = 0          # fecha_caducidad > now
        sin_plan_activado = 0        # fecha_caducidad IS NULL
        con_plan_vencido = 0         # fecha_caducidad <= now
        rangos_dias = {
            "0-7": 0,
            "8-15": 0,
            "16-30": 0,
            "31-59": 0,
            "60+": 0
        }

        # Listas para tops
        top_creditos = []
        top_dias = []

        for u in users:
            uid = u["id_tg"]
            cred = int(u["creditos"] or 0)
            plan = (u["plan"] or "FREE").upper()
            fcad = _safe_parse_date(u["fecha_caducidad"])  # puede ser None

            creditos_totales += cred
            if cred == 5: inactivos_5 += 1
            if cred == 0: creditos_cero += 1
            if cred == 5 or cred == 1000: cinco_o_1k += 1
            if cred > 1000: mas_1k += 1
            if cred > 5: mas_5 += 1

            planes_count[plan] += 1
            top_creditos.append({"ID_TG": uid, "CREDITOS": cred})

            # días restantes
            if fcad is None:
                sin_plan_activado += 1
            else:
                # normalizar a "estado"
                if fcad <= now_dt:
                    con_plan_vencido += 1
                else:
                    con_plan_activo += 1
                    # días restantes (redondeo hacia arriba para que 0.1d cuente como 1)
                    days_left = math.ceil((fcad - now_dt).total_seconds() / 86400.0)
                    # rangos
                    if 1 <= days_left <= 7:
                        rangos_dias["0-7"] += 1
                    elif 8 <= days_left <= 15:
                        rangos_dias["8-15"] += 1
                    elif 16 <= days_left <= 30:
                        rangos_dias["16-30"] += 1
                    elif 31 <= days_left <= 59:
                        rangos_dias["31-59"] += 1
                    elif days_left >= 60:
                        rangos_dias["60+"] += 1
                    top_dias.append({"ID_TG": uid, "DIAS": days_left})

        # ordenamientos
        top20_usuarios_mas_creditos = sorted(top_creditos, key=lambda x: x["CREDITOS"], reverse=True)[:20]
        top30_usuarios_mas_dias = sorted(top_dias, key=lambda x: x["DIAS"], reverse=True)[:30]

        # Bloques agregados
        creditos_globales = {
            "Usuarios_totales": total_users,
            "Inactivos_5_credits": inactivos_5,
            "Con_0_credits": creditos_cero,
            "Con_5_o_1k_credits": cinco_o_1k,
            "Con_mas_1k_credits": mas_1k,
            "Con_credits_mas_5": mas_5,
            "Creditos_totales": creditos_totales,
            "Por_plan": {
                "BASICO": planes_count.get("BASICO", 0),
                "FREE": planes_count.get("FREE", 0),
                "PREMIUM": planes_count.get("PREMIUM", 0),
                "STANDARD": planes_count.get("STANDARD", 0),
            }
        }

        dias_globales = {
            "Usuarios_totales": total_users,
            "Con_plan_activo": con_plan_activo,
            "Sin_plan_activado": sin_plan_activado,
            "Con_plan_vencido": con_plan_vencido,
            "Rangos": {
                "-_7_dias": rangos_dias["0-7"],
                "8_15_dias": rangos_dias["8-15"],
                "16_30_dias": rangos_dias["16-30"],
                "31_59_dias": rangos_dias["31-59"],
                "+_60_dias": rangos_dias["60+"]
            }
        }

        # ---------- Render estilo texto para bots ----------
        def fmt_num(n):  # separador de miles
            return f"{n:,}".replace(",", ".")

        lines = []
        lines.append(f"CONSULTAS_HOY ➾ {fmt_num(consultas_hoy)}")
        lines.append(f"CONSULTAS_GLOBALES ➾ {fmt_num(consultas_globales)}")
        lines.append("")
        lines.append("TOP 20 COMANDOS HOY:")
        for item in top20_cmd_hoy:
            c = item['consulta'] or "(vacío)"
            lines.append(f"• {c} ➾ {fmt_num(item['total'])}")
        lines.append("")
        lines.append("TOP 30 USUARIOS DE HOY:")
        for item in top30_user_hoy:
            uid = item['ID_TG'] or "(desconocido)"
            lines.append(f"• {uid} ➾ {fmt_num(item['total'])}")
        lines.append("")
        lines.append("TOP 30 COMANDOS GLOBALES:")
        for item in top30_cmd_global:
            c = item['consulta'] or "(vacío)"
            lines.append(f"• {c} ➾ {fmt_num(item['total'])}")
        lines.append("")
        lines.append("TOP 30 USUARIOS GLOBALES:")
        for item in top30_user_global:
            uid = item['ID_TG'] or "(desconocido)"
            lines.append(f"• {uid} ➾ {fmt_num(item['total'])}")
        lines.append("")
        lines.append("CREDITOS GLOBALES")
        lines.append(f"• Usuarios totales ➾ {fmt_num(total_users)}")
        lines.append(f"• Inactivos (5 créditos) ➾ {fmt_num(inactivos_5)}")
        lines.append(f"• Con 0 créditos ➾ {fmt_num(creditos_cero)}")
        lines.append(f"• Con 5 o 1k créditos ➾ {fmt_num(cinco_o_1k)}")
        lines.append(f"• Con +1k créditos ➾ {fmt_num(mas_1k)}")
        lines.append(f"• Con créditos (+5) ➾ {fmt_num(mas_5)}")
        lines.append(f"• Créditos totales ➾ {fmt_num(creditos_totales)}")
        lines.append(f"• BASICO ➾ {fmt_num(planes_count.get('BASICO', 0))} Usuarios")
        lines.append(f"• FREE ➾ {fmt_num(planes_count.get('FREE', 0))} Usuarios")
        lines.append(f"• PREMIUM ➾ {fmt_num(planes_count.get('PREMIUM', 0))} Usuarios")
        lines.append(f"• STANDARD ➾ {fmt_num(planes_count.get('STANDARD', 0))} Usuarios")
        lines.append("")
        lines.append("TOP 20 USUARIOS CON MÁS CRÉDITOS")
        for item in top20_usuarios_mas_creditos:
            lines.append(f"• {item['ID_TG']} ➾ {fmt_num(item['CREDITOS'])}")
        lines.append("")
        lines.append("DIAS GLOBALES")
        lines.append(f"• Usuarios totales ➾ {fmt_num(total_users)}")
        lines.append(f"• Con plan activo ➾ {fmt_num(con_plan_activo)}")
        lines.append(f"• Sin plan activado ➾ {fmt_num(sin_plan_activado)}")
        lines.append(f"• Con plan vencido ➾ {fmt_num(con_plan_vencido)}")
        lines.append(f"• Con - 7 días ➾ {fmt_num(rangos_dias['0-7'])}")
        lines.append(f"• Con 8-15 días ➾ {fmt_num(rangos_dias['8-15'])}")
        lines.append(f"• Con 16-30 días ➾ {fmt_num(rangos_dias['16-30'])}")
        lines.append(f"• Con 31-59 días ➾ {fmt_num(rangos_dias['31-59'])}")
        lines.append(f"• Con + 60 días ➾ {fmt_num(rangos_dias['60+'])}")
        lines.append("")
        lines.append("TOP 30 USUARIOS CON MÁS DÍAS")
        for item in top30_usuarios_mas_dias:
            lines.append(f"• {item['ID_TG']} ➾ {fmt_num(item['DIAS'])}")

        render_text = "\n".join(lines)

        # ---------- RESpuesta JSON estructurada ----------
        data = {
            "CONSULTAS_HOY": consultas_hoy,
            "CONSULTAS_GLOBALES": consultas_globales,
            "TOP_20_COMANDOS_HOY": top20_cmd_hoy,
            "TOP_30_USUARIOS_HOY": top30_user_hoy,
            "TOP_30_COMANDOS_GLOBALES": top30_cmd_global,
            "TOP_30_USUARIOS_GLOBALES": top30_user_global,
            "CREDITOS_GLOBALES": creditos_globales,
            "TOP_20_USUARIOS_MAS_CREDITOS": top20_usuarios_mas_creditos,
            "DIAS_GLOBALES": dias_globales,
            "TOP_30_USUARIOS_MAS_DIAS": top30_usuarios_mas_dias,
        }

        return jsonify({
            "status": "ok",
            "message": "Estadísticas generadas",
            "data": data,
            "render": render_text
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error generando estadísticas: {e}"
        }), 500

@app.route("/compras_id", methods=["GET"])
def compras_id():
    id_tg = request.args.get("ID_TG")
    if not id_tg:
        return jsonify({"status": "error", "message": "Falta el parámetro ID_TG"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    conn = get_conn(COMPRAS_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT ID_TG, VENDEDOR, FECHA, COMPRO FROM compras WHERE ID_TG = ? ORDER BY FECHA DESC", (id_tg,))
    rows = cur.fetchall()
    conn.close()
    data = [{"ID_TG": r["ID_TG"], "ID_VENDEDOR": r["VENDEDOR"], "FECHA": r["FECHA"], "CANTIDAD": r["COMPRO"]} for r in rows]
    msg = "Compras listadas" if data else "Sin compras para este ID_TG"
    return jsonify({"status": "ok", "message": msg, "data": data}), 200

@app.route("/hist_venta_id", methods=["GET"])
def hist_venta_id():
    id_vendedor = request.args.get("ID_VENDEDOR")
    if not id_vendedor:
        return jsonify({"status": "error", "message": "Falta el parámetro ID_VENDEDOR"}), 400
    conn = get_conn(COMPRAS_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT ID_TG, VENDEDOR, FECHA, COMPRO FROM compras WHERE VENDEDOR = ? ORDER BY FECHA DESC", (id_vendedor,))
    rows = cur.fetchall()
    conn.close()
    data = [{"ID_TG": r["ID_TG"], "ID_VENDEDOR": r["VENDEDOR"], "FECHA": r["FECHA"], "CANTIDAD": r["COMPRO"]} for r in rows]
    msg = "Ventas listadas" if data else "Sin ventas para este vendedor"
    return jsonify({"status": "ok", "message": msg, "data": data}), 200

@app.route("/historial_id", methods=["GET"])
def historial_id():
    id_tg = request.args.get("ID_TG")
    if not id_tg:
        return jsonify({"status": "error", "message": "Falta el parámetro ID_TG"}), 400
    row = get_user_by_id(id_tg)
    if not row:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    conn = get_conn(HIST_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT ID_TG, consulta, valor, fecha, plataforma FROM historial WHERE ID_TG = ? ORDER BY fecha DESC, ID DESC", (id_tg,))
    rows = cur.fetchall()
    conn.close()
    data = [{"ID_TG": r["ID_TG"], "CONSULTA": r["consulta"], "VALOR": r["valor"], "FECHA": r["fecha"], "PLATAFORMA": r["plataforma"]} for r in rows]
    msg = "Historial listado" if data else "Sin historial para este ID_TG"
    return jsonify({"status": "ok", "message": msg, "data": data}), 200

@app.route("/login_web", methods=["GET", "POST"])
@cross_origin(
    origins=["http://127.0.0.1:5500"],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"]
)
def login_web():
    """
    Login WEB:
      - Parâmetros: user, pass  (en querystring GET o en form-data/x-www-form-urlencoded POST)
      - Requisitos: el usuario debe existir con register_web=1
      - Resultado: TOKEN_API_WEB (si no existe, se genera y se retorna)
    """
    # Obtener credenciales desde args o form
    user = (request.values.get("user") or "").strip()
    password = (request.values.get("pass") or "").strip()

    if not user or not password:
        return jsonify({
            "status": "error",
            "message": "Parámetros requeridos: user y pass"
        }), 400

    # Buscar usuario por user_web (case-insensitive)
    conn = get_conn(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM usuarios WHERE LOWER(user_web) = LOWER(?)",
        (user,)
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Usuario WEB no encontrado"
        }), 404

    # Verificar que tenga WEB activado
    if not bool(row["register_web"]):
        conn.close()
        return jsonify({
            "status": "error",
            "message": "WEB no está activado para este usuario"
        }), 423

    # Validar contraseña (texto plano según esquema actual)
    if (row["pass_web"] or "") != password:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "Credenciales inválidas"
        }), 401

    # Asegurar token_api_web (si no existe, generarlo)
    token = row["token_api_web"]
    created = False
    if not token:
        token = generate_unique_token()
        cur.execute(
            "UPDATE usuarios SET token_api_web = ? WHERE id_tg = ?",
            (token, row["id_tg"])
        )
        conn.commit()
        created = True

    # Respuesta OK con datos útiles
    payload = {
        "TOKEN_API_WEB": token,
        "ID_TG": row["id_tg"],
        "PLAN": row["plan"],
        "ESTADO": row["estado"],
        "CREDITOS": row["creditos"],
        "FECHA_DE_CADUCIDAD": row["fecha_caducidad"],
        "ANTISPAM": row["antispam"],
        "TOKEN_CREATED": created
    }
    conn.close()
    return jsonify({
        "status": "ok",
        "message": "Login correcto",
        "data": payload
    }), 200


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    init_main_db()
    init_hist_db()
    init_compras_db()
    init_keys_db()
port = int(os.environ.get('PORT', '4764'))
app.run(host='0.0.0.0', port=port, debug=False)
