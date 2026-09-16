import io
import os
import sys
import zipfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Tuple, Callable, Optional
from PIL import Image, ImageOps

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}

@dataclass
class CompressionStats:
    total_files: int = 0
    success_count: int = 0
    failed_count: int = 0
    total_original_size: int = 0
    total_compressed_size: int = 0
    saved_bytes: int = 0
    reduction_percentage: float = 0.0
    elapsed_time: float = 0.0
    zip_path: str = ""
    target_mb_per_image: float = 10.0
    calibration_time: float = 0.0
    resolution_used: str = ""


def find_images(input_paths: List[str]) -> List[str]:
    found = []
    seen = set()
    for path in input_paths:
        path = os.path.abspath(path)
        if not os.path.exists(path): continue
        if os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in SUPPORTED_EXTENSIONS and path not in seen:
                seen.add(path)
                found.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in sorted(files):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        fp = os.path.abspath(os.path.join(root, f))
                        if fp not in seen:
                            seen.add(fp)
                            found.append(fp)
    return found


def _compress_one(
    image_path: str,
    target_bytes: int,
    base_folder: Optional[str]
) -> Tuple[bool, str, bytes, int, int, str, int]:
    """Comprime UNA foto priorizando el 100% de resolucion y bajando solo la calidad."""
    orig_size = 0
    try:
        orig_size = os.path.getsize(image_path)
        with Image.open(image_path) as img:
            try: img = ImageOps.exif_transpose(img)
            except: pass
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            w, h = img.size
            best_data = None
            best_q = None

            # Prioridad 1: Mantener resolucion al 100%, sin limite de max_dimension
            # Probamos en memoria (tarda ~200ms por intento, super rapido)
            # Usamos subsampling=0 (4:4:4) para preservar cada pixel de color si el target es generoso
            qualities = [98, 95, 92, 90, 88, 85, 80, 75, 70, 60]
            
            for q in qualities:
                buf = io.BytesIO()
                img.save(buf, 'JPEG', quality=q, optimize=True, subsampling=0 if q >= 90 else 1)
                data = buf.getvalue()
                if len(data) <= target_bytes:
                    best_data = data
                    best_q = q
                    break
            
            # Si piden un tamaño ridiculamente pequeño (ej 1MB para una foto de 24MP)
            # Y q=60 no fue suficiente, entonces SI bajamos la resolucion gradualmente
            if best_data is None:
                scales = [0.75, 0.5, 0.25]
                for scale in scales:
                    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
                    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
                    for q in [80, 70, 60]:
                        buf = io.BytesIO()
                        resized.save(buf, 'JPEG', quality=q, optimize=True)
                        data = buf.getvalue()
                        if len(data) <= target_bytes:
                            best_data = data
                            best_q = q
                            break
                    if best_data: break
            
            # Fallback final extremo
            if best_data is None:
                buf = io.BytesIO()
                resized = img.resize((w//4, h//4), Image.Resampling.LANCZOS)
                resized.save(buf, 'JPEG', quality=50, optimize=True)
                best_data = buf.getvalue()
                best_q = 50

        # Nombre en el ZIP
        orig_filename = os.path.basename(image_path)
        name_no_ext = os.path.splitext(orig_filename)[0]
        prefix = ""
        if base_folder and image_path.startswith(base_folder):
            rel = os.path.relpath(os.path.dirname(image_path), base_folder)
            prefix = "" if rel == '.' else rel.replace('\\', '/') + "/"
        zip_name = f"{prefix}{name_no_ext}.jpg"

        return True, zip_name, best_data, orig_size, len(best_data), "", best_q

    except Exception as e:
        return False, os.path.basename(image_path), b"", orig_size, 0, str(e), 0


class SmartCompressor:
    """Compresor adaptativo por imagen a maxima resolucion."""
    def __init__(self, target_mb_per_image: float = 10.0, workers: int = 8):
        self.target_mb_per_image = target_mb_per_image
        self.workers = workers
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def compress_to_zip(
        self, image_paths: List[str], output_zip: str, 
        base_folder: Optional[str] = None, progress_cb: Optional[Callable] = None
    ) -> CompressionStats:
        self._cancelled = False
        t_start = time.time()
        total = len(image_paths)
        target_bytes = int(self.target_mb_per_image * 1024 * 1024)

        stats = CompressionStats(total_files=total, zip_path=output_zip, target_mb_per_image=self.target_mb_per_image)
        if total == 0: return stats

        os.makedirs(os.path.dirname(os.path.abspath(output_zip)), exist_ok=True)

        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_STORED) as zf:
            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                futures = {pool.submit(_compress_one, p, target_bytes, base_folder): p for p in image_paths}
                done = 0
                qs_used = set()
                
                for future in as_completed(futures):
                    if self._cancelled: break
                    ok, name, data, orig_sz, comp_sz, err, q_used = future.result()
                    done += 1
                    stats.total_original_size += orig_sz
                    
                    if ok:
                        zf.writestr(name, data)
                        stats.total_compressed_size += comp_sz
                        stats.success_count += 1
                        if q_used: qs_used.add(q_used)
                    else:
                        stats.failed_count += 1
                        
                    if progress_cb:
                        progress_cb(done, total, os.path.basename(name), orig_sz, comp_sz)

        stats.elapsed_time = time.time() - t_start
        stats.saved_bytes = max(0, stats.total_original_size - stats.total_compressed_size)
        if stats.total_original_size > 0:
            stats.reduction_percentage = round((stats.saved_bytes / stats.total_original_size) * 100, 2)
            
        min_q = min(qs_used) if qs_used else 0
        max_q = max(qs_used) if qs_used else 0
        stats.resolution_used = f"100% Original (Calidad {min_q}-{max_q})"
        return stats
