"""
DIAGNOSTICADOR — Agente 1 del pipeline MetaSkills Clínicas
Recibe un problema en lenguaje natural, lo disecciona y emite veredicto
sobre si existe skill adecuada o si hay un vacío real que fabricar.
"""
import sys
import os
import time
import json
from datetime import datetime

# ─── Colores ANSI ─────────────────────────────────────────────────────────────
C = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "magenta": "\033[35m",
    "blue": "\033[34m",
    "dim": "\033[2m",
}

CATALOGS_DIR = os.path.join(os.path.dirname(__file__), "../../metaskills/skills/catalog")
GENERATED_PATH = os.path.join(os.path.dirname(__file__), "../../metaskills/skills/skills_generadas.json")

SECTOR_CATALOG_MAP = {
    "dental": "dental.py",
    "inmobiliaria": "inmobiliaria.py",
    "gestoria": "gestoria.py",
    "veterinaria": "veterinaria.py",
    "abogados": "abogados.py",
}

CATEGORIAS = [
    "ventas", "productividad", "marketing", "atencion-cliente",
    "fiscal", "legal", "clinica", "urgencias", "fidelizacion",
    "agenda", "analisis", "captacion", "calidad", "reputacion"
]

SECTORES = ["dental", "inmobiliaria", "legal", "gestoria", "veterinaria", "hotel", "general"]


def _banner(titulo: str):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"\n{C['bold']}{C['cyan']}╔{'═'*60}╗{C['reset']}")
    print(f"{C['bold']}{C['cyan']}║  🔬 DIAGNOSTICADOR  [{ts}]{' '*(37-len(ts))}║{C['reset']}")
    print(f"{C['bold']}{C['cyan']}║  {titulo}{' '*(58-len(titulo))}║{C['reset']}")
    print(f"{C['bold']}{C['cyan']}╚{'═'*60}╝{C['reset']}")


def _log(nivel: str, msg: str):
    iconos = {"INFO": f"{C['blue']}ℹ{C['reset']}", "OK": f"{C['green']}✓{C['reset']}",
              "WARN": f"{C['yellow']}⚠{C['reset']}", "SCAN": f"{C['magenta']}◈{C['reset']}",
              "RESULT": f"{C['green']}▶{C['reset']}"}
    ts = datetime.now().strftime("%H:%M:%S")
    icono = iconos.get(nivel, "·")
    print(f"  {C['dim']}[{ts}]{C['reset']} {icono}  {msg}")


def _cargar_ids_existentes(sector: str = "dental") -> list[str]:
    """Lee los IDs de skills del catálogo del sector dado y del JSON de generadas."""
    ids = []
    catalog_file = SECTOR_CATALOG_MAP.get(sector)
    cat_path = os.path.join(CATALOGS_DIR, catalog_file) if catalog_file else None
    gen_path = GENERATED_PATH

    # Catálogo estático del sector
    if cat_path and os.path.exists(cat_path):
        with open(cat_path, encoding="utf-8") as f:
            import re
            ids += re.findall(r'"id":\s*"([^"]+)"', f.read())

    # Skills generadas dinámicamente
    if os.path.exists(gen_path):
        with open(gen_path, encoding="utf-8") as f:
            try:
                generadas = json.load(f)
                ids += [s.get("id", "") for s in generadas]
            except json.JSONDecodeError:
                pass
    return ids


