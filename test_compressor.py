"""
Script de Prueba y Verificación del Compresor Inteligente
Genera un lote de prueba de imágenes realistas y mide rendimiento, reducción de tamaño e integridad del ZIP.
"""

import os
import shutil
import zipfile
import time
import sys
from PIL import Image, ImageDraw, ImageFilter
from compressor import ImageBatchCompressor, CompressionConfig, find_images

# Asegurar encoding compatible en consola Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass



def generate_sample_images(output_dir: str, count: int = 50):
    """Genera un lote de imágenes con patrones, degradados, fotos simuladas y canales alfa."""
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Generando {count} imágenes de prueba en '{output_dir}'...")

    for i in range(1, count + 1):
        # Variar dimensiones (algunas 4K simuladas, otras 1080p, otras estándar)
        if i % 3 == 0:
            w, h = 2560, 1440
        elif i % 5 == 0:
            w, h = 3840, 2160  # 4K
        else:
            w, h = 1920, 1080

        # Crear imagen base
        img = Image.new("RGB", (w, h), color=(
            (i * 37) % 256,
            (i * 67) % 256,
            (i * 101) % 256
        ))
        draw = ImageDraw.Draw(img)

        # Dibujar degradados y formas complejas
        for step in range(0, w, 40):
            color = ((step + i * 15) % 256, (step * 2 + i * 5) % 256, (step * 3) % 256)
            draw.rectangle([step, 0, step + 40, h], fill=color)

        for circle in range(10):
            cx = (circle * 200 + i * 50) % w
            cy = (circle * 150 + i * 70) % h
            r = (circle * 30 + 40)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=((i * 45) % 256, 200, 150))

        # Añadir algo de desenfoque y textura
        img = img.filter(ImageFilter.SMOOTH_MORE)

        # Alternar entre formatos: PNG, JPG, WebP
        if i % 3 == 1:
            # PNG con transparencia
            rgba = img.convert("RGBA")
            # Añadir canal alfa variable
            alpha_data = []
            for y in range(h):
                for x in range(w):
                    alpha_data.append(int(255 * (x / w)))
            alpha_img = Image.new("L", (w, h))
            alpha_img.putdata(alpha_data)
            rgba.putalpha(alpha_img)
            rgba.save(os.path.join(output_dir, f"sample_{i:03d}.png"))
        elif i % 3 == 2:
            # JPG de alta resolución sin comprimir
            img.save(os.path.join(output_dir, f"sample_{i:03d}.jpg"), quality=95)
        else:
            # WebP
            img.save(os.path.join(output_dir, f"sample_{i:03d}.webp"), quality=90)

    total_size = sum(os.path.getsize(os.path.join(output_dir, f)) for f in os.listdir(output_dir))
    print(f"[OK] {count} imagenes generadas. Tamano total original: {total_size / (1024 * 1024):.2f} MB")
    return total_size


def verify_zip_archive(zip_path: str, expected_count: int) -> bool:
    """Verifica que el archivo ZIP no esté corrupto y que todas las imágenes puedan ser leídas por PIL."""
    print(f"[*] Verificando integridad del ZIP '{zip_path}'...")
    if not os.path.exists(zip_path):
        print(f"[FAIL] El archivo ZIP no existe.")
        return False

    with zipfile.ZipFile(zip_path, 'r') as z:
        namelist = z.namelist()
        if len(namelist) != expected_count:
            print(f"[FAIL] Se esperaban {expected_count} imagenes en el ZIP, pero hay {len(namelist)}")
            return False

        for name in namelist:
            with z.open(name) as img_file:
                try:
                    with Image.open(img_file) as test_img:
                        test_img.verify()
                except Exception as e:
                    print(f"[FAIL] Error al validar imagen {name} dentro del ZIP: {e}")
                    return False

    print(f"[OK] Todas las {expected_count} imagenes en el ZIP son validas y legibles sin corrupcion.")
    return True



def run_tests():
    test_dir = os.path.abspath("test_samples")
    output_zip = os.path.abspath("test_output.zip")

    try:
        # Limpiar pruebas anteriores
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        if os.path.exists(output_zip):
            os.remove(output_zip)

        # Generar 60 imágenes
        image_count = 60
        orig_size = generate_sample_images(test_dir, count=image_count)

        # Configuración de compresión óptima
        config = CompressionConfig(
            output_mode="webp",
            quality=80,
            max_dimension=2048,
            workers=4
        )

        compressor = ImageBatchCompressor(config)
        images = find_images([test_dir])

        print(f"[*] Iniciando prueba de compresión...")
        start_t = time.time()
        stats = compressor.compress_batch_to_zip(
            image_paths=images,
            output_zip_path=output_zip,
            base_folder=test_dir
        )
        elapsed = time.time() - start_t

        zip_size = os.path.getsize(output_zip)
        reduction = ((orig_size - zip_size) / orig_size) * 100

        print("\n" + "=" * 50)
        print("          RESULTADOS DE LA PRUEBA")
        print("=" * 50)
        print(f"Imágenes procesadas   : {stats.success_count}/{image_count}")
        print(f"Tamaño original       : {orig_size / (1024 * 1024):.2f} MB")
        print(f"Tamaño final en ZIP   : {zip_size / (1024 * 1024):.2f} MB")
        print(f"Reducción obtenida    : {reduction:.2f}% (Objetivo: ~75%)")
        print(f"Tiempo total          : {elapsed:.2f} s ({image_count / elapsed:.1f} img/s)")
        print("=" * 50)

        # Verificar integridad
        valid = verify_zip_archive(output_zip, image_count)
        if valid and reduction >= 65.0:
            print("\n[EXITO] TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        else:
            print("\n[AVISO] Alguna prueba no cumplio los criterios esperados.")


    finally:
        # Limpieza de archivos de prueba
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        if os.path.exists(output_zip):
            os.remove(output_zip)


if __name__ == "__main__":
    run_tests()
