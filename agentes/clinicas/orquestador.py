"""
ORQUESTADOR — Pipeline completo MetaSkills Clínicas
Flujo: PROBLEMA → Diagnosticador → Hijo del Viento → Desarrollador → Meta-Skill
"""
import os
import sys
import time
from datetime import datetime

# Añadir metaskills al path para los imports
METASKILLS_DIR = os.path.join(os.path.dirname(__file__), "../../metaskills")
sys.path.insert(0, METASKILLS_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(METASKILLS_DIR, ".env"))

from diagnosticador import diagnosticar
from hijo_del_viento import volar
from desarrollador import desarrollar

C = {
    "reset": "\033[0m", "bold": "\033[1m", "cyan": "\033[36m",
    "green": "\033[32m", "yellow": "\033[33m", "magenta": "\033[35m",
    "dim": "\033[2m", "white": "\033[97m",
}


def _separador():
    print(f"\n  {C['dim']}{'─'*62}{C['reset']}\n")


def _header_principal():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{C['bold']}{C['cyan']}{'═'*64}{C['reset']}")
    print(f"{C['bold']}{C['cyan']}   METASKILLS PIPELINE — Clínicas Dentales{C['reset']}")
    print(f"{C['bold']}{C['cyan']}   Impacto Digital  ·  {ts}{C['reset']}")
    print(f"{C['bold']}{C['cyan']}{'═'*64}{C['reset']}")
    print(f"\n  {C['bold']}Flujo:{C['reset']} PROBLEMA → {C['cyan']}Diagnosticador{C['reset']} → {C['magenta']}Hijo del Viento{C['reset']} → {C['green']}Desarrollador{C['reset']} → Meta-Skill\n")


def _resumen_final(resultado_dx, resultado_vuelo, resultado_dev, t_total):
    skill = resultado_dev.get("skill_def", {})
    print(f"\n{C['bold']}{C['green']}{'═'*64}{C['reset']}")
    print(f"{C['bold']}{C['green']}   PIPELINE COMPLETADO EXITOSAMENTE{C['reset']}")
    print(f"{C['bold']}{C['green']}{'═'*64}{C['reset']}")
    print(f"\n  {C['bold']}Tiempo total        :{C['reset']} {t_total:.2f}s")
    print(f"  {C['bold']}Skills analizadas   :{C['reset']} {resultado_dx.get('ids_catalogo_total', 0)}")
    print(f"  {C['bold']}Componentes usados  :{C['reset']} {len(resultado_vuelo['componentes']['skills_relacionadas'])} skills de referencia")
    print(f"  {C['bold']}Latencia Claude AI  :{C['reset']} {resultado_dev.get('latencia_ms', 0)}ms")
    print(f"\n  {C['bold']}{C['green']}SKILL GENERADA:{C['reset']}")
    print(f"  ├─ ID         : {C['bold']}{skill.get('id', '—')}{C['reset']}")
    print(f"  ├─ Nombre     : {C['bold']}{skill.get('name', '—')}{C['reset']}")
    print(f"  ├─ Precio     : {C['bold']}{skill.get('price_eur', '—')}€/mes{C['reset']}")
    print(f"  ├─ JSON       : {os.path.relpath(resultado_dev.get('ruta_json', ''), METASKILLS_DIR)}")
    print(f"  ├─ Python     : {os.path.relpath(resultado_dev.get('ruta_py', ''), METASKILLS_DIR)}")
    print(f"  └─ Endpoint   : POST /skills/{skill.get('id', '—')}/run")
    print(f"\n  {C['bold']}System Prompt (extracto):{C['reset']}")
    sp = skill.get("system_prompt", "")
    for linea in sp[:300].split(". "):
        if linea.strip():
            print(f"    {C['dim']}{linea.strip()}.{C['reset']}")
    print(f"\n{C['bold']}{C['green']}{'═'*64}{C['reset']}\n")


def ejecutar_pipeline(problema: str, sector: str = "dental"):
    _header_principal()

    print(f"  {C['bold']}PROBLEMA ENTRANTE:{C['reset']}")
    print(f"  {C['dim']}┌{'─'*60}┐{C['reset']}")
    # Imprimir el problema en bloques de 58 chars
    palabras = problema.split()
    linea = ""
    for palabra in palabras:
        if len(linea) + len(palabra) + 1 > 58:
            print(f"  {C['dim']}│{C['reset']} {linea}")
            linea = palabra
        else:
            linea = (linea + " " + palabra).strip()
    if linea:
        print(f"  {C['dim']}│{C['reset']} {linea}")
    print(f"  {C['dim']}└{'─'*60}┘{C['reset']}")

    t_inicio = time.time()

    # ── FASE 1: DIAGNOSTICADOR ─────────────────────────────────────────────
    _separador()
    print(f"  {C['bold']}{C['cyan']}FASE 1 / 3 — DIAGNOSTICADOR{C['reset']}")
    resultado_dx = diagnosticar(problema, sector=sector)

    # ── FASE 2: HIJO DEL VIENTO ────────────────────────────────────────────
    _separador()
    print(f"  {C['bold']}{C['magenta']}FASE 2 / 3 — HIJO DEL VIENTO{C['reset']}")
    resultado_vuelo = volar(resultado_dx)

    # ── FASE 3: DESARROLLADOR ──────────────────────────────────────────────
    _separador()
    print(f"  {C['bold']}{C['green']}FASE 3 / 3 — DESARROLLADOR{C['reset']}")
    resultado_dev = desarrollar(resultado_vuelo)

    t_total = time.time() - t_inicio

    # ── RESUMEN FINAL ──────────────────────────────────────────────────────
    _separador()
    _resumen_final(resultado_dx, resultado_vuelo, resultado_dev, t_total)

    return resultado_dev


if __name__ == "__main__":
    PROBLEMA_DENTAL_INEDITO = (
        "La recepcionista no sabe cómo codificar correctamente los tratamientos dentales "
        "para las mutuas (Adeslas, Sanitas, DKV, Asisa, Mapfre Salud). "
        "Cada vez que enviamos una factura a la aseguradora nos la rechazan porque "
        "pusimos el código de nomenclatura equivocado o porque el tratamiento necesitaba "
        "autorización previa y no la pedimos. Hemos perdido más de 3.000€ este trimestre "
        "en reclamaciones rechazadas. Necesitamos que el sistema ayude a la recepcionista "
        "a elegir el código correcto al momento de cerrar la cita y le avise si el "
        "tratamiento requiere autorización previa antes de realizarlo."
    )

    ejecutar_pipeline(PROBLEMA_DENTAL_INEDITO, sector="dental")
