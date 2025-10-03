# comandos/compras_cmd.py
import os
import io
import json
import html
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from urllib import parse as _urlparse
from urllib import request as _urlreq
from urllib.error import HTTPError, URLError

from telegram import Update, InputFile
from telegram.ext import ContextTypes

API_DB_BASE = "https://web-production-843d9.up.railway.app"   # tg_info, compras_id
CONFIG_FILE_PATH = "config.json"

# ================== Carga de config ==================
CFG = {}
try:
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            CFG = json.load(f)
except Exception:
    CFG = {}

BOT_NAME = (CFG.get("BOT_NAME") or "").strip() or "#BOT"
ADMIN_IDS = set(CFG.get("ADMIN_ID") or [])

# ================== Utilidades HTTP ==================
def _fetch_json(url: str, timeout: int = 20):
    req = _urlreq.Request(url, headers={"User-Agent": "tussybot/1.0"})
    try:
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            st = resp.getcode() or 200
            body = resp.read().decode("utf-8", errors="replace")
            try:
                import json as _j
                return st, _j.loads(body)
            except Exception:
                return st, {"status": "error", "message": body}
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
            import json as _j
            data = _j.loads(body)
        except Exception:
            data = {"status": "error", "message": str(e)}
        return e.code, data
    except URLError as e:
        return 599, {"status": "error", "message": str(e)}

# ================== Utilidades de tiempo ==================
def _to_lima(iso: str | None) -> str:
    if not iso:
        return "—"
    s = iso.strip()
    if s.endswith("Z"):
        s = s[:-1]
    try:
        dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception:
        return iso
    try:
        dt = dt.astimezone(ZoneInfo("America/Lima"))
    except Exception:
        pass
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# ================== Autorización ==================
_ALLOWED_ROLES = {"FUNDADOR", "CO-FUNDADOR", "SELLER"}

def _get_user_info(id_tg: str):
    return _fetch_json(f"{API_DB_BASE}/tg_info?ID_TG={_urlparse.quote(id_tg)}")

def _is_authorized_viewer(viewer_id: int, viewer_info: dict) -> bool:
    """
    Puede ver compras de terceros si:
    - ROL_TG ∈ {FUNDADOR, CO-FUNDADOR, SELLER}, o
    - Está en ADMIN_ID del config.json
    """
    if viewer_id in ADMIN_IDS:
        return True
    data = viewer_info.get("data", {}) or {}
    rol = (data.get("ROL_TG") or "").upper()
    return rol in _ALLOWED_ROLES

# ================== Render TXT ==================
def _build_compras_txt(bot_name: str, owner_id: str, filas: list[dict]) -> bytes:
    # Ordenar por fecha DESC
    def _key(r):
        f = r.get("FECHA")
        if not f:
            return ""
        return f
    rows = sorted(filas, key=_key, reverse=True)

    total = len(rows)
    por_vendedor = {}
    total_dias = 0  # acumula días si el campo CANTIDAD trae "X DIAS"

    for r in rows:
        vend = str(r.get("ID_VENDEDOR") or "—")
        por_vendedor[vend] = por_vendedor.get(vend, 0) + 1
        # Intentar extraer número de días de "CANTIDAD" (ej: "123 DIAS")
        cant = (r.get("CANTIDAD") or "").upper().strip()
        # Busca el entero inicial de la cadena
        num = None
        for token in cant.split():
            if token.isdigit():
                num = int(token)
                break
        if num is not None and "DIA" in cant:
            total_dias += num

    header = [
        f"{bot_name} - COMPRAS REGISTRADAS",
        f"ID_TG: {owner_id}",
        "-"*48,
        f"Total de compras: {total}",
        f"Suma aproximada de días adquiridos: {total_dias}",
    ]
    if por_vendedor:
        header.append("Por vendedor (ID_VENDEDOR):")
        for k, v in sorted(por_vendedor.items(), key=lambda x: (-x[1], x[0])):
            header.append(f"  - {k}: {v}")
    header.append("-"*48)
    header.append("")

    # Tabla
    lines = []
    lines.append("FECHA_LIMA           | CANTIDAD       | VENDEDOR")
    lines.append("---------------------+----------------+---------")
    for r in rows:
        fecha = _to_lima(r.get("FECHA"))
        cantidad = (r.get("CANTIDAD") or "—")[:14]
        vendedor = str(r.get("ID_VENDEDOR") or "—")
        lines.append(f"{fecha:21} | {cantidad:14} | {vendedor}")

    content = "\n".join(header + lines) + "\n"
    return content.encode("utf-8", errors="replace")

# ================== Comando ==================
async def compras_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    caller_id = str(user.id)

    # 1) Solo en privado
    if not chat or str(chat.type).lower() != "private":
        await msg.reply_text(
            "⚠️ Este comando solo puede usarse por privado.",
            reply_to_message_id=msg.message_id
        )
        return

    # 2) /compras → propio | /compras ID → terceros (si autorizado)
    target_id = caller_id
    viewing_third_party = False

    if context.args:
        arg = "".join(context.args).strip()
        if arg.isdigit():
            target_id = arg
            viewing_third_party = (target_id != caller_id)
        else:
            await msg.reply_text(
                "Uso: <code>/compras</code> (propias) o <code>/compras ID</code>",
                parse_mode="HTML",
                reply_to_message_id=msg.message_id
            )
            return

    # 3) Si verán tercero, validar permisos del solicitante
    if viewing_third_party:
        st_view, js_view = _get_user_info(caller_id)
        if st_view != 200:
            await msg.reply_text(
                f"⚠️ No se pudo validar tu rol (code {st_view}).",
                reply_to_message_id=msg.message_id
            )
            return
        if not _is_authorized_viewer(int(caller_id), js_view):
            await msg.reply_text(
                "🚫 No tienes permisos para ver las compras de otros usuarios.",
                reply_to_message_id=msg.message_id
            )
            return

    # 4) Obtener compras del target
    st_c, js_c = _fetch_json(f"{API_DB_BASE}/compras_id?ID_TG={_urlparse.quote(target_id)}")
    if st_c != 200:
        await msg.reply_text(
            f"⚠️ No se pudieron obtener las compras (code {st_c}).",
            reply_to_message_id=msg.message_id
        )
        return

    filas = js_c.get("data", []) or []

    # 5) Construir TXT y enviar
    pretty_bot = (BOT_NAME or "#BOT").strip()
    data_bytes = _build_compras_txt(pretty_bot, target_id, filas)
    filename = f"compras_{target_id}.txt"

    bio = io.BytesIO(data_bytes)
    bio.name = filename

    caption = (
        f"<b>{pretty_bot} • Exportación de compras</b>\n"
        f"ID consultado: <code>{html.escape(target_id)}</code>\n"
        f"Registros: <b>{len(filas)}</b>"
    )

    await msg.reply_document(
        document=InputFile(bio, filename=filename),
        caption=caption,
        parse_mode="HTML",
        reply_to_message_id=msg.message_id
    )
