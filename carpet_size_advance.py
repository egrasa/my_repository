""" Interfaz gráfica para analizar el tamaño de subdirectorios """

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import concurrent.futures
from concurrent.futures import as_completed
import numpy as np
import matplotlib.pyplot as plt

# Event para permitir cancelar el cálculo en curso
stop_state = {'event': None}

def get_directory_size(path):
    """Calcula el tamaño total de un directorio (bytes).
    Evita symlinks y atrapa errores de acceso."""
    total_size = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_file(follow_symlinks=False):
                        total_size += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total_size += get_directory_size(entry.path)
                except (PermissionError, FileNotFoundError):
                    # ignorar entradas inaccesibles
                    continue
    except (PermissionError, FileNotFoundError):
        return 0
    return total_size

def bytes_to_readable(n):
    """Convierte bytes a unidad legible, devuelve (valor, unidad) y cadena formateada."""
    if n is None:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(n)
    idx = 0
    while size >= 1024 and idx < len(units)-1:
        size /= 1024.0
        idx += 1
    return f"{size:.2f} {units[idx]}"

def list_directories(path):
    """Devuelve (total_size_bytes, lista_subdirs) donde lista_subdirs contiene
    tuplas (ruta, bytes, GB, porcentaje)."""
    if not os.path.isdir(path):
        raise FileNotFoundError(f"No es un directorio válido: {path}")
    total_size = get_directory_size(path)
    directory_sizes = []
    try:
        for name in os.listdir(path):
            directory_path = os.path.join(path, name)
            if os.path.isdir(directory_path) and not os.path.islink(directory_path):
                size = get_directory_size(directory_path)
                size_gb = size / (1024 ** 3)
                percentage = (size / total_size * 100) if total_size > 0 else 0.0
                directory_sizes.append((directory_path, size, size_gb, percentage))
    except (PermissionError, FileNotFoundError, OSError):
        # protección adicional: solo capturar errores de acceso/sistema de archivos
        pass
    directory_sizes.sort(key=lambda x: x[1], reverse=True)
    return total_size, directory_sizes

# Helper: calcular tamaño con os.walk (más eficiente que llamadas recursivas repetidas)
def _walk_dir_size(path: str, stop_evt: threading.Event) -> tuple:
    total = 0
    num_files = 0
    try:
        for root_dir, _, files in os.walk(path, topdown=True, followlinks=False):
            if stop_evt.is_set():
                raise KeyboardInterrupt
            for f in files:
                try:
                    fp = os.path.join(root_dir, f)
                    # evitar seguir symlinks
                    if not os.path.islink(fp):
                        total += os.path.getsize(fp)
                        num_files += 1
                except (OSError, FileNotFoundError, PermissionError):
                    continue
    except KeyboardInterrupt:
        return 0, 0
    except (OSError, FileNotFoundError, PermissionError):
        return total, num_files
    return total, num_files


# --- Interfaz gráfica ---
def browse_and_compute():
    """Abre un diálogo para seleccionar una carpeta y calcular sus subdirectorios."""
    folder = filedialog.askdirectory()
    if not folder:
        return
    path_var.set(folder)
    # limpiar Treeview y mostrar estado inicial
    try:
        results_tree.delete(*results_tree.get_children())
    except (tk.TclError, RuntimeError):
        # El widget pudo haber sido destruido o no estar disponible; ignorar de forma segura
        pass
    results_info.config(text="Calculando tamaños...")
    compute_btn.config(state="disabled")
    cancel_btn.config(state="normal")
    # crear nuevo evento de cancelación para este trabajo
    stop_state['event'] = threading.Event()
    # lanzar hilo de cálculo
    thread = threading.Thread(target=compute_and_show,
                              args=(folder, stop_state['event']), daemon=True)
    thread.start()


# nuevo handler para cancelar
def cancel_compute():
    """Cancela el cálculo en curso."""
    if stop_state.get('event'):
        stop_state['event'].set()
        status_var.set("Cancelando...")
        cancel_btn.config(state="disabled")

