import os
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

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

# --- /buy ---
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Obtener @ del bot
    me = await context.bot.get_me()
    bot_arroba = f"@{me.username}" if non_empty(me.username) else "bot"

    texto = (
        "✨ <b>PLANES Y TARIFAS</b> ✨\n"
        f"⚡️ <i>By:</i> <b>{bot_arroba}</b>\n\n"
        "💰 <b>PLAN POR CREDITOS</b> 💰\n\n"
        "⟦🔰⟧ <b>BASICO (45's)</b>\n"
        "• 50 + 20 Creditos ➩ 10 Soles\n"
        "• 100 + 30 Creditos ➩ 15 Soles\n"
        "• 200 + 50 Creditos ➩ 23 Soles\n"
        "• 350 + 80 Creditos ➩ 30 Soles\n\n"
        "⟦⭐⟧ <b>STANDARD (15's)</b>\n"
        "• 500 + 100 Creditos ➩ 50 Soles\n"
        "• 800 + 150 Creditos ➩ 70 Soles\n"
        "• 1000 + 200 Creditos ➩ 90 Soles\n\n"
        "⟦💎⟧ <b>PREMIUM (5's)</b>\n"
        "• 1500 + 200 Creditos ➩ 100 Soles\n"
        "• 2000 + 300 Creditos ➩ 130 Soles\n"
        "• 2800 + 400 Creditos ➩ 170 Soles\n\n"
        "⏳ <b>PLAN POR DIAS</b> ⏳\n\n"
        "⟦🔰⟧ <b>BASICO - NV1 (25's)</b>\n"
        "• 3 Dias ➩ 12 Soles\n"
        "• 7 Dias ➩ 17 Soles\n\n"
        "⟦⭐⟧ <b>STANDARD - NV2 (15's)</b>\n"
        "• 15 Dias ➩ 30 Soles\n"
        "• 30 Dias ➩ 50 Soles\n\n"
        "⟦💎⟧ <b>PREMIUM - NV3 (5's)</b>\n"
        "• 60 Dias ➩ 75 Soles\n"
        "• 90 Dias ➩ 110 Soles\n\n"
        "[⚠️] <b>IMPORTANTE</b> ➩ Antes de comprar leer los terminos y condiciones usa /terminos"
    )

    # Botones
    buttons = []

    owner_text = cfg.get("BT_OWNER")
    owner_link = cfg.get("OWNER_LINK")
    if non_empty(owner_text) and non_empty(owner_link):
        buttons.append(btn(f"[❄️] {owner_text}", owner_link))

    sellers = [
        (cfg.get("BT_SELLER"),  cfg.get("SELLER_LINK")),
        (cfg.get("BT_SELLER1"), cfg.get("SELLER_LINK1")),
        (cfg.get("BT_SELLER2"), cfg.get("SELLER_LINK2")),
        (cfg.get("BT_SELLER3"), cfg.get("SELLER_LINK3")),
    ]
    for text, url in sellers:
        if non_empty(text) and non_empty(url):
            buttons.append(btn(f"[❄️] {text}", url))

    rows = []
    for i in range(0, len(buttons), 2):
        rows.append(buttons[i:i+2])

    keyboard = InlineKeyboardMarkup(rows) if rows else None

    # Imagen del config
    FT_BUY = (cfg.get("LOGO") or {}).get("FT_BUY")

    if non_empty(FT_BUY):
        await update.message.reply_photo(
            photo=FT_BUY,
            caption=texto,
            parse_mode="HTML",
            reply_markup=keyboard,
            reply_to_message_id=update.message.message_id
        )
    else:
        await update.message.reply_text(
            text=texto,
            parse_mode="HTML",
            reply_markup=keyboard,
            reply_to_message_id=update.message.message_id
        )
