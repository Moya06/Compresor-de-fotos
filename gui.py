"""
Interfaz Gráfica de Usuario (GUI) moderna con Tkinter para Compresión de Imágenes
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from compressor import ImageBatchCompressor, CompressionConfig, find_images


def format_bytes(size_bytes: int) -> str:
    """Convierte bytes a formato legible."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


class CompressorGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Compresor Inteligente de Imágenes por Lotes")
        self.geometry("760x650")
        self.minsize(680, 580)

        # Configurar colores y estilos
        self.configure(bg="#F4F6F9")
        self._setup_styles()

        self.selected_images = []
        self.base_folder = None
        self.compressor = None
        self.is_compressing = False
        self.generated_zip_path = None

        self._build_ui()

    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Configurar colores de estilo
        self.style.configure(".", font=("Segoe UI", 10), background="#F4F6F9")
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background="#F4F6F9", foreground="#1E293B")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 10), background="#F4F6F9", foreground="#64748B")
        
        self.style.configure("Card.TFrame", background="#FFFFFF", relief="solid", borderwidth=1)
        self.style.configure("CardInner.TFrame", background="#FFFFFF")
        self.style.configure("CardLabel.TLabel", background="#FFFFFF", font=("Segoe UI", 10, "bold"), foreground="#0F172A")
        self.style.configure("CardText.TLabel", background="#FFFFFF", font=("Segoe UI", 9), foreground="#334155")
        
        # Botones
        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background="#2563EB", foreground="#FFFFFF")
        self.style.map("Primary.TButton", background=[("active", "#1D4ED8"), ("disabled", "#94A3B8")])

        self.style.configure("Secondary.TButton", font=("Segoe UI", 9), background="#E2E8F0", foreground="#1E293B")
        self.style.map("Secondary.TButton", background=[("active", "#CBD5E1")])

        self.style.configure("Success.TButton", font=("Segoe UI", 10, "bold"), background="#059669", foreground="#FFFFFF")
        self.style.map("Success.TButton", background=[("active", "#047857")])

        # Progressbar
        self.style.configure("Horizontal.TProgressbar", troughcolor="#E2E8F0", background="#2563EB", bordercolor="#CBD5E1")

    def _build_ui(self):
        # Contenedor principal con scroll/padding
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Cabecera
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            header_frame,
            text="⚡ Compresor de Imágenes a ZIP",
            style="Header.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            header_frame,
            text="Reduce drásticamente el tamaño (hasta un 75%+) con calidad visual prácticamente imperceptible.",
            style="SubHeader.TLabel"
        ).pack(anchor="w", pady=(2, 0))

        # 2. Tarjeta: Selección de Archivos / Carpeta
        select_card = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
        select_card.pack(fill=tk.X, pady=6)

        ttk.Label(select_card, text="1. Entrada de imágenes", style="CardLabel.TLabel").pack(anchor="w")
        ttk.Label(
            select_card,
            text="Soporta lotes de 100-150+ fotos (PNG, JPG, WebP, BMP)",
            style="CardText.TLabel"
        ).pack(anchor="w", pady=(2, 10))

        btn_row = ttk.Frame(select_card, style="CardInner.TFrame")
        btn_row.pack(fill=tk.X)

        self.btn_select_folder = ttk.Button(
            btn_row,
            text="📁 Seleccionar Carpeta",
            style="Secondary.TButton",
            command=self._select_folder
        )
        self.btn_select_folder.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_select_files = ttk.Button(
            btn_row,
            text="🖼️ Seleccionar Archivos Múltiples",
            style="Secondary.TButton",
            command=self._select_files
        )
        self.btn_select_files.pack(side=tk.LEFT)

        self.lbl_selection_status = ttk.Label(
            select_card,
            text="Ninguna imagen seleccionada aún.",
            style="CardText.TLabel",
            foreground="#64748B"
        )
        self.lbl_selection_status.pack(anchor="w", pady=(10, 0))

        # 3. Tarjeta: Configuración de Compresión
        config_card = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
        config_card.pack(fill=tk.X, pady=6)

        ttk.Label(config_card, text="2. Opciones de Compresión Inteligente", style="CardLabel.TLabel").pack(anchor="w", pady=(0, 8))

        grid_frame = ttk.Frame(config_card, style="CardInner.TFrame")
        grid_frame.pack(fill=tk.X)

        # Modo de Formato
        ttk.Label(grid_frame, text="Formato de salida:", style="CardText.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        self.var_format = tk.StringVar(value="webp")
        
        fmt_frame = ttk.Frame(grid_frame, style="CardInner.TFrame")
        fmt_frame.grid(row=0, column=1, sticky="w", padx=10, pady=4)
        
        r1 = ttk.Radiobutton(
            fmt_frame,
            text="WebP Inteligente (Recomendado ~75% reducción)",
            variable=self.var_format,
            value="webp"
        )
        r1.pack(side=tk.LEFT, padx=(0, 10))
        r2 = ttk.Radiobutton(
            fmt_frame,
            text="Mantener Formato Original",
            variable=self.var_format,
            value="original"
        )
        r2.pack(side=tk.LEFT)

        # Calidad Visual
        ttk.Label(grid_frame, text="Nivel de calidad:", style="CardText.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        q_frame = ttk.Frame(grid_frame, style="CardInner.TFrame")
        q_frame.grid(row=1, column=1, sticky="w", padx=10, pady=4)

        self.var_quality = tk.IntVar(value=80)
        self.slider_quality = ttk.Scale(
            q_frame,
            from_=50,
            to=95,
            orient=tk.HORIZONTAL,
            variable=self.var_quality,
            command=self._on_quality_change,
            length=180
        )
        self.slider_quality.pack(side=tk.LEFT)

        self.lbl_quality_val = ttk.Label(
            q_frame,
            text="80 (Balance Óptimo)",
            style="CardText.TLabel",
            width=18
        )
        self.lbl_quality_val.pack(side=tk.LEFT, padx=10)

        # Resolución máxima
        ttk.Label(grid_frame, text="Dimensión máxima:", style="CardText.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        self.var_max_dim = tk.StringVar(value="2048 px")
        cb_dims = ttk.Combobox(
            grid_frame,
            textvariable=self.var_max_dim,
            values=["2560 px (Alta nitidez 2K+)", "2048 px (Recomendado)", "1920 px (Full HD)", "1280 px (Web ligera)", "Sin límite (Mantener píxeles)"],
            state="readonly",
            width=28
        )
        cb_dims.grid(row=2, column=1, sticky="w", padx=10, pady=4)

        # 4. Tarjeta: Archivo ZIP de Salida
        out_card = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
        out_card.pack(fill=tk.X, pady=6)

        ttk.Label(out_card, text="3. Archivo ZIP de Destino", style="CardLabel.TLabel").pack(anchor="w", pady=(0, 6))
        
        out_row = ttk.Frame(out_card, style="CardInner.TFrame")
        out_row.pack(fill=tk.X)

        default_zip = os.path.join(os.path.expanduser("~"), "Desktop", "imagenes_comprimidas.zip")
        if not os.path.exists(os.path.dirname(default_zip)):
            default_zip = os.path.abspath("imagenes_comprimidas.zip")

        self.var_output_zip = tk.StringVar(value=default_zip)
        self.entry_output_zip = ttk.Entry(out_row, textvariable=self.var_output_zip)
        self.entry_output_zip.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        btn_browse_zip = ttk.Button(
            out_row,
            text="Examinar...",
            style="Secondary.TButton",
            command=self._choose_output_zip
        )
        btn_browse_zip.pack(side=tk.RIGHT)

        # 5. Tarjeta: Progreso y Ejecución
        action_card = ttk.Frame(main_frame, style="Card.TFrame", padding=15)
        action_card.pack(fill=tk.BOTH, expand=True, pady=6)

        btn_action_row = ttk.Frame(action_card, style="CardInner.TFrame")
        btn_action_row.pack(fill=tk.X, pady=(0, 10))

        self.btn_start = ttk.Button(
            btn_action_row,
            text="🚀 Iniciar Compresión y Generar ZIP",
            style="Primary.TButton",
            command=self._start_compression
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 10), ipady=4)

        self.btn_open_folder = ttk.Button(
            btn_action_row,
            text="📂 Abrir Carpeta del ZIP",
            style="Secondary.TButton",
            command=self._open_output_folder,
            state="disabled"
        )
        self.btn_open_folder.pack(side=tk.LEFT, ipady=4)

        # Barra de progreso
        self.progress_bar = ttk.Progressbar(
            action_card,
            orient=tk.HORIZONTAL,
            mode="determinate",
            style="Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))

        # Indicador de estado y estadísticas
        self.lbl_progress_status = ttk.Label(
            action_card,
            text="Listo para comprimir.",
            style="CardText.TLabel",
            foreground="#475569"
        )
        self.lbl_progress_status.pack(anchor="w")

        self.lbl_stats = ttk.Label(
            action_card,
            text="",
            style="CardLabel.TLabel",
            foreground="#059669"
        )
        self.lbl_stats.pack(anchor="w", pady=(6, 0))

    def _on_quality_change(self, val):
        q = int(float(val))
        if q >= 88:
            desc = "Máxima Calidad"
        elif q >= 78:
            desc = "Balance Óptimo"
        else:
            desc = "Mayor Reducción"
        self.lbl_quality_val.config(text=f"{q} ({desc})")

    def _select_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar Carpeta con Imágenes")
        if folder:
            self.base_folder = os.path.abspath(folder)
            images = find_images([self.base_folder])
            self._update_selected_images(images, f"Carpeta: {os.path.basename(self.base_folder)}")

    def _select_files(self):
        filetypes = [
            ("Imágenes compatibles", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.tiff;*.tif"),
            ("Todos los archivos", "*.*")
        ]
        files = filedialog.askopenfilenames(title="Seleccionar Imágenes", filetypes=filetypes)
        if files:
            self.base_folder = None
            images = find_images(list(files))
            self._update_selected_images(images, f"{len(images)} archivos seleccionados")

    def _update_selected_images(self, images, source_desc):
        self.selected_images = images
        if not images:
            self.lbl_selection_status.config(
                text="⚠️ No se encontraron imágenes compatibles en la selección.",
                foreground="#DC2626"
            )
            return

        total_bytes = sum(os.path.getsize(p) for p in images if os.path.exists(p))
        self.lbl_selection_status.config(
            text=f"✓ {len(images)} imágenes listas ({format_bytes(total_bytes)}) | {source_desc}",
            foreground="#059669"
        )

    def _choose_output_zip(self):
        path = filedialog.asksaveasfilename(
            title="Guardar archivo ZIP comprimido",
            defaultextension=".zip",
            filetypes=[("Archivo ZIP", "*.zip")]
        )
        if path:
            self.var_output_zip.set(os.path.abspath(path))

    def _parse_max_dim(self) -> int:
        val = self.var_max_dim.get()
        if "2560" in val:
            return 2560
        elif "2048" in val:
            return 2048
        elif "1920" in val:
            return 1920
        elif "1280" in val:
            return 1280
        return 0

    def _start_compression(self):
        if self.is_compressing:
            return

        if not self.selected_images:
            messagebox.showwarning("Atención", "Por favor selecciona primero las imágenes o una carpeta.")
            return

        output_zip = self.var_output_zip.get().strip()
        if not output_zip:
            messagebox.showwarning("Atención", "Por favor especifica una ruta válida para el archivo ZIP.")
            return

        # Preparar configuración
        config = CompressionConfig(
            output_mode=self.var_format.get(),
            quality=int(self.var_quality.get()),
            max_dimension=self._parse_max_dim() or None,
            quantize_png=True if self.var_format.get() == "original" else False
        )

        self.compressor = ImageBatchCompressor(config)
        self.is_compressing = True
        self.btn_start.config(state="disabled")
        self.btn_open_folder.config(state="disabled")
        self.lbl_stats.config(text="")
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = len(self.selected_images)

        # Ejecutar compresión en un hilo separado para que la UI no se congele
        thread = threading.Thread(
            target=self._run_compression_thread,
            args=(self.selected_images, output_zip, self.base_folder),
            daemon=True
        )
        thread.start()

    def _run_compression_thread(self, images, output_zip, base_folder):
        def progress_callback(current, total, filename, orig_bytes, comp_bytes):
            self.after(0, self._update_progress, current, total, filename)

        try:
            stats = self.compressor.compress_batch_to_zip(
                image_paths=images,
                output_zip_path=output_zip,
                base_folder=base_folder,
                progress_callback=progress_callback
            )
            self.after(0, self._on_compression_complete, stats)
        except Exception as e:
            self.after(0, self._on_compression_error, str(e))

    def _update_progress(self, current, total, filename):
        self.progress_bar["value"] = current
        percent = (current / max(total, 1)) * 100
        short_name = (filename[:28] + "..") if len(filename) > 30 else filename
        self.lbl_progress_status.config(
            text=f"Procesando ({current}/{total} - {percent:.0f}%): {short_name}"
        )

    def _on_compression_complete(self, stats):
        self.is_compressing = False
        self.btn_start.config(state="normal")
        self.generated_zip_path = stats.zip_path
        self.btn_open_folder.config(state="normal")

        self.lbl_progress_status.config(
            text=f"✅ ¡Proceso completado en {stats.elapsed_time:.2f} segundos! ({stats.success_count} imágenes procesadas)"
        )

        orig_str = format_bytes(stats.total_original_size)
        comp_str = format_bytes(stats.total_compressed_size)
        saved_str = format_bytes(stats.saved_bytes)

        self.lbl_stats.config(
            text=f"🎉 Original: {orig_str}  ➔  Final: {comp_str}  |  Ahorro: {saved_str} (-{stats.reduction_percentage}%)"
        )

        messagebox.showinfo(
            "Compresión Finalizada",
            f"Se han comprimido {stats.success_count} imágenes exitosamente.\n\n"
            f"• Tamaño Original: {orig_str}\n"
            f"• Tamaño en ZIP: {comp_str}\n"
            f"• Reducción de espacio: {stats.reduction_percentage}%\n"
            f"• Tiempo: {stats.elapsed_time:.2f} s\n\n"
            f"Guardado en: {stats.zip_path}"
        )

    def _on_compression_error(self, err_msg):
        self.is_compressing = False
        self.btn_start.config(state="normal")
        self.lbl_progress_status.config(text=f"❌ Error durante el proceso: {err_msg}")
        messagebox.showerror("Error de Compresión", f"Ocurrió un error inesperado:\n{err_msg}")

    def _open_output_folder(self):
        if self.generated_zip_path and os.path.exists(self.generated_zip_path):
            folder = os.path.dirname(os.path.abspath(self.generated_zip_path))
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", os.path.abspath(self.generated_zip_path)])
            else:
                subprocess.Popen(["xdg-open", folder])


def run_gui():
    app = CompressorGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
