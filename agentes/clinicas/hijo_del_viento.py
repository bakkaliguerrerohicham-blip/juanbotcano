"""
HIJO DEL VIENTO — Cerebro del pipeline MetaSkills
El usuario describe su problema en lenguaje libre.
HdV decide: sector, especialistas a convocar, formato de entrega.
No se le pide nada al usuario salvo el problema.
"""
import os
import sys
import json
import time
import re
import ast as _ast
from datetime import datetime

METASKILLS_DIR = os.path.join(os.path.dirname(__file__), "../../metaskills")
CATALOGS_DIR = os.path.join(METASKILLS_DIR, "skills/catalog")
GENERATED_PATH = os.path.join(METASKILLS_DIR, "skills/skills_generadas.json")
AUTOGENERADAS_DIR = os.path.join(METASKILLS_DIR, "skills/autogeneradas")

SECTOR_CATALOG_MAP = {
    "dental": "dental.py",
    "inmobiliaria": "inmobiliaria.py",
    "gestoria": "gestoria.py",
    "veterinaria": "veterinaria.py",
    "abogados": "abogados.py",
}

FORMATOS_SALIDA = [
    "meta_skill",   # Automatización recurrente → JSON + Python
    "protocolo",    # Proceso/procedimiento → pasos ordenados
    "guion",        # Comunicación → script de llamada/WhatsApp
    "checklist",    # Validación → lista de verificación
    "informe",      # Análisis → reporte ejecutivo
    "plantilla",    # Documento → plantilla rellenable
]

C = {
    "reset": "\033[0m", "bold": "\033[1m", "cyan": "\033[36m",
    "green": "\033[32m", "yellow": "\033[33m", "red": "\033[31m",
    "magenta": "\033[35m", "blue": "\033[34m", "dim": "\033[2m",
    "white": "\033[97m",
}


# ─── Logging ──────────────────────────────────────────────────────────────────

def _log(nivel: str, msg: str):
    iconos = {
        "ESCUCHA": f"{C['magenta']}👂{C['reset']}",
        "VUELO":   f"{C['magenta']}⟿{C['reset']}",
        "RUTA":    f"{C['cyan']}⇒{C['reset']}",
        "HALLAZGO":f"{C['green']}✦{C['reset']}",
        "AI":      f"{C['magenta']}◈{C['reset']}",
        "OK":      f"{C['green']}✓{C['reset']}",
        "WARN":    f"{C['yellow']}⚠{C['reset']}",
        "INFO":    f"{C['blue']}ℹ{C['reset']}",
        "ENTREGA": f"{C['green']}📦{C['reset']}",
    }
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {C['dim']}[{ts}]{C['reset']} {iconos.get(nivel,'·')}  {msg}")


def _banner(texto_libre: str):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"\n{C['bold']}{C['magenta']}╔{'═'*62}╗{C['reset']}")
    print(f"{C['bold']}{C['magenta']}║  🌬  HIJO DEL VIENTO  [{ts}]{' '*(36-len(ts))}║{C['reset']}")
    print(f"{C['bold']}{C['magenta']}║  Escuchando · Decidiendo · Entregando                  ║{C['reset']}")
    print(f"{C['bold']}{C['magenta']}╚{'═'*62}╝{C['reset']}")
    _log("ESCUCHA", f"Problema recibido ({len(texto_libre)} chars)")


# ─── Motor IA (Claude → GPT-4o fallback) ─────────────────────────────────────

