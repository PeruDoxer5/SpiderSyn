# comandos/cmds.py
import os
import json
import html
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

CONFIG_FILE_PATH = "config.json"

def _load_cfg():
    cfg = {}
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
    return cfg or {}

def _get_menu_image(cfg: dict) -> str | None:
    # Preferimos CMDS.FT_CMDS; fallback a LOGO.FT_START
    img = (cfg.get("LOGO") or {}).get("FT_CMDS")
    if not img:
        img = (cfg.get("LOGO") or {}).get("FT_START")
    return img

def _user_link(u) -> str:
    if u.username:
        return f"https://t.me/{u.username}"
    return f"tg://user?id={u.id}"

def _kb_home():
    buttons = [
        [
            InlineKeyboardButton(text="[🪪] RENIEC", callback_data="cmds_cat_reniec"),
            InlineKeyboardButton(text="[🚗] VEHÍCULOS", callback_data="cmds_cat_vehiculos"),
        ],
        [
            InlineKeyboardButton(text="[👮] DELITOS", callback_data="cmds_cat_delitos"),
            InlineKeyboardButton(text="[👩‍👩‍👦‍👦] FAMILIA", callback_data="cmds_cat_familia"),
        ],
        [
            InlineKeyboardButton(text="[📞] TELEFONÍA", callback_data="cmds_cat_telefonia"),
            InlineKeyboardButton(text="[🏠] SUNARP", callback_data="cmds_cat_sunarp"),
        ],
        [
            InlineKeyboardButton(text="[💼] LABORAL", callback_data="cmds_cat_laboral"),
            InlineKeyboardButton(text="[📋] ACTAS", callback_data="cmds_cat_actas"),
        ],
        [
            InlineKeyboardButton(text="[⚖️] MIGRACIONES", callback_data="cmds_cat_migraciones"),
            InlineKeyboardButton(text="[📚] EXTRAS", callback_data="cmds_cat_extras"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def _kb_cat_nav():
    # Navegación para categorías (1/1)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️", callback_data="cmds_nav_prev"),
            InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
            InlineKeyboardButton("➡️", callback_data="cmds_nav_next"),
        ]
    ])

async def cmds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = _load_cfg()
    bot_name = (cfg.get("BOT_NAME") or "[#BOT] ➾").strip()
    img_url = _get_menu_image(cfg)

    user = update.effective_user
    msg = update.effective_message

    nombre = html.escape(user.first_name or "Usuario")
    link = _user_link(user)

    caption = (
        f"<b>{bot_name} SISTEMA DE COMANDOS</b>\n\n"
        f"➣ 𝙃𝙤𝙡𝙖, <a href=\"{link}\">{nombre}</a>\n\n"
        "𝑩𝑰𝑬𝑵𝑽𝑬𝑵𝑰𝑫𝑶 𝑨 𝑵𝑼𝑬𝑺𝑻𝑹𝑶 𝑴𝑬𝑵𝑼 𝑷𝑹𝑰𝑵𝑪𝑰𝑷𝑨𝑳 𝑫𝑬 𝑪𝑶𝑴𝑨𝑵𝑫𝑶𝑺.\n\n"
        "⚙️ Por favor, selecciona una categoría para comenzar:"
    )

    if img_url:
        await msg.reply_photo(
            photo=img_url,
            caption=caption,
            parse_mode="HTML",
            reply_markup=_kb_home(),
            reply_to_message_id=msg.message_id
        )
    else:
        await msg.reply_text(
            text=caption,
            parse_mode="HTML",
            reply_markup=_kb_home(),
            disable_web_page_preview=True,
            reply_to_message_id=msg.message_id
        )

async def cmds_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    cfg = _load_cfg()
    bot_name = (cfg.get("BOT_NAME") or "[#BOT] ➾").strip()

