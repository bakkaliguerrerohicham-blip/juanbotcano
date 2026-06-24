"""
STRESS TEST — MetaSkills Pipeline Multi-Sector
Ejecuta 3 problemas inéditos de nichos distintos en bucle y genera
un informe de estabilidad para producción.

Problemas:
  1. Inmobiliaria — contratos bloqueados por firmas corruptas
  2. Taller mecánico — sincronización de stock de piezas antiguas
  3. Gestoría — errores en remesas AEAT
"""
import os
import sys
import json
import time
import traceback
from datetime import datetime

METASKILLS_DIR = os.path.join(os.path.dirname(__file__), "../../metaskills")
sys.path.insert(0, METASKILLS_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(METASKILLS_DIR, ".env"))

from diagnosticador import diagnosticar
from hijo_del_viento import volar
from desarrollador import desarrollar

GENERATED_JSON = os.path.join(METASKILLS_DIR, "skills/skills_generadas.json")
AUTOGENERADAS_DIR = os.path.join(METASKILLS_DIR, "skills/autogeneradas")

C = {
    "reset": "\033[0m", "bold": "\033[1m", "cyan": "\033[36m",
    "green": "\033[32m", "yellow": "\033[33m", "red": "\033[31m",
    "magenta": "\033[35m", "blue": "\033[34m", "dim": "\033[2m",
    "white": "\033[97m", "bg_green": "\033[42m", "bg_red": "\033[41m",
}

# ─── Casos de prueba ──────────────────────────────────────────────────────────

CASOS = [
    {
        "id": "CASO-01",
        "sector": "inmobiliaria",
        "titulo": "Contratos Bloqueados por Firmas Corruptas",
        "problema": (
            "Cuando enviamos contratos de compraventa al notario o al cliente para firma digital "
            "con herramientas como DocuSign o Signaturit, las firmas llegan corruptas o con "
            "metadatos inválidos y el contrato queda bloqueado en el sistema. Esto nos ha retrasado "
            "3 cierres este mes, con clientes desesperados y vendedores amenazando con romper el trato. "
            "Necesitamos un protocolo claro: qué verificar antes de enviar, cómo detectar una firma "
            "corrupta antes de que llegue al notario, y qué pasos ejecutar para desbloquear el contrato "
            "en menos de 2 horas sin perder la operación."
        ),
    },
    {
        "id": "CASO-02",
        "sector": "taller",
        "titulo": "Stock de Piezas Antiguas Desincronizado",
        "problema": (
            "Nuestro taller mecánico especializado en coches clásicos (pre-1990) tiene el inventario "
            "de piezas en una hoja Excel que nadie actualiza en tiempo real. Cuando el mecánico va a "
            "buscar una junta de culata para un BMW E30 o un carburador Weber para un Seat 127, "
            "el Excel dice que hay stock pero físicamente no está. O al revés: hay piezas que no "
            "aparecen en el sistema. Perdemos 4-5 horas semanales buscando piezas que no existen "
            "y decepcionando a clientes que vienen de lejos. Necesitamos algo que nos ayude a "
            "registrar entradas y salidas de piezas en tiempo real, identificar referencias de "
            "piezas antiguas por múltiples nomenclaturas (OEM, aftermarket, descriptivo) y alertar "
            "cuando el stock de una pieza crítica baje de mínimos."
        ),
    },
    {
        "id": "CASO-03",
        "sector": "gestoria",
        "titulo": "Errores en Remesas AEAT",
        "problema": (
            "Gestionamos las remesas bancarias para el pago de impuestos de 60 clientes autónomos "
            "y pymes. Cada trimestre enviamos al banco el fichero XML de la AEAT (SEPA) con los "
            "cargos automáticos. En los últimos 2 trimestres hemos tenido errores: IBANs mal "
            "formateados, conceptos que superan los 140 caracteres permitidos, fechas de valor "
            "incorrectas y algunos cargos duplicados por doble importación. El banco rechaza la "
            "remesa completa cuando hay un solo error, lo que significa que ningún cliente paga "
            "y todos entran en mora con Hacienda. Necesitamos validar el fichero XML antes de "
            "enviarlo al banco: detectar IBANs inválidos, conceptos largos, duplicados, fechas "
            "incorrectas y totales que no cuadran con el sumatorio de apuntes."
        ),
    },
]


# ─── Utilidades de stress test ────────────────────────────────────────────────

