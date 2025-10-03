import json
import os
from urllib import request as _urlreq
from urllib import parse as _urlparse
from urllib.error import HTTPError, URLError

CONFIG_FILE_PATH = "config.json"

CFG = {}
try:
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            CFG = json.load(f)
except Exception:
    CFG = {}

API_DB_BASE = CFG.get("API_DB_BASE", "http://127.0.0.1:4764")


# --- Función base para consultas ---
def _fetch_json(url: str, timeout: int = 20):
    req = _urlreq.Request(url, headers={"User-Agent": "SpiderSynBot/1.0"})
    try:
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            st = resp.getcode() or 200
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return st, json.loads(body)
            except Exception:
                return st, {"status": "error", "message": body}
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
            data = json.loads(body)
        except Exception:
            data = {"status": "error", "message": str(e)}
        return e.code, data
    except URLError as e:
        return 599, {"status": "error", "message": str(e)}


# --- Verificar usuario ---
def verificar_usuario(id_tg: str):
    """
    Devuelve (True, info_usuario) si el usuario existe y está ACTIVO.
    Devuelve (False, {}) si no existe o está inactivo.
    """
    st, js = _fetch_json(f"{API_DB_BASE}/tg_info?ID_TG={_urlparse.quote(id_tg)}")
    if st != 200:
        return False, {}
    data = js.get("data", {}) or {}
    estado = (data.get("ESTADO") or "").upper().strip()
    if estado != "ACTIVO":
        return False, data
    # Bandera de ilimitado por suscripción
    exp = data.get("FECHA DE CADUCIDAD")
    ilimitado = False
    from datetime import datetime, timezone
    if exp:
        try:
            exp_dt = datetime.fromisoformat(exp.replace("Z", "")).replace(tzinfo=timezone.utc)
            ilimitado = exp_dt > datetime.now(timezone.utc)
        except Exception:
            ilimitado = False
    data["ilimitado"] = ilimitado
    return True, data


# --- Descontar créditos ---
def descontar_creditos(id_tg: str, cantidad: int = 1):
    st, js = _fetch_json(f"{API_DB_BASE}/cred?ID_TG={_urlparse.quote(id_tg)}&operacion=restar&cantidad={cantidad}")
    if st != 200:
        return False, {}
    return True, js.get("data", {}) or {}
