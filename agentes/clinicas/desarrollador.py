"""
DESARROLLADOR — Agente 3 del pipeline MetaSkills Clínicas
Recibe el diagnóstico + componentes y fabrica la Meta-Skill real:
- Llama al MetaFabricador (Claude claude-sonnet-4-6)
- Guarda en skills/autogeneradas/<id>.json
- Actualiza skills_generadas.json
- Genera el archivo Python de la skill lista para usar
"""
import os
import sys
import json
import time
import re
from datetime import datetime

C = {
    "reset": "\033[0m", "bold": "\033[1m", "cyan": "\033[36m",
    "green": "\033[32m", "yellow": "\033[33m", "red": "\033[31m",
    "magenta": "\033[35m", "blue": "\033[34m", "dim": "\033[2m",
    "white": "\033[97m",
}

METASKILLS_DIR = os.path.join(os.path.dirname(__file__), "../../metaskills")
AUTOGENERADAS_DIR = os.path.join(METASKILLS_DIR, "skills/autogeneradas")
GENERATED_JSON = os.path.join(METASKILLS_DIR, "skills/skills_generadas.json")


def _banner():
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"\n{C['bold']}{C['green']}╔{'═'*60}╗{C['reset']}")
    print(f"{C['bold']}{C['green']}║  ⚙  DESARROLLADOR  [{ts}]{' '*(36-len(ts))}║{C['reset']}")
    print(f"{C['bold']}{C['green']}║  Motor: Claude claude-sonnet-4-6 (Anthropic)                     ║{C['reset']}")
    print(f"{C['bold']}{C['green']}╚{'═'*60}╝{C['reset']}")


def _log(nivel: str, msg: str):
    iconos = {
        "BUILD": f"{C['green']}⚙{C['reset']}", "WRITE": f"{C['cyan']}✍{C['reset']}",
        "OK": f"{C['green']}✓{C['reset']}", "INFO": f"{C['blue']}ℹ{C['reset']}",
        "AI": f"{C['magenta']}◈{C['reset']}", "SAVE": f"{C['yellow']}💾{C['reset']}",
    }
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {C['dim']}[{ts}]{C['reset']} {iconos.get(nivel,'·')}  {msg}")


def _generar_skill_con_ia(problema: str, sector: str, componentes: dict) -> tuple[dict, str]:
    """Llama al MetaFabricador con Claude (fallback GPT-4o) con contexto enriquecido."""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(METASKILLS_DIR, ".env"))

    precio_ref = componentes.get("precio_recomendado", 79)
    patrones = componentes.get("patrones", {})
    verbos = ", ".join(patrones.get("verbos_accion", ["Clasifica", "Genera", "Extrae"])[:4])

    prompt = f"""Eres el arquitecto de microservicios de IA de Impacto Digital. Tu trabajo: convertir cualquier problema profesional en una skill de IA vendible como SaaS.

Un profesional del sector "{sector}" tiene este problema:

PROBLEMA: {problema}

CONTEXTO DEL CATÁLOGO EXISTENTE:
- Precio medio del sector: {precio_ref}€/mes
- Verbos dominantes en prompts exitosos: {verbos}
- Categorías ya cubiertas: {', '.join(patrones.get('categorias_usadas', [])[:6])}

INSTRUCCIÓN ESPECIAL: Esta skill debe cubrir un vacío REAL. El catálogo actual NO tiene ninguna skill de codificación de nomenclatura para mutuas/seguros. Crea algo genuinamente nuevo y específico.

Genera una skill de IA que resuelva exactamente ese problema. La skill debe:
1. Resolver el problema en menos de 30 segundos de uso
2. Poder venderse como microservicio por 49-149€/mes
3. Tener un system_prompt tan bueno que cualquier modelo lo ejecute perfectamente

Responde SOLO con este JSON (sin texto extra, sin bloques de código):

{{
  "id": "slug-kebab-case-unico-descriptivo",
  "name": "Nombre Comercial de la Skill (máx 5 palabras)",
  "description": "Qué hace en 1 frase y qué problema concreto resuelve",
  "category": "clinica",
  "sector": "{sector}",
  "price_eur": 89,
  "price_setup_eur": 497,
  "system_prompt": "Eres un experto en facturación dental a mutuas (Adeslas, Sanitas, DKV, Mapfre Salud, Asisa). Tu trabajo es identificar el código de nomenclatura correcto (CODES, tabla de prestaciones del seguro) para el tratamiento dental que el usuario describe. El usuario te dará: nombre del tratamiento realizado, descripción breve. Tú debes devolver: código correcto, nombre oficial del código, mutuas que lo aceptan, errores frecuentes en esa codificación, y un campo 'alerta' si el tratamiento puede necesitar autorización previa. Siempre indica si la información puede variar por convenio con la mutua específica. Responde en formato estructurado con secciones claramente delimitadas.",
  "temperature": 0.1,
  "model": "gpt-4o",
  "ejemplo_input": "Tratamiento: Extracción de tercer molar inferior con odontosección. Mutua: Adeslas.",
  "ejemplo_output": "CÓDIGO: 0801 | Exodoncia quirúrgica de tercer molar | Adeslas: cubierto con autorización previa | Error frecuente: confundir con 0802 (exodoncia simple) | ALERTA: requiere parte de autorización previo.",
  "problema_que_resuelve": "Sin esta skill, la recepcionista codifica mal y la mutua rechaza la factura, perdiendo 3.000€/trimestre en reclamaciones",
  "pitch_comercial": "Nunca más una factura rechazada por código incorrecto en la mutua.",
  "version": "1.0.0"
}}"""

    raw = None
    motor = None
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if anthropic_key:
        try:
            import anthropic as _anthropic
            client = _anthropic.Anthropic(api_key=anthropic_key)
            message = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            motor = "claude-sonnet-4-6"
        except Exception:
            pass

    if raw is None:
        from openai import OpenAI
        client_oai = OpenAI(api_key=openai_key)
        resp = client_oai.chat.completions.create(
            model="gpt-4o", max_tokens=1500,
            messages=[
                {"role": "system", "content": "Eres un arquitecto de microservicios de IA. Respondes SOLO con JSON válido."},
                {"role": "user", "content": prompt},
            ],
        )
        raw = resp.choices[0].message.content.strip()
        motor = "gpt-4o"

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("El motor IA no devolvió JSON válido")
    return json.loads(match.group()), motor