def diagnosticar(problema: str, sector: str = "dental") -> dict:
    """
    Analiza el problema y devuelve un diagnóstico estructurado.
    Motor: Claude claude-sonnet-4-6 para la clasificación inteligente.
    """
    _banner("ANÁLISIS DE PROBLEMA ENTRANTE")

    _log("INFO", f"Problema recibido: {C['bold']}\"{problema[:80]}...\"" if len(problema) > 80 else f"Problema recibido: {C['bold']}\"{problema}\"")
    _log("INFO", f"Sector declarado: {C['bold']}{sector.upper()}{C['reset']}")

    time.sleep(0.3)
    _log("SCAN", f"Cargando base de conocimientos del catálogo {sector.upper()}...")
    ids_existentes = _cargar_ids_existentes(sector)
    _log("OK", f"Base de conocimientos cargada — {C['bold']}{len(ids_existentes)} skills{C['reset']} indexadas")

    time.sleep(0.2)
    _log("SCAN", "Invocando motor Claude claude-sonnet-4-6 para clasificación semántica...")

    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), "../../metaskills/.env")
    load_dotenv(env_path)

    prompt = f"""Eres el sistema de clasificación de problemas de Impacto Digital, empresa de IA para negocios.

Un cliente del sector "{sector}" nos envía este problema:

PROBLEMA: {problema}

IDs de skills YA EXISTENTES en nuestro catálogo:
{json.dumps(ids_existentes, ensure_ascii=False, indent=2)}

Analiza el problema y devuelve SOLO este JSON (sin texto extra):
{{
  "sector": "{sector}",
  "categoria_sugerida": "<una de: {', '.join(CATEGORIAS)}>",
  "es_skill_nueva": true,
  "razon": "<por qué no existe en el catálogo actual — máx 2 frases>",
  "skills_relacionadas": ["<id-skill-1>", "<id-skill-2>"],
  "nombre_skill_propuesto": "<Nombre Comercial Corto>",
  "urgencia": "<alta|media|baja>",
  "potencial_comercial": "<alto|medio|bajo>",
  "palabras_clave": ["<kw1>", "<kw2>", "<kw3>"]
}}

Si alguna skill existente YA resuelve el problema, pon es_skill_nueva: false e indica cuál en skills_relacionadas."""

    raw = None
    motor = None

    # Intentar Claude primero, fallback a OpenAI
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if anthropic_key:
        try:
            import anthropic as _anthropic
            client = _anthropic.Anthropic(api_key=anthropic_key)
            message = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            motor = "claude-sonnet-4-6"
        except Exception as e:
            _log("WARN", f"Claude no disponible ({type(e).__name__}), usando GPT-4o...")

    if raw is None:
        from openai import OpenAI
        client_oai = OpenAI(api_key=openai_key)
        resp = client_oai.chat.completions.create(
            model="gpt-4o", max_tokens=800,
            messages=[
                {"role": "system", "content": "Eres un clasificador de problemas. Responde SOLO con JSON válido."},
                {"role": "user", "content": prompt},
            ],
        )
        raw = resp.choices[0].message.content.strip()
        motor = "gpt-4o"

    if motor:
        _log("INFO", f"Motor de clasificación: {C['bold']}{motor}{C['reset']}")

    import re
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    diagnostico = json.loads(match.group()) if match else {}

    time.sleep(0.2)

    print(f"\n  {C['bold']}{C['cyan']}┌─ RESULTADO DEL DIAGNÓSTICO {'─'*32}┐{C['reset']}")
    es_nueva = diagnostico.get("es_skill_nueva", True)
    estado = f"{C['green']}🆕 SKILL NUEVA NECESARIA{C['reset']}" if es_nueva else f"{C['yellow']}⚠  SKILL SIMILAR EXISTENTE{C['reset']}"
    print(f"  {C['bold']}{C['cyan']}│{C['reset']}  Estado        : {estado}")
    print(f"  {C['bold']}{C['cyan']}│{C['reset']}  Categoría     : {C['bold']}{diagnostico.get('categoria_sugerida', '—')}{C['reset']}")
    print(f"  {C['bold']}{C['cyan']}│{C['reset']}  Nombre prop.  : {C['bold']}{diagnostico.get('nombre_skill_propuesto', '—')}{C['reset']}")
    print(f"  {C['bold']}{C['cyan']}│{C['reset']}  Urgencia      : {diagnostico.get('urgencia', '—')}")
    print(f"  {C['bold']}{C['cyan']}│{C['reset']}  Pot. comercial: {diagnostico.get('potencial_comercial', '—')}")
    print(f"  {C['bold']}{C['cyan']}│{C['reset']}  Razón         : {C['dim']}{diagnostico.get('razon', '—')}{C['reset']}")
    skills_rel = diagnostico.get("skills_relacionadas", [])
    if skills_rel:
        print(f"  {C['bold']}{C['cyan']}│{C['reset']}  Skills relac. : {', '.join(skills_rel)}")
    print(f"  {C['bold']}{C['cyan']}└{'─'*60}┘{C['reset']}")

    _log("OK", f"Diagnóstico completado — veredicto: {'FABRICAR SKILL NUEVA' if es_nueva else 'REDIRIGIR A SKILL EXISTENTE'}")

    return {
        "problema": problema,
        "sector": sector,
        "diagnostico": diagnostico,
        "ids_catalogo_total": len(ids_existentes),
    }


if __name__ == "__main__":
    PROBLEMA_DEMO = (
        "La recepcionista no sabe cómo codificar correctamente los tratamientos dentales "
        "para las mutuas (Adeslas, Sanitas, DKV). Cada vez que enviamos una factura a la aseguradora, "
        "nos la rechazan porque pusimos el código de nomenclatura equivocado. Hemos perdido más de 3.000€ "
        "este trimestre en reclamaciones rechazadas. Necesitamos algo que ayude a la recepcionista a "
        "elegir el código correcto al momento de cerrar la cita."
    )
    resultado = diagnosticar(PROBLEMA_DEMO, sector="dental")
    print(f"\n  {C['dim']}→ Diagnóstico listo para Hijo del Viento{C['reset']}\n")
    sys.exit(0)