def compute_and_show(folder, stop_evt: threading.Event):
    """Calcula y muestra los tamaños de los subdirectorios, actualizando la barra de progreso.
    stop_evt es un threading.Event que, si se setea, cancela el trabajo."""
    try:
        entries = [os.path.join(folder, name) for name in os.listdir(folder)
                   if os.path.isdir(os.path.join(folder, name)) and not
                   os.path.islink(os.path.join(folder, name))]
        total_dirs = len(entries)
        # decidir modo: indeterminado (marquee) para procesos rápidos,
        # determinista para procesos largos
        fast_threshold = 6
        use_indeterminate = total_dirs <= fast_threshold
        if use_indeterminate:
            # modo indeterminado: iniciar animación (marquee)
            root.after(0, lambda: progress_bar.configure(mode="indeterminate"))
            root.after(0, lambda: progress_bar.start(80))
            root.after(0, lambda: status_var.set("Calculando..."))
        else:
            root.after(0, lambda: progress_bar.configure(maximum=max(1, total_dirs),
                                                         value=0, mode="determinate"))

        # sumar ficheros en la raíz (no recursivo)
        root_files_size = 0
        try:
            with os.scandir(folder) as it:
                for e in it:
                    try:
                        if stop_evt.is_set():
                            raise KeyboardInterrupt
                        if e.is_file(follow_symlinks=False) and not e.is_symlink():
                            root_files_size += e.stat(follow_symlinks=False).st_size
                    except (PermissionError, FileNotFoundError):
                        continue
        except (PermissionError, FileNotFoundError):
            root_files_size = 0

        items_partial = []
        # calcular en paralelo por subdirectorio
        max_workers = min(8, (os.cpu_count() or 1))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as exc:
            future_to_path = {exc.submit(_walk_dir_size, p, stop_evt): p for p in entries}
            completed = 0
            for fut in as_completed(future_to_path):
                p = future_to_path[fut]
                if stop_evt.is_set():
                    break
                try:
                    size, num_files = fut.result()
                except KeyboardInterrupt:
                    size, num_files = 0, 0
                except concurrent.futures.CancelledError:
                    size, num_files = 0, 0
                except (OSError, FileNotFoundError, PermissionError, RuntimeError, ValueError):
                    size, num_files = 0, 0
                items_partial.append((p, size, num_files))
                completed += 1
                # actualizar progreso y estado (solo si usamos modo determinate)
                if not use_indeterminate:
                    root.after(0, lambda v=completed: progress_bar.configure(value=v))
                root.after(0, lambda i=completed, t=total_dirs,
                           path=p: status_var.set(f"Procesando {i}/{t}: {os.path.basename(path)}"))

        if stop_evt.is_set():
            root.after(0, lambda: status_var.set("Cancelado"))
            items = []
            total_bytes = 0
        else:
            total_bytes = root_files_size + sum(s for _, s, _ in items_partial)
            items = [(p, s, s / (1024 ** 3),
                      (s / total_bytes * 100 if total_bytes > 0 else 0.0), nf) for p,
                     s, nf in items_partial]

    except (FileNotFoundError, PermissionError, OSError, KeyboardInterrupt) as e:
        root.after(0, lambda: messagebox.showerror("Error",
                                                   f"No se pudo analizar la carpeta:\n{e}"))
        root.after(0, lambda: progress_bar.configure(value=0))
        root.after(0, lambda: status_var.set("Error"))
        items = []
        total_bytes = 0
    finally:
        # detener animación si se estaba usando modo indeterminado
        if use_indeterminate:
            root.after(0, progress_bar.stop)
            root.after(0, lambda: progress_bar.configure(mode="determinate", value=0))
        else:
            root.after(0, lambda: progress_bar.configure(value=0))
        root.after(0, lambda: compute_btn.config(state="normal"))
        root.after(0, lambda: cancel_btn.config(state="disabled"))
        root.after(0, lambda: status_var.set("Listo"))

    def show():
        # poblar Treeview en lugar de Text
        try:
            results_tree.delete(*results_tree.get_children())
        except (tk.TclError, RuntimeError):
            # El widget pudo haber sido destruido o no estar disponible; ignorar de forma segura
            pass

        if not items:
            results_info.config(text=f"Carpeta: {folder}\nNo hay subdirectorios"
                                " o el directorio está vacío.")
            # insertar fila vacía para indicar ausencia (size_bytes vacío)
            results_tree.insert('', 'end', values=("", "", "", "", "", ""))
        else:
            total_str = bytes_to_readable(total_bytes)
            results_info.config(text=f"Carpeta: {folder}    Tamaño total (usado): {total_str}")
            for path, size_bytes, size_gb, pct, num_files in items:
                readable = bytes_to_readable(size_bytes)
                # insertar size_bytes como primer valor (col oculta)
                # para permitir orden numérico preciso
                results_tree.insert('', 'end',
                                    values=(str(size_bytes), f"{size_gb:.2f}",
                                            readable, f"{pct:.2f}%", path, str(num_files)))

            # ordenar inicialmente por tamaño absoluto descendente
            sort_tree('size_bytes', True)

        # finalizar estado y resetear barra
        root.after(0, lambda: status_var.set("Listo"))
        root.after(0, lambda: progress_bar.configure(value=0))
        compute_btn.config(state="normal")

    root.after(0, show)

