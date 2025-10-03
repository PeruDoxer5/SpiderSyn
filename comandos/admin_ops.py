# comandos/admin_ops.py
import os
import json
import html
from typing import Tuple

from urllib import parse as _urlparse
from urllib import request as _urlreq
from urllib.error import HTTPError, URLError

from telegram import Update
from telegram.ext import ContextTypes

# =========================
# Config
# =========================
API_DB_BASE = "http://127.0.0.1:4764"
CONFIG_FILE_PATH = "config.json"

# Endpoints
CRED_ENDPOINT     = f"{API_DB_BASE}/cred"       # ?ID_TG=&operacion=&cantidad=
SUB_ENDPOINT      = f"{API_DB_BASE}/sub"        # ?ID_TG=&operacion=&cantidad=
PLAN_ENDPOINT     = f"{API_DB_BASE}/plan"       # ?ID_TG=&plan=
ROL_ENDPOINT      = f"{API_DB_BASE}/rol_tg"     # ?ID_TG=&rol=
TGINFO_ENDPOINT   = f"{API_DB_BASE}/tg_info"    # ?ID_TG=
COMPRAS_ENDPOINT  = f"{API_DB_BASE}/compras"    # ?ID_TG=&ID_VENDEDOR=&CANTIDAD=
ANTISPAM_ENDPOINT = f"{API_DB_BASE}/antispam"   # ?ID_TG=&valor=

CFG = {}
try:
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            CFG = json.load(f) or {}
except Exception:
    CFG = {}
ADMIN_IDS = set(CFG.get("ADMIN_ID") or [])

def _brand_clean(s: str) -> str:
    s = (s or "#BOT")
    for tag in ("<code>", "</code>", "<b>", "</b>", "<i>", "</i>"):
        s = s.replace(tag, "")
    s = " ".join(s.split()).strip()
    return s

BOT_NAME_RAW = (CFG.get("BOT_NAME") or "#BOT").strip()
BOT_BRAND = _brand_clean(BOT_NAME_RAW)

# =========================
# Utils
# =========================
_ALLOWED_ALL = {"FUNDADOR", "CO-FUNDADOR", "SELLER"}
_ALLOWED_SETROL = {"FUNDADOR", "CO-FUNDADOR"}

PLAN_MAP_NUM2TXT = {"1": "BASICO", "2": "STANDARD", "3": "PREMIUM"}
PLAN_MAP_TXT = {"BASICO", "STANDARD", "PREMIUM"}
PLAN_TO_ANTISPAM = {"BASICO": 30, "STANDARD": 15, "PREMIUM": 5}

def _fetch_json(url: str, timeout: int = 20) -> Tuple[int, dict]:
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

def _get_tg_info(id_tg: str) -> Tuple[int, dict]:
    return _fetch_json(f"{TGINFO_ENDPOINT}?ID_TG={_urlparse.quote(id_tg)}")

def _caller_role_and_auth(user_id: int, need_setrol: bool = False) -> Tuple[bool, str]:
    if user_id in ADMIN_IDS:
        return True, "ADMIN"
    st, js = _get_tg_info(str(user_id))
    if st != 200:
        return False, ""
    data = js.get("data", {}) or {}
    rol = (data.get("ROL_TG") or "").upper()
    if need_setrol:
        ok = rol in _ALLOWED_SETROL
    else:
        ok = rol in _ALLOWED_ALL
    return ok, rol

def _normalize_plan(p: str) -> str | None:
    s = (p or "").strip().upper()
    if s in PLAN_MAP_TXT:
        return s
    return PLAN_MAP_NUM2TXT.get(s)

def _pretty_card(title: str, lines: list[str], icon: str = "✅") -> str:
    body = "\n".join([l for l in lines if l])
    return f"{icon} <b>{html.escape(title)}</b>\n\n{body}"

def _warn_card(title: str, lines: list[str], icon: str = "⚠️") -> str:
    body = "\n".join([l for l in lines if l])
    return f"{icon} <b>{html.escape(title)}</b>\n\n{body}"

def _err_card(title: str, lines: list[str]) -> str:
    return _warn_card(title, lines, icon="❌")

