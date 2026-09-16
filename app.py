"""
Punto de Entrada Principal para la Aplicación de Compresión de Imágenes
Lanza la interfaz gráfica (GUI) si se ejecuta directamente, o la interfaz de consola (CLI) si se pasan argumentos.
"""

import sys


def main():
    # Si se pasa --web o -w, lanzar servidor web en localhost
    if len(sys.argv) == 2 and sys.argv[1] in ("--web", "-w"):
        from web_app import start_server
        start_server()
    # Si se pasa --gui o no se pasan argumentos (o solo el nombre del script), lanzar la GUI
    elif len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ("--gui", "-g")):
        from gui import run_gui
        run_gui()
    else:
        from cli import run_cli
        run_cli()



if __name__ == "__main__":
    main()