def generate_graph():
    """Genera una gráfica de barras con los tamaños de los subdirectorios.
    Si hay outliers, usa dos subplots con 'broken axis' donde el subplot superior
    está en escala logarítmica y es más grande; el inferior muestra valores
    truncados (min(valor, upper_bound)) para representar todos los datos."""
    items = results_tree.get_children()
    if not items:
        messagebox.showinfo("Gráfica", "No hay datos para graficar. Calcula primero.")
        return

    names = []
    sizes_gb = []
    for item in items:
        values = results_tree.item(item, 'values')
        if len(values) >= 5:
            size_gb = float(values[1]) if values[1] else 0.0
            path = values[4]
            name = os.path.basename(path) if path else "Desconocido"
            names.append(name)
            sizes_gb.append(size_gb)

    if not sizes_gb:
        messagebox.showinfo("Gráfica", "No hay tamaños válidos para graficar.")
        return

    # Ordenar por tamaño descendente para consistencia visual
    order = sorted(range(len(sizes_gb)), key=lambda i: sizes_gb[i], reverse=True)
    names = [names[i] for i in order]
    sizes_gb = [sizes_gb[i] for i in order]

    sizes_array = np.array(sizes_gb)
    q75 = np.percentile(sizes_array, 75)
    q25 = np.percentile(sizes_array, 25)
    iqr = q75 - q25
    upper_bound = q75 + 1.5 * iqr
    has_outliers = np.any(sizes_array > upper_bound)

    plt.rcParams.update({'figure.autolayout': True})
    if has_outliers and len(sizes_gb) > 3:
        # Broken axis: top en escala log (más grande), bottom muestra valores truncados
        max_val = float(np.max(sizes_array))
        # límites seguros para log (deben ser > 0)
        top_lower = max(upper_bound * 0.9, max_val * 0.001, 1e-6)
        top_upper = max(max_val * 1.15, upper_bound * 1.2, top_lower * 10)
        bottom_max = max(upper_bound * 1.05, top_lower * 0.5)

        # hacer subplot superior ligeramente más grande: height_ratios con top mayor
        _, (ax_top, ax_bottom) = plt.subplots(2, 1, sharex=True,
                                                gridspec_kw={'height_ratios': [3, 2]},
                                                figsize=(14, 8))

        x = np.arange(len(names))
        # bottom: todos los valores truncados al umbral (min(valor, upper_bound))
        bottom_vals = [min(v, upper_bound) for v in sizes_gb]
        # top: mostrar solo la porción completa para outliers (v > upper_bound)
        top_vals = [v if v > upper_bound else 0 for v in sizes_gb]

        # colores coherentes (outlier vs resto)
        colors = ['#ff7f0e' if v > upper_bound else '#1f77b4' for v in sizes_gb]

        # dibujar: primero bottom truncado, luego las barras completas de outliers en top
        ax_bottom.bar(x, bottom_vals, color=colors, edgecolor='k', zorder=2)
        # Para el top en log, solo dibujar barras para valores > upper_bound
        # Evitar dibujar barras con altura 0 en escala log; filtrar índices
        outlier_indices = [i for i, v in enumerate(top_vals) if v > 0]
        if outlier_indices:
            ax_top.bar([i for i in outlier_indices],
                       [top_vals[i] for i in outlier_indices],
                       color=[colors[i] for i in outlier_indices],
                       edgecolor='k', zorder=3)

        # Escala log en el subplot superior
        ax_top.set_yscale('log')

        # aplicar límites
        ax_top.set_ylim(top_lower, top_upper)
        ax_bottom.set_ylim(0, bottom_max)

        # Dibujar marcas diagonales que indican eje roto
        d = .015
        kwargs_top = dict(transform=ax_top.transAxes, color='k', clip_on=False)
        kwargs_bottom = dict(transform=ax_bottom.transAxes, color='k', clip_on=False)
        ax_top.plot((-d, +d), (-d, +d), **kwargs_top)
        ax_top.plot((1 - d, 1 + d), (-d, +d), **kwargs_top)
        ax_bottom.plot((-d, +d), (1 - d, 1 + d), **kwargs_bottom)
        ax_bottom.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs_bottom)

        # Anotar los N mayores reales en la parte superior para referencia
        top_n = min(8, len(names))
        idx_sorted = sorted(range(len(sizes_gb)), key=lambda i: sizes_gb[i], reverse=True)[:top_n]
        for idx in idx_sorted:
            val = sizes_gb[idx]
            if val > upper_bound:
                ax_top.annotate(f"{val:.2f} GB",
                                xy=(idx, val),
                                xytext=(0, 8), textcoords='offset points',
                                ha='center', va='bottom', fontsize=8, color='black')
            else:
                # anotar en bottom usando el valor truncado (opcional)
                ax_bottom.annotate(f"{val:.2f}",
                                   xy=(idx, bottom_vals[idx]),
                                   xytext=(0, 4), textcoords='offset points',
                                   ha='center', va='bottom', fontsize=7, color='black')

        ax_bottom.set_xlabel('Subdirectorios')
        ax_bottom.set_xticks(x)
        ax_bottom.set_xticklabels(names, rotation=45, ha='right', fontsize=9)
        ax_top.set_ylabel('Tamaño (GB) [log]')
        ax_bottom.set_ylabel('Tamaño (GB)')
        ax_top.set_title('Tamaños de Subdirectorios (eje superior en escala logarítmica)')
        ax_top.grid(axis='y', linestyle='--', alpha=0.4)
        ax_bottom.grid(axis='y', linestyle='--', alpha=0.4)

    else:
        # Sin outliers: gráfico sencillo
        plt.figure(figsize=(12, 6))
        x = range(len(names))
        plt.bar(x, sizes_gb, color='skyblue', edgecolor='k')
        plt.xticks(x, names, rotation=45, ha='right', fontsize=9)
        plt.ylabel('Tamaño (GB)')
        plt.title('Tamaños de Subdirectorios')
        plt.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.show()

