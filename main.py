import os
import sys
import json
import time
import sqlite3
from urllib import request as _urlreq
from urllib.error import HTTPError, URLError
from urllib import parse as _urlparse
from datetime import datetime
from telegram import Update
from telegram.ext import CommandHandler, Application, CallbackQueryHandler, ContextTypes, CallbackContext, MessageHandler, filters

from comandos.dnim import dnim_command
from comandos.c4blanco import c4blanco_command
from comandos.c4 import c4_command
from comandos.dnivel import dnivel_command
from comandos.dnivam import dnivam_command
from comandos.dnivaz import dnivaz_command
from comandos.c4azul import c4azul_command
from comandos.dni import dni_command
from comandos.dnif import dnif_command
from comandos.nm import nm_command
from comandos.revitec import revitec_command
from comandos.tiveqr import tiveqr_command
from comandos.soat import soat_command
from comandos.tive import tive_command
from comandos.tiveor import tiveor_command
from comandos.tarjetafisica import tarjetafisica_command
from comandos.placasiento import placasiento_command
from comandos.pla import pla_command
from comandos.papeletas import papeletas_command
from comandos.insve import insve_command
from comandos.licencia import licencia_command
from comandos.licenciapdf import licenciapdf_command
from comandos.bolinv import bolinv_command
from comandos.rqv import rqv_command
from comandos.denunciasv import denunciasv_command
from comandos.det import det_command
from comandos.ant import ant_command
from comandos.antpe import antpe_command
from comandos.antpo import antpo_command
from comandos.antju import antju_command
from comandos.denuncias import denuncias_command
from comandos.rq import rq_command
from comandos.fis import fis_command
from comandos.fispdf import fispdf_command
from comandos.hogar import hogar_command
from comandos.ag import ag_command
from comandos.agv import agv_command
from comandos.her import her_command
from comandos.numclaro import numclaro_command
from comandos.correo import correo_command
from comandos.enteldb import enteldb_command
from comandos.movistar import movistar_command
from comandos.bitel import bitel_command
from comandos.claro import claro_command
from comandos.vlop import vlop_command
from comandos.vlnum import vlnum_command
from comandos.cel import cel_command
from comandos.tels import tels_command
from comandos.telp import telp_command
from comandos.tel import tel_command
from comandos.sunarp import sunarp_command
from comandos.sunarpdf import sunarpdf_command
from comandos.sueldos import sueldos_command
from comandos.trabajos import trabajos_command
from comandos.actamdb import actamdb_command
from comandos.actaddb import actaddb_command
from comandos.migrapdf import migrapdf_command
from comandos.afp import afp_command
from comandos.dir import dir_command
from comandos.trabajadores import trabajadores_command
from comandos.sbs import sbs_command
from comandos.notas import notas_command
from comandos.essalud import essalud_command
from comandos.doc import doc_command
from comandos.ruc import ruc_command
from comandos.sunat import sunat_command
from comandos.seeker import seeker_command
from comandos.facial import facial_command
from comandos.start import start_command
from comandos.buy import buy_command
from comandos.me import me_command
from comandos.register import register_command
from comandos.terminos import terminos_command
from comandos.cmds import cmds_command, cmds_callback
from comandos.historial import historial_command
from comandos.compras import compras_command
from comandos.admin_ops import (
    setcred_command, cred_command, uncred_command,
    setsub_command, sub_command, unsub_command,
    setrol_command, setantispam_command
)
from comandos.cmdsadmin import cmdsadmin_command
from comandos.genkey import genkey, redeem, keyslog, keysinfo
from comandos import admin_requests

# ---------- Config ----------
CONFIG_FILE_PATH = 'config.json'
API_DB_BASE = "https://web-production-843d9.up.railway.app"  # para tg_info
TELEGRAM_TOKEN = None
ADMIN_ID = None

if not os.path.exists(CONFIG_FILE_PATH):
    print(f"Error: El archivo de configuración '{CONFIG_FILE_PATH}' no se encuentra.")
    print("Asegúrate de que 'config.json' esté en el mismo directorio que 'main.py'.")
    sys.exit(1)

try:
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    TELEGRAM_TOKEN = config_data.get('TOKEN_BOT')
    ADMIN_ID = int(config_data.get('ADMIN_ID'))
    if not TELEGRAM_TOKEN:
        print("Error: 'TOKEN_BOT' o 'ADMIN_ID' no encontrado en 'config.json'. Por favor, asegúrate de que esté configurado.")
        sys.exit(1)
    print(f"ID cargado desde config.json: {ADMIN_ID}")
    print("TOKEN_BOT cargado exitosamente desde config.json.")