# ------- RENIEC 1 -------
    if data == "cmds_cat_reniec_p1" or data == "cmds_cat_reniec":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>RENIEC [🪪]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>10</code> disponibles\n"
            "📖 <b>PÁGINA</b> ➾ <code>1/2</code>\n\n"
            "📍 <b>RENIEC ONLINE NV 1 · BASICO</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/dni 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>1 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Imagen del rostro + datos en texto</i>\n\n"
            "📍 <b>RENIEC ONLINE NV 2 · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/dnif 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>3 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Imagen del rostro, huella, firma + datos en texto</i>\n\n"
            "📍 <b>GRUPO DE VOTACION · BASICO</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/dnim 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>2 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Dni, grupo votacion, correo, telefono</i>\n\n"
            "📍 <b>CERTIFICADO DE INSCRIPCION (C4) · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/c4 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>PDF generado</i>\n\n"
            "📍 <b>BUSQUEDA DE NOMBRE · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/nm nombre|paterno|materno</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>2 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>DNI, nombre y edad</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_reniec_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_reniec_p2"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_reniec_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_reniec_p2"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return

# ------- RENIEC 2 -------
    if data == "cmds_cat_reniec_p2":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>RENIEC [🪪]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>10</code> disponibles\n"
            "📖 <b>PÁGINA</b> ➾ <code>2/2</code>\n\n"
            "📍 <b>DNI VIRTUAL AMARILLO · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/dnivam 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Anverso y reverso del dni amarillo</i>\n\n"
            "📍 <b>DNI VIRTUAL AZUL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/dnivaz 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Anverso y reverso del dni azul</i>\n\n"
            "📍 <b>DNI VIRTUAL ELECTRONICO · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/dnivel 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Anverso y reverso del dni electronico</i>\n\n"
            "📍 <b>FICHA RENIEC AZUL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/c4azul 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf ficha azul</i>\n\n"
            "📍 <b>FICHA RENIEC BLANCA · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/c4blanco 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf ficha blanco</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_reniec_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_reniec_p1"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_reniec_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_reniec_p1"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
     
# ------- VEHÍCULOS 1 -------
    if data == "cmds_cat_vehiculos_p1" or data == "cmds_cat_vehiculos":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>VEHÍCULOS [🚗]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>13</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>1/3</code>\n\n"
            "📍 <b>REVISIONES TÉCNICAS · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/revitec AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Busca revisiones, estado, observación, etc.</i>\n\n"
            "📍 <b>BOLETA INFORMATIVA · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/bolinv AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>8 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>PDF con características completas del vehículo.</i>\n\n"
            "📍 <b>SATT - PAPELETAS [LIMA, TARAPOTO y TRUJILLO] · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/papeletas AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>8 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Detalles de papeletas y imagenes.</i>\n\n"
            "📍 <b>DATOS PLACA IMAGEN · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/pla AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>3 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Busca datos del vehiculo, dueños, etc.</i>\n\n"
            "📍 <b>SUNARP | ASIENTOS · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/placasiento AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Cambios de dueño, caracteristicas, etc.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_vehiculos_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_vehiculos_p2"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_vehiculos_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_vehiculos_p2"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
# ------- VEHÍCULOS 2 -------
    if data == "cmds_cat_vehiculos_p2":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>VEHÍCULOS [🚗]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>13</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>2/3</code>\n\n"
            "📍 <b>TARJETA DE PROPIEDAD FISICA · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/tarjetafisica AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Tarjeta de propiedad fisica ambas partes.</i>\n\n"
            "📍 <b>TIVE GENERADOR CON QR · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/tiveqr AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>15 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf tarjeta de propiedad electrónica con qr.</i>\n\n"
            "📍 <b>TIVE ORIGINAL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/tiveor AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf tarjeta de propiedad electrónica original.</i>\n\n"
            "📍 <b>TIVE GENERADOR SIN QR · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/tive AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>8 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf tarjeta de propiedad electronica qr falso.</i>\n\n"
            "📍 <b>SOAT VEHÍCULAR PDF · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/soat AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>7 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Soat activo en PDF.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_vehiculos_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_vehiculos_p3"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_vehiculos_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_vehiculos_p3"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return

# ------- VEHICULOS 3 -------
    if data == "cmds_cat_vehiculos_p3":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>VEHÍCULOS [🚗]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>13</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>3/3</code>\n\n"
            "📍 <b>LICENCIA TEXTO · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/licencia 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Obten informacion de licencia en texto.</i>\n\n"
            "📍 <b>LICENCIA PDF · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/licenciapdf 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>8 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf con licencia.</i>\n\n"
            "📍 <b>INSCRIPCION VEHICULAR · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/insve AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>6 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf de inscripcion vehicular.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_vehiculos_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_vehiculos_p2"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_vehiculos_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_vehiculos_p2"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
