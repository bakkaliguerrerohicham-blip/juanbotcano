"""
ENTRADA — Punto de acceso único al pipeline MetaSkills
El usuario describe su problema. El sistema hace el resto.
Uso: python3 entrada.py
  o: python3 entrada.py "mi problema en texto libre"
"""
import os
import sys

METASKILLS_DIR = os.path.join(os.path.dirname(__file__), "../../metaskills")
sys.path.insert(0, METASKILLS_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(METASKILLS_DIR, ".env"))

from hijo_del_viento import procesar

C = {
    "reset": "\033[0m", "bold": "\033[1m", "cyan": "\033[36m",
    "magenta": "\033[35m", "dim": "\033[2m", "yellow": "\033[33m",
}


def _pantalla_bienvenida():
    print(f"""
{C['bold']}{C['magenta']}  ╔══════════════════════════════════════════════════════════════╗
  ║   🌬  MetaSkills — Impacto Digital                          ║
  ║   Describe tu problema. El sistema decide el resto.          ║
  ╚══════════════════════════════════════════════════════════════╝{C['reset']}

  {C['dim']}Puedo generar:
    · Meta-Skills (microservicios de IA listos para vender)
    · Protocolos paso a paso
    · Guiones de llamada o WhatsApp
    · Checklists de validación
    · Informes ejecutivos
    · Plantillas de documentos

  No necesitas especificar nada más. Solo cuéntame el problema.{C['reset']}
""")


def main():
    if len(sys.argv) > 1:
        texto = " ".join(sys.argv[1:]).strip()
        if not texto:
            print("  Sin texto, sin solución.")
            sys.exit(1)
        procesar(texto)
        return

    _pantalla_bienvenida()

    while True:
        try:
            print(f"  {C['bold']}{C['cyan']}¿Cuál es tu problema?{C['reset']}")
            print(f"  {C['dim']}(escribe 'salir' para terminar){C['reset']}\n")
            texto = input("  > ").strip()

            if not texto:
                continue
            if texto.lower() in ("salir", "exit", "quit", "q"):
                print(f"\n  {C['dim']}Hasta pronto.{C['reset']}\n")
                break

            procesar(texto)

            print(f"\n  {C['dim']}{'─'*62}{C['reset']}")
            print(f"  {C['yellow']}¿Hay otro problema que resolver? (Enter para continuar, 'salir' para terminar){C['reset']}\n")

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {C['dim']}Sesión terminada.{C['reset']}\n")
            break


if __name__ == "__main__":
    main()