except json.JSONDecodeError as e:
    print(f"Error al decodificar JSON en '{CONFIG_FILE_PATH}': {e}")
    print("Asegúrate de que 'config.json' tenga un formato JSON válido.")
    sys.exit(1)
except Exception as e:
    print(f"Error inesperado al cargar la configuración desde '{CONFIG_FILE_PATH}': {e}")
    sys.exit(1)
    
# ---------- Anti-spam helpers ----------
# Memoria del último uso por usuario y comando
_last_call_ts: dict[tuple[int, str], float] = {}

def _fetch_json(url: str, timeout: int = 12):
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

def _get_antispam_seconds(user_id: int) -> int:
    """
    Lee ANTISPAM desde /tg_info. Fallback: 15s si falla o no viene.
    """
    st, js = _fetch_json(f"{API_DB_BASE}/tg_info?ID_TG={_urlparse.quote(str(user_id))}")
    if st == 200:
        data = (js.get("data") or {})
        try:
            val = int(data.get("ANTISPAM", 15))
            return max(0, val)
        except Exception:
            return 15
    # si no está registrado o falla, aplica 15s por defecto
    return 15

def anti_spam_guard(handler_coro, cmd_name: str):
    """
    Devuelve un wrapper async que respeta el anti-spam por usuario/command.
    """
    async def _wrapped(update, context):
        # Si no hay usuario/mensaje, delega
        if not getattr(update, "effective_user", None) or not getattr(update, "effective_message", None):
            return await handler_coro(update, context)

        user_id = update.effective_user.id
        key = (user_id, cmd_name)
        now = time.monotonic()
        antispam = _get_antispam_seconds(user_id)

        last = _last_call_ts.get(key)
        if last is not None and (now - last) < antispam:
            wait = int(antispam - (now - last)) + 1
            # Mensaje consistente con lo que reconoce tu parser:
            # "UPS, POR FAVOR ESPERA EL ANTI-SPAM DE X SEGUNDOS."
            await update.effective_message.reply_text(
                f"UPS, por favor espera el anti-spam de {wait} segundos.",
                reply_to_message_id=update.effective_message.message_id
            )
            return

        # marca desde YA para evitar race al ejecutar
        _last_call_ts[key] = now
        await handler_coro(update, context)

    return _wrapped