# ------- DELITOS 1 -------
    if data == "cmds_cat_delitos_p1" or data == "cmds_cat_delitos":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>DELITOS [👮]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>11</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>1/3</code>\n\n"
            "📍 <b>FISCALIA TEXTO · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/fis 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Texto con casos fiscales.</i>\n\n"
            "📍 <b>FISCALIA EN PDF · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/fispdf 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>25 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf con casos fiscales.</i>\n\n"
            "📍 <b>RQ VEHICULAR · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/rqv AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Requisitoria de vehiculo.</i>\n\n"
            "📍 <b>REQUISITORIA · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/rq 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>8 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Requisitoria de persona.</i>\n\n"
            "📍 <b>DENUNCIAS DNI · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/denuncias 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Denuncias con dni.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_delitos_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_delitos_p2"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_delitos_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_delitos_p2"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
# ------- DELITOS 2 -------
    if data == "cmds_cat_delitos_p2":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>DELITOS [👮]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>11</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>2/3</code>\n\n"
            "📍 <b>DENUNCIAS CON PLACA · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/denunciasv AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Texto con casos fiscales.</i>\n\n"
            "📍 <b>CERTIF. ANTECEDENTES POLICIALES · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/antpo 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>7 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Certificado de antecedentes policiales.</i>\n\n"
            "📍 <b>CERTIF. ANTECEDENTES JUDICIALES · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/antju AAA000</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>7 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Certificado de antecedentes judiciales.</i>\n\n"
            "📍 <b>CERTIF. ANTECEDENTES PENALES · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/antpe 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>7 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Certificado de antecedentes penales.</i>\n\n"
            "📍 <b>ANTECEDENTES · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/ant 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>8 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Antecedentes con dni.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_delitos_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_delitos_p3"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_delitos_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_delitos_p3"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
# ------- DELITOS 3 -------
    if data == "cmds_cat_delitos_p3":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>DELITOS [👮]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>11</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>3/3</code>\n\n"
            "📍 <b>DETENCIONES · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/det 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Detenciones con dni.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_delitos_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_delitos_p2"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_delitos_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_delitos_p2"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
# ------- FAMILIA 1 -------
    if data == "cmds_cat_familia_p1" or data == "cmds_cat_familia":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷 <b>CATEGORÍA</b> ➾ <code>FAMILIA [👩‍👩‍👦‍👦]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>4</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>1/1</code>\n\n"
            "📍 <b>HOGAR · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/hogar 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Texto con familia en casa.</i>\n\n"
            "📍 <b>ARBOL GENEALOGICO · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/ag 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Texto con arbol genealogico.</i>\n\n"
            "📍 <b>ARBOL GENEALOGICO VISUAL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/agv 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>20 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Arbol genealogico en foto.</i>\n\n"
            "📍 <b>HERMANOS · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/her 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Texto con solo hermanos.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_familia_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_familia_p1"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_familia_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_familia_p1"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return

