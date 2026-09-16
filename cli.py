"""
Interfaz de Línea de Comandos (CLI) para Compresión de Imágenes por Lotes
"""

import argparse
import os
import sys
import time
from compressor import ImageBatchCompressor, CompressionConfig, find_images

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass



def format_bytes(size_bytes: int) -> str:
    """Convierte bytes a formato legible (KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def render_progress_bar(current: int, total: int, filename: str, bar_len: int = 30):
    """Muestra una barra de progreso limpia en consola."""
    fraction = current / max(total, 1)
    filled = int(round(fraction * bar_len))
    bar = "=" * filled + "-" * (bar_len - filled)
    percent = fraction * 100
    display_name = (filename[:22] + "..") if len(filename) > 24 else filename.ljust(24)
    sys.stdout.write(f"\r[{bar}] {percent:5.1f}% ({current}/{total}) | {display_name}")
    sys.stdout.flush()


def run_cli(args=None):
    parser = argparse.ArgumentParser(
        description="Compresor Inteligente de Lotes de Imágenes a archivo ZIP."
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        nargs="+",
        help="Ruta(s) de carpetas o imágenes individuales a comprimir."
    )
    parser.add_argument(
        "-o", "--output",
        default="imagenes_comprimidas.zip",
        help="Ruta del archivo ZIP de salida (por defecto: imagenes_comprimidas.zip)."
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["jpeg", "webp", "original"],
        default="jpeg",
        help="Modo de formato: 'jpeg' (recomendado para fotos/DSLR), 'webp' o 'original'."
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=88,
        help="Nivel de calidad (1-100). Por defecto: 88 (PSNR > 40 dB, nitidez fotográfica intacta)."
    )
    parser.add_argument(
        "-d", "--max-dimension",
        type=int,
        default=2560,
        help="Dimensión máxima en píxeles (ancho o alto). 2560 para 2.5K Quad HD, 0 para conservar 100%% original."
    )
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=min(os.cpu_count() or 4, 8),
        help="Número de hilos de trabajo paralelos (por defecto: 8)."
    )

    parsed_args = parser.parse_args(args)

    print("=" * 65)
    print("      COMPRESOR INTELIGENTE DE IMÁGENES POR LOTES A ZIP")
    print("=" * 65)

    # 1. Buscar imágenes
    print("[*] Buscando imágenes compatibles...")
    images = find_images(parsed_args.input)
    if not images:
        print("[!] No se encontraron imágenes válidas en las rutas indicadas.")
        sys.exit(1)

    print(f"[*] Se encontraron {len(images)} imágenes para procesar.")

    config = CompressionConfig(
        output_mode=parsed_args.mode,
        quality=parsed_args.quality,
        max_dimension=parsed_args.max_dimension if parsed_args.max_dimension > 0 else None,
        workers=parsed_args.threads
    )

    print(f"[*] Configuración: Modo={config.output_mode.upper()}, Calidad={config.quality}, "
          f"MaxDim={config.max_dimension or '100% Original'}px, Hilos={config.workers}")



    # Determinar carpeta base si la entrada es un directorio
    base_folder = None
    if len(parsed_args.input) == 1 and os.path.isdir(parsed_args.input[0]):
        base_folder = os.path.abspath(parsed_args.input[0])

    compressor = ImageBatchCompressor(config)

    def on_progress(current, total, filename, orig, comp):
        render_progress_bar(current, total, filename)

    print("[*] Iniciando compresión multihilo...")
    stats = compressor.compress_batch_to_zip(
        image_paths=images,
        output_zip_path=parsed_args.output,
        base_folder=base_folder,
        progress_callback=on_progress
    )

    sys.stdout.write("\n")
    print("=" * 65)
    print("                 RESUMEN DE COMPRESIÓN")
    print("=" * 65)
    print(f"  Total de imágenes procesadas : {stats.success_count}/{stats.total_files}")
    if stats.failed_count > 0:
        print(f"  Imágenes con error           : {stats.failed_count}")
    print(f"  Tamaño original total        : {format_bytes(stats.total_original_size)}")
    print(f"  Tamaño final comprimido      : {format_bytes(stats.total_compressed_size)}")
    print(f"  Espacio ahorrado             : {format_bytes(stats.saved_bytes)} ({stats.reduction_percentage}%)")
    print(f"  Tiempo transcurrido          : {stats.elapsed_time:.2f} segundos")
    print(f"  Velocidad promedio           : {stats.total_files / max(stats.elapsed_time, 0.001):.1f} img/seg")
    print(f"  Archivo ZIP guardado en      : {os.path.abspath(stats.zip_path)}")
    print("=" * 65)


if __name__ == "__main__":
    run_cli()