def _guardar_autogenerada(skill_def: dict) -> str:
    """Guarda la skill en skills/autogeneradas/<id>.json"""
    os.makedirs(AUTOGENERADAS_DIR, exist_ok=True)
    skill_id = skill_def.get("id", f"skill-{int(time.time())}")
    ruta = os.path.join(AUTOGENERADAS_DIR, f"{skill_id}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(skill_def, f, ensure_ascii=False, indent=2)
    return ruta


def _actualizar_json_principal(skill_def: dict):
    """Añade la skill al JSON principal de skills generadas."""
    skills = []
    if os.path.exists(GENERATED_JSON):
        with open(GENERATED_JSON, encoding="utf-8") as f:
            try:
                skills = json.load(f)
            except json.JSONDecodeError:
                skills = []

    existing_ids = {s.get("id") for s in skills}
    sid = skill_def.get("id", "")
    if sid in existing_ids:
        skill_def["id"] = f"{sid}-{int(time.time())}"

    skills.append(skill_def)
    with open(GENERATED_JSON, "w", encoding="utf-8") as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)


def _generar_archivo_python(skill_def: dict) -> str:
    """Genera el archivo Python de la skill lista para usar en el servidor."""
    skill_id = skill_def.get("id", "skill_nueva")
    class_name = "".join(w.capitalize() for w in skill_id.replace("-", "_").split("_"))
    py_content = f'''"""
Auto-generada por MetaSkills Factory — DESARROLLADOR Pipeline
Skill ID: {skill_id}
Generada: {datetime.now().strftime("%Y-%m-%d %H:%M")}
Motor: claude-sonnet-4-6
"""
from skills.base import BaseSkill


class {class_name}(BaseSkill):
    id = "{skill_id}"
    name = {json.dumps(skill_def.get("name", ""), ensure_ascii=False)}
    description = {json.dumps(skill_def.get("description", ""), ensure_ascii=False)}
    category = {json.dumps(skill_def.get("category", "clinica"), ensure_ascii=False)}
    sector = {json.dumps(skill_def.get("sector", "dental"), ensure_ascii=False)}
    price_eur = {skill_def.get("price_eur", 89)}
    price_setup_eur = {skill_def.get("price_setup_eur", 497)}
    version = "1.0.0"

    @property
    def system_prompt(self) -> str:
        return {json.dumps(skill_def.get("system_prompt", ""), ensure_ascii=False)}

    def to_dict(self):
        d = super().to_dict()
        d.update({{
            "sector": self.sector,
            "price_setup_eur": self.price_setup_eur,
            "pitch_comercial": {json.dumps(skill_def.get("pitch_comercial", ""), ensure_ascii=False)},
            "problema_que_resuelve": {json.dumps(skill_def.get("problema_que_resuelve", ""), ensure_ascii=False)},
        }})
        return d
'''
    ruta_py = os.path.join(AUTOGENERADAS_DIR, f"{skill_id}.py")
    with open(ruta_py, "w", encoding="utf-8") as f:
        f.write(py_content)
    return ruta_py