# ------- TELEFONIA 1 -------
    if data == "cmds_cat_telefonia_p1" or data == "cmds_cat_telefonia":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷 <b>CATEGORÍA</b> ➾ <code>TELEFONIA [📞]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>12</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>1/3</code>\n\n"
            "📍 <b>NUMEROS DB · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/tel 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>3 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Numeros por dni db.</i>\n\n"
            "📍 <b>NUMEROS 2025 · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/telp 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>7 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Numeros base 2025.</i>\n\n"
            "📍 <b>TITULAR CALL CENTER · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/tels 987654321</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Titular db call center.</i>\n\n"
            "📍 <b>TITULAR EN TIEMPO REAL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/cel 987654321</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>7 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Texto titular en tiempo real.</i>\n\n"
            "📍 <b>VERIFICAR OPERADOR · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/vlop 987654321</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>1 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Operador del numero.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_telefonia_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_telefonia_p2"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_telefonia_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_telefonia_p2"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
    # ------- TELEFONIA 2 -------
    if data == "cmds_cat_telefonia_p2":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷 <b>CATEGORÍA</b> ➾ <code>TELEFONIA [📞]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>12</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>2/3</code>\n\n"
            "📍 <b>NUMEROS OSIPTEL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/vlnum 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>1 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Numeros de checalineas.</i>\n\n"
            "📍 <b>BITEL TIEMPO REAL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/bitel 987654321</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>7 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Bitel en tiempo real.</i>\n\n"
            "📍 <b>CLARO TIEMPO REAL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/claro 987654321</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Claro en tiempo real.</i>\n\n"
            "📍 <b>MOVISTAR EN TIEMPO REAL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/movistar 987654321</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>7 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Movistar en tiempo real.</i>\n\n"
            "📍 <b>ENTEL DB · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/enteldb 987654321</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>3 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Titular entel db.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_telefonia_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_telefonia_p3"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_telefonia_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_telefonia_p3"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
    # ------- TELEFONIA 3 -------
    if data == "cmds_cat_telefonia_p3":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷 <b>CATEGORÍA</b> ➾ <code>TELEFONIA [📞]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>12</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>3/3</code>\n\n"
            "📍 <b>CORREOS · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/correo 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>3 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Correos por dni.</i>\n\n"
            "📍 <b>NUMERO CLARO EN TIEMPO REAL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/numclaro 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>7 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Numeros claro con dni.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_telefonia_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_telefonia_p2"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_telefonia_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_telefonia_p2"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
    # ------- SUNARP 1 -------
    if data == "cmds_cat_sunarp_p1" or data == "cmds_cat_sunarp":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷 <b>CATEGORÍA</b> ➾ <code>SUNARP [🏠]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>2</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>1/1</code>\n\n"
            "📍 <b>PROPIEDADES SUNARP · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/sunarp 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Texto con propiedades con dni.</i>\n\n"
            "📍 <b>PARTIDA PROPIEDAD · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/sunarpdf 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>20 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf con partida de la propiedad con dni.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_sunarp_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_sunarp_p1"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_sunarp_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_sunarp_p1"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
    # ------- LABORAL 1 -------
    if data == "cmds_cat_laboral_p1" or data == "cmds_cat_laboral":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷 <b>CATEGORÍA</b> ➾ <code>LABORAL [💼]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>2</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>1/1</code>\n\n"
            "📍 <b>SUELDOS · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/sueldos 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Sueldos con dni.</i>\n\n"
            "📍 <b>TRABAJOS · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/trabajos 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Trabajos con dni.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_laboral_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_laboral_p1"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_laboral_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_laboral_p1"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return

# ------- ACTAS 1 -------
    if data == "cmds_cat_actas_p1" or data == "cmds_cat_actas":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷 <b>CATEGORÍA</b> ➾ <code>ACTAS [📋]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>2</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>1/1</code>\n\n"
            "📍 <b>ACTA DE MATRIMONIO · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/actamdb 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf matrimonio database.</i>\n\n"
            "📍 <b>ACTA DE DEFUNCION · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/actaddb 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf defuncion database.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_actas_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_actas_p1"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_actas_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_actas_p1"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
    # ------- MIGRACIONES 1 -------
    if data == "cmds_cat_migraciones_p1" or data == "cmds_cat_migraciones":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷 <b>CATEGORÍA</b> ➾ <code>MIGRACIONES [⚖️]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>1</code> disponible\n"
            "📖 <b>PÁGINA</b> ➾ <code>1/1</code>\n\n"
            "📍 <b>MIGRACIONES PDF · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> <code>[✅]</code>\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/migrapdf 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>6 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Migraciones en pdf.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_migraciones_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_migraciones_p1"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_migraciones_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_migraciones_p1"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return
    
    # ------- EXTRAS 1 -------
    if data == "cmds_cat_extras_p1" or data == "cmds_cat_extras":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>EXTRAS [📚]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>11</code> disponibles\n"
            "📖 <b>PÁGINA</b> ➾ <code>1/3</code>\n\n"
            "📍 <b>SEEKER COMPLETO · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/seeker 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>10 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf seeker completo.</i>\n\n"
            "📍 <b>SUNAT PDF · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/sunat 10444455557</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>8 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf sunat con ruc.</i>\n\n"
            "📍 <b>RUC DNI · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/ruc 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Consulta si tiene ruc.</i>\n\n"
            "📍 <b>VERIFICAR DOCTOR · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/doc 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>3 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Verificar con dni si es doctor.</i>\n\n"
            "📍 <b>ESSALUD · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/essalud 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>3 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Verificar si está asegurado en essalud.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_extras_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_extras_p2"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_extras_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_extras_p2"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return

