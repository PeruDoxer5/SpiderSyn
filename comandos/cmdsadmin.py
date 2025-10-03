# comandos/cmdsadmin.py
import os
import json
import html
from urllib import parse as _urlparse
from urllib import request as _urlreq
from urllib.error import HTTPError, URLError

from telegram import Update
from telegram.ext import ContextTypes

CONFIG_FILE_PATH = "config.json"
API_DB_BASE = "http://127.0.0.1:4764"
TGINFO_ENDPOINT = f"{API_DB_BASE}/tg_info"     # ?ID_TG=

# =========================
# Carga de config
# =========================
CFG = {}
try:
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            CFG = json.load(f) or {}
except Exception:
    CFG = {}

ADMIN_IDS = set([int(CFG.get("ADMIN_ID") or 0)])

def _brand_clean(s: str) -> str:
    s = (s or "#BOT")
    for tag in ("<code>", "</code>", "<b>", "</b>", "<i>", "</i>"):
        s = s.replace(tag, "")
    return " ".join(s.split()).strip()

BOT_NAME_RAW = (CFG.get("BOT_NAME") or "#BOT").strip()
BOT_BRAND = _brand_clean(BOT_NAME_RAW)

CMDS = CFG.get("CMDS", {}) or {}
LOGO = CFG.get("LOGO", {}) or {}

# Banner: LOGO.FT_CMDSADMIN -> LOGO.FT_CMDS -> CMDS.FT_CMDSADMIN -> CMDS.FT_CMDS
FT_CMDSADMIN = (
    (LOGO.get("FT_CMDSADMIN") or "").strip()
    or (LOGO.get("FT_CMDS") or "").strip()
    or (CMDS.get("FT_CMDSADMIN") or "").strip()
    or (CMDS.get("FT_CMDS") or "").strip()
    or ""
)
TXT_CMDSADMIN = (CMDS.get("TXT_CMDSADMIN") or "").strip() or None

# =========================
# Utils
# =========================
_ALLOWED_VIEW = {"FUNDADOR", "CO-FUNDADOR", "SELLER"}

def _fetch_json(url: str, timeout: int = 18):
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

def _get_role(uid: int) -> str:
    if uid in ADMIN_IDS:
        return "ADMIN"
    st, js = _fetch_json(f"{TGINFO_ENDPOINT}?ID_TG={_urlparse.quote(str(uid))}")
    print(f"API Response for {uid}: {js}")  # Imprime la respuesta completa de la API
    if st != 200:
        return ""
    data = js.get("data", {}) or {}
    print(f"Data from API for user {uid}: {data}")  # Imprime los datos
    role = (data.get("ROL_TG") or "").upper()
    print(f"Role for user {uid}: {role}")  # Imprime el rol asignado
    return role

def _badge(txt: str) -> str:
    return f"<code>{html.escape(str(txt))}</code>"

def _divider() -> str:
    return "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

def _h(title: str, icon: str = "•") -> str:
    return f"{icon} <b>{html.escape(title)}</b>"

# =========================
# Texto del menú
# =========================
def _build_admin_menu() -> str:
    p = []
    p.append(f"🛠️ <b>{html.escape(BOT_BRAND)} • PANEL ADMIN</b>")
    p.append(_divider())
    if TXT_CMDSADMIN:
        p.append(f"<i>{html.escape(TXT_CMDSADMIN)}</i>")
        p.append(_divider())

    p.append(_h("Acceso"))
    p.append("• Disponible para: " + _badge("FUNDADOR / CO-FUNDADOR / SELLER") + " o en " + _badge("ADMIN_ID"))
    p.append(_divider())

    p.append(_h("Créditos", "🪙"))
    p.append("Acciones:")
    p.append("  • Igualar → " + _badge("/setcred ID|PLAN|CANTIDAD"))
    p.append("  • Sumar   → " + _badge("/cred ID|PLAN|CANTIDAD"))
    p.append("  • Restar  → " + _badge("/uncred ID|PLAN|CANTIDAD"))
    p.append("Ejemplo: " + _badge("/cred 6551563057|PREMIUM|50"))
    p.append("Modo respuesta (sin ID): " + _badge("Responder al usuario y enviar: PLAN|CANTIDAD"))
    p.append("Ej (respuesta): " + _badge("PREMIUM|25"))
    p.append("ℹ️ Si pasas PLAN, también se actualiza el plan del usuario y su anti-spam:")
    p.append("   BASICO → " + _badge("30s") + "  •  STANDARD → " + _badge("15s") + "  •  PREMIUM → " + _badge("5s"))
    p.append(_divider())

    p.append(_h("Suscripción / Días", "⏳"))
    p.append("Acciones:")
    p.append("  • Igualar → " + _badge("/setsub ID|PLAN|CANTIDAD"))
    p.append("  • Sumar   → " + _badge("/sub ID|PLAN|CANTIDAD"))
    p.append("  • Restar  → " + _badge("/unsub ID|PLAN|CANTIDAD"))
    p.append("Ejemplo: " + _badge("/setsub 6551563057|STANDARD|30"))
    p.append("Modo respuesta (sin ID): " + _badge("Responder y enviar: PLAN|CANTIDAD"))
    p.append("Ej (respuesta): " + _badge("BASICO|7"))
    p.append("ℹ️ Al pasar PLAN, también se ajusta anti-spam automáticamente (30/15/5s).")
    p.append(_divider())

    p.append(_h("Rol", "🧩"))
    p.append("Cambiar rol: " + _badge("/setrol ID|ROL"))
    p.append("Roles válidos: " + _badge("FREE, BASICO, STANDARD, PREMIUM, SELLER, CO-FUNDADOR, FUNDADOR, ADMIN, USER"))
    p.append("Permiso: solo " + _badge("FUNDADOR / CO-FUNDADOR") + " o en " + _badge("ADMIN_ID"))
    p.append(_divider())

    p.append(_h("Anti-Spam", "⏱️"))
    p.append("Definir manualmente:")
    p.append("  • Modo respuesta → " + _badge("/setantispam 10"))
    p.append("  • Modo manual    → " + _badge("/setantispam ID|10"))
    p.append("Rango recomendado: " + _badge("0 – 3600") + " segundos")
    p.append("ℹ️ Cambiando el PLAN con Créditos/Días se ajusta automático (30/15/5s).")
    p.append(_divider())

    p.append(_h("Registro de compras (auto)", "🧾"))
    p.append("Cada operación de créditos/días se registra en backend con el vendedor ejecutor:")
    p.append("  • Créditos → " + _badge("+N CREDITOS / -N CREDITOS"))
    p.append("  • Días     → " + _badge("+N DIAS / -N DIAS"))
    p.append(_divider())

    p.append(_h("Ayuda", "❓"))
    p.append("Envía cualquier comando sin argumentos para ver su ayuda contextual.")
    return "\n".join(p)