def _header_stress():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{C['bold']}{C['yellow']}{'█'*64}{C['reset']}")
    print(f"{C['bold']}{C['yellow']}  METASKILLS STRESS TEST — Multi-Sector Pipeline{C['reset']}")
    print(f"{C['bold']}{C['yellow']}  Impacto Digital  ·  {ts}{C['reset']}")
    print(f"{C['bold']}{C['yellow']}  3 casos · 3 sectores · verificación JSON completa{C['reset']}")
    print(f"{C['bold']}{C['yellow']}{'█'*64}{C['reset']}\n")


def _caso_header(caso: dict, idx: int, total: int):
    print(f"\n{C['bold']}{C['cyan']}{'═'*64}{C['reset']}")
    print(f"{C['bold']}{C['cyan']}  [{caso['id']}] CASO {idx}/{total} — {caso['titulo']}{C['reset']}")
    print(f"{C['bold']}{C['cyan']}  Sector: {caso['sector'].upper()}{C['reset']}")
    print(f"{C['bold']}{C['cyan']}{'═'*64}{C['reset']}")


def _verificar_json_integridad() -> dict:
    """Verifica que el JSON de skills generadas está bien formado y sin duplicados."""
    resultado = {
        "ok": False, "total": 0, "duplicados": [], "campos_faltantes": [],
        "ids_validos": 0, "error": None,
    }
    try:
        if not os.path.exists(GENERATED_JSON):
            resultado["error"] = "Archivo no existe"
            return resultado

        with open(GENERATED_JSON, encoding="utf-8") as f:
            skills = json.load(f)

        resultado["total"] = len(skills)
        CAMPOS_REQUERIDOS = ["id", "name", "description", "category", "sector",
                              "price_eur", "system_prompt", "fabricado_por"]

        ids_vistos = {}
        for i, s in enumerate(skills):
            sid = s.get("id", f"[sin-id-{i}]")
            if sid in ids_vistos:
                resultado["duplicados"].append(sid)
            else:
                ids_vistos[sid] = i

            faltantes = [c for c in CAMPOS_REQUERIDOS if not s.get(c)]
            if faltantes:
                resultado["campos_faltantes"].append({"id": sid, "faltantes": faltantes})
            else:
                resultado["ids_validos"] += 1

        resultado["ok"] = (
            len(resultado["duplicados"]) == 0 and
            len(resultado["campos_faltantes"]) == 0 and
            resultado["total"] > 0
        )

    except json.JSONDecodeError as e:
        resultado["error"] = f"JSON malformado: {e}"
    except Exception as e:
        resultado["error"] = str(e)

    return resultado


def _verificar_archivos_autogeneradas(skill_id: str) -> dict:
    """Verifica que los archivos .json y .py de la skill existen y son válidos."""
    json_path = os.path.join(AUTOGENERADAS_DIR, f"{skill_id}.json")
    py_path = os.path.join(AUTOGENERADAS_DIR, f"{skill_id}.py")

    checks = {
        "json_existe": os.path.exists(json_path),
        "py_existe": os.path.exists(py_path),
        "json_valido": False,
        "py_tiene_class": False,
        "py_tiene_prompt": False,
    }

    if checks["json_existe"]:
        try:
            with open(json_path, encoding="utf-8") as f:
                d = json.load(f)
            checks["json_valido"] = bool(d.get("id") and d.get("system_prompt"))
        except Exception:
            pass

    if checks["py_existe"]:
        with open(py_path, encoding="utf-8") as f:
            contenido = f.read()
        checks["py_tiene_class"] = "class " in contenido
        checks["py_tiene_prompt"] = "system_prompt" in contenido

    return checks


def _imprimir_checks(checks: dict, label: str):
    todos_ok = all(v for v in checks.values())
    estado = f"{C['green']}PASS{C['reset']}" if todos_ok else f"{C['red']}FAIL{C['reset']}"
    print(f"  {C['bold']}{label}{C['reset']} [{estado}]")
    for k, v in checks.items():
        icono = f"{C['green']}✓{C['reset']}" if v else f"{C['red']}✗{C['reset']}"
        print(f"    {icono} {k}")