# pie button moved down to the controls_frame area (created after controls_frame)
def generate_pie_chart():
    """Genera una gráfica de sectores circulares con los tamaños de los subdirectorios.
    Agrupa en 'Otros' los que ocupen <=1%."""
    items = results_tree.get_children()
    if not items:
        messagebox.showinfo("Gráfica Circular", "No hay datos para graficar. Calcula primero.")
        return

    names = []
    sizes_gb = []
    percentages = []
    for item in items:
        values = results_tree.item(item, 'values')
        if len(values) >= 5:
            size_gb = float(values[1]) if values[1] else 0.0
            pct = float(values[3].rstrip('%')) if values[3] else 0.0
            path = values[4]
            name = os.path.basename(path) if path else "Desconocido"
            names.append(name)
            sizes_gb.append(size_gb)
            percentages.append(pct)

    if not sizes_gb:
        messagebox.showinfo("Gráfica Circular", "No hay tamaños válidos para graficar.")
        return

    # Agrupar en 'Otros' los <=1%
    main_labels = []
    main_sizes = []
    other_size = 0
    for name, size, pct in zip(names, sizes_gb, percentages):
        if pct > 1:
            main_labels.append(name)
            main_sizes.append(size)
        else:
            other_size += size

    if other_size > 0:
        main_labels.append("Otros (<=1%)")
        main_sizes.append(other_size)

    plt.figure(figsize=(8, 8))
    plt.pie(main_sizes, labels=main_labels, autopct='%1.1f%%', startangle=140)
    plt.title('Distribución de Tamaños de Subdirectorios')
    plt.axis('equal')
    plt.show()