# =========================
# Handler principal
# =========================
async def cmdsadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /cmdsadmin
    - Muestra el panel admin con la foto de banner y el texto.
    - Intenta enviar TODO el texto en el caption si entra (<~1024).
      Si no entra, corta de forma elegante y envía el resto en un segundo mensaje.
    - Permisos: FUNDADOR / CO-FUNDADOR / SELLER o en ADMIN_ID.
    """
    msg = update.effective_message
    user = update.effective_user

    # Obtener rol del usuario
    role = _get_role(user.id)
    print(f"User ID: {user.id}, Role: {role}")

    # Verificar si el usuario tiene acceso
    if (user.id not in ADMIN_IDS) and (role not in _ALLOWED_VIEW):
        print(f"Role for user {user.id}: {role}")
        print(f"Access Denied: User ID {user.id}, Role {role}")
        await msg.reply_text(
            "❌ <b>Acceso denegado</b>\nSolo para FUNDADOR / CO-FUNDADOR / SELLER.",
            parse_mode="HTML",
            reply_to_message_id=msg.message_id,
        )
        return

    # Construir texto completo del menú
    full_text = _build_admin_menu()
    if TXT_CMDSADMIN:
        full_text = f"<i>{html.escape(TXT_CMDSADMIN)}</i>\n\n{full_text}"

    # Banner elegido desde LOGO/CMDS
    banner_url = (FT_CMDSADMIN or "").strip()

    # Helper para cortar por límite de caption (≈1024 con margen de seguridad)
    CAP_LIMIT = 1000  # margen para etiquetas HTML
    def split_for_caption(s: str):
        if len(s) <= CAP_LIMIT:
            return s, None
        # cortar en salto de línea más cercano antes del límite
        cut = s.rfind("\n", 0, CAP_LIMIT)
        if cut < 0:
            cut = CAP_LIMIT
        head = s[:cut].rstrip()
        tail = s[cut:].lstrip()
        return head, tail

    # Intento 1: si hay banner, enviarlo con caption (todo o parcial)
    if banner_url:
        cap_head, cap_tail = split_for_caption(full_text)
        try:
            await msg.reply_photo(
                photo=banner_url,
                caption=cap_head,
                parse_mode="HTML",
                reply_to_message_id=msg.message_id
            )
            # Si sobró texto, lo enviamos debajo
            if cap_tail:
                await msg.reply_text(
                    cap_tail,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_to_message_id=msg.message_id
                )
            return
        except Exception:
            # Intento 2: caption corto si el largo falló (ej. 400)
            short_caption = f"🛠️ <b>{html.escape(BOT_BRAND)}</b>\n<i>Panel de administración</i>"
            try:
                await msg.reply_photo(
                    photo=banner_url,
                    caption=short_caption,
                    parse_mode="HTML",
                    reply_to_message_id=msg.message_id
                )
                # texto completo aparte
                await msg.reply_text(
                    full_text,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_to_message_id=msg.message_id
                )
                return
            except Exception:
                pass  # caemos a enviar solo texto

    # Sin banner o si falló todo con la foto → solo texto
    await msg.reply_text(
        full_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=msg.message_id
    )