def _badge(text: str) -> str:
    return f"<code>{html.escape(str(text))}</code>"

def _operate(endpoint: str, target_id: str, oper: str, cantidad: int) -> Tuple[int, dict]:
    url = f"{endpoint}?ID_TG={_urlparse.quote(target_id)}&operacion={_urlparse.quote(oper)}&cantidad={_urlparse.quote(str(cantidad))}"
    return _fetch_json(url)

def _log_compra(id_tg: str, id_vendedor: str, cantidad_texto: str):
    try:
        url = f"{COMPRAS_ENDPOINT}?ID_TG={_urlparse.quote(id_tg)}&ID_VENDEDOR={_urlparse.quote(id_vendedor)}&CANTIDAD={_urlparse.quote(cantidad_texto)}"
        _fetch_json(url, timeout=12)
    except Exception:
        pass

def _set_antispam(id_tg: str, valor: int) -> Tuple[int, dict]:
    url = f"{ANTISPAM_ENDPOINT}?ID_TG={_urlparse.quote(id_tg)}&valor={_urlparse.quote(str(valor))}"
    return _fetch_json(url, timeout=12)

def _do_plan_update_if_provided(target_id: str, plan_txt: str | None) -> tuple[bool, str, int | None]:
    """
    Si plan_txt viene, actualiza plan y ajusta antispam acorde al plan.
    Retorna: (ok, msg, antispam_aplicado | None)
    """
    if not plan_txt:
        return True, "—", None
    st, js = _fetch_json(
        f"{PLAN_ENDPOINT}?ID_TG={_urlparse.quote(target_id)}&plan={_urlparse.quote(plan_txt)}"
    )
    if st != 200:
        return False, f"code {st}: {js.get('message','error')}", None

    anti = PLAN_TO_ANTISPAM.get(plan_txt)
    if anti is not None:
        _set_antispam(target_id, anti)  # best effort; ignoramos errores
    return True, plan_txt, anti

# =========================
# Parsers (con soporte "reply")
# =========================
def _parse_three_parts(args: list[str]) -> tuple[str|None, str|None, int|None, str|None]:
    joined = " ".join(args).strip()
    if "|" not in joined:
        return None, None, None, "Formato inválido. Usa: <code>ID|PLAN|CANTIDAD</code>"
    p = [x.strip() for x in joined.split("|")]
    if len(p) != 3:
        return None, None, None, "Debes enviar exactamente 3 campos: <code>ID|PLAN|CANTIDAD</code>."
    id_tg, plan_in, cant_in = p
    if not id_tg.isdigit():
        return None, None, None, "ID inválido (debe ser numérico)."
    plan_txt = _normalize_plan(plan_in)
    if not plan_txt:
        return None, None, None, "PLAN inválido. Usa 1/2/3 o BASICO/STANDARD/PREMIUM."
    try:
        cantidad = int(cant_in)
        if cantidad < 0:
            return None, None, None, "CANTIDAD debe ser ≥ 0."
    except Exception:
        return None, None, None, "CANTIDAD inválida (debe ser entero)."
    return id_tg, plan_txt, cantidad, None

def _parse_reply_two_parts(args: list[str]) -> tuple[str|None, int|None, str|None]:
    joined = " ".join(args).strip()
    if "|" not in joined:
        return None, None, "Formato inválido en respuesta. Usa: <code>PLAN|CANTIDAD</code>"
    p = [x.strip() for x in joined.split("|")]
    if len(p) != 2:
        return None, None, "Debes enviar 2 campos en respuesta: <code>PLAN|CANTIDAD</code>."
    plan_in, cant_in = p
    plan_txt = _normalize_plan(plan_in)
    if not plan_txt:
        return None, None, "PLAN inválido. Usa 1/2/3 o BASICO/STANDARD/PREMIUM."
    try:
        cantidad = int(cant_in)
        if cantidad < 0:
            return None, None, "CANTIDAD debe ser ≥ 0."
    except Exception:
        return None, None, "CANTIDAD inválida (debe ser entero)."
    return plan_txt, cantidad, None

def _extract_reply_target(update: Update) -> str | None:
    m = update.effective_message
    if m and m.reply_to_message and m.reply_to_message.from_user:
        return str(m.reply_to_message.from_user.id)
    return None

