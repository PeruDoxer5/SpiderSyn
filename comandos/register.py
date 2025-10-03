# comandos/register.py
import os
import json
import html
from urllib import request as _urlreq
from urllib.error import HTTPError, URLError

from telegram import Update
from telegram.ext import ContextTypes

API_BASE = "http://127.0.0.1:4764"
CONFIG_FILE_PATH = "config.json"

BOT_NAME = "SpiderSyn"
if os.path.exists(CONFIG_FILE_PATH):
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        BOT_NAME = (cfg.get("BOT_NAME") or "").strip()
    except Exception:
        BOT_NAME = ""

def _fetch_json(url: str, timeout: int = 15):
    req = _urlreq.Request(url, headers={"User-Agent": "tussybot/1.0"})
    try:
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode() or 200
            body = resp.read().decode("utf-8", errors="replace")
            try:
                import json as _json
                return status, _json.loads(body)
            except Exception:
                return status, {"status": "error", "message": body}
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
            import json as _json
            data = _json.loads(body)
        except Exception:
            data = {"status": "error", "message": str(e)}
        return e.code, data
    except URLError as e:
        return 599, {"status": "error", "message": str(e)}

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.effective_message
    id_tg = str(user.id)

    status, data = _fetch_json(f"{API_BASE}/register?ID_TG={id_tg}")

    nombre = html.escape(user.first_name or "Usuario")
    perfil = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"
    header = f"{BOT_NAME} REGISTRO".strip() or "REGISTRO"

    if status == 200:
        texto = (
            f"🎉 <b>{header}</b>\n\n"
            f"¡Bienvenido, <a href=\"{perfil}\">{nombre}</a>!\n"
            f"✅ <b>Registro completado</b>\n"
            f"🆔 <b>ID</b> ➾ <code>{id_tg}</code>\n\n"
            f"📌 Ya puedes usar <b>/me</b>, <b>/cmds</b> y más comandos."
        )
        await msg.reply_text(
            texto, parse_mode="HTML", disable_web_page_preview=True,
            reply_to_message_id=msg.message_id
        )
        return

    if status == 423:
        texto = (
            f"🎉 <b>{header}</b>\n\n"
            f"Hola, <a href=\"{perfil}\">{nombre}</a>.\n"
            f"⚠️ <b>Ya estabas registrado</b>\n"
            f"🆔 <b>ID</b> ➾ <code>{id_tg}</code>\n\n"
            f"Usa <b>/me</b> para ver tu perfil."
        )
        await msg.reply_text(
            texto, parse_mode="HTML", disable_web_page_preview=True,
            reply_to_message_id=msg.message_id
        )
        return

    texto = (
        f"❌ <b>{header}</b>\n\n"
        f"⚠️ Ocurrió un problema al registrar tu cuenta.\n"
        f"Código: <code>{status}</code>\n"
        f"Detalle: <code>{html.escape(str(data.get('message','Error desconocido')))}</code>"
    )
    await msg.reply_text(
        texto, parse_mode="HTML", disable_web_page_preview=True,
        reply_to_message_id=msg.message_id
    )