# creación de la ventana
root = tk.Tk()
root.title("Tamaños de subdirectorios")
root.geometry("860x760")

# color de fondo uniforme y paleta clara
UNIFORM_BG = "#f7fafc"    # fondo claro y neutro
ACCENT = "#5e677a"        # azul de acento para botones
UNIFORM_TEXT = "#27292E"
root.configure(bg=UNIFORM_BG)

# estilos globales y fuentes
DEFAULT_FONT = ("Segoe UI", 10)
MONO_FONT = ("Consolas", 10)
title_font = ("Segoe UI", 12, "bold")
style = ttk.Style(root)
try:
    style.theme_use("clam")
except tk.TclError:
    pass
style.configure("TFrame", background=UNIFORM_BG)
style.configure("Card.TFrame", background=UNIFORM_BG, relief="flat")
style.configure("TLabel", background=UNIFORM_BG, foreground=UNIFORM_TEXT, font=DEFAULT_FONT)
style.configure("Title.TLabel", background=UNIFORM_BG, foreground=UNIFORM_TEXT, font=title_font)
style.configure("TButton", padding=6, font=DEFAULT_FONT)
# estilo de botón acentuado (ajustado para ser más discreto y consistente)
style.configure("Accent.TButton",
                background="#e6eef6",     # tono suave, menos contraste
                foreground=UNIFORM_TEXT,
                font=DEFAULT_FONT,
                padding=(6,4),
                relief="flat",
                borderwidth=0)
style.map("Accent.TButton",
            background=[("active", "#d0dbea"), ("disabled", "#f1f5f9")],
            foreground=[("disabled", "#9aa4ad")])

# estilo para entradas (visible sobre el fondo uniforme)
style.configure("TEntry", fieldbackground="#ffffff", foreground=UNIFORM_TEXT)

# pequeña cabecera con icono
header = ttk.Frame(root, padding=(12,8), style="TFrame")
header.pack(fill="x")
ttk.Label(header, text="📊  Analizador de Tamaños", style="Title.TLabel").pack(side="left")

frame = ttk.Frame(root, padding=12, style="Card.TFrame")
frame.pack(fill="both", expand=True, padx=12, pady=(0,12))

top_frame = ttk.Frame(frame)
top_frame.pack(fill="x", pady=(6,8))

ttk.Label(top_frame, text="📁 Carpeta:").pack(side="left")
path_var = tk.StringVar()
# usar estilo de entrada configurado
path_entry = ttk.Entry(top_frame, textvariable=path_var, style="TEntry")
path_entry.pack(side="left", fill="x", expand=True, padx=(8,8))

# reorganizar botones: grupo a la derecha para un layout más limpio
controls_frame = ttk.Frame(top_frame)
controls_frame.pack(side="right", padx=(4,0))
# reorganizar botones: grupo a la derecha para un layout más limpio
controls_frame = ttk.Frame(top_frame)
controls_frame.pack(side="right", padx=(4,0))

# botón con estilo más discreto y texto corto
compute_btn = ttk.Button(controls_frame, text="Seleccionar...",
                         command=browse_and_compute, style="Accent.TButton")
compute_btn.pack(side="right", padx=(6,0))

# añadir botón para gráfica
graph_btn = ttk.Button(controls_frame, text="Gráfica",
                       command=generate_graph, style="Accent.TButton")
graph_btn.pack(side="right", padx=(6,0))

# botón para gráfica circular
# pasar la función directamente en lugar de envolverla en un lambda innecesario
pie_btn = ttk.Button(controls_frame, text="Circular",
                     command=generate_pie_chart, style="Accent.TButton")
pie_btn.pack(side="right", padx=(6,0))
# botón para cancelar (inicialmente deshabilitado)
cancel_btn = ttk.Button(controls_frame, text="Cancelar",
                        command=cancel_compute, state="disabled", style="Accent.TButton")
cancel_btn.pack(side="right", padx=2)

# Resultado en Treeview con scrollbar (reemplaza el Text)
results_frame = ttk.Frame(frame)
results_frame.pack(fill="both", expand=True, pady=(4,0))