def _llamar_ia(prompt: str, max_tokens: int = 1200, temp: float = 0.3) -> str:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(METASKILLS_DIR, ".env"))

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    raw = None

    if anthropic_key:
        try:
            import anthropic as _anthropic
            c = _anthropic.Anthropic(api_key=anthropic_key)
            msg = c.messages.create(
                model="claude-sonnet-4-6", max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception:
            pass

    from openai import OpenAI
    c2 = OpenAI(api_key=openai_key)
    r = c2.chat.completions.create(
        model="gpt-4o", max_tokens=max_tokens, temperature=temp,
        messages=[
            {"role": "system", "content": "Responde SOLO con JSON válido, sin texto extra."},
            {"role": "user", "content": prompt},
        ],
    )
    return r.choices[0].message.content.strip()


# ─── Fase 1: Análisis de intención ───────────────────────────────────────────

def _analizar_intencion(texto: str, ids_catalogo: list[str]) -> dict:
    """IA lee el problema y decide: sector, formato, urgencia, si es nueva skill."""
    _log("AI", "Analizando intención libre con IA...")

    sectores_disponibles = list(SECTOR_CATALOG_MAP.keys()) + [
        "taller", "restaurante", "hotel", "farmacia", "ecommerce",
        "consultoria", "educacion", "seguridad", "logistica", "otro",
    ]
    formatos_desc = {
        "meta_skill":  "El problema es recurrente y automatizable — hay que crear un microservicio de IA",
        "protocolo":   "El problema es un proceso que necesita pasos ordenados",
        "guion":       "El problema es de comunicación (llamadas, WhatsApp, emails, negociación)",
        "checklist":   "El problema es de validación, revisión o auditoría",
        "informe":     "El problema pide análisis, diagnóstico o reporte ejecutivo",
        "plantilla":   "El problema pide un documento, contrato o formulario reutilizable",
    }

    prompt = f"""Eres el cerebro del sistema MetaSkills de Impacto Digital.
Un usuario ha descrito su problema en lenguaje libre. Debes entenderlo y decidir cómo resolverlo.

PROBLEMA DEL USUARIO:
\"\"\"{texto}\"\"\"

IDs de skills YA disponibles en el catálogo:
{json.dumps(ids_catalogo[:40], ensure_ascii=False)}

Sectores disponibles: {', '.join(sectores_disponibles)}

Formatos de salida posibles:
{json.dumps(formatos_desc, ensure_ascii=False, indent=2)}

Responde SOLO con este JSON:
{{
  "sector": "<sector más probable del negocio del usuario>",
  "sector_es_conocido": <true si está en SECTOR_CATALOG_MAP, false si es nuevo>,
  "formato_salida": "<uno de: {', '.join(FORMATOS_SALIDA)}>",
  "razon_formato": "<por qué este formato en 1 frase>",
  "skill_existente_id": "<id de skill existente que resuelve esto, o null si no hay>",
  "es_skill_nueva": <true|false>,
  "nombre_propuesto": "<Nombre Comercial Corto — máx 5 palabras>",
  "categoria": "<categoría del problema>",
  "urgencia": "<alta|media|baja>",
  "palabras_clave": ["<kw1>", "<kw2>", "<kw3>"],
  "resumen_problema": "<el problema en 1 frase directa>"
}}"""

    raw = _llamar_ia(prompt, max_tokens=600, temp=0.2)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"sector": "general", "formato_salida": "meta_skill", "es_skill_nueva": True,
                "palabras_clave": [], "nombre_propuesto": "Skill Nueva", "urgencia": "media",
                "resumen_problema": texto[:100], "skill_existente_id": None,
                "sector_es_conocido": False, "categoria": "general", "razon_formato": "—"}
    return json.loads(match.group())


# ─── Fase 2: Vuelo por la base de conocimiento ───────────────────────────────

def _cargar_catalogo(sector: str) -> list[dict]:
    skills = []
    catalog_file = SECTOR_CATALOG_MAP.get(sector)

    if catalog_file:
        cat_path = os.path.join(CATALOGS_DIR, catalog_file)
        if os.path.exists(cat_path):
            with open(cat_path, encoding="utf-8") as f:
                contenido = f.read()
            try:
                tree = _ast.parse(contenido)
                for node in _ast.walk(tree):
                    if isinstance(node, _ast.Assign):
                        for t in node.targets:
                            if isinstance(t, _ast.Name) and t.id == "SKILLS":
                                skills.extend(_ast.literal_eval(node.value))
            except Exception:
                pass
    else:
        # Sector nuevo: carga todos para extraer patrones cross-sector
        for fname in SECTOR_CATALOG_MAP.values():
            cat_path = os.path.join(CATALOGS_DIR, fname)
            if os.path.exists(cat_path):
                with open(cat_path, encoding="utf-8") as f:
                    contenido = f.read()
                try:
                    tree = _ast.parse(contenido)
                    for node in _ast.walk(tree):
                        if isinstance(node, _ast.Assign):
                            for t in node.targets:
                                if isinstance(t, _ast.Name) and t.id == "SKILLS":
                                    skills.extend(_ast.literal_eval(node.value))
                except Exception:
                    pass

    if os.path.exists(GENERATED_PATH):
        with open(GENERATED_PATH, encoding="utf-8") as f:
            try:
                skills.extend(json.load(f))
            except json.JSONDecodeError:
                pass

    return skills