# =========================
# Núcleo de operaciones con registro de compras
# =========================
async def _handle_cred_like(update: Update, context: ContextTypes.DEFAULT_TYPE, oper: str):
    msg = update.effective_message
    caller = update.effective_user

    ok, rol = _caller_role_and_auth(caller.id, need_setrol=False)
    if not ok:
        await msg.reply_text(
            _err_card(f"{BOT_BRAND} • Permiso denegado", [f"Tu rol actual: {_badge(rol or '—')}."]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    reply_target = _extract_reply_target(update)

    if reply_target:
        if not context.args:
            await msg.reply_text(
                _warn_card(f"{BOT_BRAND} • Uso (respuesta)", ["Responde al usuario y envía: <code>PLAN|CANTIDAD</code>"]),
                parse_mode="HTML",
                reply_to_message_id=msg.message_id
            )
            return
        plan_txt, cantidad, err = _parse_reply_two_parts(context.args)
        if err:
            await msg.reply_text(_err_card(f"{BOT_BRAND} • Entrada inválida", [err]), parse_mode="HTML", reply_to_message_id=msg.message_id)
            return
        target_id = reply_target
    else:
        if not context.args:
            await msg.reply_text(
                _warn_card(f"{BOT_BRAND} • Uso", ["<b>Formato:</b> <code>ID|PLAN|CANTIDAD</code>  (o responde: <code>PLAN|CANTIDAD</code>)"]),
                parse_mode="HTML",
                reply_to_message_id=msg.message_id
            )
            return
        target_id, plan_txt, cantidad, err = _parse_three_parts(context.args)
        if err:
            await msg.reply_text(_err_card(f"{BOT_BRAND} • Entrada inválida", [err]), parse_mode="HTML", reply_to_message_id=msg.message_id)
            return

    # (1) Ajustar plan si se pasó (+ antispam automático)
    plan_ok, plan_msg, anti_val = _do_plan_update_if_provided(target_id, plan_txt)
    if not plan_ok:
        await msg.reply_text(
            _err_card(f"{BOT_BRAND} • No se pudo actualizar el plan", [plan_msg]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    # (2) Operar créditos
    st, js = _operate(CRED_ENDPOINT, target_id, oper, cantidad)
    if st != 200:
        await msg.reply_text(
            _err_card(f"{BOT_BRAND} • Fallo al operar créditos", [f"Código: {st}", str(js.get('message','Error'))]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    # (3) Log de compra (CREDITOS)
    signo = "+" if oper == "sumar" else "-"
    cantidad_txt = f"{signo}{cantidad} CREDITOS"
    _log_compra(id_tg=target_id, id_vendedor=str(caller.id), cantidad_texto=cantidad_txt)

    # (4) Mostrar resultado
    new_cred = (js.get("data") or {}).get("CREDITOS", "—")
    lines = [
        f"Cliente: {_badge(target_id)}",
        f"Plan aplicado: {_badge(plan_txt)}",
        f"Operación: {_badge(cantidad_txt)}",
        f"Nuevo saldo: {_badge(new_cred)}",
    ]
    if anti_val is not None:
        lines.append(f"Anti-spam ajustado: {_badge(anti_val)} s")
    pretty = _pretty_card(f"{BOT_BRAND} • Créditos ({oper})", lines)
    await msg.reply_text(pretty, parse_mode="HTML", reply_to_message_id=msg.message_id)

async def _handle_sub_like(update: Update, context: ContextTypes.DEFAULT_TYPE, oper: str):
    msg = update.effective_message
    caller = update.effective_user

    ok, rol = _caller_role_and_auth(caller.id, need_setrol=False)
    if not ok:
        await msg.reply_text(
            _err_card(f"{BOT_BRAND} • Permiso denegado", [f"Tu rol actual: {_badge(rol or '—')}."]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    reply_target = _extract_reply_target(update)

    if reply_target:
        if not context.args:
            await msg.reply_text(
                _warn_card(f"{BOT_BRAND} • Uso (respuesta)", ["Responde al usuario y envía: <code>PLAN|CANTIDAD</code>"]),
                parse_mode="HTML",
                reply_to_message_id=msg.message_id
            )
            return
        plan_txt, cantidad, err = _parse_reply_two_parts(context.args)
        if err:
            await msg.reply_text(_err_card(f"{BOT_BRAND} • Entrada inválida", [err]), parse_mode="HTML", reply_to_message_id=msg.message_id)
            return
        target_id = reply_target
    else:
        if not context.args:
            await msg.reply_text(
                _warn_card(f"{BOT_BRAND} • Uso", ["<b>Formato:</b> <code>ID|PLAN|CANTIDAD</code>  (o responde: <code>PLAN|CANTIDAD</code>)"]),
                parse_mode="HTML",
                reply_to_message_id=msg.message_id
            )
            return
        target_id, plan_txt, cantidad, err = _parse_three_parts(context.args)
        if err:
            await msg.reply_text(_err_card(f"{BOT_BRAND} • Entrada inválida", [err]), parse_mode="HTML", reply_to_message_id=msg.message_id)
            return

    # (1) Ajustar plan si se pasó (+ antispam automático)
    plan_ok, plan_msg, anti_val = _do_plan_update_if_provided(target_id, plan_txt)
    if not plan_ok:
        await msg.reply_text(
            _err_card(f"{BOT_BRAND} • No se pudo actualizar el plan", [plan_msg]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    # (2) Operar suscripción/días
    st, js = _operate(SUB_ENDPOINT, target_id, oper, cantidad)
    if st != 200:
        await msg.reply_text(
            _err_card(f"{BOT_BRAND} • Fallo al operar suscripción", [f"Código: {st}", str(js.get('message','Error'))]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    # (3) Log de compra (DIAS)
    signo = "+" if oper == "sumar" else "-"
    cantidad_txt = f"{signo}{cantidad} DIAS"
    _log_compra(id_tg=target_id, id_vendedor=str(caller.id), cantidad_texto=cantidad_txt)

    # (4) Mostrar resultado
    lines = [
        f"Cliente: {_badge(target_id)}",
        f"Plan aplicado: {_badge(plan_txt)}",
        f"Operación: {_badge(cantidad_txt)}",
    ]
    if anti_val is not None:
        lines.append(f"Anti-spam ajustado: {_badge(anti_val)} s")
    pretty = _pretty_card(f"{BOT_BRAND} • Suscripción ({oper})", lines)
    await msg.reply_text(pretty, parse_mode="HTML", reply_to_message_id=msg.message_id)

# =========================
# /setrol (sin log de compras)
# =========================
def _parse_setrol(args: list[str]) -> tuple[str|None, str|None, str|None]:
    joined = " ".join(args).strip()
    if "|" not in joined:
        return None, "Formato inválido. Usa: <code>/setrol ID|ROL</code>", None
    parts = [x.strip() for x in joined.split("|")]
    if len(parts) != 2:
        return None, "Debes enviar: <code>/setrol ID|ROL</code>", None
    id_tg, rol_txt = parts
    if not id_tg.isdigit():
        return None, "ID inválido (numérico).", None
    rol_up = rol_txt.upper()
    allowed_roles = {"FREE", "BASICO", "STANDARD", "PREMIUM", "SELLER", "CO-FUNDADOR", "FUNDADOR", "ADMIN", "USER"}
    if rol_up not in allowed_roles:
        return None, "ROL inválido.", None
    return id_tg, None, rol_up

async def setrol_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    caller = update.effective_user

    ok, rol = _caller_role_and_auth(caller.id, need_setrol=True)
    if not ok:
        await msg.reply_text(
            _err_card(f"{BOT_BRAND} • Permiso denegado", [f"Se requiere rol {_badge('FUNDADOR/CO-FUNDADOR')} o estar en ADMIN_ID. Tu rol: {_badge(rol or '—')}"]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    if not context.args:
        await msg.reply_text(
            _warn_card(f"{BOT_BRAND} • Uso", ["<b>Formato:</b> <code>/setrol ID|ROL</code>"]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    target_id, err, rol_to = _parse_setrol(context.args)
    if err:
        await msg.reply_text(_err_card(f"{BOT_BRAND} • Entrada inválida", [err]), parse_mode="HTML", reply_to_message_id=msg.message_id)
        return

    st, js = _fetch_json(f"{ROL_ENDPOINT}?ID_TG={_urlparse.quote(target_id)}&rol={_urlparse.quote(rol_to)}")
    if st != 200:
        await msg.reply_text(
            _err_card(f"{BOT_BRAND} • No se pudo cambiar el rol", [f"Código: {st}", str(js.get('message','Error'))]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    pretty = _pretty_card(
        f"{BOT_BRAND} • Rol actualizado",
        [f"ID: {_badge(target_id)}", f"Nuevo rol: {_badge(rol_to)}"]
    )
    await msg.reply_text(pretty, parse_mode="HTML", reply_to_message_id=msg.message_id)

# =========================
# /setantispam
# =========================
def _parse_setantispam_args(args: list[str], reply_target: str | None) -> tuple[str|None, int|None, str|None]:
    """
    - Modo reply:   /setantispam 10           -> (id_respuesta, 10, None)
    - Modo manual:  /setantispam ID|10        -> (ID, 10, None)
    """
    joined = " ".join(args).strip()
    if reply_target:
        if not joined:
            return None, None, "Uso (respuesta): <code>/setantispam 10</code>"
        try:
            val = int(joined)
        except Exception:
            return None, None, "Valor inválido. Debe ser un entero (segundos)."
        if val < 0 or val > 3600:
            return None, None, "Valor fuera de rango (0–3600s)."
        return reply_target, val, None
    # Manual
    if "|" not in joined:
        return None, None, "Uso: <code>/setantispam ID|VALOR</code>"
    p = [x.strip() for x in joined.split("|")]
    if len(p) != 2:
        return None, None, "Formato inválido. Usa: <code>ID|VALOR</code>"
    id_tg, val_s = p
    if not id_tg.isdigit():
        return None, None, "ID inválido (numérico)."
    try:
        val = int(val_s)
    except Exception:
        return None, None, "Valor inválido. Debe ser un entero (segundos)."
    if val < 0 or val > 3600:
        return None, None, "Valor fuera de rango (0–3600s)."
    return id_tg, val, None

async def setantispam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setantispam:
      - Respondiendo a un usuario: /setantispam 10
      - Manual:                    /setantispam ID|10
    Permisos: FUNDADOR / CO-FUNDADOR / SELLER o ADMIN_ID
    """
    msg = update.effective_message
    caller = update.effective_user

    ok, rol = _caller_role_and_auth(caller.id, need_setrol=False)
    if not ok:
        await msg.reply_text(
            _err_card(f"{BOT_BRAND} • Permiso denegado", [f"Tu rol actual: {_badge(rol or '—')}."]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    reply_target = _extract_reply_target(update)
    id_tg, val, err = _parse_setantispam_args(context.args, reply_target)
    if err:
        await msg.reply_text(_err_card(f"{BOT_BRAND} • Entrada inválida", [err]), parse_mode="HTML", reply_to_message_id=msg.message_id)
        return

    st, js = _set_antispam(id_tg, val)
    if st != 200:
        await msg.reply_text(
            _err_card(f"{BOT_BRAND} • No se pudo actualizar anti-spam", [f"Código: {st}", str(js.get('message','Error'))]),
            parse_mode="HTML",
            reply_to_message_id=msg.message_id
        )
        return

    pretty = _pretty_card(
        f"{BOT_BRAND} • Anti-spam actualizado",
        [f"Usuario: {_badge(id_tg)}", f"Valor: {_badge(val)} s"]
    )
    await msg.reply_text(pretty, parse_mode="HTML", reply_to_message_id=msg.message_id)

# =========================
# Wrappers públicos
# =========================
async def setcred_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _handle_cred_like(update, context, oper="igualar")

async def cred_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _handle_cred_like(update, context, oper="sumar")

async def uncred_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _handle_cred_like(update, context, oper="restar")

async def setsub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _handle_sub_like(update, context, oper="igualar")

async def sub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _handle_sub_like(update, context, oper="sumar")

async def unsub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _handle_sub_like(update, context, oper="restar")
