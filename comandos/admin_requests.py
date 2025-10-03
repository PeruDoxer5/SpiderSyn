import sqlite3
from telegram import Update
from telegram.ext import ContextTypes

DB_FILE = "requests.db"
ADMIN_ID = 7454664711  # tu ID


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            command TEXT,
            status TEXT,
            admin_msg_id INTEGER,
            cost INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()


async def create_request(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, cost: int = 1):
    user = update.effective_user
    message = update.message

    # Payload
    if message.text:
        payload = message.text
    elif message.caption:
        payload = message.caption
    else:
        payload = "📎 Archivo adjunto"

    # Guardamos en BD con costo
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO requests (user_id, username, command, status, cost) VALUES (?, ?, ?, ?, ?)",
        (user.id, user.username, command, "pending", cost)
    )
    request_id = c.lastrowid
    conn.commit()
    conn.close()

    # Aviso al usuario
    await message.reply_text(
        f"✅ Tu solicitud *{command.upper()}* está siendo procesada por el bot.\n"
        f"ID de solicitud: {request_id}",
        parse_mode="Markdown"
    )

    # Aviso al admin con lo que pidió
    sent = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Nueva solicitud #{request_id}\n"
             f"👤 Usuario: @{user.username or user.id}\n"
             f"📌 Comando: {command}\n"
             f"📝 Pedido: {payload}\n\n"
             f"Responde con /reply {request_id} <texto> o responde a este mensaje con un archivo."
    )

    # Guardamos el mensaje en la BD
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE requests SET admin_msg_id=? WHERE id=?", (sent.message_id, request_id))
    conn.commit()
    conn.close()


async def reply_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Uso: /reply <id> <texto>")
        return

    try:
        request_id = int(parts[1])
        reply_text = parts[2]
    except ValueError:
        await update.message.reply_text("ID inválido, debe ser un número.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, cost FROM requests WHERE id=?", (request_id,))
    row = c.fetchone()

    if not row:
        await update.message.reply_text("Solicitud no encontrada.")
        conn.close()
        return

    user_id, cost = row

    # 👇 Control de descuento dinámico
    if reply_text.strip() != "《⚠️》 No se encontró información.":
        from comandos.utils import verificar_usuario, descontar_creditos
        valido, info = verificar_usuario(str(user_id))
        if valido and not info.get("ilimitado", False):
            descontar_creditos(str(user_id), cost)

    # Mandamos la respuesta al usuario
    await context.bot.send_message(
        chat_id=user_id,
        text=f"📬 Respuesta a tu solicitud #{request_id}:\n\n{reply_text}"
    )

    await update.message.reply_text("Respuesta enviada ✅")
    conn.close()


async def forward_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        return

    reply_msg_id = update.message.reply_to_message.message_id
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, user_id, cost FROM requests WHERE admin_msg_id=?", (reply_msg_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return

    request_id, user_id, cost = row

    # reenviamos el archivo al usuario
    for file in update.message.photo or []:
        await context.bot.send_photo(chat_id=user_id, photo=file.file_id)

    if update.message.document:
        await context.bot.send_document(chat_id=user_id, document=update.message.document.file_id)

    if update.message.video:
        await context.bot.send_video(chat_id=user_id, video=update.message.video.file_id)

    # 👇 Descontamos siempre en caso de archivo
    from comandos.utils import verificar_usuario, descontar_creditos
    valido, info = verificar_usuario(str(user_id))
    if valido and not info.get("ilimitado", False):
        descontar_creditos(str(user_id), cost)

    await update.message.reply_text("Archivo enviado ✅")
    conn.close()