def _volar(sector: str, palabras_clave: list[str], skills_rel_ids: list[str]) -> dict:
    skills = _cargar_catalogo(sector)
    skills_sector = [s for s in skills if s.get("sector") == sector] or skills

    modo = "propio" if any(s.get("sector") == sector for s in skills) else "cross-sector"
    _log("VUELO", f"Catálogo {sector.upper()} ({modo}) — {C['bold']}{len(skills_sector)} skills{C['reset']}")

    skills_rel = [s for s in skills if s.get("id") in skills_rel_ids]
    skills_kw = []
    for kw in palabras_clave:
        for s in skills_sector:
            texto = (s.get("description", "") + s.get("system_prompt", "")).lower()
            if kw.lower() in texto and s not in skills_kw and s not in skills_rel:
                skills_kw.append(s)
                break

    for sr in skills_rel:
        _log("HALLAZGO", f"[{sr['id']}] {sr.get('name', '')} ({sr.get('category', '')})")
    for sk in skills_kw:
        _log("HALLAZGO", f"[{sk['id']}] {sk.get('name', '')} — por keyword")

    precios = [s.get("price_eur", 0) for s in skills_sector if s.get("price_eur")]
    precio_medio = int(sum(precios) / len(precios)) if precios else 79

    verbos = set()
    formatos = []
    categorias = []
    for s in skills_sector:
        p = s.get("system_prompt", "")
        c = s.get("category", "")
        if c and c not in categorias:
            categorias.append(c)
        verbos.update(re.findall(r'Genera|Clasifica|Extrae|Calcula|Analiza|Detecta|Responde|Crea|Valida', p))
        if re.search(r'OPCIÓN \d|FASE \d|PASO \d|NIVEL \d', p):
            formatos.append("numerado")
        elif re.search(r'[A-Z]{3,}:', p):
            formatos.append("secciones")

    plantilla = ""
    if skills_rel:
        plantilla = skills_rel[0].get("system_prompt", "")[:400]
    elif skills_sector:
        ref = max(skills_sector, key=lambda s: s.get("price_eur", 0))
        plantilla = ref.get("system_prompt", "")[:400]

    return {
        "skills_relacionadas": [
            {"id": s.get("id"), "name": s.get("name"), "category": s.get("category"),
             "price_eur": s.get("price_eur")}
            for s in skills_rel
        ],
        "skills_kw": [{"id": s.get("id"), "name": s.get("name")} for s in skills_kw],
        "patrones": {
            "verbos_accion": list(verbos),
            "formatos_output": list(set(formatos)),
            "categorias_usadas": categorias,
            "precio_medio_sector": precio_medio,
        },
        "plantilla_referencia": plantilla,
        "total_skills_sector": len(skills_sector),
        "precio_recomendado": precio_medio,
        "categorias_disponibles": categorias,
    }


# ─── Fase 3: Especialistas ───────────────────────────────────────────────────

def _convocar_desarrollador(problema: str, sector: str, nombre: str,
                             categoria: str, componentes: dict) -> dict:
    """Llama al Desarrollador para fabricar una Meta-Skill."""
    from desarrollador import desarrollar

    # Construye el paquete que desarrollador.py espera
    diagnostico_simulado = {
        "problema": problema,
        "sector": sector,
        "diagnostico": {
            "categoria_sugerida": categoria,
            "nombre_skill_propuesto": nombre,
            "skills_relacionadas": [s["id"] for s in componentes.get("skills_relacionadas", [])],
        },
    }
    paquete_vuelo = {
        "diagnostico_entrada": diagnostico_simulado,
        "componentes": componentes,
    }
    return desarrollar(paquete_vuelo)