def _informe_final(resultados: list[dict], t_total: float):
    """Genera el informe completo de estabilidad para producción."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n\n{C['bold']}{C['white']}{'═'*64}{C['reset']}")
    print(f"{C['bold']}{C['white']}  INFORME DE ESTABILIDAD — MetaSkills Pipeline v1{C['reset']}")
    print(f"{C['bold']}{C['white']}  Generado: {ts}{C['reset']}")
    print(f"{C['bold']}{C['white']}{'═'*64}{C['reset']}\n")

    # Resumen por caso
    total_ok = 0
    for r in resultados:
        caso = r["caso"]
        ok = r["exito"]
        icono = f"{C['green']}✓ PASS{C['reset']}" if ok else f"{C['red']}✗ FAIL{C['reset']}"
        motor = r.get("motor_fabricacion", "—")
        latencia = r.get("latencia_ms", 0)
        skill_id = r.get("skill_id", "—")

        print(f"  {C['bold']}[{caso['id']}]{C['reset']} {caso['titulo']}")
        print(f"    Estado         : {icono}")
        print(f"    Sector         : {caso['sector'].upper()}")
        print(f"    Skill generada : {C['bold']}{skill_id}{C['reset']}")
        print(f"    Motor IA       : {motor}")
        print(f"    Latencia AI    : {latencia}ms")

        if not ok:
            print(f"    Error          : {C['red']}{r.get('error', 'desconocido')}{C['reset']}")
        else:
            total_ok += 1

        # Checks de archivos
        checks = r.get("checks_archivos", {})
        if checks:
            arch_ok = all(checks.values())
            print(f"    Archivos       : {'✓ todos OK' if arch_ok else '✗ errores'}")

        print()

    # Verificación JSON global
    print(f"  {C['bold']}VERIFICACIÓN JSON GLOBAL{C['reset']}")
    json_check = _verificar_json_integridad()
    json_icono = f"{C['green']}✓ VÁLIDO{C['reset']}" if json_check["ok"] else f"{C['red']}✗ INVÁLIDO{C['reset']}"
    print(f"    Estado         : {json_icono}")
    print(f"    Total skills   : {json_check['total']}")
    print(f"    IDs válidos    : {json_check['ids_validos']}")
    print(f"    Duplicados     : {len(json_check['duplicados'])} {'(ninguno)' if not json_check['duplicados'] else json_check['duplicados']}")
    print(f"    Campos faltantes: {len(json_check['campos_faltantes'])} {'(ninguno)' if not json_check['campos_faltantes'] else ''}")
    if json_check.get("error"):
        print(f"    Error JSON     : {C['red']}{json_check['error']}{C['reset']}")

    # Métricas globales
    tasa = (total_ok / len(resultados)) * 100
    latencias = [r.get("latencia_ms", 0) for r in resultados if r.get("latencia_ms")]
    lat_media = int(sum(latencias) / len(latencias)) if latencias else 0
    lat_max = max(latencias) if latencias else 0

    print(f"\n  {C['bold']}MÉTRICAS DE RENDIMIENTO{C['reset']}")
    print(f"    Tasa de éxito  : {C['bold']}{tasa:.0f}%{C['reset']} ({total_ok}/{len(resultados)} casos)")
    print(f"    Tiempo total   : {C['bold']}{t_total:.1f}s{C['reset']}")
    print(f"    Latencia media AI : {lat_media}ms")
    print(f"    Latencia máx AI   : {lat_max}ms")

    # Veredicto de producción
    listo_prod = (tasa == 100 and json_check["ok"] and lat_max < 30000)
    print(f"\n  {C['bold']}VEREDICTO DE PRODUCCIÓN{C['reset']}")
    if listo_prod:
        print(f"  {C['bold']}{C['green']}{'█'*48}{C['reset']}")
        print(f"  {C['bold']}{C['green']}  ✓ PIPELINE LISTO PARA PRODUCCIÓN{C['reset']}")
        print(f"  {C['bold']}{C['green']}    Todos los casos OK · JSON íntegro · Latencias aceptables{C['reset']}")
        print(f"  {C['bold']}{C['green']}{'█'*48}{C['reset']}")
    else:
        issues = []
        if tasa < 100: issues.append(f"{100-tasa:.0f}% de casos fallaron")
        if not json_check["ok"]: issues.append("JSON con errores")
        if lat_max >= 30000: issues.append(f"Latencia máxima {lat_max}ms (límite: 30s)")
        print(f"  {C['bold']}{C['yellow']}{'█'*48}{C['reset']}")
        print(f"  {C['bold']}{C['yellow']}  ⚠  PIPELINE CON ADVERTENCIAS — REVISAR ANTES DE PRODUCCIÓN{C['reset']}")
        for issue in issues:
            print(f"  {C['bold']}{C['yellow']}    · {issue}{C['reset']}")
        print(f"  {C['bold']}{C['yellow']}{'█'*48}{C['reset']}")

    # Guardar informe en JSON
    informe_path = os.path.join(AUTOGENERADAS_DIR, "_stress_report.json")
    informe = {
        "timestamp": ts,
        "total_casos": len(resultados),
        "casos_ok": total_ok,
        "tasa_exito_pct": tasa,
        "tiempo_total_s": round(t_total, 2),
        "latencia_media_ms": lat_media,
        "latencia_max_ms": lat_max,
        "json_integridad": json_check,
        "listo_produccion": listo_prod,
        "casos": [
            {
                "id": r["caso"]["id"],
                "sector": r["caso"]["sector"],
                "skill_id": r.get("skill_id"),
                "exito": r["exito"],
                "latencia_ms": r.get("latencia_ms"),
                "motor": r.get("motor_fabricacion"),
                "error": r.get("error"),
            }
            for r in resultados
        ],
    }
    with open(informe_path, "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=2)

    print(f"\n  {C['dim']}Informe guardado en: skills/autogeneradas/_stress_report.json{C['reset']}")
    print(f"{C['bold']}{C['white']}{'═'*64}{C['reset']}\n")


# ─── Runner principal ─────────────────────────────────────────────────────────

def ejecutar_stress():
    _header_stress()
    resultados = []
    t_inicio_global = time.time()

    for idx, caso in enumerate(CASOS, 1):
        _caso_header(caso, idx, len(CASOS))
        resultado = {
            "caso": caso,
            "exito": False,
            "skill_id": None,
            "latencia_ms": None,
            "motor_fabricacion": None,
            "checks_archivos": {},
            "error": None,
        }

        try:
            # FASE 1: Diagnosticador
            print(f"\n  {C['bold']}{C['cyan']}▶ FASE 1 — DIAGNOSTICADOR{C['reset']}")
            dx = diagnosticar(caso["problema"], sector=caso["sector"])
            diagnostico_info = dx.get("diagnostico", {})
            es_nueva = diagnostico_info.get("es_skill_nueva", True)
            print(f"  {C['dim']}   → Veredicto: {'SKILL NUEVA' if es_nueva else 'SKILL EXISTENTE'} · "
                  f"Categoría: {diagnostico_info.get('categoria_sugerida', '—')} · "
                  f"Urgencia: {diagnostico_info.get('urgencia', '—')}{C['reset']}")

            # FASE 2: Hijo del Viento
            print(f"\n  {C['bold']}{C['magenta']}▶ FASE 2 — HIJO DEL VIENTO{C['reset']}")
            vuelo = volar(dx)
            comp = vuelo.get("componentes", {})
            print(f"  {C['dim']}   → Skills escrutadas: {comp.get('total_skills_sector', 0)} · "
                  f"Relacionadas: {len(comp.get('skills_relacionadas', []))} · "
                  f"Precio recom.: {comp.get('precio_recomendado', '—')}€/mes{C['reset']}")

            # FASE 3: Desarrollador
            print(f"\n  {C['bold']}{C['green']}▶ FASE 3 — DESARROLLADOR{C['reset']}")
            dev = desarrollar(vuelo)
            skill_def = dev.get("skill_def", {})
            skill_id = skill_def.get("id", "—")
            latencia = dev.get("latencia_ms", 0)
            motor = skill_def.get("fabricado_por", "—").split("(")[1].split(")")[0] if "(" in skill_def.get("fabricado_por", "") else "—"

            resultado["skill_id"] = skill_id
            resultado["latencia_ms"] = latencia
            resultado["motor_fabricacion"] = motor

            # Verificar archivos
            print(f"\n  {C['bold']}▶ VERIFICACIÓN DE ARTEFACTOS{C['reset']}")
            checks = _verificar_archivos_autogeneradas(skill_id)
            _imprimir_checks(checks, f"Skill '{skill_id}'")
            resultado["checks_archivos"] = checks

            # Verificar JSON después de este caso
            json_check = _verificar_json_integridad()
            json_icono = f"{C['green']}✓ OK{C['reset']}" if json_check["ok"] else f"{C['red']}✗ ERROR{C['reset']}"
            print(f"\n  {C['bold']}▶ JSON INTEGRIDAD POST-CASO{C['reset']}: {json_icono} "
                  f"({json_check['total']} skills, {len(json_check['duplicados'])} duplicados)")

            resultado["exito"] = (
                bool(skill_id) and
                all(checks.values()) and
                json_check["ok"]
            )

        except Exception as e:
            resultado["error"] = str(e)
            print(f"\n  {C['red']}✗ ERROR en {caso['id']}: {e}{C['reset']}")
            traceback.print_exc()

        resultados.append(resultado)

        if idx < len(CASOS):
            print(f"\n  {C['dim']}{'─'*62}{C['reset']}")
            print(f"  {C['dim']}Pausa 2s entre casos para respetar rate limits...{C['reset']}")
            time.sleep(2)

    t_total = time.time() - t_inicio_global
    _informe_final(resultados, t_total)


if __name__ == "__main__":
    ejecutar_stress()
