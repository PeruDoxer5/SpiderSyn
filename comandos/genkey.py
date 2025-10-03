import sqlite3
import random
import string
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

# ID del admin
ADMIN_ID = 7454664711  # <-- cámbialo si tienes otro

# -------------------- CONEXIONES A DB --------------------
def connect_users():
    return sqlite3.connect("multiplataforma.db")

def connect_keys():
    return sqlite3.connect("keys.db")

# -------------------- GENERAR KEYS --------------------
def generar_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return

    if len(context.args) < 3:
        await update.message.reply_text("Uso: /genkey <dias|creditos> <cantidad> <usos>")
        return

    tipo = context.args[0].lower()
    cantidad = int(context.args[1])
    usos = int(context.args[2])

    if tipo not in ["dias", "creditos"]:
        await update.message.reply_text("Tipo inválido. Usa: dias o creditos.")
        return

    key = generar_key()

    conn = connect_keys()
    c = conn.cursor()
    c.execute("INSERT INTO keys (key, tipo, cantidad, usos, creador_id) VALUES (?, ?, ?, ?, ?)",
              (key, tipo, cantidad, usos, update.effective_user.id))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ Key generada:\n`{key}`\n\nTipo: {tipo}\nCantidad: {cantidad}\nUsos: {usos}", parse_mode="Markdown")

# -------------------- CANJEAR KEYS --------------------
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Uso: /redeem <KEY>")
        return

    key_input = context.args[0].strip().upper()
    user_id = update.effective_user.id

    conn_keys = connect_keys()
    c = conn_keys.cursor()
    c.execute("SELECT key, tipo, cantidad, usos FROM keys WHERE key = ?", (key_input,))
    row = c.fetchone()

    if not row:
        await update.message.reply_text("❌ Key inválida.")
        conn_keys.close()
        return

    key, tipo, cantidad, usos = row
    if usos <= 0:
        await update.message.reply_text("❌ Esta key ya no tiene usos disponibles.")
        conn_keys.close()
        return

    # Actualizar usuario en multiplataforma.db
    conn_users = connect_users()
    cu = conn_users.cursor()
    cu.execute("SELECT id_tg, creditos, fecha_caducidad FROM usuarios WHERE id_tg = ?", (user_id,))
    user = cu.fetchone()

    if not user:
        await update.message.reply_text("❌ No estás registrado. Usa /register primero.")
        conn_users.close()
        conn_keys.close()
        return

    if tipo == "creditos":
        nuevo_valor = user[1] + cantidad
        cu.execute("UPDATE usuarios SET creditos = ? WHERE id_tg = ?", (nuevo_valor, user_id))
        mensaje = f"✅ Has canjeado {cantidad} créditos.\nAhora tienes {nuevo_valor} créditos."
    
    if tipo == "dias":
        # Verificar si la fecha de caducidad es válida
        fecha_caducidad = user[2]

        if fecha_caducidad == '0' or not fecha_caducidad:  # Si la fecha es inválida o vacía
            # Asignar una fecha de caducidad predeterminada si es inválida
            fecha_caducidad_dt = datetime.now()  # Establecer la fecha de caducidad como la fecha actual
        else:
            try:
                # Intentar convertir la fecha de caducidad en formato 'YYYY-MM-DD'
                fecha_caducidad_dt = datetime.strptime(fecha_caducidad, '%Y-%m-%d')
            except ValueError:
                # Si la fecha no tiene el formato correcto, asignar la fecha actual
                fecha_caducidad_dt = datetime.now()

        # Sumar los días al valor actual
        nueva_fecha_caducidad = fecha_caducidad_dt + timedelta(days=cantidad)

        # Convertir de nuevo a formato string
        nueva_fecha_caducidad_str = nueva_fecha_caducidad.strftime('%Y-%m-%d')

        # Actualizar la fecha de caducidad en la base de datos
        cu.execute("UPDATE usuarios SET fecha_caducidad = ? WHERE id_tg = ?", (nueva_fecha_caducidad_str, user_id))
        mensaje = f"✅ Has canjeado {cantidad} días.\nAhora tu fecha de caducidad es {nueva_fecha_caducidad_str}."

    conn_users.commit()
    conn_users.close()

    # Actualizar key (restar un uso)
    c.execute("UPDATE keys SET usos = usos - 1 WHERE key = ?", (key,))
    c.execute("INSERT INTO redemptions (key, user_id) VALUES (?, ?)", (key, user_id))
    conn_keys.commit()
    conn_keys.close()

    await update.message.reply_text(mensaje)

# -------------------- LOG DE CANJES --------------------
async def keyslog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return

    conn = connect_keys()
    c = conn.cursor()
    c.execute("""
        SELECT r.key, r.user_id, r.fecha_canje, k.tipo, k.cantidad
        FROM redemptions r
        JOIN keys k ON r.key = k.key
        ORDER BY r.fecha_canje DESC
        LIMIT 15
    """)
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📭 No hay canjes registrados aún.")
        return

    mensaje = "📜 Últimos canjes de keys:\n\n"
    for key, user_id, fecha, tipo, cantidad in rows:
        mensaje += f"🔑 {key}\n👤 User: `{user_id}`\n📅 {fecha}\n➕ {cantidad} {tipo}\n\n"

    await update.message.reply_text(mensaje, parse_mode="Markdown")

# -------------------- INFO DE UNA KEY --------------------
async def keysinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Uso: /keysinfo <KEY>")
        return

    key_input = context.args[0].strip().upper()

    conn = connect_keys()
    c = conn.cursor()
    c.execute("""
        SELECT key, tipo, cantidad, usos, creador_id, fecha_creacion
        FROM keys WHERE key = ?
    """, (key_input,))
    row = c.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("❌ Key no encontrada.")
        return

    key, tipo, cantidad, usos, creador_id, fecha_creacion = row

    mensaje = (
        f"🔑 Información de la Key:\n\n"
        f"🔹 Key: `{key}`\n"
        f"📌 Tipo: {tipo}\n"
        f"➕ Cantidad: {cantidad}\n"
        f"♻️ Usos restantes: {usos}\n"
        f"👤 Creada por: `{creador_id}`\n"
        f"📅 Fecha creación: {fecha_creacion}"
    )

    await update.message.reply_text(mensaje, parse_mode="Markdown")