def _generar_salida_libre(problema: str, formato: str, sector: str,
                           componentes: dict, intencion: dict) -> str:
    """Para formatos que no son meta_skill, genera el contenido con IA directamente."""
    _log("AI", f"Generando {C['bold']}{formato.upper()}{C['reset']} con IA...")

    nombre = intencion.get("nombre_propuesto", "Solución")
    precio_ref = componentes.get("precio_recomendado", 79)
    skills_ref = componentes.get("skills_relacionadas", [])
    skills_desc = "\n".join(
        f"- [{s['id']}] {s['name']}: {s.get('category', '')}" for s in skills_ref[:3]
    ) or "— (sin referencias directas, sector nuevo)"

    instruccion_formato = {
        "protocolo": (
            "Genera un PROTOCOLO paso a paso (numerado, máx 10 pasos). "
            "Cada paso: acción concreta, quién la hace, cuánto tarda, qué falla si se salta."
        ),
        "guion": (
            "Genera un GUIÓN listo para usar (WhatsApp, llamada o email según el problema). "
            "Incluye apertura, desarrollo, objeciones posibles y cierre. Texto literal, no instrucciones."
        ),
        "checklist": (
            "Genera una CHECKLIST de verificación con ítems binarios (✓/✗). "
            "Agrupa por fase. Incluye el criterio de aceptación para cada ítem."
        ),
        "informe": (
            "Genera un INFORME EJECUTIVO: resumen en 3 bullets, análisis del problema, "
            "causas probables, impacto económico estimado, 3 recomendaciones priorizadas."
        ),
        "plantilla": (
            "Genera una PLANTILLA de documento rellenable con campos [ENTRE CORCHETES]. "
            "Incluye todas las secciones necesarias con instrucciones breves."
        ),
    }.get(formato, "Genera la solución más útil para el problema dado.")

    prompt = f"""Eres un consultor senior de Impacto Digital especializado en sector {sector}.

PROBLEMA DEL CLIENTE:
\"\"\"{problema}\"\"\"

CONTEXTO DEL CATÁLOGO:
{skills_desc}

INSTRUCCIÓN: {instruccion_formato}

NOMBRE DE LA SOLUCIÓN: {nombre}
SECTOR: {sector}

Genera la solución directamente en español, lista para usar. Sin introducción. Sin meta-comentarios."""

    return _llamar_ia(prompt, max_tokens=1500, temp=0.4)


# ─── Renderizado de salida ────────────────────────────────────────────────────

def _mostrar_skill(dev_resultado: dict, formato_visual: str = "meta_skill"):
    skill = dev_resultado.get("skill_def", {})
    lat = dev_resultado.get("latencia_ms", 0)
    ruta_json = dev_resultado.get("ruta_json", "")
    ruta_py = dev_resultado.get("ruta_py", "")

    print(f"\n  {C['bold']}{C['green']}╔{'═'*60}╗{C['reset']}")
    print(f"  {C['bold']}{C['green']}║  📦 META-SKILL LISTA PARA PRODUCCIÓN{'─'*21}║{C['reset']}")
    print(f"  {C['bold']}{C['green']}╠{'═'*60}╣{C['reset']}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  ID       : {C['bold']}{skill.get('id', '—')}{C['reset']}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Nombre   : {C['bold']}{skill.get('name', '—')}{C['reset']}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Sector   : {skill.get('sector', '—')} · {skill.get('category', '—')}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Precio   : {C['bold']}{skill.get('price_eur', '—')}€/mes{C['reset']}  (setup {skill.get('price_setup_eur', '—')}€)")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Latencia : {lat}ms")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  JSON     : {os.path.relpath(ruta_json, METASKILLS_DIR) if ruta_json else '—'}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Python   : {os.path.relpath(ruta_py, METASKILLS_DIR) if ruta_py else '—'}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Endpoint : POST /skills/{skill.get('id', '—')}/run")
    pitch = skill.get("pitch_comercial", "")
    if pitch:
        print(f"  {C['bold']}{C['green']}║{C['reset']}")
        print(f"  {C['bold']}{C['green']}║{C['reset']}  Pitch    : {C['dim']}{pitch[:56]}{C['reset']}")
    problema = skill.get("problema_que_resuelve", "")
    if problema:
        print(f"  {C['bold']}{C['green']}║{C['reset']}  Resuelve : {C['dim']}{problema[:56]}...{C['reset']}" if len(problema) > 56 else f"  {C['bold']}{C['green']}║{C['reset']}  Resuelve : {C['dim']}{problema}{C['reset']}")
    print(f"  {C['bold']}{C['green']}╚{'═'*60}╝{C['reset']}")


