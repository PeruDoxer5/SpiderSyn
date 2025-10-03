# comandos/me.py
import os
import json
import html
import sqlite3
import json as jsonlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Tuple
from urllib import request as _urlreq
from urllib.error import HTTPError, URLError

from telegram import Update
from telegram.ext import ContextTypes

API_BASE = "http://127.0.0.1:4764"
CONFIG_FILE_PATH = "config.json"

BOT_NAME = ""
if os.path.exists(CONFIG_FILE_PATH):
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        BOT_NAME = (cfg.get("BOT_NAME") or "").strip()
    except Exception:
        BOT_NAME = ""

def _to_lima_iso_hm(iso_str: Optional[str]) -> str:
    if not iso_str:
        return "—"
    s = iso_str.strip()
    if s.endswith("Z"):
        s = s[:-1]
    try:
        dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception:
        return iso_str
    try:
        lima = dt.astimezone(ZoneInfo("America/Lima"))
    except Exception:
        lima = dt
    return lima.strftime("%Y-%m-%d %H:%M:%S")

def _days_left(exp_iso: Optional[str]) -> Tuple[str, bool, Optional[int]]:
    if not exp_iso:
        return ("Sin plan", False, None)
    s = exp_iso.strip()
    if s.endswith("Z"):
        s = s[:-1]
    try:
        exp = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception:
        return (exp_iso, False, None)
    now = datetime.now(timezone.utc)
    delta = exp - now
    days = int(delta.total_seconds() // 86400)
    if delta.total_seconds() <= 0:
        return (f"Vencido hace {abs(days)} día(s)", False, max(days, 0))
    return (f"{days} día(s)", True, days)

def _fetch_json(url: str, timeout: int = 15):
    req = _urlreq.Request(url, headers={"User-Agent": "tussybot/1.0"})
    try:
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode() or 200
            data = resp.read().decode("utf-8", errors="replace")
            try:
                return status, jsonlib.loads(data)
            except Exception:
                return status, {"status": "error", "message": data}
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
            data = jsonlib.loads(body)
        except Exception:
            data = {"status": "error", "message": str(e)}
        return e.code, data
    except URLError as e:
        return 599, {"status": "error", "message": str(e)}

async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    invoker = update.effective_user
    msg = update.effective_message

    # —— Soportar /me y /me <ID_TG>
    target_id = str(invoker.id)
    if context.args:
        arg = (context.args[0] or "").strip()
        if arg.isdigit():
            target_id = arg
        else:
            await msg.reply_text(
                "⚠️ Formato inválido. Usa <code>/me</code> o <code>/me ID_TG</code>.",
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_to_message_id=msg.message_id,
            )
            return

    # —— Consultar API con el ID objetivo
    s1, j1 = _fetch_json(f"{API_BASE}/tg_info?ID_TG={target_id}")
    if s1 == 404:
        await msg.reply_text(
            "⚠️ Usuario no encontrado en la base. Usa /register primero.",
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_to_message_id=msg.message_id,
        )
        return
    if s1 != 200:
        await msg.reply_text(
            f"⚠️ Error consultando perfil (code {s1}): <code>{html.escape(str(j1.get('message','error')))}</code>",
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_to_message_id=msg.message_id,
        )
        return

    data = j1.get("data", {}) or {}
    antispam = data.get("ANTISPAM")
    creditos = data.get("CREDITOS")
    estado = data.get("ESTADO")
    fecha_reg = data.get("FECHA_REGISTER_TG")
    id_api = data.get("ID_TG")
    plan = data.get("PLAN")
    rol_tg = data.get("ROL_TG")
    exp = data.get("FECHA DE CADUCIDAD")

    # —— Historial: totales y de hoy (Lima)
    s2, j2 = _fetch_json(f"{API_BASE}/historial_id?ID_TG={target_id}")
    total_consultas = 0
    hoy_consultas = 0
    if s2 == 200:
        rows = j2.get("data", []) or []
        total_consultas = len(rows)
        try:
            lima_today = datetime.now(ZoneInfo("America/Lima")).date()
        except Exception:
            lima_today = datetime.utcnow().date()
        for r in rows:
            f = r.get("FECHA")
            if not f:
                continue
            ff = f[:-1] if f.endswith("Z") else f
            try:
                dt = datetime.fromisoformat(ff).replace(tzinfo=timezone.utc)
                try:
                    dt = dt.astimezone(ZoneInfo("America/Lima"))
                except Exception:
                    pass
                if dt.date() == lima_today:
                    hoy_consultas += 1
            except Exception:
                pass

    # —— Intentar obtener nombre/username/foto del TARGET (si interactuó con el bot)
    target_name = None
    target_username = None
    try:
        chat = await context.bot.get_chat(int(target_id))
        # Para usuarios que hablaron con el bot, get_chat devuelve first_name/username
        target_name = getattr(chat, "first_name", None) or getattr(chat, "title", None)
        target_username = getattr(chat, "username", None)
    except Exception:
        # Si no se puede (nunca habló con el bot), intentamos con el invocador si es el mismo ID
        if target_id == str(invoker.id):
            target_name = invoker.first_name
            target_username = invoker.username

    # —— Enlaces de perfil
    perfil_link = f"https://t.me/{target_username}" if target_username else f"tg://user?id={target_id}"
    nombre_html = html.escape(target_name or f"ID {target_id}")

    # —— Formateos de tiempo y créditos
    exp_str_local = _to_lima_iso_hm(exp)
    tiempo_str, activo, _ = _days_left(exp)
    creditos_str = f"{creditos}{' ♾️' if activo else ''}"

    header = f"{BOT_NAME} ME - PERFIL".strip() or "ME - PERFIL"
    line1 = f"<b>{header}</b>\n"
    line2 = f"\n<b>PERFIL DE</b> ➾ <a href=\"{perfil_link}\">{nombre_html}</a>\n"
    bloque1 = (
        "\n<b>INFORMACIÓN PERSONAL</b>\n"
        f"[🙎‍♂️] <b>ID</b> ➾ <code>{id_api}</code>\n"
        f"[👨🏻‍💻] <b>USER</b> ➾ @{target_username if target_username else '—'}\n"
        f"[👺] <b>ESTADO</b> ➾ {estado}\n"
        f"[📅] <b>F. REGISTRO</b> ➾ {_to_lima_iso_hm(fecha_reg)}\n"
    )
    bloque2 = (
        "\n<b>🌐 ESTADO DE CUENTA</b>\n\n"
        f"[〽️] <b>ROL TG</b> ➾ <code>{rol_tg}</code>\n"
        f"[📈] <b>PLAN</b> ➾ <code>{plan}</code>\n"
        f"[⏱️] <b>ANTI-SPAM</b> ➾ <code>{antispam}</code>\n"
        f"[💰] <b>CREDITOS</b> ➾ <code>{creditos_str}</code>\n"
        f"[⏳] <b>TIEMPO</b> ➾ <code>{tiempo_str}</code>\n"
        f"[📅] <b>F. EXPIRACIÓN</b> ➾ <code>{exp_str_local}</code>\n"
    )
    bloque3 = (
        f"\n[🛒] <b>Verifica tus compras</b> ➾ /compras"
    )

    caption = line1 + line2 + bloque1 + bloque2 + bloque3

    # —— Foto del TARGET, si existe
    try:
        photos = await context.bot.get_user_profile_photos(user_id=int(target_id), limit=1)
        if photos and photos.total_count > 0:
            largest = photos.photos[0][-1]
            await msg.reply_photo(
                photo=largest.file_id,
                caption=caption,
                parse_mode="HTML",
                reply_to_message_id=msg.message_id,
            )
            return
    except Exception:
        pass

    await msg.reply_text(
        caption,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=msg.message_id,
    )

# Aquí van otras funciones que puedas tener en el archivo...

# Función para ver el perfil del usuario (créditos y días válidos)
async def me(update, context):
    """Función para ver el perfil del usuario (créditos y días válidos)."""
    user_id = update.message.from_user.id  # El ID del usuario que ejecuta el comando
    
    # Obtener los datos del perfil del usuario
    conn = sqlite3.connect("multiplataforma.db")
    cursor = conn.cursor()

    cursor.execute("SELECT creditos, fecha_caducidad FROM usuarios WHERE id_tg = ?", (user_id,))
    result = cursor.fetchone()
    
    conn.close()

    if result:
        credits, expiration_date = result
        # Si la fecha de caducidad está presente, calculamos los días restantes
        days_left = None
        if expiration_date:
            expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d %H:%M:%S')
            days_left = (expiration_date - datetime.now()).days
        
        response = f"Tu perfil:\nCréditos: {credits}\nDías válidos: {days_left if days_left else 'No tiene fecha de caducidad'}"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("No se encontraron datos para tu perfil.")
