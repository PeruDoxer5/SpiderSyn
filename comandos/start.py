import os
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# --- Cargar config.json ---
CONFIG_FILE_PATH = 'config.json'
cfg = {}
if os.path.exists(CONFIG_FILE_PATH):
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"⚠️ Error leyendo config.json: {e}")
else:
    print(f"⚠️ No se encontró {CONFIG_FILE_PATH}")

def non_empty(s: str) -> bool:
    return isinstance(s, str) and s.strip() != ""

def btn(text: str, url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, url=url)

# --- /start ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    MARCA       = cfg.get("MARCA")
    NAME        = cfg.get("NAME")
    VERSION     = cfg.get("VERSION")
    LOGO_URL    = (cfg.get("LOGO") or {}).get("FT_START")

    GRUPO_LINK  = cfg.get("GRUPO_LINK")
    CANAL_LINK  = cfg.get("CANAL_LINK")
    OWNER_LINK  = cfg.get("OWNER_LINK")

    BT_OWNER    = cfg.get("BT_OWNER") or "OWNER"
    BT_CANAL    = cfg.get("BT_CANAL") or "CANAL"
    BT_GRUPO    = cfg.get("BT_GRUPO") or "GRUPO"

    sellers_raw = [
        (cfg.get("BT_SELLER"),  cfg.get("SELLER_LINK")),
        (cfg.get("BT_SELLER1"), cfg.get("SELLER_LINK1")),
        (cfg.get("BT_SELLER2"), cfg.get("SELLER_LINK2")),
        (cfg.get("BT_SELLER3"), cfg.get("SELLER_LINK3")),
    ]

    if not (non_empty(GRUPO_LINK) and non_empty(CANAL_LINK) and non_empty(OWNER_LINK)):
        await update.message.reply_text(
            "⚠️ Config incompleta: faltan enlaces obligatorios (GRUPO_LINK, CANAL_LINK u OWNER_LINK) en config.json.",
            reply_to_message_id=update.message.message_id
        )
        return

    marca_visible = MARCA or NAME or "BOT"
    version_line = f" - <code>{VERSION}</code>" if non_empty(VERSION) else ""
    caption = (
        f"👋 Hola, <b><a href='tg://user?id={user.id}'>{user.first_name}</a></b>\n\n"
        f"Has ingresado a: <b>{marca_visible}</b>{version_line}\n"
        "Un espacio donde los datos se convierten en conocimiento útil.\n\n"
        "<b>Comandos principales</b>\n"
        "/register ➾ Registra tu cuenta\n"
        "/cmds ➾ Lista de comandos\n"
        "/me ➾ Revisa tu perfil y actividad\n"
        "/buy ➾ Compra Cred/Dias\n\n"
        "<b>Nota</b>\n"
        "El uso de la información recae bajo total responsabilidad del usuario."
    )

    # Botones obligatorios
    buttons = [
        btn(f"[💭] {BT_GRUPO}", GRUPO_LINK),
        btn(f"[📣] {BT_CANAL}", CANAL_LINK),
        btn(f"[❄️] {BT_OWNER}", OWNER_LINK),
    ]

    # Botones opcionales (sellers)
    for text, url in sellers_raw:
        if non_empty(text) and non_empty(url):
            buttons.append(btn(f"[❄️] {text}", url))

    # Distribuir en filas de 2 botones
    rows = []
    for i in range(0, len(buttons), 2):
        rows.append(buttons[i:i+2])

    keyboard = InlineKeyboardMarkup(rows)

    if non_empty(LOGO_URL):
        await update.message.reply_photo(
            photo=LOGO_URL,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
            reply_to_message_id=update.message.message_id
        )
    else:
        await update.message.reply_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
            reply_to_message_id=update.message.message_id
        )