def desarrollar(resultado_vuelo: dict) -> dict:
    """
    Motor principal: fabrica la Meta-Skill y la persiste.
    """
    _banner()

    diagnostico = resultado_vuelo.get("diagnostico_entrada", {})
    componentes = resultado_vuelo.get("componentes", {})
    problema = diagnostico.get("problema", "")
    sector = diagnostico.get("sector", "dental")
    info_dx = diagnostico.get("diagnostico", {})
    nombre_propuesto = info_dx.get("nombre_skill_propuesto", "Skill Nueva")

    _log("INFO", f"Problema a resolver: {C['bold']}\"{nombre_propuesto}\"{C['reset']}")
    _log("INFO", f"Componentes recibidos del Hijo del Viento: {C['bold']}{len(componentes.get('skills_relacionadas', []))} referencias{C['reset']}")
    _log("BUILD", f"Directorio destino: {C['bold']}skills/autogeneradas/{C['reset']}")

    time.sleep(0.3)
    _log("AI", f"{C['magenta']}Invocando Claude claude-sonnet-4-6 — fabricando Meta-Skill...{C['reset']}")
    print(f"  {C['dim']}  ┌ motor    : claude-sonnet-4-6 (Anthropic){C['reset']}")
    print(f"  {C['dim']}  ├ temp     : 0.1 (alta precisión, baja creatividad){C['reset']}")
    print(f"  {C['dim']}  ├ max_tok  : 1500{C['reset']}")
    print(f"  {C['dim']}  └ contexto : catálogo dental completo + patrones extraídos{C['reset']}")

    t0 = time.time()
    skill_def, motor_usado = _generar_skill_con_ia(problema, sector, componentes)
    latencia = int((time.time() - t0) * 1000)

    _log("AI", f"Motor de fabricación: {C['bold']}{motor_usado}{C['reset']}")
    skill_def["fabricado_en"] = int(time.time())
    skill_def["fabricado_por"] = f"MetaSkills Pipeline v1 ({motor_usado}) — diagnosticador + hijo_del_viento + desarrollador"

    _log("AI", f"Skill generada por Claude en {C['bold']}{latencia}ms{C['reset']}")

    time.sleep(0.2)
    _log("WRITE", "Guardando skill en skills/autogeneradas/...")
    ruta_json = _guardar_autogenerada(skill_def)
    _log("SAVE", f"JSON creado: {C['bold']}{os.path.relpath(ruta_json, METASKILLS_DIR)}{C['reset']}")

    ruta_py = _generar_archivo_python(skill_def)
    _log("SAVE", f"Python creado: {C['bold']}{os.path.relpath(ruta_py, METASKILLS_DIR)}{C['reset']}")

    _log("WRITE", "Actualizando skills_generadas.json...")
    _actualizar_json_principal(skill_def)
    _log("OK", f"JSON principal actualizado — skill registrada como {C['bold']}{skill_def.get('id')}{C['reset']}")

    # Mostrar resultado final
    print(f"\n  {C['bold']}{C['green']}╔{'═'*60}╗{C['reset']}")
    print(f"  {C['bold']}{C['green']}║  META-SKILL FABRICADA EXITOSAMENTE{'─'*24}║{C['reset']}")
    print(f"  {C['bold']}{C['green']}╠{'═'*60}╣{C['reset']}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  ID            : {C['bold']}{skill_def.get('id', '—')}{C['reset']}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Nombre        : {C['bold']}{skill_def.get('name', '—')}{C['reset']}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Categoría     : {skill_def.get('category', '—')}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Precio        : {C['bold']}{skill_def.get('price_eur', '—')}€/mes{C['reset']}  |  Setup: {skill_def.get('price_setup_eur', '—')}€")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Latencia AI   : {C['bold']}{latencia}ms{C['reset']}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Archivos      : {os.path.basename(ruta_json)} + {os.path.basename(ruta_py)}")
    print(f"  {C['bold']}{C['green']}║{C['reset']}")

    desc = skill_def.get("description", "")
    if len(desc) > 56:
        desc = desc[:53] + "..."
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Descripción   : {C['dim']}{desc}{C['reset']}")

    pitch = skill_def.get("pitch_comercial", "")
    if len(pitch) > 56:
        pitch = pitch[:53] + "..."
    print(f"  {C['bold']}{C['green']}║{C['reset']}  Pitch         : {C['dim']}{pitch}{C['reset']}")

    print(f"  {C['bold']}{C['green']}╚{'═'*60}╝{C['reset']}\n")

    _log("OK", "Pipeline completado — skill lista para servir en /skills/{id}/run")

    return {
        "skill_def": skill_def,
        "ruta_json": ruta_json,
        "ruta_py": ruta_py,
        "latencia_ms": latencia,
    }


if __name__ == "__main__":
    print("Uso: ejecutar vía orquestador.py")