# etiqueta resumen encima de la tabla
results_info = ttk.Label(results_frame, text="", style="TLabel")
results_info.pack(fill="x", padx=2, pady=(4,2))

# estado de ordenación: columna y sentido (reverse True = descendente)
sort_state = {'col': 'size_bytes', 'reverse': True}

# Treeview para mostrar resultados en columnas
# añadimos una columna oculta 'size_bytes' para ordenar numéricamente por bytes exactos
columns = ("size_bytes", "size_gb", "readable", "pct", "path", "files")
results_tree = ttk.Treeview(results_frame, columns=columns, show="headings",
                            selectmode="browse", height=20)

# encabezados (no mostramos encabezado para la columna oculta)
results_tree.heading("size_bytes", text="")  # columna oculta
results_tree.heading("size_gb", text="Size(GB)", command=lambda c="size_gb": on_heading_click(c))
results_tree.heading("readable", text="Size(*B)", command=lambda c="readable": on_heading_click(c))
results_tree.heading("pct", text="%", command=lambda c="pct": on_heading_click(c))
results_tree.heading("path", text="Path", command=lambda c="path": on_heading_click(c))
results_tree.heading("files", text="Files", command=lambda c="files": on_heading_click(c))

# columnas y anchuras (ocultamos size_bytes)
results_tree.column("size_bytes", width=0, stretch=False, anchor="e")  # oculta
results_tree.column("size_gb", width=100, anchor="e")
results_tree.column("readable", width=140, anchor="e")
results_tree.column("pct", width=80, anchor="e")
results_tree.column("path", width=400, anchor="w")
results_tree.column("files", width=80, anchor="e")
results_tree.pack(side="left", fill="both", expand=True)

scroll = ttk.Scrollbar(results_frame, orient="vertical", command=results_tree.yview)
scroll.pack(side="right", fill="y")
results_tree.configure(yscrollcommand=scroll.set)

# función para ordenar el Treeview por columna
def sort_tree(col: str, reverse: bool = False):
    """Ordena las filas del Treeview según la columna.
    Columna 'size_bytes', 'size_gb', 'pct' se tratan como numéricas."""
    # obtener pares (valor, item_id)
    items = [(results_tree.set(k, col), k) for k in results_tree.get_children('')]
    def parse_val(v):
        if v is None or v == "":
            return 0
        try:
            # valores numéricos almacenados como strings: intentar float
            return float(v)
        except (ValueError, TypeError):
            # solo capturar errores esperados al convertir a float
            return v.lower() if isinstance(v, str) else v
    try:
        items.sort(key=lambda t: parse_val(t[0]), reverse=reverse)
    except (TypeError, ValueError, AttributeError):
        # fallback lexicográfico si falla al comparar/convertir valores no numéricos
        items.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
    # reinsertar en nuevo orden
    for index, (_, k) in enumerate(items):
        results_tree.move(k, '', index)
    # actualizar estado
    sort_state['col'] = col
    sort_state['reverse'] = reverse

def on_heading_click(col: str):
    """Handler para clicks en encabezados: alterna asc/desc si se vuelve a pulsar."""
    if sort_state.get('col') == col:
        new_reverse = not sort_state.get('reverse', False)
    else:
        # por defecto ordenar ascendente al cambiar columna
        # (excepto size_bytes queremos descendente)
        new_reverse = False if col not in ('size_bytes', 'size_gb') else True
    sort_tree(col, new_reverse)

# pequeño pie con ayuda/estado + barra de progreso
footer = ttk.Frame(root, padding=(8,6), style="TFrame")
footer.pack(fill="x")
ttk.Label(footer, style="TLabel",
          text="Tip: selecciona una carpeta para ver subdirectorios"
          " ordenados por tamaño.").pack(side="left")
# etiqueta de estado (centro)
status_var = tk.StringVar(value="Listo")
status_label = ttk.Label(footer, textvariable=status_var, style="TLabel")
status_label.pack(side="left", padx=(16,8))
# barra de progreso en footer (inicialmente a 0)
progress_bar = ttk.Progressbar(footer, orient="horizontal", length=240, mode="determinate")
progress_bar.pack(side="right", padx=(8,8))

# iniciar loop
root.mainloop()
# iniciar loop
root.mainloop()