# ---------- Main ----------
def main():
    admin_requests.init_db()
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Públicos / generales
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("me", me_command))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("terminos", terminos_command))
    application.add_handler(CommandHandler("historial", historial_command))
    application.add_handler(CommandHandler("compras", compras_command))

    # Admin ops
    application.add_handler(CommandHandler("setcred", setcred_command))
    application.add_handler(CommandHandler("cred", cred_command))
    application.add_handler(CommandHandler("uncred", uncred_command))

    application.add_handler(CommandHandler("setsub", setsub_command))
    application.add_handler(CommandHandler("sub", sub_command))
    application.add_handler(CommandHandler("unsub", unsub_command))

    application.add_handler(CommandHandler("setrol", setrol_command))
    application.add_handler(CommandHandler("setantispam", setantispam_command))

    # -------------------- CMDS Y MENU ADMIN --------------------
    application.add_handler(CommandHandler("cmds", cmds_command))
    application.add_handler(CallbackQueryHandler(cmds_callback, pattern="^cmds_"))
    application.add_handler(CommandHandler("cmdsadmin", cmdsadmin_command))
    
    # -------------------- COMANDOS RENIEC --------------------
    application.add_handler(CommandHandler("nm", nm_command))
    application.add_handler(CommandHandler("dni", dni_command))
    application.add_handler(CommandHandler("dnif", dnif_command))
    application.add_handler(CommandHandler("dnim", dnim_command))
    application.add_handler(CommandHandler("c4", c4_command))
    application.add_handler(CommandHandler("c4blanco", c4blanco_command))
    application.add_handler(CommandHandler("c4azul", c4azul_command))
    application.add_handler(CommandHandler("dnivel", dnivel_command))
    application.add_handler(CommandHandler("dnivam", dnivam_command))
    application.add_handler(CommandHandler("dnivaz", dnivaz_command))

    # -------------------- COMANDOS VEHICULO --------------------
    application.add_handler(CommandHandler("revitec", revitec_command))
    application.add_handler(CommandHandler("tiveqr", tiveqr_command))
    application.add_handler(CommandHandler("soat", soat_command))
    application.add_handler(CommandHandler("tive", tive_command))
    application.add_handler(CommandHandler("tiveor", tiveor_command))
    application.add_handler(CommandHandler("tarjetafisica", tarjetafisica_command))
    application.add_handler(CommandHandler("placasiento", placasiento_command))
    application.add_handler(CommandHandler("pla", pla_command))
    application.add_handler(CommandHandler("papeletas", papeletas_command))
    application.add_handler(CommandHandler("bolinv", bolinv_command))
    application.add_handler(CommandHandler("insve", insve_command))
    application.add_handler(CommandHandler("licencia", licencia_command))
    application.add_handler(CommandHandler("licenciapdf", licenciapdf_command))

    # -------------------- COMANDOS DELITOS --------------------
    application.add_handler(CommandHandler("rqv", rqv_command))
    application.add_handler(CommandHandler("denunciasv", denunciasv_command))
    application.add_handler(CommandHandler("det", det_command))
    application.add_handler(CommandHandler("ant", ant_command))
    application.add_handler(CommandHandler("antpe", antpe_command))
    application.add_handler(CommandHandler("antpo", antpo_command))
    application.add_handler(CommandHandler("antju", antju_command))
    application.add_handler(CommandHandler("denuncias", denuncias_command))
    application.add_handler(CommandHandler("rq", rq_command))
    application.add_handler(CommandHandler("fis", fis_command))
    application.add_handler(CommandHandler("fispdf", fispdf_command))

    # -------------------- COMANDOS FAMILIA --------------------
    application.add_handler(CommandHandler("hogar", hogar_command))
    application.add_handler(CommandHandler("ag", ag_command))
    application.add_handler(CommandHandler("agv", agv_command))
    application.add_handler(CommandHandler("her", her_command))

    # -------------------- COMANDOS TELEFONIA --------------------
    application.add_handler(CommandHandler("numclaro", numclaro_command))
    application.add_handler(CommandHandler("correo", correo_command))
    application.add_handler(CommandHandler("enteldb", enteldb_command))
    application.add_handler(CommandHandler("movistar", movistar_command))
    application.add_handler(CommandHandler("bitel", bitel_command))
    application.add_handler(CommandHandler("claro", claro_command))
    application.add_handler(CommandHandler("vlop", vlop_command))
    application.add_handler(CommandHandler("vlnum", vlnum_command))
    application.add_handler(CommandHandler("cel", cel_command))
    application.add_handler(CommandHandler("tels", tels_command))
    application.add_handler(CommandHandler("telp", telp_command))
    application.add_handler(CommandHandler("tel", tel_command))

    # -------------------- COMANDOS SUNARP --------------------
    application.add_handler(CommandHandler("sunarp", sunarp_command))
    application.add_handler(CommandHandler("sunarpdf", sunarpdf_command))

    # -------------------- COMANDOS LABORAL --------------------
    application.add_handler(CommandHandler("sueldos", sueldos_command))
    application.add_handler(CommandHandler("trabajos", trabajos_command))

    # -------------------- COMANDOS ACTAS --------------------
    application.add_handler(CommandHandler("actamdb", actamdb_command))
    application.add_handler(CommandHandler("actaddb", actaddb_command))

    # -------------------- COMANDOS MIGRACIONES --------------------
    application.add_handler(CommandHandler("migrapdf", migrapdf_command))

    # -------------------- COMANDOS VARIOS --------------------
    application.add_handler(CommandHandler("afp", afp_command))
    application.add_handler(CommandHandler("dir", dir_command))
    application.add_handler(CommandHandler("trabajadores", trabajadores_command))
    application.add_handler(CommandHandler("sbs", sbs_command))
    application.add_handler(CommandHandler("notas", notas_command))
    application.add_handler(CommandHandler("essalud", essalud_command))
    application.add_handler(CommandHandler("doc", doc_command))
    application.add_handler(CommandHandler("ruc", ruc_command))
    application.add_handler(CommandHandler("sunat", sunat_command))
    application.add_handler(CommandHandler("seeker", seeker_command))
    
    # -------------------- GENERAR Y CANJEAR KEYS --------------------
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("keyslog", keyslog))
    application.add_handler(CommandHandler("keysinfo", keysinfo))

    # --- Handlers del admin ---
    application.add_handler(CommandHandler("reply", admin_requests.reply_request))
    application.add_handler(MessageHandler(filters.ALL, admin_requests.forward_file))

    print("Bot started and polling for updates...")
    application.run_polling()

if __name__ == '__main__':
    main()