def _mostrar_skill_existente(skill_id: str, skills: list[dict]):
    skill = next((s for s in skills if s.get("id") == skill_id), None)
    if not skill:
        _log("WARN", f"Skill '{skill_id}' referenciada pero no encontrada en catálogo")
        return

    print(f"\n  {C['bold']}{C['yellow']}╔{'═'*60}╗{C['reset']}")
    print(f"  {C['bold']}{C['yellow']}║  ✦ SKILL EXISTENTE ENCONTRADA{'─'*29}║{C['reset']}")
    print(f"  {C['bold']}{C['yellow']}╠{'═'*60}╣{C['reset']}")
    print(f"  {C['bold']}{C['yellow']}║{C['reset']}  ID       : {C['bold']}{skill.get('id', '—')}{C['reset']}")
    print(f"  {C['bold']}{C['yellow']}║{C['reset']}  Nombre   : {C['bold']}{skill.get('name', '—')}{C['reset']}")
    print(f"  {C['bold']}{C['yellow']}║{C['reset']}  Sector   : {skill.get('sector', '—')} · {skill.get('category', '—')}")
    print(f"  {C['bold']}{C['yellow']}║{C['reset']}  Precio   : {skill.get('price_eur', '—')}€/mes")
    print(f"  {C['bold']}{C['yellow']}║{C['reset']}  Endpoint : POST /skills/{skill.get('id', '—')}/run")
    desc = skill.get("description", "")
    if desc:
        print(f"  {C['bold']}{C['yellow']}║{C['reset']}  Uso      : {C['dim']}{desc[:58]}{C['reset']}")
    print(f"  {C['bold']}{C['yellow']}╚{'═'*60}╝{C['reset']}")


def _mostrar_salida_libre(contenido: str, formato: str, nombre: str):
    titulo = {
        "protocolo":  "PROTOCOLO GENERADO",
        "guion":      "GUIÓN LISTO PARA USAR",
        "checklist":  "CHECKLIST DE VERIFICACIÓN",
        "informe":    "INFORME EJECUTIVO",
        "plantilla":  "PLANTILLA DE DOCUMENTO",
    }.get(formato, "SOLUCIÓN GENERADA")

    print(f"\n  {C['bold']}{C['cyan']}╔{'═'*60}╗{C['reset']}")
    print(f"  {C['bold']}{C['cyan']}║  📋 {titulo}{' '*(54-len(titulo))}║{C['reset']}")
    print(f"  {C['bold']}{C['cyan']}║  {nombre}{' '*(58-min(len(nombre),58))}║{C['reset']}")
    print(f"  {C['bold']}{C['cyan']}╠{'═'*60}╣{C['reset']}")
    print()
    for linea in contenido.strip().split("\n"):
        print(f"  {linea}")
    print(f"\n  {C['bold']}{C['cyan']}╚{'═'*60}╝{C['reset']}")


# ─── Punto de entrada público ─────────────────────────────────────────────────

