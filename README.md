# ⚡ Compresor Inteligente de Imágenes por Lotes a ZIP

Aplicación de alto rendimiento para procesar y comprimir lotes de 100 a 150+ imágenes (PNG, JPG, WebP, BMP), reduciendo el tamaño total aproximadamente un **75% a 85%** (ej. de 40 MB a ~8-10 MB) preservando una calidad visual prácticamente imperceptible al ojo humano.

---

## 🚀 Características Principales

- **Compresión Inteligente y Adaptativa**:
  - **Modo WebP Inteligente (Recomendado)**: Convierte imágenes a WebP con calidad optimizada (80-82) y compresión método 6. Soporta canales alfa / transparencia nativamente y supera el 75% de ahorro.
  - **Modo Formato Original**: Optimiza JPG con codificación progresiva y tablas Huffman, y optimiza PNG/WebP conservando sus extensiones originales.
  - **Downscaling con Filtro Lanczos**: Permite limitar resoluciones excesivas (ej. fotos de smartphone de 4000x3000 a 2048px o Full HD) para ahorrar decenas de megabytes sin perder nitidez en pantallas.
  - **Corrección de Orientación EXIF**: Rota automáticamente fotos tomadas con teléfonos móviles para evitar imágenes volteadas.
- **Empaquetado Directo a ZIP**:
  - Genera un archivo `.zip` final con compresión deflate que contiene todas las imágenes listas para compartir o almacenar.
- **Procesamiento Multihilo de Alta Velocidad**:
  - Utiliza `ThreadPoolExecutor` distribuyendo el trabajo en todos los núcleos de la CPU. Puede procesar 150 imágenes en pocos segundos.
- **Modo Dual**:
  - **Interfaz Gráfica Moderna (GUI)** con Tkinter nativo (sin dependencias pesadas).
  - **Línea de Comandos (CLI)** con barra de progreso y estadísticas detalladas.
  - **Acceso Directo con Doble Clic** en Windows mediante `run_app.bat`.

---

## 📦 Instalación

### Requisitos Previos
- Python 3.8 o superior instalado en el sistema.

### Pasos de Instalación
1. Abre una terminal en esta carpeta:
   ```bash
   cd c:\Users\XPC\Desktop\compress
   ```
2. Instala la única dependencia requerida (`Pillow`):
   ```bash
   pip install -r requirements.txt
   ```

---

## 🖥️ Uso de la Aplicación

### Opción 1: Lanzador con Doble Clic (Recomendado en Windows)
Simplemente haz doble clic sobre el archivo **`run_app.bat`**. Si falta alguna dependencia, la instalará automáticamente y abrirá la interfaz gráfica.

---

### Opción 2: Interfaz Gráfica (GUI)
Ejecuta:
```bash
python app.py
```
o
```bash
python gui.py
```

**Flujo en la GUI:**
1. Haz clic en **"Seleccionar Carpeta"** o **"Seleccionar Archivos Múltiples"**.
2. Selecciona el modo:
   - **WebP Inteligente** (recomendado para obtener ~75% de reducción).
   - **Mantener Formato Original** (si requieres conservar extensiones .jpg/.png).
3. Ajusta el nivel de calidad (80 es el valor óptimo recomendado).
4. Selecciona la dimensión máxima (por defecto 2048px).
5. Elige la ruta del archivo `.zip` destino.
6. Presiona **"🚀 Iniciar Compresión y Generar ZIP"**.
7. Al finalizar, verás las estadísticas de ahorro y podrás pulsar **"📂 Abrir Carpeta del ZIP"**.

---

### Opción 3: Línea de Comandos (CLI)
Ideal para scripts, servidores o automatizaciones:

```bash
# Compresión básica de una carpeta completa a un ZIP:
python app.py -i "C:\Ruta\A\MisFotos" -o "resultado.zip"

# Especificar modo WebP con calidad 80 y límite de 2048px:
python app.py -i "C:\Ruta\A\MisFotos" -o "fotos_optimizadas.zip" -m webp -q 80 -d 2048

# Conservar formato original:
python app.py -i "C:\Ruta\A\MisFotos" -o "fotos_originales.zip" -m original -q 80

# Ver todas las opciones disponibles:
python app.py --help
```

#### Parámetros del CLI:
| Parámetro | Descripción | Por Defecto |
|---|---|---|
| `-i`, `--input` | Ruta(s) de carpetas o imágenes individuales | *(Requerido)* |
| `-o`, `--output` | Nombre o ruta del archivo ZIP generado | `imagenes_comprimidas.zip` |
| `-m`, `--mode` | Modo: `webp` (recomendado) o `original` | `webp` |
| `-q`, `--quality` | Calidad de 1 a 100 | `80` |
| `-d`, `--max-dimension` | Límite máximo en px (0 = sin límite) | `2048` |
| `-t`, `--threads` | Hilos concurrentes de la CPU | `Núcleos CPU` |
| `--quantize-png` | Cuantizar PNG a 256 colores en modo original | `False` |

---

## 🧪 Pruebas Automatizadas

Se incluye una suite de pruebas para generar lotes sintéticos de prueba y verificar el ratio de reducción y la integridad del ZIP:

```bash
python test_compressor.py
```
El script generará un lote de prueba de 60 imágenes en alta resolución, las comprimirá en memoria, verificará que el ratio de compresión supere el objetivo del 75% y validará que cada imagen dentro del ZIP esté libre de corrupción.
