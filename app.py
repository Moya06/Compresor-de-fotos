"""
Punto de Entrada Principal para la Aplicación de Compresión de Imágenes
Lanza la interfaz gráfica (GUI), consola (CLI), o sirve como entrada web para Vercel.
"""

import sys
from web_app import app  # Exporta la instancia de Flask para Vercel


def main():
    # Si se pasa --web o -w, lanzar servidor web en localhost
    if len(sys.argv) == 2 and sys.argv[1] in ("--web", "-w"):
        from web_app import run_server
        run_server()
    # Si se pasa --gui o no se pasan argumentos, lanzar la GUI
    elif len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ("--gui", "-g")):
        try:
            from gui import run_gui
            run_gui()
        except Exception:
            from web_app import run_server
            run_server()
    else:
        from cli import run_cli
        run_cli()


if __name__ == "__main__":
    main()