def procesar(texto_libre: str) -> dict:
    """
    Entrada única: el usuario describe su problema.
    HdV decide todo lo demás y entrega el resultado.
    """
    _banner(texto_libre)
    t0 = time.time()

    # ── Cargar IDs conocidos para que la IA los tenga de referencia
    todos_los_ids = []
    for fname in SECTOR_CATALOG_MAP.values():
        cat_path = os.path.join(CATALOGS_DIR, fname)
        if os.path.exists(cat_path):
            with open(cat_path, encoding="utf-8") as f:
                todos_los_ids += re.findall(r'"id":\s*"([^"]+)"', f.read())
    if os.path.exists(GENERATED_PATH):
        with open(GENERATED_PATH, encoding="utf-8") as f:
            try:
                todos_los_ids += [s.get("id", "") for s in json.load(f)]
            except Exception:
                pass

    _log("INFO", f"Base de conocimiento: {C['bold']}{len(todos_los_ids)} skills{C['reset']} indexadas")

    # ── Fase 1: Analizar intención
    intencion = _analizar_intencion(texto_libre, todos_los_ids)
    sector = intencion.get("sector", "general")
    formato = intencion.get("formato_salida", "meta_skill")
    es_nueva = intencion.get("es_skill_nueva", True)
    skill_existente_id = intencion.get("skill_existente_id")
    palabras_clave = intencion.get("palabras_clave", [])
    nombre = intencion.get("nombre_propuesto", "Solución")
    categoria = intencion.get("categoria", "general")
    urgencia = intencion.get("urgencia", "media")
    resumen = intencion.get("resumen_problema", texto_libre[:80])
    sector_conocido = intencion.get("sector_es_conocido", False)

    print(f"\n  {C['bold']}{C['magenta']}┌─ INTENCIÓN DETECTADA {'─'*38}┐{C['reset']}")
    print(f"  {C['bold']}{C['magenta']}│{C['reset']}  Sector   : {C['bold']}{sector.upper()}{C['reset']} {'(catálogo propio)' if sector_conocido else '(sector nuevo — modo cross-sector)'}")
    print(f"  {C['bold']}{C['magenta']}│{C['reset']}  Formato  : {C['bold']}{formato.upper()}{C['reset']} — {intencion.get('razon_formato', '')[:42]}")
    print(f"  {C['bold']}{C['magenta']}│{C['reset']}  Nombre   : {C['bold']}{nombre}{C['reset']}")
    print(f"  {C['bold']}{C['magenta']}│{C['reset']}  Urgencia : {urgencia}  |  Categoría: {categoria}")
    print(f"  {C['bold']}{C['magenta']}│{C['reset']}  Resumen  : {C['dim']}{resumen[:55]}{C['reset']}")
    accion = "USAR SKILL EXISTENTE" if (not es_nueva and skill_existente_id) else f"FABRICAR {formato.upper()}"
    print(f"  {C['bold']}{C['magenta']}│{C['reset']}  Acción   : {C['bold']}{C['green']}{accion}{C['reset']}")
    print(f"  {C['bold']}{C['magenta']}└{'─'*60}┘{C['reset']}\n")

    # ── Fase 2: Vuelo por la base de conocimiento
    _log("VUELO", f"Explorando base de conocimiento para '{sector}'...")
    componentes = _volar(sector, palabras_clave, [skill_existente_id] if skill_existente_id else [])

    # ── Fase 3: Routing según la intención detectada
    resultado = {"intencion": intencion, "componentes": componentes}

    if not es_nueva and skill_existente_id:
        # ── Ruta A: Skill existente encontrada
        _log("RUTA", f"Ruta A — Skill existente: {C['bold']}{skill_existente_id}{C['reset']}")
        todos_skills = _cargar_catalogo(sector)
        _mostrar_skill_existente(skill_existente_id, todos_skills)
        resultado["tipo"] = "existente"
        resultado["skill_id"] = skill_existente_id

    elif formato == "meta_skill":
        # ── Ruta B: Fabricar Meta-Skill nueva
        _log("RUTA", f"Ruta B — Fabricando Meta-Skill: {C['bold']}{nombre}{C['reset']}")
        dev = _convocar_desarrollador(texto_libre, sector, nombre, categoria, componentes)
        _mostrar_skill(dev, formato)
        resultado["tipo"] = "meta_skill"
        resultado["skill_id"] = dev.get("skill_def", {}).get("id")
        resultado["dev_resultado"] = dev

    else:
        # ── Ruta C: Generar contenido libre (protocolo, guion, checklist, informe, plantilla)
        _log("RUTA", f"Ruta C — Generando {C['bold']}{formato.upper()}{C['reset']}: {nombre}")
        contenido = _generar_salida_libre(texto_libre, formato, sector, componentes, intencion)
        _mostrar_salida_libre(contenido, formato, nombre)
        resultado["tipo"] = formato
        resultado["contenido"] = contenido

    t_total = time.time() - t0
    _log("OK", f"Entregado en {C['bold']}{t_total:.1f}s{C['reset']} — formato: {C['bold']}{formato.upper()}{C['reset']}")

    return resultado


# ─── Punto de entrada standalone ─────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(METASKILLS_DIR, ".env"))

    if len(sys.argv) > 1:
        texto = " ".join(sys.argv[1:])
    else:
        print(f"\n  {C['bold']}{C['magenta']}🌬  MetaSkills — Hijo del Viento{C['reset']}")
        print(f"  {C['dim']}Describe tu problema con tus propias palabras:{C['reset']}\n")
        texto = input("  > ").strip()
        if not texto:
            print("  Sin problema, sin solución.")
            sys.exit(0)

    procesar(texto)