# ------- EXTRAS 2 -------
    if data == "cmds_cat_extras_p2":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>EXTRAS [📚]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>11</code> disponibles\n"
            "📖 <b>PÁGINA</b> ➾ <code>2/3</code>\n\n"
            "📍 <b>CONSTANCIA DE NOTAS · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/notas 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>25 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf con original de constancia de notas.</i>\n\n"
            "📍 <b>DEUDAS · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/sbs 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>5 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Consulta deudas.</i>\n\n"
            "📍 <b>TRABAJADORES EMPRESA · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/trabajadores 10444455557</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>8 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Consulta trabajadores de una empresa.</i>\n\n"
            "📍 <b>DIRECCIONES · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/dir 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>3 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Consultar direcciones con dni.</i>\n\n"
            "📍 <b>AFP · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/afp 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>3 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Informacion de afp con dni.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_extras_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_extras_p3"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_extras_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_extras_p3"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return

# ------- EXTRAS 3 -------
    if data == "cmds_cat_extras_p3":
        caption = (
            f"<b>{bot_name}</b> <i>SISTEMA DE COMANDOS</i>\n"
            "🏷️ <b>CATEGORÍA</b> ➾ <code>EXTRAS [📚]</code>\n"
            "🧩 <b>COMANDOS</b> ➾ <code>11</code> disponibles\n"
            "📖 <b>PÁGINA</b> ➾ <code>3/3</code>\n\n"
            "📍 <b>RECONOCIMIENTO FACIAL · STANDARD</b>\n"
            "┈┈┈┈┈┈┈┈┈┈\n"
            "🟢 <b>ESTADO</b> ➾ <b>OPERATIVO</b> ✅\n"
            "⌨️ <b>COMANDO</b> ➾ <code>/facial 44443333</code>\n"
            "💳 <b>PRECIO</b> ➾ <code>30 créditos</code>\n"
            "📦 <b>RESULTADO</b> ➾ <i>Pdf con reconocimiento facial.</i>\n\n"
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_extras_p2"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_extras_p2"),
                ]])
            )
        except Exception:
            await query.edit_message_text(
                text=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️", callback_data="cmds_cat_extras_p1"),
                    InlineKeyboardButton("🏠", callback_data="cmds_nav_home"),
                    InlineKeyboardButton("➡️", callback_data="cmds_cat_extras_p1"),
                ]]),
                disable_web_page_preview=True
            )
        await query.answer()
        return

    if data == "cmds_nav_home":
        user = query.from_user
        nombre = html.escape(user.first_name or "Usuario")
        link = _user_link(user)
        caption = (
            f"<b>{bot_name} SISTEMA DE COMANDOS</b>\n\n"
            f"➣ 𝙃𝙤𝙡𝙖, <a href=\"{link}\">{nombre}</a>\n\n"
            "𝑩𝑰𝑬𝑵𝑽𝑬𝑵𝑰𝑫𝑶 𝑨 𝑵𝑼𝑬𝑺𝑻𝑹𝑶 𝑴𝑬𝑵𝑼 𝑷𝑹𝑰𝑵𝑪𝑰𝑷𝑨𝑳 𝑫𝑬 𝑪𝑶𝑴𝑨𝑵𝑫𝑶𝑺.\n\n"
            "𝑷𝑶𝑹 𝑭𝑨𝑽𝑶𝑹, 𝑺𝑬𝑳𝑬𝑪𝑪𝑰𝑶𝑵𝑨 𝑼𝑵𝑨 𝑶𝑷𝑪𝑰𝑶𝑵 𝑺𝑬𝑮𝑼𝑵 𝑳𝑨 𝑪𝑨𝑻𝑬𝑮𝑶𝑹𝑰𝑨 𝑸𝑼𝑬 𝑫𝑬𝑺𝑬𝑨𝑺 𝑬𝑿𝑷𝑳𝑶𝑹𝑨𝑹."
        )
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=_kb_home()
            )
        except Exception:
            try:
                await query.edit_message_text(
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=_kb_home(),
                    disable_web_page_preview=True
                )
            except Exception:
                pass
        await query.answer("Inicio")
        return

    if data in ("cmds_nav_prev", "cmds_nav_next"):
        await query.answer("No hay más páginas", show_alert=False)
        return

    await query.answer()
