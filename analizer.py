""" Analizador de vídeos contenidos en una carpeta """

import errno
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import time
import os
import csv
import shutil
import threading
import json
from datetime import datetime
#from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, CancelledError
import numpy as np
import matplotlib.pyplot as plt
from moviepy import VideoFileClip

# --- Colores estilo oscuro ---
COLOR_BG = "#23272a"
COLOR_FRAME = "#2c2f33"
COLOR_LABEL = "#4A970A"
COLOR_TEXT = "#f3bc09"
COLOR_ENTRY = "#23272a"
COLOR_BUTTON = "#36393f"
COLOR_BUTTON_TEXT = "#e0e0e0"
COLOR_BUTTON_STOP = "#f04747"
COLOR_PROGRESS = "#7289da"
COLOR_TAB_DISABLED = "#7a848d"
COLOR_BUTTON_HIGHLIGHT = "#ff8c00"

lista_de_errores = list()  # Para almacenar errores únicos

def mostrar_grafico_visual(resultados, carpeta):
    """Muestra una gráfica de barras: eje X=nombre archivo, 
    eje Y=relación peso/duración, etiqueta=tiempo y línea 80MB/min.
    El video más largo en rojo, el más corto en verde."""
    lista_de_errores.append(carpeta)
    if not resultados:
        messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
        return
    nombres = [nombre for nombre, _, _ in resultados]
    duraciones = [dur for _, dur, _ in resultados]
    relaciones = [(peso / dur) if dur > 0 else 0 for _, dur, peso in resultados]

    # Identificar índices del video más largo y más corto
    idx_max = duraciones.index(max(duraciones))
    idx_min = duraciones.index(min(duraciones))

    # Colores: por defecto azul, el más largo rojo, el más corto verde
    colores = ["#7289da"] * len(nombres)
    colores[idx_max] = "red"
    colores[idx_min] = "green"

    plt.style.use('grayscale')
    _, ax = plt.subplots(figsize=(max(12, len(nombres) * 0.5), 6))
    bars = ax.bar(nombres, relaciones, color=colores, edgecolor='k', alpha=0.8)
    plt.xlabel("Archivo")
    plt.ylabel("Peso / Duración (MB/min)")
    plt.title("Relación Peso/Duración por archivo")
    plt.xticks(rotation=45, ha="right")

    # Añadir etiquetas con el tiempo encima de cada barra
    for bar1, dur in zip(bars, duraciones):
        ax.text(bar1.get_x() + bar1.get_width()/2, bar1.get_height(),
                f"{dur:.1f}", ha='center', va='bottom', fontsize=9, color='black', rotation=0)

    # Línea horizontal en 80 MB/min
    ax.axhline(80, color='red', linestyle='--', linewidth=1.5, label='80 MB/min')
    # Línea horizontal en 150 MB/min para resaltar el umbral de optimización
    ax.axhline(150, color='purple', linestyle='--', linewidth=1.5, label='150 MB/min')
    ax.legend()

    plt.tight_layout()
    plt.show()

def calcular_peso_medio(resultados):
    """ Calcula el peso medio por minuto de los vídeos analizados """
    if not resultados:
        return 0
    total_peso = sum(peso for _, _, peso in resultados)
    total_duracion = sum(duracion for _, duracion, _ in resultados)
    if total_duracion == 0:
        return 0
    return total_peso / total_duracion

def calcular_duracion_media(resultados):
    """ Calcula la duración media de los vídeos analizados """
    if not resultados:
        return 0
    total_duracion = sum(duracion for _, duracion, _ in resultados)
    return total_duracion / len(resultados)

def mostrar_grafico(resultados, carpeta):
    """ Muestra un gráfico de dispersión mejorado de duración vs tamaño de los vídeos """
    if not resultados:
        messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
        return
    duraciones = [dur for _, dur, _ in resultados]
    pesos = [peso for _, _, peso in resultados]

    # Elegir estilo disponible
    preferred_styles = ['seaborn-v0_8-darkgrid', 'seaborn-darkgrid', 'seaborn', 'ggplot', 'default']
    for s in preferred_styles:
        if s in plt.style.available:
            try:
                plt.style.use(s)
            except (OSError, ValueError, ImportError):
                continue
            break

    # Crear figura con mejor tamaño
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#f5f5f5')
    ax.set_facecolor('#ffffff')

    # Calcular ratios para colorear puntos según categoría
    ratios = [(peso / dur if dur > 0 else 0) for dur, peso in zip(duraciones, pesos)]

    # Crear categorías: verde=ideal, azul=normal, naranja=alto, rojo=muy alto
    colores = []
    tamanios = []
    for dur, peso, ratio in zip(duraciones, pesos, ratios):
        if dur > 20 and ratio < 50:
            colores.append('#2ecc71')  # Verde: candidato a review
            tamanios.append(120)
        elif ratio > 100:
            colores.append('#e74c3c')  # Rojo: necesita optimizar
            tamanios.append(140)
        elif ratio > 50:
            colores.append('#f39c12')  # Naranja: moderado
            tamanios.append(110)
        else:
            colores.append('#3498db')  # Azul: normal
            tamanios.append(100)

    # Scatter plot mejorado
    scatter = ax.scatter(duraciones, pesos, c=colores, s=tamanios, 
                        edgecolor='#2c3e50', alpha=0.7, linewidth=1.5)

    # Anotaciones inteligentes: solo para valores destacados
    for i, (nombre, dur, peso) in enumerate(resultados):
        ratio = ratios[i]
        # Anotar solo si supera 200 MB/min y duración > 5 min
        if ratio > 200 and dur > 5:
            ax.annotate(nombre, (dur, peso), fontsize=8, 
                       xytext=(5, 5), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=colores[i], alpha=0.6),
                       fontweight='bold')

    # Línea de tendencia (sin extremos)
    if len(duraciones) > 2:
        ratios_con_idx = [(ratio, idx) for idx, ratio in enumerate(ratios)]
        ratios_ordenados = sorted(ratios_con_idx, key=lambda x: x[0])

        # Descartar extremos solo si hay suficientes datos
        if len(ratios) > 20:
            indices_a_descartar = {ratios_ordenados[0][1], ratios_ordenados[1][1],
                                   ratios_ordenados[-1][1], ratios_ordenados[-2][1]}
        else:
            indices_a_descartar = set()

        duraciones_filtradas = [dur for i,
                                dur in enumerate(duraciones) if i not in indices_a_descartar]
        pesos_filtrados = [peso for i,
                           peso in enumerate(pesos) if i not in indices_a_descartar]

        if len(duraciones_filtradas) > 1:
            z = np.polyfit(duraciones_filtradas, pesos_filtrados, 1)
            p = np.poly1d(z)
            x_linea = np.linspace(min(duraciones_filtradas), max(duraciones_filtradas), 100)
            ax.plot(x_linea, p(x_linea), color='#95a5a6', linestyle='--', 
                   linewidth=2.5, label='Tendencia', alpha=0.8)

    # Líneas de referencia mejoradas
    if duraciones:
        x_vals = [min(duraciones), max(duraciones)]
        
        # Línea de 50 MB/min (ideal)
        y_vals_50 = [x * 50 for x in x_vals]
        ax.plot(x_vals, y_vals_50, color='#2ecc71', linestyle='-.', 
               linewidth=2, label='50 MB/min (Ideal)', alpha=0.7)
        
        # Línea de 80 MB/min (bueno)
        y_vals_80 = [x * 80 for x in x_vals]
        ax.plot(x_vals, y_vals_80, color='#3498db', linestyle='--', 
               linewidth=2, label='80 MB/min (Bueno)', alpha=0.7)
        
        # Línea de 100 MB/min (umbral)
        y_vals_100 = [x * 100 for x in x_vals]
        ax.plot(x_vals, y_vals_100, color='#f39c12', linestyle=':', 
               linewidth=2, label='100 MB/min (Alto)', alpha=0.7)
        
        # Línea de 150 MB/min (crítico)
        y_vals_150 = [x * 150 for x in x_vals]
        ax.plot(x_vals, y_vals_150, color='#e74c3c', linestyle='-', 
               linewidth=2.5, label='150 MB/min (Crítico)', alpha=0.8)

    # Etiquetas y título mejorados
    ax.set_xlabel('Duración (minutos)', fontsize=12, fontweight='bold', color='#2c3e50')
    ax.set_ylabel('Tamaño (MB)', fontsize=12, fontweight='bold', color='#2c3e50')
    
    title_text = os.path.basename(carpeta) if carpeta else "Análisis: Duración vs Tamaño"
    ax.set_title(title_text, fontsize=14, fontweight='bold', 
                color='#2c3e50', pad=20)
    
    # Grid mejorado
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7, color='#bdc3c7')
    
    # Leyenda mejorada
    legend = ax.legend(loc='upper left', fontsize=10, framealpha=0.95, 
                      edgecolor='#2c3e50', fancybox=True, shadow=True)
    legend.get_frame().set_facecolor('#ecf0f1')
    
    # Ajustar límites con margen
    if duraciones and pesos:
        margin_x = (max(duraciones) - min(duraciones)) * 0.1
        margin_y = (max(pesos) - min(pesos)) * 0.1
        ax.set_xlim(max(0, min(duraciones) - margin_x), max(duraciones) + margin_x)
        ax.set_ylim(max(0, min(pesos) - margin_y), max(pesos) + margin_y)
    
    # Mejorar apariencia general
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#2c3e50')
    ax.spines['bottom'].set_color('#2c3e50')
    ax.tick_params(colors='#2c3e50', labelsize=9)
    
    plt.tight_layout()
    plt.show()

class GestorHistorialAnalisis:
    """Gestiona el historial de análisis realizados con estadísticas por formato"""
    def __init__(self, archivo_historial="analisis_historial.json", callback_actualizar=None):
        self.archivo_historial = archivo_historial
        self.historial = []
        self.callback_actualizar = callback_actualizar
        self.cargar_historial()

    def cargar_historial(self):
        """Carga el historial desde el archivo JSON"""
        if os.path.exists(self.archivo_historial):
            try:
                with open(self.archivo_historial, 'r', encoding='utf-8') as f:
                    self.historial = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.historial = []

    def guardar_historial(self):
        """Guarda el historial en el archivo JSON"""
        try:
            with open(self.archivo_historial, 'w', encoding='utf-8') as f:
                json.dump(self.historial, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error guardando historial: {e}")

    def registrar_analisis(self, carpeta, counts_by_ext, avg_by_ext, total_archivos):
        """Registra un análisis con estadísticas por formato"""
        analisis = {
            'timestamp': datetime.now().isoformat(),
            'carpeta': carpeta,
            'total_archivos': total_archivos,
            'estadisticas_por_formato': {}
        }

        # Agregar estadísticas por cada formato encontrado
        for ext in sorted(counts_by_ext.keys()):
            analisis['estadisticas_por_formato'][ext] = {
                'cantidad': counts_by_ext[ext],
                'ratio_promedio_mb_min': round(avg_by_ext.get(ext, 0.0), 2)
            }

        self.historial.append(analisis)
        self.guardar_historial()
        # Ejecutar callback si existe para actualizar UI
        if self.callback_actualizar:
            self.callback_actualizar()

    def deshacer_ultimo(self):
        """Deshace el último análisis registrado"""
        if not self.historial:
            return False, "No hay análisis para deshacer"

        ultimo = self.historial[-1]
        self.historial.pop()
        self.guardar_historial()
        return True, f"Análisis de {ultimo['carpeta']} eliminado del historial"

    def deshacer_multiples(self, cantidad):
        """Deshace múltiples análisis"""
        if cantidad > len(self.historial):
            cantidad = len(self.historial)

        deshechados = 0
        for _ in range(cantidad):
            exito, _ = self.deshacer_ultimo()
            if exito:
                deshechados += 1

        return deshechados, 0

    def exportar_csv(self, archivo_salida="analisis_historial.csv"):
        """Exporta el historial a CSV"""
        if not self.historial:
            return False, "No hay análisis para exportar"

        try:
            with open(archivo_salida, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Carpeta', 'Total Archivos', 'Formato',
                                 'Cantidad', 'Ratio Promedio (MB/min)'])

                for analisis in self.historial:
                    for ext, stats in analisis['estadisticas_por_formato'].items():
                        writer.writerow([
                            analisis['timestamp'],
                            analisis['carpeta'],
                            analisis['total_archivos'],
                            ext,
                            stats['cantidad'],
                            stats['ratio_promedio_mb_min']
                        ])
            return True, f"Historial exportado a {archivo_salida}"
        except IOError as e:
            return False, f"Error exportando CSV: {e}"

    def exportar_json(self, archivo_salida="analisis_historial_export.json"):
        """Exporta el historial a JSON"""
        if not self.historial:
            return False, "No hay análisis para exportar"

        try:
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                json.dump(self.historial, f, ensure_ascii=False, indent=2)
            return True, f"Historial exportado a {archivo_salida}"
        except IOError as e:
            return False, f"Error exportando JSON: {e}"

    def obtener_resumen(self):
        """Obtiene un resumen del historial"""
        if not self.historial:
            return "No hay análisis registrados"

        total = len(self.historial)
        return f"Total análisis registrados: {total}"

    def limpiar_historial(self):
        """Limpia todo el historial"""
        self.historial = []
        self.guardar_historial()

class ToolTip:
    """Tooltip para widgets de Tkinter"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, _event=None):
        """Muestra el tooltip"""
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert") if self.widget.winfo_ismapped() else (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 20
        y = y + cy + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#333", foreground="#fff",
                         relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "9", "normal"))
        label.pack(ipadx=6, ipady=2)

    def hide_tip(self, _event=None):
        """Oculta el tooltip"""
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class AnalizadorVideosApp:
    """ Aplicación para analizar vídeos en una carpeta """
    def __init__(self, master):
        self.root = master
        self.root.title("Analizador de vídeos")
        self.resultados = []
        self.preview_counts = {}
        self.videos_problema = []
        self._analysis_executor = None
        self._analisis_future = None
        self.carpeta = None  # Inicializar el atributo carpeta
        self._parar_analisis = False  # Control de parada
        self.gestor_historial = GestorHistorialAnalisis(
            callback_actualizar=self._habilitar_botones_historial)

        self.root.configure(bg=COLOR_BG)

        # Frame principal para selección de carpeta y análisis
        self.frame_principal = ttk.Frame(master, padding=5)
        self.frame_principal.pack(fill="x", pady=5)

        # --- Fila para selección de carpeta y mostrar ruta ---
        frame_dir = tk.Frame(self.frame_principal, bg=COLOR_FRAME)
        frame_dir.pack(fill="x", pady=2)

        self.boton = tk.Button(frame_dir, text="    📁    Carpeta ", width=15,
                       command=self.seleccionar_carpeta, height=2,
                       bg=COLOR_BUTTON_HIGHLIGHT, fg=COLOR_BUTTON_TEXT,
                       activebackground=COLOR_PROGRESS)
        self.boton.pack(side="left", padx=(0, 5))
        ToolTip(self.boton, "Selecciona la carpeta raíz para analizar")

        self.carpeta_var = tk.StringVar()
        self.label_carpeta = tk.Label(frame_dir, textvariable=self.carpeta_var,
                                      width=60, anchor="w", bg=COLOR_FRAME, fg=COLOR_LABEL)
        self.label_carpeta.pack(side="left", padx=(0, 5), fill="x", expand=True)
        self.label_carpeta.config(text="")  # Inicialmente vacío

        # Botón para iniciar el análisis (se crea aquí, pero se mostrará en la pestaña Resultados)
        self.boton_analizar = tk.Button(frame_dir, text="   ▶ Analizar  ",
                                        command=self.analizar_carpeta,
                                        bg=COLOR_BUTTON, fg=COLOR_LABEL, width=14,
                                        activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_analizar["state"] = "disabled"
        self.boton_previsualizar = tk.Button(frame_dir, text="  🔍 Pre-visualizar  ",
                              command=self.previsualizar_resumen,
                              bg=COLOR_BUTTON, fg=COLOR_LABEL, width=14,
                              activebackground=COLOR_PROGRESS, relief="groove")
        self.boton_previsualizar["state"] = "disabled"
        ToolTip(self.boton_analizar, "Ejecuta el análisis completo sobre la carpeta seleccionada")
        ToolTip(self.boton_previsualizar, "Resume rápidamente cuántos archivos hay por extensión")

        # Sistema de pestañas
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Pestaña para archivos AVI
        self.frame_avi = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_avi, text="__AVI")

        # Pestaña para archivos MOV (misma funcionalidad que AVI)
        self.frame_mov = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_mov, text="__MOV")

        # Pestaña para archivos MKV (definida justo después de MOV)
        self.frame_mkv = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_mkv, text="__MKV")

        # Añadir pestaña separadora visual entre grupos de pestañas
        self.frame_separador = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_separador, text=" ")
        self.notebook.tab(self.frame_separador, state="disabled")

        # Pestaña para gráficos
        self.frame_graficos = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_graficos, text=" - Gráficos - ")

        # Pestaña principal con resultados
        self.frame_resultados = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(self.frame_resultados, text=" - Resultados - ")

        # Empezar con las pestañas de formato desactivadas hasta saber qué archivos hay
        self._actualizar_tabs_formatos({})
        # --- CONTENIDO PESTAÑA AVI ---
        avi_buttons_frame = tk.Frame(self.frame_avi, bg=COLOR_FRAME)
        avi_buttons_frame.pack(fill="x", pady=10)

        # Botón para contar archivos AVI en subcarpetas
        self.boton_contar_avis = tk.Button(avi_buttons_frame, text="Contar AVI", width=15,
                                           command=self.contar_avis_en_subcarpetas,
                                           bg=COLOR_BUTTON, fg=COLOR_PROGRESS, relief="flat",
                                           activebackground=COLOR_PROGRESS)
        self.boton_contar_avis.pack(side="left", padx=5)

        # Botón para mover archivos AVI a la carpeta 'avi'
        self.boton_avi = tk.Button(avi_buttons_frame, text="Mover AVI", width=15,
                                   command=self.mover_avis_a_carpeta, relief="flat",
                                   bg=COLOR_BUTTON, fg=COLOR_PROGRESS,
                                   activebackground=COLOR_PROGRESS)
        self.boton_avi.pack(side="left", padx=5)
        self.boton_avi["state"] = "disabled"

        # Etiqueta para mostrar resultados de conteo en la pestaña AVI
        self.label_conteo_avi = tk.Label(self.frame_avi, text="", bg=COLOR_FRAME,
                         fg=COLOR_LABEL, anchor="w")
        self.label_conteo_avi.pack(fill="x", padx=8)

        # (El botón global "Ver Vacías" se crea en la pestaña Resultados)

        # Botón para buscar archivos AVI repetidos
        self.boton_repetidos = tk.Button(avi_buttons_frame, text="Buscar Repetidos", width=15,
                                         command=self.buscar_avis_repetidos, relief="flat",
                                         bg=COLOR_BUTTON, fg=COLOR_TEXT,
                                         activebackground=COLOR_PROGRESS)
        self.boton_repetidos.pack(side="left", padx=5)

        # Área de texto específica para la pestaña AVI (resultados de esa pestaña)
        texto_avi_container = ttk.Frame(self.frame_avi)
        texto_avi_container.pack(fill="both", expand=True, pady=(10,0), padx=8)
        self.texto_avi = tk.Text(texto_avi_container, height=15, width=80, fg=COLOR_TEXT,
                                 bg=COLOR_BG, insertbackground=COLOR_LABEL,
                                 state="disabled", wrap="word", relief="flat")
        self.texto_avi.pack(side="left", fill="both", expand=True)
        scroll_avi = ttk.Scrollbar(texto_avi_container, orient="vertical",
                                   command=self.texto_avi.yview)
        scroll_avi.pack(side="right", fill="y")
        self.texto_avi.configure(yscrollcommand=scroll_avi.set)
        self.texto_avi.config(font=("Consolas", 10))

        # --- CONTENIDO PESTAÑA MOV (duplicado funcionalmente de AVI) ---
        mov_buttons_frame = tk.Frame(self.frame_mov, bg=COLOR_FRAME)
        mov_buttons_frame.pack(fill="x", pady=10)

        # Botón para contar archivos MOV en subcarpetas
        self.boton_contar_movs = tk.Button(mov_buttons_frame, text="Contar MOV", width=15,
                           command=self.contar_movs_en_subcarpetas,
                           bg=COLOR_BUTTON, fg=COLOR_PROGRESS, relief="flat",
                           activebackground=COLOR_PROGRESS)
        self.boton_contar_movs.pack(side="left", padx=5)

        # Botón para mover archivos MOV a la carpeta 'mov'
        self.boton_mov = tk.Button(mov_buttons_frame, text="Mover MOV", width=15,
                       command=self.mover_movs_a_carpeta, relief="flat",
                       bg=COLOR_BUTTON, fg=COLOR_PROGRESS,
                       activebackground=COLOR_PROGRESS)
        self.boton_mov.pack(side="left", padx=5)
        self.boton_mov["state"] = "disabled"

        # (El botón global "Ver Vacías" se crea en la pestaña Resultados)

        # Botón para buscar archivos MOV repetidos
        self.boton_repetidos_mov = tk.Button(mov_buttons_frame, text="Buscar Repetidos", width=15,
                            command=self.buscar_movs_repetidos, relief="flat",
                            bg=COLOR_BUTTON, fg=COLOR_TEXT,
                            activebackground=COLOR_PROGRESS)
        self.boton_repetidos_mov.pack(side="left", padx=5)

        self.label_conteo_mov = tk.Label(self.frame_mov, text="", bg=COLOR_FRAME,
                         fg=COLOR_LABEL, anchor="w")
        self.label_conteo_mov.pack(fill="x", padx=8)

        # Área de texto específica para la pestaña MOV
        texto_mov_container = ttk.Frame(self.frame_mov)
        texto_mov_container.pack(fill="both", expand=True, pady=(10,0), padx=8)
        self.texto_mov = tk.Text(texto_mov_container, height=15, width=80, fg=COLOR_TEXT,
                     bg=COLOR_BG, insertbackground=COLOR_LABEL,
                     state="disabled", wrap="word", relief="flat")
        self.texto_mov.pack(side="left", fill="both", expand=True)
        # configure scrollbar for MOV text area
        scroll_mov = ttk.Scrollbar(texto_mov_container, orient="vertical",
                                   command=self.texto_mov.yview)
        scroll_mov.pack(side="right", fill="y")
        self.texto_mov.configure(yscrollcommand=scroll_mov.set)
        self.texto_mov.config(font=("Consolas", 10))

        # --- CONTENIDO PESTAÑA MKV (duplicado funcionalmente de AVI/MOV) ---
        mkv_buttons_frame = tk.Frame(self.frame_mkv, bg=COLOR_FRAME)
        mkv_buttons_frame.pack(fill="x", pady=10)

        # Botón para contar archivos MKV en subcarpetas
        self.boton_contar_mkvs = tk.Button(mkv_buttons_frame, text="Contar MKV", width=15,
                           command=self.contar_mkvs_en_subcarpetas,
                           bg=COLOR_BUTTON, fg=COLOR_PROGRESS, relief="flat",
                           activebackground=COLOR_PROGRESS)
        self.boton_contar_mkvs.pack(side="left", padx=5)

        # Botón para mover archivos MKV a la carpeta 'mkv'
        self.boton_mkv = tk.Button(mkv_buttons_frame, text="Mover MKV", width=15,
                       command=self.mover_mkvs_a_carpeta, relief="flat",
                       bg=COLOR_BUTTON, fg=COLOR_PROGRESS,
                       activebackground=COLOR_PROGRESS)
        self.boton_mkv.pack(side="left", padx=5)
        self.boton_mkv["state"] = "disabled"

        # (El botón global "Ver Vacías" se crea en la pestaña Resultados)

        # Botón para buscar archivos MKV repetidos
        self.boton_repetidos_mkv = tk.Button(mkv_buttons_frame, text="Buscar Repetidos", width=15,
                            command=self.buscar_mkvs_repetidos, relief="flat",
                            bg=COLOR_BUTTON, fg=COLOR_TEXT,
                            activebackground=COLOR_PROGRESS)
        self.boton_repetidos_mkv.pack(side="left", padx=5)

        self.label_conteo_mkv = tk.Label(self.frame_mkv, text="", bg=COLOR_FRAME,
                         fg=COLOR_LABEL, anchor="w")
        self.label_conteo_mkv.pack(fill="x", padx=8)

        # Área de texto específica para la pestaña MKV
        texto_mkv_container = ttk.Frame(self.frame_mkv)
        texto_mkv_container.pack(fill="both", expand=True, pady=(10,0), padx=8)
        self.texto_mkv = tk.Text(texto_mkv_container, height=15, width=80, fg=COLOR_TEXT,
                     bg=COLOR_BG, insertbackground=COLOR_LABEL,
                     state="disabled", wrap="word", relief="flat")
        self.texto_mkv.pack(side="left", fill="both", expand=True)
        scroll_mkv = ttk.Scrollbar(texto_mkv_container, orient="vertical",
                                   command=self.texto_mkv.yview)
        scroll_mkv.pack(side="right", fill="y")
        self.texto_mkv.configure(yscrollcommand=scroll_mkv.set)
        self.texto_mkv.config(font=("Consolas", 10))

        # --- CONTENIDO PESTAÑA GRÁFICOS ---
        graficos_buttons_frame = tk.Frame(self.frame_graficos, bg=COLOR_FRAME)
        graficos_buttons_frame.pack(fill="x", pady=10)

        self.boton_grafico = tk.Button(graficos_buttons_frame, text="📈 Gráfico", relief="ridge",
                                       command=self.mostrar_grafico, width=20,
                                       bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                       activebackground=COLOR_PROGRESS)
        self.boton_grafico.pack(side="left", padx=5)
        ToolTip(self.boton_grafico, "Muestra duración vs peso para los archivos analizados")

        self.boton_histograma = tk.Button(graficos_buttons_frame, text="📊 Histograma duración",
                                          width=20, command=self.mostrar_histograma_duraciones,
                                          bg=COLOR_BUTTON, fg=COLOR_TEXT, relief="ridge",
                                          activebackground=COLOR_PROGRESS, state="disabled")
        self.boton_histograma.pack(side="left", padx=5)

        self.boton_boxplot = tk.Button(graficos_buttons_frame, text="📊 Histograma ratio", width=20,
                                       command=self.mostrar_boxplot_ratio,
                                       bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                       activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_boxplot.pack(side="left", padx=5)

        self.boton_visual = tk.Button(graficos_buttons_frame, text="Visual", width=20,
                                    command=lambda: mostrar_grafico_visual(self.resultados,
                                                                           self.carpeta),
                                    bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                    activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_visual.pack(side="left", padx=5)

        self.boton_pie_previsualizar = tk.Button(graficos_buttons_frame,
                             text="🥧 Pie Previsualizar", width=20,
                             command=self.mostrar_pie_previsualizar,
                             bg=COLOR_BUTTON, fg=COLOR_TEXT,
                             activebackground=COLOR_PROGRESS,
                             relief="ridge", state="disabled")
        self.boton_pie_previsualizar.pack(side="left", padx=5)
        ToolTip(self.boton_pie_previsualizar,
                "Grafica el resumen de extensiones generado por Pre-visualizar")

        # --- CONTENIDO PESTAÑA RESULTADOS ---
        # Frame para control y progreso
        self.frame3 = tk.Frame(self.frame_resultados, bg=COLOR_FRAME)
        self.frame3.pack(fill="x", pady=5)

        # Añadir aquí el botón de Analizar dentro de la pestaña "Resultados"
        self.boton_parar = tk.Button(self.frame3, text="Parar", width=10,
                         command=self.parar_analisis,
                         bg=COLOR_BUTTON, fg=COLOR_BUTTON_STOP,
                         activebackground=COLOR_PROGRESS)
        # Empaquetar el botón "Analizar" junto al control de progreso
        # para que esté en la pestaña Resultados
        self.boton_analizar.pack(side="left", padx=5)
        self.boton_previsualizar.pack(side="left", padx=5)

        # Botón global para ver carpetas vacías (habilitado cuando se selecciona carpeta)
        self.boton_ver_vacias_general = tk.Button(self.frame3, text="🧹 Ver Vacías", width=12,
                                  command=self.ver_carpetas_vacias,
                              bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                              activebackground=COLOR_PROGRESS, state="disabled")
        self.boton_ver_vacias_general.pack(side="left", padx=5)
        ToolTip(self.boton_ver_vacias_general,
                "Lista carpetas vacías dentro de la carpeta seleccionada")

        self.boton_parar.pack(side="left", padx=10)
        self.boton_parar["state"] = "disabled"

        # Barra de progreso y porcentaje
        self.progress = None
        self.label_porcentaje = tk.Label(self.frame3, text="", bg=COLOR_FRAME, fg=COLOR_LABEL)
        self.label_porcentaje.pack(side='left', padx=5)

        # Etiqueta de resultados
        self.label_resultado = tk.Label(self.frame_resultados, text="Resultados: ", width=130,
                                        bg=COLOR_FRAME, fg=COLOR_LABEL, anchor="w")
        self.label_resultado.pack(pady=2, fill="x")

        # Frame para botones de carpetas especiales
        carpetas_frame = tk.Frame(self.frame_resultados, bg=COLOR_FRAME)
        carpetas_frame.pack(fill="x", pady=5)

        # Frame para botones adicionales
        extras_frame = tk.Frame(self.frame_resultados, bg=COLOR_FRAME)
        extras_frame.pack(fill="x", pady=5)

        # Botón para búsqueda avanzada
        self.boton_mostrar_problemas = tk.Button(extras_frame, text="Mostrar problemáticos",
                             command=self.mostrar_videos_problema,
                             bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                             state="disabled")
        self.boton_mostrar_problemas.pack(side="right", padx=5)

        self.boton_mover_problemas = tk.Button(extras_frame, text="Mover problemáticos",
                               command=self.mover_videos_problema,
                               bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                               state="disabled")
        self.boton_mover_problemas.pack(side="right", padx=5)

        self.boton_busqueda_avanzada = tk.Button(extras_frame, text="Búsqueda avanzada",
                            command=self.abrir_busqueda_avanzada,
                            bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT)
        self.boton_busqueda_avanzada.pack(side="right", padx=5)

        # Boton para ver errores
        self.boton_print_errores = tk.Button(extras_frame, text="Ver Errores", borderwidth=0,
                             command=self.ver_lista_errores, state="disabled",
                             bg=COLOR_FRAME, fg=COLOR_BUTTON_TEXT,
                             activebackground=COLOR_PROGRESS)
        self.boton_print_errores.pack(side="right", padx=5)

        # Frame para botones de historial
        historial_frame = tk.Frame(self.frame_resultados, bg=COLOR_FRAME)
        historial_frame.pack(fill="x", pady=5)

        # Botón para mostrar historial
        self.boton_mostrar_historial = tk.Button(historial_frame, text="📋 Historial",
                                                 command=self.mostrar_historial_movimientos,
                                                 bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                                                 state="disabled")
        self.boton_mostrar_historial.pack(side="left", padx=5)
        ToolTip(self.boton_mostrar_historial, "Muestra el historial de movimientos realizados")

        # Botón para deshacer último movimiento
        self.boton_deshacer = tk.Button(historial_frame, text="↩️ Deshacer",
                                        command=self.deshacer_ultimo_movimiento,
                                        bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT, state="disabled")
        self.boton_deshacer.pack(side="left", padx=5)
        ToolTip(self.boton_deshacer, "Deshace el último movimiento de archivo")

        # Botón para exportar historial a CSV
        self.boton_exportar_csv = tk.Button(historial_frame, text="📊 CSV",
                                            command=self.exportar_historial_csv,
                                            bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT, state="disabled")
        self.boton_exportar_csv.pack(side="left", padx=5)
        ToolTip(self.boton_exportar_csv, "Exporta el historial a formato CSV")

        # Botón para exportar historial a JSON
        self.boton_exportar_json = tk.Button(historial_frame, text="📄 JSON",
                                             command=self.exportar_historial_json,
                                             bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                                             state="disabled")
        self.boton_exportar_json.pack(side="left", padx=5)
        ToolTip(self.boton_exportar_json, "Exporta el historial a formato JSON")

        # Botón para limpiar historial
        self.boton_limpiar_historial = tk.Button(historial_frame, text="🗑️ Limpiar",
                                                 command=self.limpiar_historial,
                                                 bg=COLOR_BUTTON_STOP, fg=COLOR_BUTTON_TEXT,
                                                 state="disabled")
        self.boton_limpiar_historial.pack(side="left", padx=5)
        ToolTip(self.boton_limpiar_historial, "Limpia todo el historial de movimientos")

        # Recuadro tipo Text para mostrar archivos
        self.texto_archivos = tk.Text(self.frame_resultados, height=25, width=120, fg=COLOR_TEXT,
                                      bg=COLOR_BG, insertbackground=COLOR_LABEL,
                                      state="disabled", wrap="word", relief="flat")
        self.texto_archivos.pack(pady=2, padx=10, fill="both", expand=True)
        self.texto_archivos.config(font=("Consolas", 10))

        # Cambiar estilos ttk
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TFrame", background=COLOR_FRAME)
        style.configure("TNotebook", background=COLOR_FRAME)
        style.configure("TNotebook.Tab", background=COLOR_BUTTON, foreground=COLOR_BUTTON_TEXT)
        # Configurar pestaña seleccionada con mejor contraste
        style.map("TNotebook.Tab",
              background=[("selected", COLOR_PROGRESS)],
              foreground=[("selected", "#FFFFFF"),
                      ("disabled", COLOR_TAB_DISABLED)])
        style.configure("TProgressbar", troughcolor=COLOR_BG,
                        background=COLOR_PROGRESS, bordercolor=COLOR_FRAME,
                        lightcolor=COLOR_PROGRESS, darkcolor=COLOR_PROGRESS)
        style.configure("TLabel", background=COLOR_FRAME, foreground=COLOR_LABEL)
        style.configure("TButton", background=COLOR_BUTTON, foreground=COLOR_BUTTON_TEXT)

        # Habilitar botones de historial si hay datos previos
        self._habilitar_botones_historial()

    def mostrar_grafico(self):
        """ Llama a la función global mostrar_grafico con los resultados actuales """
        mostrar_grafico(self.resultados, self.carpeta)

    def mostrar_pie_previsualizar(self):
        """Muestra un gráfico de sectores basado en los recuentos de la previsualización"""
        if not self.preview_counts:
            messagebox.askokcancel("Sin datos", "Ejecuta 'Pre-visualizar' antes de graficar.")
            return
        etiquetas = []
        valores = []
        for ext, cantidad in sorted(self.preview_counts.items(), key=lambda item: item[0]):
            etiquetas.append(ext if ext else "sin_ext")
            valores.append(cantidad)
        plt.style.use('fivethirtyeight')
        _, ax = plt.subplots(figsize=(8, 6))
        ax.pie(valores, labels=etiquetas, autopct="%1.1f%%", startangle=140,
               colors=plt.get_cmap('tab20').colors, wedgeprops=dict(edgecolor='k'))
        ax.set_title("Distribución de archivos por extensión (Pre-visualizar)")
        ax.axis('equal')
        plt.tight_layout()
        plt.show()

    def ver_carpetas_vacias(self):
        """Muestra en el cuadro Text las carpetas y subcarpetas vacías 
        dentro de la carpeta seleccionada"""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return
        vacias = []
        for rooti, dirs, files in os.walk(self.carpeta):
            # Si no hay archivos y no hay subcarpetas con archivos
            if not files and not any(os.listdir(os.path.join(rooti, d)) for d in dirs) and not dirs:
                vacias.append(rooti)
        self.texto_archivos.config(state="normal")
        self.texto_archivos.delete(1.0, tk.END)
        if vacias:
            self.texto_archivos.insert('1.0', "Carpetas vacías:\n")
            for carpeta in vacias:
                self.texto_archivos.insert('1.0', carpeta + "\n")
        else:
            self.texto_archivos.insert('1.0', "No hay carpetas vacías.\n")
        self.texto_archivos.config(state="disabled")

    def ver_lista_errores(self):
        """ Muestra los errores encontrados en un diálogo """
        #print(int(len(lista_de_errores)/2), '\n')
        print(lista_de_errores)
        print(" ")

    def analizar_carpeta(self):
        """Inicia el análisis de la carpeta seleccionada"""
        if self.carpeta:
            self._parar_analisis = False  # Reset al iniciar
            # -- seleccionar la pestaña "Resultados" automáticamente --
            try:
                self.notebook.select(self.frame_resultados)
            except (tk.TclError, AttributeError) as e:
                # En caso de problemas específicos con tkinter/notebook (por ejemplo
                # si el widget no existe o hay un error de Tcl), registrar el error
                # y continuar sin interrumpir. Evitamos capturar Exception de forma genérica.
                try:
                    print(f"Ignoring notebook selection error: {e}")
                except OSError:
                    # Proteger el print en entornos donde stdout pueda fallar
                    pass
            self.boton_parar["state"] = "normal"
            self.boton["state"] = "disabled"
            self.boton_grafico["state"] = "disabled"
            self.boton_histograma["state"] = "disabled"
            self.boton_avi["state"] = "normal"
            self.boton_previsualizar["state"] = "disabled"
            # enable MOV tab controls as well
            try:
                self.boton_mov["state"] = "normal"
            except AttributeError:
                pass
            try:
                self.boton_mkv["state"] = "normal"
            except AttributeError:
                pass
            self.boton_print_errores["state"] = "normal"
            threading.Thread(target=self._analizar_videos_thread, args=(self.carpeta,),
                             daemon=True).start()

    def seleccionar_carpeta(self):
        """ Abre un diálogo para seleccionar una carpeta """
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.carpeta = carpeta
            self.carpeta_var.set(carpeta)
            self.boton["state"] = "normal"
            self.boton_analizar["state"] = "normal"
            self.preview_counts = {}
            self.videos_problema = []
            self.boton_pie_previsualizar["state"] = "disabled"
            self.boton_grafico["state"] = "disabled"
            self.boton_avi["state"] = "normal"
            self.boton_previsualizar["state"] = "normal"
            self.boton_mostrar_problemas["state"] = "disabled"
            self.boton_mover_problemas["state"] = "disabled"
            # enable MOV-specific buttons when a folder is selected
            try:
                self.boton_mov["state"] = "normal"
            except AttributeError:
                pass
            # enable MKV-specific buttons when a folder is selected
            try:
                self.boton_mkv["state"] = "normal"
            except AttributeError:
                pass

            # Habilitar el botón global "Ver Vacías"
            try:
                self.boton_ver_vacias_general["state"] = "normal"
            except AttributeError:
                pass
            self.boton.configure(bg=COLOR_BUTTON)
            self._actualizar_tabs_formatos({})
        else:
            self.boton_analizar["state"] = "disabled"
            self.boton_avi["state"] = "disabled"
            try:
                self.boton_ver_vacias_general["state"] = "disabled"
            except AttributeError:
                pass
            self.boton_previsualizar["state"] = "disabled"
            self.boton_pie_previsualizar["state"] = "disabled"
            self.boton.configure(bg=COLOR_BUTTON_HIGHLIGHT)
            self._actualizar_tabs_formatos({})
            self.boton_mostrar_problemas["state"] = "disabled"
            self.boton_mover_problemas["state"] = "disabled"

    def previsualizar_resumen(self):
        """Muestra un resumen rápido del número de archivos
        por extensión en la carpeta seleccionada"""
        if not self.carpeta:
            messagebox.askokcancel("Aviso", "Primero selecciona una carpeta.")
            return

        # Buscar y mover archivos de la carpeta xcut a la raíz
        xcut_dir = os.path.join(self.carpeta, "xcut")
        if os.path.exists(xcut_dir) and os.path.isdir(xcut_dir):
            archivos_movidos = 0
            try:
                # Listar todos los archivos en la carpeta xcut
                for archivo in os.listdir(xcut_dir):
                    ruta_archivo = os.path.join(xcut_dir, archivo)
                    # Solo mover si es un archivo (no una carpeta)
                    if os.path.isfile(ruta_archivo):
                        destino = os.path.join(self.carpeta, archivo)
                        try:
                            shutil.move(ruta_archivo, destino)
                            archivos_movidos += 1
                        except (OSError, shutil.Error) as e:
                            print(f"No se pudo mover {archivo} desde xcut: {e}")

                # Intentar eliminar la carpeta xcut si está vacía
                try:
                    if os.path.exists(xcut_dir) and not os.listdir(xcut_dir):
                        os.rmdir(xcut_dir)
                except (OSError, shutil.Error) as e:
                    print(f"No se pudo eliminar la carpeta xcut: {e}")

                if archivos_movidos > 0:
                    print(f"Se movieron {archivos_movidos} archivos desde xcut a la raíz")
            except (OSError, shutil.Error) as e:
                print(f"Error procesando la carpeta xcut: {e}")

        # Llevar el foco a la pestaña Resultados antes de mostrar el resumen
        self.notebook.select(self.frame_resultados)
        self.texto_archivos.focus_set()
        counts = {}
        for _, _, files in os.walk(self.carpeta):
            for nombre in files:
                ext = os.path.splitext(nombre)[1].lower() or 'sin_ext'
                counts[ext] = counts.get(ext, 0) + 1
        if not counts:
            messagebox.askokcancel("Resultado", "No se encontraron archivos en la carpeta.")
            return
        self.preview_counts = counts
        self.boton_pie_previsualizar["state"] = "normal"
        resumen = ["Previsualización rápida:\n", "Número de archivos por extensión:\n"]
        for ext, cnt in sorted(counts.items(), key=lambda item: item[0]):
            resumen.append(f"- {cnt} archivos {ext}\n")
        texto = "".join(resumen)
        self.texto_archivos.config(state="normal")
        self.texto_archivos.delete(1.0, tk.END)
        self.texto_archivos.insert('1.0', texto)
        self.texto_archivos.config(state="disabled")
        self._actualizar_tabs_formatos(counts)

    def _actualizar_tabs_formatos(self, counts):
        """Activa o desactiva las pestañas AVI/MOV/MKV según los recuentos"""
        formato_tabs = {
            '.avi': self.frame_avi,
            '.mov': self.frame_mov,
            '.mkv': self.frame_mkv,
        }
        for ext, frame in formato_tabs.items():
            has_files = counts.get(ext, 0) > 0
            self.notebook.tab(frame, state="normal" if has_files else "disabled")

    def contar_avis_en_subcarpetas(self):
        """Cuenta todos los archivos .avi en la carpeta seleccionada y sus subcarpetas"""
        if not self.carpeta:
            mensaje = "Primero selecciona una carpeta."
            self.label_resultado.config(text=mensaje)
            self.label_conteo_avi.config(text=mensaje)
            return
        total_avis = 0
        total_roots = 0
        root_list = []
        carpetas_con_avis = []
        for root_dir, _, files in os.walk(self.carpeta):
            avis_en_esta_carpeta = sum(1 for f in files if f.lower().endswith('.avi'))
            total_avis += avis_en_esta_carpeta
            if avis_en_esta_carpeta > 0:
                total_roots += 1
                carpetas_con_avis.append(root_dir)
            root_list.append(root_dir)
        mensaje = (f"Total - {total_avis} - archivos .avi  en "
               f"{total_roots} carpetas de ({len(root_list)})")
        self.label_resultado.config(text=mensaje)
        self.label_conteo_avi.config(text=mensaje)
        # Mostrar en el cuadro de texto
        # también escribir en la caja de la pestaña AVI si existe
        try:
            self.texto_avi.config(state="normal")
            self.texto_avi.delete(1.0, tk.END)
            if carpetas_con_avis:
                self.texto_avi.insert(tk.END, "Carpetas con archivos .avi:\n")
                for carpeta in carpetas_con_avis:
                    self.texto_avi.insert(tk.END, carpeta + "\n")
            else:
                self.texto_avi.insert(tk.END, "No se encontraron carpetas con archivos .avi.\n")
            self.texto_avi.config(state="disabled")
        except tk.TclError:
            # Ignorar errores específicos de tkinter al actualizar el widget Text
            pass
        # mantener comportamiento previo en el Text principal
        self.texto_archivos.config(state="normal")
        self.texto_archivos.delete(1.0, tk.END)
        if carpetas_con_avis:
            self.texto_archivos.insert('1.0', "Carpetas con archivos .avi:\n")
            for carpeta in carpetas_con_avis:
                self.texto_archivos.insert('1.0', carpeta + "\n")
        else:
            self.texto_archivos.insert('1.0', "No se encontraron carpetas con archivos .avi.\n")
        self.texto_archivos.config(state="disabled")

    def mover_avis_a_carpeta(self):
        """Crea una carpeta 'avi' y mueve todos los archivos .avi a esa carpeta 
        dentro de la carpeta seleccionada."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return

        archivos_avi = [f for f in os.listdir(self.carpeta) if f.lower().endswith('.avi')]
        nombre_carpeta1 = os.path.basename(self.carpeta) or self.carpeta

        if not archivos_avi:
            # informar también en la pestaña AVI
            try:
                self.texto_avi.config(state="normal")
                self.texto_avi.insert(tk.END, f"-- {nombre_carpeta1} --   0 archivos .avi\n")
                self.texto_avi.config(state="disabled")
            except tk.TclError:
                # Ignorar errores específicos de tkinter al actualizar el widget Text
                pass
            print(f"-- {nombre_carpeta1} --", "   0 archivos .avi")
            return

        avi_dir = os.path.join(self.carpeta, "avi")
        if not os.path.exists(avi_dir):
            try:
                os.makedirs(avi_dir)
            except (OSError, shutil.Error) as e:
                print(f"No se pudo crear la carpeta 'avi': {e}")
                try:
                    self.texto_avi.config(state="normal")
                    self.texto_avi.insert(tk.END, f"Error creando carpeta 'avi': {e}\n")
                    self.texto_avi.config(state="disabled")
                except tk.TclError:
                    pass
                return

        movidos = 0
        for archivo in archivos_avi:
            origen = os.path.join(self.carpeta, archivo)
            destino = os.path.join(avi_dir, archivo)
            try:
                shutil.move(origen, destino)
                movidos += 1
                try:
                    self.texto_avi.config(state="normal")
                    self.texto_avi.insert(tk.END, f"Movido: {archivo} -> {avi_dir}\n")
                    self.texto_avi.config(state="disabled")
                except tk.TclError:
                    # Ignorar errores específicos de tkinter al actualizar el widget Text
                    pass
            except (OSError, shutil.Error) as e:
                print(f" //No se pudo mover {archivo}: {e}//")
                try:
                    self.texto_avi.config(state="normal")
                    self.texto_avi.insert(tk.END, f"Error moviendo {archivo}: {e}\n")
                    self.texto_avi.config(state="disabled")
                except tk.TclError:
                    # Ignorar errores específicos de tkinter al actualizar el widget Text
                    pass

        try:
            self.texto_avi.config(state="normal")
            self.texto_avi.insert(tk.END,
                                  f"-- {nombre_carpeta1} --  Se movieron [ {movidos} ]"
                                  " archivos .avi\n")
            self.texto_avi.config(state="disabled")
        except tk.TclError:
            # Ignorar errores específicos de tkinter al actualizar el widget Text
            pass

    def contar_movs_en_subcarpetas(self):
        """Cuenta todos los archivos .mov en la carpeta seleccionada y sus subcarpetas"""
        if not self.carpeta:
            mensaje = "Primero selecciona una carpeta."
            self.label_resultado.config(text=mensaje)
            self.label_conteo_mov.config(text=mensaje)
            return
        total_movs = 0
        total_roots = 0
        root_list = []
        carpetas_con_movs = []
        for root_dir, _, files in os.walk(self.carpeta):
            movs_en_esta_carpeta = sum(1 for f in files if f.lower().endswith('.mov'))
            total_movs += movs_en_esta_carpeta
            if movs_en_esta_carpeta > 0:
                total_roots += 1
                carpetas_con_movs.append(root_dir)
            root_list.append(root_dir)
        mensaje = (f"Total - {total_movs} - archivos .mov  en "
               f"{total_roots} carpetas de ({len(root_list)})")
        self.label_resultado.config(text=mensaje)
        self.label_conteo_mov.config(text=mensaje)
        try:
            self.texto_mov.config(state="normal")
            self.texto_mov.delete(1.0, tk.END)
            if carpetas_con_movs:
                self.texto_mov.insert(tk.END, "Carpetas con archivos .mov:\n")
                for carpeta in carpetas_con_movs:
                    self.texto_mov.insert(tk.END, carpeta + "\n")
            else:
                self.texto_mov.insert(tk.END, "No se encontraron carpetas con archivos .mov.\n")
            self.texto_mov.config(state="disabled")
        except tk.TclError:
            pass
        # also mirror to main text box
        self.texto_archivos.config(state="normal")
        self.texto_archivos.delete(1.0, tk.END)
        if carpetas_con_movs:
            self.texto_archivos.insert('1.0', "Carpetas con archivos .mov:\n")
            for carpeta in carpetas_con_movs:
                self.texto_archivos.insert('1.0', carpeta + "\n")
        else:
            self.texto_archivos.insert('1.0', "No se encontraron carpetas con archivos .mov.\n")
        self.texto_archivos.config(state="disabled")

    def mover_movs_a_carpeta(self):
        """Crea una carpeta 'mov' y mueve todos los archivos .mov
        a esa carpeta dentro de la carpeta seleccionada."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return

        archivos_mov = [f for f in os.listdir(self.carpeta) if f.lower().endswith('.mov')]
        nombre_carpeta1 = os.path.basename(self.carpeta) or self.carpeta

        if not archivos_mov:
            try:
                self.texto_mov.config(state="normal")
                self.texto_mov.insert(tk.END, f"-- {nombre_carpeta1} --   0 archivos .mov\n")
                self.texto_mov.config(state="disabled")
            except tk.TclError:
                pass
            print(f"-- {nombre_carpeta1} --", "   0 archivos .mov")
            return

        mov_dir = os.path.join(self.carpeta, "mov")
        if not os.path.exists(mov_dir):
            try:
                os.makedirs(mov_dir)
            except (OSError, shutil.Error) as e:
                print(f"No se pudo crear la carpeta 'mov': {e}")
                try:
                    self.texto_mov.config(state="normal")
                    self.texto_mov.insert(tk.END, f"Error creando carpeta 'mov': {e}\n")
                    self.texto_mov.config(state="disabled")
                except tk.TclError:
                    pass
                return

        movidos = 0
        for archivo in archivos_mov:
            origen = os.path.join(self.carpeta, archivo)
            destino = os.path.join(mov_dir, archivo)
            try:
                shutil.move(origen, destino)
                movidos += 1
                try:
                    self.texto_mov.config(state="normal")
                    self.texto_mov.insert(tk.END, f"Movido: {archivo} -> {mov_dir}\n")
                    self.texto_mov.config(state="disabled")
                except tk.TclError:
                    pass
            except (OSError, shutil.Error) as e:
                print(f" //No se pudo mover {archivo}: {e}//")
                try:
                    self.texto_mov.config(state="normal")
                    self.texto_mov.insert(tk.END, f"Error moviendo {archivo}: {e}\n")
                    self.texto_mov.config(state="disabled")
                except tk.TclError:
                    pass

        try:
            self.texto_mov.config(state="normal")
            self.texto_mov.insert(tk.END,
                                  f"-- {nombre_carpeta1} --  Se movieron [ {movidos} ]"
                                  " archivos .mov\n")
            self.texto_mov.config(state="disabled")
        except tk.TclError:
            pass

    def buscar_movs_repetidos(self):
        """Busca archivos .mov que tengan el mismo nombre base pero con diferente extensión
        y los mueve a una carpeta 'repeat'."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return

        extensiones_video = ('.mp4', '.avi', '.mkv', '.wmv', '.flv', '.webm')
        archivos_repetidos = []

        for root_dir, _, files in os.walk(self.carpeta):
            archivos_mov = [f for f in files if f.lower().endswith('.mov')]

            for archivo_mov in archivos_mov:
                nombre_base = os.path.splitext(archivo_mov)[0]
                for archivo in files:
                    if archivo != archivo_mov and os.path.splitext(archivo)[0] == nombre_base:
                        if archivo.lower().endswith(extensiones_video):
                            archivos_repetidos.append((os.path.join(root_dir, archivo_mov),
                                                       root_dir))
                            break

        if not archivos_repetidos:
            print("No se encontraron archivos .mov repetidos.")
            try:
                self.texto_mov.config(state="normal")
                self.texto_mov.insert(tk.END, "No se encontraron archivos .mov repetidos.\n")
                self.texto_mov.config(state="disabled")
            except tk.TclError:
                pass
            return

        movidos = 0
        for ruta_mov, carpeta_origen in archivos_repetidos:
            repeat_dir = os.path.join(carpeta_origen, "repeat")
            if not os.path.exists(repeat_dir):
                os.makedirs(repeat_dir)

            nombre_archivo = os.path.basename(ruta_mov)
            destino = os.path.join(repeat_dir, nombre_archivo)

            try:
                shutil.move(ruta_mov, destino)
                movidos += 1
                print(f"Movido: {nombre_archivo} -> repeat/")
                try:
                    self.texto_mov.config(state="normal")
                    self.texto_mov.insert(tk.END, f"Movido: {nombre_archivo} -> {repeat_dir}\n")
                    self.texto_mov.config(state="disabled")
                except tk.TclError:
                    pass
            except (OSError, shutil.Error) as e:
                print(f"No se pudo mover {nombre_archivo}: {e}")
                try:
                    self.texto_mov.config(state="normal")
                    self.texto_mov.insert(tk.END, f"No se pudo mover {nombre_archivo}: {e}\n")
                    self.texto_mov.config(state="disabled")
                except tk.TclError:
                    pass

        try:
            self.texto_mov.config(state="normal")
            self.texto_mov.insert(tk.END,
                                  f"Se movieron {movidos} archivos .mov repetidos"
                                  " a carpetas 'repeat'.\n")
            self.texto_mov.config(state="disabled")
        except tk.TclError:
            pass

    def contar_mkvs_en_subcarpetas(self):
        """Cuenta todos los archivos .mkv en la carpeta seleccionada y sus subcarpetas"""
        if not self.carpeta:
            mensaje = "Primero selecciona una carpeta."
            self.label_resultado.config(text=mensaje)
            self.label_conteo_mkv.config(text=mensaje)
            return
        total = 0
        total_roots = 0
        root_list = []
        carpetas = []
        for root_dir, _, files in os.walk(self.carpeta):
            mkvs = sum(1 for f in files if f.lower().endswith('.mkv'))
            total += mkvs
            if mkvs > 0:
                total_roots += 1
                carpetas.append(root_dir)
            root_list.append(root_dir)
        mensaje = (f"Total - {total} - archivos .mkv"
               f"  en {total_roots} carpetas de ({len(root_list)})")
        self.label_resultado.config(text=mensaje)
        self.label_conteo_mkv.config(text=mensaje)
        try:
            self.texto_mkv.config(state="normal")
            self.texto_mkv.delete(1.0, tk.END)
            if carpetas:
                self.texto_mkv.insert(tk.END, "Carpetas con archivos .mkv:\n")
                for c in carpetas:
                    self.texto_mkv.insert(tk.END, c + "\n")
            else:
                self.texto_mkv.insert(tk.END, "No se encontraron carpetas con archivos .mkv.\n")
            self.texto_mkv.config(state="disabled")
        except tk.TclError:
            pass
        self.texto_archivos.config(state="normal")
        self.texto_archivos.delete(1.0, tk.END)
        if carpetas:
            self.texto_archivos.insert('1.0', "Carpetas con archivos .mkv:\n")
            for c in carpetas:
                self.texto_archivos.insert('1.0', c + "\n")
        else:
            self.texto_archivos.insert('1.0', "No se encontraron carpetas con archivos .mkv.\n")
        self.texto_archivos.config(state="disabled")

    def mover_mkvs_a_carpeta(self):
        """Crea una carpeta 'mkv' y mueve todos los archivos .mkv a esa carpeta
        dentro de la carpeta seleccionada."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return
        archivos = [f for f in os.listdir(self.carpeta) if f.lower().endswith('.mkv')]
        nombre_carpeta1 = os.path.basename(self.carpeta) or self.carpeta
        if not archivos:
            try:
                self.texto_mkv.config(state="normal")
                self.texto_mkv.insert(tk.END, f"-- {nombre_carpeta1} --   0 archivos .mkv\n")
                self.texto_mkv.config(state="disabled")
            except tk.TclError:
                pass
            print(f"-- {nombre_carpeta1} --", "   0 archivos .mkv")
            return
        mkv_dir = os.path.join(self.carpeta, "mkv")
        if not os.path.exists(mkv_dir):
            try:
                os.makedirs(mkv_dir)
            except (OSError, shutil.Error) as e:
                try:
                    self.texto_mkv.config(state="normal")
                    self.texto_mkv.insert(tk.END, f"Error creando carpeta 'mkv': {e}\n")
                    self.texto_mkv.config(state="disabled")
                except tk.TclError:
                    pass
                return
        movidos = 0
        for archivo in archivos:
            origen = os.path.join(self.carpeta, archivo)
            destino = os.path.join(mkv_dir, archivo)
            try:
                shutil.move(origen, destino)
                movidos += 1
                try:
                    self.texto_mkv.config(state="normal")
                    self.texto_mkv.insert(tk.END, f"Movido: {archivo} -> {mkv_dir}\n")
                    self.texto_mkv.config(state="disabled")
                except tk.TclError:
                    pass
            except (OSError, shutil.Error) as e:
                try:
                    self.texto_mkv.config(state="normal")
                    self.texto_mkv.insert(tk.END, f"Error moviendo {archivo}: {e}\n")
                    self.texto_mkv.config(state="disabled")
                except tk.TclError:
                    pass
        try:
            self.texto_mkv.config(state="normal")
            self.texto_mkv.insert(tk.END, f"-- {nombre_carpeta1} --"
                                  f"  Se movieron [ {movidos} ] archivos .mkv\n")
            self.texto_mkv.config(state="disabled")
        except tk.TclError:
            pass

    def buscar_mkvs_repetidos(self):
        """Busca archivos .mkv que tengan el mismo nombre base
        pero con diferente extensión y los mueve a 'repeat'."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return
        extensiones_video = ('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm')
        repetidos = []
        for root_dir, _, files in os.walk(self.carpeta):
            mkvs = [f for f in files if f.lower().endswith('.mkv')]
            for archivo_mkv in mkvs:
                base = os.path.splitext(archivo_mkv)[0]
                for archivo in files:
                    if archivo != archivo_mkv and os.path.splitext(archivo)[0] == base:
                        if archivo.lower().endswith(extensiones_video):
                            repetidos.append((os.path.join(root_dir, archivo_mkv), root_dir))
                            break
        if not repetidos:
            try:
                self.texto_mkv.config(state="normal")
                self.texto_mkv.insert(tk.END, "No se encontraron archivos .mkv repetidos.\n")
                self.texto_mkv.config(state="disabled")
            except tk.TclError:
                pass
            return
        movidos = 0
        for ruta, carpeta_origen in repetidos:
            repeat_dir = os.path.join(carpeta_origen, "repeat")
            if not os.path.exists(repeat_dir):
                os.makedirs(repeat_dir)
            nombre = os.path.basename(ruta)
            destino = os.path.join(repeat_dir, nombre)
            try:
                shutil.move(ruta, destino)
                movidos += 1
                try:
                    self.texto_mkv.config(state="normal")
                    self.texto_mkv.insert(tk.END, f"Movido: {nombre} -> {repeat_dir}\n")
                    self.texto_mkv.config(state="disabled")
                except tk.TclError:
                    pass
            except (OSError, shutil.Error) as e:
                try:
                    self.texto_mkv.config(state="normal")
                    self.texto_mkv.insert(tk.END, f"No se pudo mover {nombre}: {e}\n")
                    self.texto_mkv.config(state="disabled")
                except tk.TclError:
                    pass
        try:
            self.texto_mkv.config(state="normal")
            self.texto_mkv.insert(tk.END, f"Se movieron {movidos} archivos .mkv"
                                  " repetidos a carpetas 'repeat'.\n")
            self.texto_mkv.config(state="disabled")
        except tk.TclError:
            pass


    def mostrar_histograma_duraciones(self):
        """Muestra un histograma mejorado de la distribución de duraciones de vídeos."""
        if not self.resultados:
            messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
            return
        
        duraciones = [dur for _, dur, _ in self.resultados]
        
        # Elegir estilo disponible
        preferred_styles = ['seaborn-v0_8-darkgrid', 'seaborn-darkgrid', 'seaborn', 'ggplot', 'default']
        for s in preferred_styles:
            if s in plt.style.available:
                try:
                    plt.style.use(s)
                except (OSError, ValueError, ImportError):
                    continue
                break

        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('#f5f5f5')
        ax.set_facecolor('#ffffff')

        # Calcular número de bins óptimo
        n_bins = max(15, int(np.ceil(np.log2(len(duraciones)) + 1)))
        
        # Crear histograma con colores degradados
        n, bins, patches = ax.hist(duraciones, bins=n_bins, edgecolor='#2c3e50', 
                                   alpha=0.8, linewidth=1.2)

        # Colorear los bins con degradado según frecuencia
        cm = plt.colormaps.get_cmap('RdYlGn_r')
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        col = bin_centers - min(bin_centers)
        if max(col) > 0:
            col /= max(col)
        for c, p in zip(col, patches):
            p.set_facecolor(cm(c))

        # Calcular estadísticas
        media = np.mean(duraciones)
        mediana = np.median(duraciones)
        q1 = np.percentile(duraciones, 25)
        q3 = np.percentile(duraciones, 75)

        # Líneas de referencia con estadísticas
        ax.axvline(media, color='#e74c3c', linestyle='--', linewidth=2.5, 
                  label=f'Media: {media:.1f} min', alpha=0.9)
        ax.axvline(mediana, color='#3498db', linestyle='-.', linewidth=2.5, 
                  label=f'Mediana: {mediana:.1f} min', alpha=0.9)
        ax.axvline(q1, color='#95a5a6', linestyle=':', linewidth=1.5, 
                  label=f'Q1: {q1:.1f} min', alpha=0.7)
        ax.axvline(q3, color='#95a5a6', linestyle=':', linewidth=1.5, 
                  label=f'Q3: {q3:.1f} min', alpha=0.7)

        # Zona sombreada para rangos interpretativos
        ax.axvspan(0, 5, alpha=0.1, color='#e74c3c', label='Muy corto (< 5 min)')
        ax.axvspan(5, 20, alpha=0.1, color='#f39c12', label='Corto (5-20 min)')
        ax.axvspan(20, 60, alpha=0.1, color='#2ecc71', label='Normal (20-60 min)')
        if max(duraciones) > 60:
            ax.axvspan(60, max(duraciones) + 5, alpha=0.1, color='#3498db', 
                      label='Largo (> 60 min)')

        # Etiquetas y título mejorados
        ax.set_xlabel('Duración (minutos)', fontsize=12, fontweight='bold', color='#2c3e50')
        ax.set_ylabel('Cantidad de vídeos', fontsize=12, fontweight='bold', color='#2c3e50')
        ax.set_title('Distribución de duraciones de vídeos', fontsize=14, fontweight='bold', 
                    color='#2c3e50', pad=20)

        # Grid mejorado
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7, color='#bdc3c7')
        ax.set_axisbelow(True)

        # Leyenda mejorada
        legend = ax.legend(loc='upper right', fontsize=10, framealpha=0.95, 
                          edgecolor='#2c3e50', fancybox=True, shadow=True, ncol=2)
        legend.get_frame().set_facecolor('#ecf0f1')

        # Estadísticas en texto
        stats_text = f'Total: {len(duraciones)} vídeos\nDesv. Est: {np.std(duraciones):.1f} min\nRango: {min(duraciones):.1f} - {max(duraciones):.1f} min'
        ax.text(0.5, 0.98, stats_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top', horizontalalignment='center',
               bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.9, edgecolor='#2c3e50', pad=0.8),
               family='monospace', fontweight='bold', color='#2c3e50')

        # Mejorar apariencia general
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#2c3e50')
        ax.spines['bottom'].set_color('#2c3e50')
        ax.tick_params(colors='#2c3e50', labelsize=10)

        plt.tight_layout()
        plt.show()

    def mostrar_boxplot_ratio(self):
        """Genera dos histogramas de la relación Peso/Duración (MB/min)
        uno para archivos MKV y otro para todos los demás."""
        if not self.resultados:
            messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
            return

        # Separar ratios por formato (MKV vs otros)
        ratios_mkv = []
        ratios_otros = []

        for nombre, dur, peso in self.resultados:
            if dur and dur > 0:
                ratio = peso / dur
                ext = os.path.splitext(nombre)[1].lower()
                if ext == '.mkv':
                    ratios_mkv.append(ratio)
                else:
                    ratios_otros.append(ratio)

        if not ratios_mkv and not ratios_otros:
            messagebox.askokcancel("Sin datos", "No hay ratios válidos (duración 0).")
            return

        # Elegir estilo disponible (fallback seguro)
        preferred_styles = ['seaborn-darkgrid', 'seaborn', 'ggplot', 'default']
        for s in preferred_styles:
            if s in plt.style.available:
                try:
                    plt.style.use(s)
                except (OSError, ValueError, ImportError):
                    continue
                break

        # Crear dos subplots (uno arriba, otro abajo)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
        cm = plt.colormaps.get_cmap('viridis')

        # --- Subplot 1: Archivos MKV ---
        if ratios_mkv:
            n_bins = max(10, int(np.ceil(np.log2(len(ratios_mkv)) + 1)))
            n, bins, patches = ax1.hist(ratios_mkv, bins=n_bins, color='#9fb3c8',
                                         edgecolor='#2b5f78', alpha=0.75, linewidth=1.2)

            # Colorear los bins en degradado
            bin_centers = 0.5 * (bins[:-1] + bins[1:])
            col = bin_centers - min(bin_centers)
            if max(col) > 0:
                col /= max(col)
            for c, p in zip(col, patches):
                plt.setp(p, 'facecolor', cm(c))

            # Líneas de referencia
            media_mkv = np.mean(ratios_mkv)
            mediana_mkv = np.median(ratios_mkv)
            ax1.axvline(media_mkv, color='red', linestyle='--', linewidth=2,
                       label=f'Media: {media_mkv:.2f} MB/min')
            ax1.axvline(mediana_mkv, color='green', linestyle='--', linewidth=2,
                       label=f'Mediana: {mediana_mkv:.2f} MB/min')

            ax1.set_xlabel('Ratio (MB/min)', fontsize=11)
            ax1.set_ylabel('Frecuencia', fontsize=11)
            ax1.set_title(f'Archivos MKV (n={len(ratios_mkv)})', fontsize=12, fontweight='bold')
            ax1.legend(loc='upper right')
            ax1.grid(True, alpha=0.3)
        else:
            ax1.text(0.5, 0.5, 'Sin datos MKV', ha='center', va='center',
                    transform=ax1.transAxes, fontsize=12, color='gray')
            ax1.set_title('Archivos MKV (n=0)', fontsize=12, fontweight='bold')

        # --- Subplot 2: Otros formatos ---
        if ratios_otros:
            n_bins = max(10, int(np.ceil(np.log2(len(ratios_otros)) + 1)))
            n, bins, patches = ax2.hist(ratios_otros, bins=n_bins, color='#9fb3c8',
                                         edgecolor='#2b5f78', alpha=0.75, linewidth=1.2)

            # Colorear los bins en degradado
            bin_centers = 0.5 * (bins[:-1] + bins[1:])
            col = bin_centers - min(bin_centers)
            if max(col) > 0:
                col /= max(col)
            for c, p in zip(col, patches):
                plt.setp(p, 'facecolor', cm(c))

            # Líneas de referencia
            media_otros = np.mean(ratios_otros)
            mediana_otros = np.median(ratios_otros)
            ax2.axvline(media_otros, color='red', linestyle='--', linewidth=2,
                       label=f'Media: {media_otros:.2f} MB/min')
            ax2.axvline(mediana_otros, color='green', linestyle='--', linewidth=2,
                       label=f'Mediana: {mediana_otros:.2f} MB/min')

            ax2.set_xlabel('Ratio (MB/min)', fontsize=11)
            ax2.set_ylabel('Frecuencia', fontsize=11)
            ax2.set_title(f'Otros formatos (n={len(ratios_otros)})', fontsize=12, fontweight='bold')
            ax2.legend(loc='upper right')
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'Sin datos', ha='center', va='center',
                    transform=ax2.transAxes, fontsize=12, color='gray')
            ax2.set_title('Otros formatos (n=0)', fontsize=12, fontweight='bold')

        fig.suptitle('Histograma: distribución de Peso/Duración (MB/min)', 
                     fontsize=13, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.show()

    def abrir_busqueda_avanzada(self):
        """Abre una ventana para búsqueda avanzada por peso, duración, formato, etc."""
        ventana = tk.Toplevel(self.root)
        ventana.title("Búsqueda avanzada")
        ventana.geometry("400x300")
        ventana.configure(bg=COLOR_FRAME)

        # Duración
        tk.Label(ventana, text="Duración mínima (min):", bg=COLOR_FRAME,
                 fg=COLOR_LABEL).pack(pady=2)
        entry_dur_min = tk.Entry(ventana)
        entry_dur_min.pack()
        tk.Label(ventana, text="Duración máxima (min):", bg=COLOR_FRAME,
                 fg=COLOR_LABEL).pack(pady=2)
        entry_dur_max = tk.Entry(ventana)
        entry_dur_max.pack()

        # Peso
        tk.Label(ventana, text="Peso mínimo (MB):", bg=COLOR_FRAME, fg=COLOR_LABEL).pack(pady=2)
        entry_peso_min = tk.Entry(ventana)
        entry_peso_min.pack()
        tk.Label(ventana, text="Peso máximo (MB):", bg=COLOR_FRAME, fg=COLOR_LABEL).pack(pady=2)
        entry_peso_max = tk.Entry(ventana)
        entry_peso_max.pack()

        # Formato
        tk.Label(ventana, text="Formato (ej: mp4, avi, mkv):", bg=COLOR_FRAME,
                 fg=COLOR_LABEL).pack(pady=2)
        entry_formato = tk.Entry(ventana)
        entry_formato.pack()

        def buscar_avanzado():
            """ Realiza la búsqueda avanzada según los criterios introducidos """
            try:
                dur_min = float(entry_dur_min.get()) if entry_dur_min.get() else None
                dur_max = float(entry_dur_max.get()) if entry_dur_max.get() else None
                peso_min = float(entry_peso_min.get()) if entry_peso_min.get() else None
                peso_max = float(entry_peso_max.get()) if entry_peso_max.get() else None
                formato = entry_formato.get().strip().lower()
            except ValueError:
                messagebox.askokcancel("Error", "Introduce valores numéricos válidos.")
                return

            encontrados = []
            for nombre, duracion, peso in self.resultados:
                cumple = True
                if dur_min is not None and duracion < dur_min:
                    cumple = False
                if dur_max is not None and duracion > dur_max:
                    cumple = False
                if peso_min is not None and peso < peso_min:
                    cumple = False
                if peso_max is not None and peso > peso_max:
                    cumple = False
                if formato and not nombre.lower().endswith(f".{formato}"):
                    cumple = False
                if cumple:
                    encontrados.append((nombre, duracion, peso))

            self.texto_archivos.config(state="normal")
            self.texto_archivos.delete(1.0, tk.END)
            if encontrados:
                self.texto_archivos.insert('1.0', "Resultados de búsqueda avanzada:\n")
                for nombre, dur, peso in encontrados:
                    self.texto_archivos.insert('1.0', f"{nombre}\t{dur:.2f} min\t{peso:.2f} MB\n")
            else:
                self.texto_archivos.insert('1.0',
                                           "No se encontraron archivos con esos criterios.\n")
            self.texto_archivos.config(state="disabled")
            ventana.destroy()

        boton_buscar = tk.Button(ventana, text="Buscar", command=buscar_avanzado,
                                bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT)
        boton_buscar.pack(pady=10)

    def parar_analisis(self):
        """ Detiene el análisis de vídeos """
        self._parar_analisis = True
        # Calcula el porcentaje analizado hasta el momento
        try:
            if self.progress:
                porcentaje = int(self.progress['value'] / self.progress['maximum'] * 100)
            else:
                porcentaje = 0
        except tk.TclError:
            porcentaje = 0
        print(f"Análisis abortado mediante el botón PARAR. Porcentaje analizado: {porcentaje}%")
        self._detener_procesos_analisis(wait=False)

    def _procesar_video(self, ruta):
        """Carga el clip y devuelve duración/peso (MB/min)"""
        with VideoFileClip(ruta) as clip:
            duracion = clip.duration / 60
            peso = os.path.getsize(ruta) / (1024 * 1024)
        return duracion, peso

    def _mover_archivo_a_errores(self, ruta, archivo):
        """Mueve un archivo a su carpeta 'errores' y devuelve si tuvo éxito"""
        errores_dir = os.path.join(os.path.dirname(ruta), "errores")
        if not os.path.exists(errores_dir):
            try:
                os.makedirs(errores_dir)
            except (OSError, shutil.Error) as exc:
                print(f"No se pudo crear la carpeta 'errores': {exc}")
                return False
        destino = os.path.join(errores_dir, archivo)
        max_intentos = 5
        for intento in range(1, max_intentos + 1):
            try:
                shutil.move(ruta, destino)
                # Registrar el movimiento en el historial
                return True
            except (OSError, shutil.Error) as exc:
                err_num = getattr(exc, "errno", None)
                win_err = getattr(exc, "winerror", None)
                if intento < max_intentos and (win_err == 32 or err_num == errno.EACCES):
                    wait = 0.4 + intento * 0.1
                    print(f"Intento {intento} de mover {archivo} bloqueado; esperando {wait:.1f}s")
                    time.sleep(wait)
                    continue
                print(f"Error al mover {archivo} a 'errores': {exc}")
                return False

    def _detener_procesos_analisis(self, wait=False):
        """Cancela y cierra el executor que analiza vídeos"""
        if self._analisis_future and not self._analisis_future.done():
            try:
                self._analisis_future.cancel()
            except Exception:
                pass
        if self._analysis_executor:
            try:
                self._analysis_executor.shutdown(wait=wait)
            except Exception:
                pass
            finally:
                self._analysis_executor = None
        self._analisis_future = None

    def _analizar_videos_thread(self, carpeta):
        """ Función que se ejecuta en un hilo para analizar los vídeos en carpeta y subcarpetas """
        tiempo_inicio = time.time()
        extensiones_video = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
        archivos = []
        rutas_archivos = []
        carpetas_archivos = []
        # Recorrer carpeta y subcarpetas
        for root_dir, _, files in os.walk(carpeta):
            if os.path.basename(root_dir).lower() == "errores":
                continue
            for f in files:
                if f.lower().endswith(extensiones_video):
                    archivos.append(f)
                    rutas_archivos.append(os.path.join(root_dir, f))
                    carpetas_archivos.append(root_dir)
        total = len(rutas_archivos)
        resultados = []
        # Contadores para movimientos realizados durante el análisis
        moved_counts = {'optimizar': 0, 'review': 0, 'errores': 0}
        self.texto_archivos.delete(1.0, tk.END)
        self.videos_problema.clear()
        self._detener_procesos_analisis(wait=False)
        self.root.after(0, self._actualizar_botones_problemas)

        def crear_barra():
            """ Crea la barra de progreso """
            self.progress = ttk.Progressbar(self.frame3, length=800,
                                            mode="determinate", maximum=total)
            self.progress.pack(pady=2)
            self.label_porcentaje.config(text="0%")
            self.frame3.update_idletasks()
        self.root.after(0, crear_barra)
        self._analysis_executor = ThreadPoolExecutor(max_workers=1)

        for idx, (
            archivo, ruta, carpeta_actual
            ) in enumerate(zip(archivos, rutas_archivos, carpetas_archivos), 1):
            if self._parar_analisis:
                break  # Sale del bucle si se pulsó "Parar"
            carpetita = os.path.basename(os.path.dirname(ruta))
            self.texto_archivos.config(state="normal")
            self.texto_archivos.insert('1.0', f"Analizando archivo: {idx}"
                                       f"\n{carpetita} - {archivo}\n")
            self.texto_archivos.config(state="disabled")

            if not self._analysis_executor:
                self._analysis_executor = ThreadPoolExecutor(max_workers=1)
            future = self._analysis_executor.submit(self._procesar_video, ruta)
            self._analisis_future = future
            skip_video = False

            try:
                duracion, peso = future.result(timeout=30)
                if duracion > 0:
                    resultados.append((archivo, duracion, peso, ruta, carpeta_actual))
            except TimeoutError:
                self._registrar_video_problema(ruta, archivo, "Timeout >30s")
                self.texto_archivos.config(state="normal")
                self.texto_archivos.insert('1.0',
                                           f"Timeout >30s en {archivo}, registro problemático.\n")
                self.texto_archivos.config(state="disabled")
                skip_video = True
            except CancelledError:
                # Cuando se cancela la tarea, continuar sin marcar como problema
                self.texto_archivos.config(state="normal")
                self.texto_archivos.insert('1.0',
                                           f"Análisis cancelado para {archivo}.\n")
                self.texto_archivos.config(state="disabled")
                skip_video = True
            except (OSError, ValueError) as e:
                parent_basename = os.path.basename(os.path.dirname(ruta)).lower()
                err_msg = str(e)
                self.texto_archivos.config(state="normal")
                try:
                    self.texto_archivos.insert('1.0', err_msg + "\n")
                except tk.TclError:
                    pass
                self.texto_archivos.config(state="disabled")
                self._registrar_video_problema(ruta, archivo, err_msg)
                if parent_basename == "errores":
                    print(f"Archivo ya en 'errores', no se mueve: {ruta}")
                skip_video = True
            except Exception as e:
                # Capturar cualquier otra excepción inesperada sin detener el análisis
                exc_msg = f"Error inesperado: {str(e)}"
                self.texto_archivos.config(state="normal")
                try:
                    self.texto_archivos.insert('1.0', exc_msg + "\n")
                except tk.TclError:
                    pass
                self.texto_archivos.config(state="disabled")
                self._registrar_video_problema(ruta, archivo, exc_msg)
                skip_video = True

            porcentaje = int((idx / total) * 100)
            self.root.after(0, lambda val=idx,
                            pct=porcentaje: self._actualizar_progreso(val, pct))

            if skip_video:
                continue
            if idx % 5 == 0:
                self.root.after(0, self.frame3.update_idletasks)

        self.boton_parar["state"] = "disabled"
        self._detener_procesos_analisis(wait=True)
        self.root.after(0, self._actualizar_botones_problemas)

        # --- Mover archivos que cumplen la condición a la carpeta
        # "review", "xcut" o "optimizar" ---
        for nombre, duracion, peso, ruta, carpeta_actual in resultados:
            # Evita crear subcarpetas dentro de sí mismas (review/xcut/optimizar)
            basename_actual = os.path.basename(carpeta_actual).lower()
            # calcular ratio MB/min de forma segura
            ratio = (peso / duracion) if duracion else 0

            # Prioridad: mover a 'optimizar' si la relación peso/duración es excesiva
            if ratio > 100:
                if basename_actual != "optimizar":
                    optim_dir = os.path.join(carpeta_actual, "optimizar")
                else:
                    optim_dir = carpeta_actual
                if not os.path.exists(optim_dir):
                    os.makedirs(optim_dir)
                destino = os.path.join(optim_dir, nombre)
                try:
                    shutil.move(ruta, destino)
                    moved_counts['optimizar'] += 1
                except (OSError, shutil.Error) as e:
                    print(f"No se pudo mover {nombre} a 'optimizar': {e}")

            elif duracion > 20 and ratio < 50:
                # Verificar que el archivo sea .mkv antes de mover a review
                ext_archivo = os.path.splitext(nombre)[1].lower()
                if ext_archivo == ".mkv":
                    if basename_actual != "review":
                        review_dir = os.path.join(carpeta_actual, "review")
                    else:
                        review_dir = carpeta_actual
                    if not os.path.exists(review_dir):
                        os.makedirs(review_dir)
                    destino = os.path.join(review_dir, nombre)
                    try:
                        shutil.move(ruta, destino)
                        moved_counts['review'] += 1
                    except (OSError, shutil.Error) as e:
                        print(f"No se pudo mover {nombre}: {e}")

        # Calcular estadísticas por extensión y preparar resumen
        # Conteo total de archivos por extensión (a partir de la lista inicial `archivos`)
        counts_by_ext = {}
        for f in archivos:
            ext = os.path.splitext(f)[1].lower() or 'sin_ext'
            counts_by_ext[ext] = counts_by_ext.get(ext, 0) + 1

        # Calcular peso medio por minuto por extensión usando los resultados válidos
        peso_sum_by_ext = {}
        dur_sum_by_ext = {}
        for nombre, dur, peso, *_ in resultados:
            ext = os.path.splitext(nombre)[1].lower() or 'sin_ext'
            peso_sum_by_ext[ext] = peso_sum_by_ext.get(ext, 0.0) + peso
            dur_sum_by_ext[ext] = dur_sum_by_ext.get(ext, 0.0) + dur

        avg_by_ext = {}
        for ext in counts_by_ext:
            total_peso = peso_sum_by_ext.get(ext, 0.0)
            total_dur = dur_sum_by_ext.get(ext, 0.0)
            avg = (total_peso / total_dur) if total_dur > 0 else 0.0
            avg_by_ext[ext] = avg

        # Preparar texto del resumen
        resumen_lines = []
        resumen_lines.append("\nResumen del análisis:\n")
        resumen_lines.append("Número de archivos por extensión:\n")
        for ext, cnt in sorted(counts_by_ext.items(), key=lambda x: x[0]):
            resumen_lines.append(f"- {cnt} archivos {ext}\n")
        resumen_lines.append("\nPeso medio por minuto por extensión:\n")
        for ext, avg in sorted(avg_by_ext.items(), key=lambda x: x[0]):
            resumen_lines.append(f"- {ext}: {avg:.2f} MB/min\n")
        resumen_lines.append("\nArchivos movidos durante el análisis:\n")
        for k in moved_counts:
            resumen_lines.append(f"- {moved_counts[k]} archivos -> {k}\n")
        if self.videos_problema:
            resumen_lines.append(
                f"\nSe detectaron {len(self.videos_problema)} vídeos problemáticos."
                " Usa 'Mostrar problemáticos' para verlos y"
                " 'Mover problemáticos' para enviarlos a errores.\n")

        resumen_text = "".join(resumen_lines)

        # Preparado el resumen (se mostrará desde 'actualizar_interfaz')

        def destruir_barra():
            if self.progress is not None:
                self.progress.destroy()

        self.root.after(0, lambda: self._actualizar_progreso(total, 100))
        self.root.after(0, destruir_barra)
        
        # Registrar el análisis en el historial con estadísticas por formato
        self.gestor_historial.registrar_analisis(
            carpeta=self.carpeta,
            counts_by_ext=counts_by_ext,
            avg_by_ext=avg_by_ext,
            total_archivos=len(self.resultados)
        )
        
        # Actualiza resultados para mostrar solo nombre, duracion, peso
        self.resultados = [(nombre, duracion, peso) for nombre, duracion, peso, _, _ in resultados]

        tiempo_fin = time.time()  # <-- Añade esto justo antes de actualizar_interfaz
        tiempo_total = tiempo_fin - tiempo_inicio

        def actualizar_interfaz():
            if not self.resultados:
                self.label_resultado.config(text="No se encontraron vídeos válidos.")
                self.boton_grafico["state"] = "disabled"
                self.boton_visual["state"] = "disabled"
                self.boton["state"] = "normal"
                return
            peso_medio = calcular_peso_medio(self.resultados)
            duracion_media = calcular_duracion_media(self.resultados)
            total_archivos = len(self.resultados)
            resultados_text =(f"Peso medio por minuto: {peso_medio:.2f} MB/min"
                     f"   |   Duración media: {duracion_media:.1f} min"
                     f"   |   Total archivos: {total_archivos}"
                     f"   |   Tiempo analizando: {tiempo_total:.1f} s"
                     f"   |   Tiempo por video: {tiempo_total/total_archivos:.2f} s"
                     f"   |   Errores: {int(len(lista_de_errores)/2)}")
            self.label_resultado.config(text=resultados_text)
            self.boton_grafico["state"] = "normal"
            self.boton_histograma["state"] = "normal"
            self.boton["state"] = "normal"
            try:
                self.boton_previsualizar["state"] = "normal"
            except AttributeError:
                pass

            # Habilitar/deshabilitar botón Boxplot según número de ratios válidos
            # Condición: necesitamos al menos 3 vídeos con duración > 0
            # para que el boxplot tenga sentido
            valid_ratios_count = sum(1 for _, dur, _ in self.resultados if dur and dur > 0)
            if valid_ratios_count >= 3:
                self.boton_boxplot["state"] = "normal"
            else:
                self.boton_boxplot["state"] = "disabled"
                # Add a lightweight tooltip explaining the requirement (appears on hover)
                ToolTip(self.boton_boxplot,
                        "Se necesitan al menos 3 vídeos con duración > 0 para mostrar el boxplot.")

            # --- Cambia el estado y tooltip del botón Visual según el número de archivos ---
            if total_archivos > 100:
                self.boton_visual["state"] = "disabled"
                ToolTip(self.boton_visual, "demasiados videos")
            else:
                self.boton_visual["state"] = "normal"
                # Elimina tooltip si existe (crea uno vacío)
                ToolTip(self.boton_visual, "")
            # Mostrar el resumen final y la sección de destacados en la pestaña Resultados
            destacados = []
            destacados.append("\nArchivos destacados (duración >15 min y ratio <80 MB/min):\n")
            encontrados_destacados = False
            for nombre, duracion, peso in self.resultados:
                if duracion > 15 and (peso / duracion) < 80:
                    destacados.append(f"- {nombre}\t \t{peso/duracion:.2f} MB/min\n")
                    encontrados_destacados = True
            if not encontrados_destacados:
                destacados.append("No hay archivos de más de 15 min menores de 80 MB/min.\n")
            destacados_text = "".join(destacados)
            try:
                self.texto_archivos.config(state="normal")
                self.texto_archivos.delete(1.0, tk.END)
                self.texto_archivos.insert('1.0', resumen_text)
                self.texto_archivos.insert('1.0', destacados_text)
                self.texto_archivos.config(state="disabled")
            except tk.TclError:
                pass

        self.root.after(0, actualizar_interfaz)

    def _actualizar_progreso(self, valor, porcentaje):
        try:
            if self.progress:
                self.progress.config(value=valor)
        except tk.TclError:
            pass  # La barra ya no existe, ignora el error
        self.label_porcentaje.config(text=f"{porcentaje}%")

    def _registrar_video_problema(self, ruta, archivo, motivo):
        """Registra un video como problemático para mostrar/mover luego"""
        carpeta_actual = os.path.basename(os.path.dirname(ruta))
        lista_de_errores.append(carpeta_actual)
        lista_de_errores.append(archivo)
        self.videos_problema.append({
            'ruta': ruta,
            'archivo': archivo,
            'motivo': motivo,
        })

    def _actualizar_botones_problemas(self):
        estado = "normal" if self.videos_problema else "disabled"
        try:
            self.boton_mostrar_problemas["state"] = estado
            self.boton_mover_problemas["state"] = estado
        except tk.TclError:
            pass

    def mostrar_videos_problema(self):
        """Muestra en una ventana los vídeos problemáticos registrados"""
        if not self.videos_problema:
            messagebox.askokcancel("Videos problemáticos",
                                   "No hay vídeos problemáticos registrados.")
            return
        ventana = tk.Toplevel(self.root)
        ventana.title("Vídeos problemáticos")
        ventana.configure(bg=COLOR_FRAME)
        contenedor = ttk.Frame(ventana)
        contenedor.pack(fill="both", expand=True)
        texto = tk.Text(contenedor, height=20, width=100, bg=COLOR_BG, fg=COLOR_TEXT)
        texto.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        texto.config(state="normal")
        for idx, entrada in enumerate(self.videos_problema, 1):
            texto.insert(tk.END, f"{idx}. {entrada['archivo']} - {entrada['motivo']}\n")
            texto.insert(tk.END, f"   {entrada['ruta']}\n\n")
        texto.config(state="disabled")
        scroll = ttk.Scrollbar(contenedor, orient="vertical", command=texto.yview)
        scroll.pack(side="right", fill="y")
        texto.configure(yscrollcommand=scroll.set)

    def mover_videos_problema(self):
        """Mueve manualmente los vídeos problemáticos registrados a la carpeta 'errores'"""
        if not self.videos_problema:
            messagebox.askokcancel("Videos problemáticos",
                                   "No hay vídeos problemáticos registrados.")
            return
        pendientes = list(self.videos_problema)
        movidos = 0
        ya_en_errores = 0
        for entrada in pendientes:
            ruta = entrada['ruta']
            archivo = entrada['archivo']
            parent_basename = os.path.basename(os.path.dirname(ruta)).lower()
            if parent_basename == "errores":
                ya_en_errores += 1
                continue
            if self._mover_archivo_a_errores(ruta, archivo):
                movidos += 1
        self.videos_problema.clear()
        self.root.after(0, self._actualizar_botones_problemas)
        mensaje = f"Movidos {movidos} vídeos a errores." if movidos else "No se movió ningún vídeo."
        if ya_en_errores:
            mensaje += f" {ya_en_errores} ya estaban en 'errores'."
        try:
            self.texto_archivos.config(state="normal")
            self.texto_archivos.insert('1.0', mensaje + "\n")
            self.texto_archivos.config(state="disabled")
        except tk.TclError:
            pass
        messagebox.showinfo("Videos problemáticos", mensaje)

    def mostrar_historial_movimientos(self):
        """Muestra una ventana con el historial de análisis realizados"""
        if not self.gestor_historial.historial:
            messagebox.showinfo("Historial", "No hay análisis registrados aún.")
            return

        ventana = tk.Toplevel(self.root)
        ventana.title("Historial de Análisis")
        ventana.geometry("950x600")
        ventana.configure(bg=COLOR_BG)

        # Frame superior con información
        frame_info = tk.Frame(ventana, bg=COLOR_FRAME)
        frame_info.pack(fill="x", padx=5, pady=5)

        resumen = self.gestor_historial.obtener_resumen()
        label_info = tk.Label(frame_info, text=resumen, bg=COLOR_FRAME,
                              fg=COLOR_LABEL, font=("Arial", 10, "bold"))
        label_info.pack(pady=5)

        # Texto con scroll para mostrar el historial
        frame_texto = ttk.Frame(ventana)
        frame_texto.pack(fill="both", expand=True, padx=5, pady=5)

        texto = tk.Text(frame_texto, height=25, width=110, bg=COLOR_BG, fg=COLOR_TEXT,
                       insertbackground=COLOR_LABEL, state="normal", wrap="word")
        texto.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(frame_texto, orient="vertical", command=texto.yview)
        scroll.pack(side="right", fill="y")
        texto.configure(yscrollcommand=scroll.set)
        texto.config(font=("Consolas", 9))

        # Llenar el texto con el historial de análisis
        for analisis in reversed(self.gestor_historial.historial):
            timestamp = analisis.get('timestamp', 'N/A')
            carpeta = analisis.get('carpeta', 'N/A')
            total_archivos = analisis.get('total_archivos', 0)
            
            # Encabezado del análisis
            linea_encabezado = f"\n{'='*100}\n"
            linea_encabezado += f"📅 {timestamp} | 📁 {carpeta} | 📊 Total: {total_archivos} archivos\n"
            linea_encabezado += f"{'='*100}\n"
            texto.insert(tk.END, linea_encabezado)
            
            # Estadísticas por formato
            stats = analisis.get('estadisticas_por_formato', {})
            if stats:
                texto.insert(tk.END, "Estadísticas por formato:\n")
                for ext in sorted(stats.keys()):
                    cant = stats[ext]['cantidad']
                    ratio = stats[ext]['ratio_promedio_mb_min']
                    linea = f"  {ext:10} │ Cantidad: {cant:4} │ Ratio promedio: {ratio:7.2f} MB/min\n"
                    texto.insert(tk.END, linea)
            else:
                texto.insert(tk.END, "Sin estadísticas disponibles.\n")

        texto.config(state="disabled")

    def deshacer_ultimo_movimiento(self):
        """Deshace el último análisis registrado"""
        exito, mensaje = self.gestor_historial.deshacer_ultimo()

        if exito:
            messagebox.showinfo("Deshacer", f"✓ {mensaje}")
            print(f"Deshacer exitoso: {mensaje}")
            self._habilitar_botones_historial()
        else:
            messagebox.showerror("Error", f"✗ {mensaje}")
            print(f"Error al deshacer: {mensaje}")

    def exportar_historial_csv(self):
        """Exporta el historial a un archivo CSV"""
        if not self.gestor_historial.historial:
            messagebox.showwarning("Historial vacío", "No hay movimientos para exportar.")
            return

        archivo_salida = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"movimientos_historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if archivo_salida:
            exito, mensaje = self.gestor_historial.exportar_csv(archivo_salida)
            if exito:
                messagebox.showinfo("Exportación exitosa", mensaje)
                print(f"CSV exportado: {archivo_salida}")
            else:
                messagebox.showerror("Error en exportación", mensaje)

    def exportar_historial_json(self):
        """Exporta el historial a un archivo JSON"""
        if not self.gestor_historial.historial:
            messagebox.showwarning("Historial vacío", "No hay movimientos para exportar.")
            return

        archivo_salida = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"movimientos_historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if archivo_salida:
            exito, mensaje = self.gestor_historial.exportar_json(archivo_salida)
            if exito:
                messagebox.showinfo("Exportación exitosa", mensaje)
                print(f"JSON exportado: {archivo_salida}")
            else:
                messagebox.showerror("Error en exportación", mensaje)

    def limpiar_historial(self):
        """Limpia todo el historial con confirmación"""
        if not self.gestor_historial.historial:
            messagebox.showinfo("Historial vacío", "No hay movimientos para limpiar.")
            return

        confirmacion = messagebox.askyesno(
            "Confirmar limpieza",
            f"¿Deseas eliminar los {len(self.gestor_historial.historial)} movimientos"
            " registrados?\nEsta acción no se puede deshacer."
        )

        if confirmacion:
            self.gestor_historial.limpiar_historial()
            messagebox.showinfo("Historial", "Historial limpiado correctamente.")
            print("Historial limpiado")
            self._habilitar_botones_historial()

    def _habilitar_botones_historial(self):
        """Habilita los botones de historial si hay datos en el historial"""
        if self.gestor_historial.historial:
            self.boton_mostrar_historial["state"] = "normal"
            self.boton_deshacer["state"] = "normal"
            self.boton_exportar_csv["state"] = "normal"
            self.boton_exportar_json["state"] = "normal"
            self.boton_limpiar_historial["state"] = "normal"
        else:
            self.boton_mostrar_historial["state"] = "disabled"
            self.boton_deshacer["state"] = "disabled"
            self.boton_exportar_csv["state"] = "disabled"
            self.boton_exportar_json["state"] = "disabled"
            self.boton_limpiar_historial["state"] = "disabled"

    def buscar_avis_repetidos(self):
        """Busca archivos .avi que tengan el mismo nombre base pero con diferente extensión
        y los mueve a una carpeta 'repeat'."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return

        extensiones_video = ('.mp4', '.mov', '.mkv', '.wmv', '.flv', '.webm')
        archivos_repetidos = []

        # Recorrer carpeta y subcarpetas
        for root_dir, _, files in os.walk(self.carpeta):
            archivos_avi = [f for f in files if f.lower().endswith('.avi')]

            for archivo_avi in archivos_avi:
                nombre_base = os.path.splitext(archivo_avi)[0]

                # Buscar si existe el mismo nombre con otra extensión
                for archivo in files:
                    if archivo != archivo_avi and os.path.splitext(archivo)[0] == nombre_base:
                        if archivo.lower().endswith(extensiones_video):
                            archivos_repetidos.append((os.path.join(root_dir, archivo_avi),
                                                       root_dir))
                            break

        if not archivos_repetidos:
            print("No se encontraron archivos .avi repetidos.")
            try:
                self.texto_avi.config(state="normal")
                self.texto_avi.insert(tk.END, "No se encontraron archivos .avi repetidos.\n")
                self.texto_avi.config(state="disabled")
            except tk.TclError:
                pass
            #messagebox.askokcancel("Resultado", "No se encontraron archivos .avi repetidos.")
            return

        # Mover archivos repetidos a carpeta 'repeat'
        movidos = 0
        for ruta_avi, carpeta_origen in archivos_repetidos:
            repeat_dir = os.path.join(carpeta_origen, "repeat")
            if not os.path.exists(repeat_dir):
                os.makedirs(repeat_dir)

            nombre_archivo = os.path.basename(ruta_avi)
            destino = os.path.join(repeat_dir, nombre_archivo)

            try:
                shutil.move(ruta_avi, destino)
                movidos += 1
                print(f"Movido: {nombre_archivo} -> repeat/")
                try:
                    self.texto_avi.config(state="normal")
                    self.texto_avi.insert(tk.END, f"Movido: {nombre_archivo} -> {repeat_dir}\n")
                    self.texto_avi.config(state="disabled")
                except tk.TclError:
                    # Ignorar errores de actualización del widget Text
                    # (por ejemplo, si la interfaz se cerró)
                    pass
            except (OSError, shutil.Error) as e:
                print(f"No se pudo mover {nombre_archivo}: {e}")
                try:
                    self.texto_avi.config(state="normal")
                    self.texto_avi.insert(tk.END, f"No se pudo mover {nombre_archivo}: {e}\n")
                    self.texto_avi.config(state="disabled")
                except tk.TclError:
                    # Ignorar errores de actualización del widget Text relacionados con Tkinter
                    pass

        print(f"Se movieron {movidos} archivos .avi repetidos a carpetas 'repeat'.")
        try:
            self.texto_avi.config(state="normal")
            self.texto_avi.insert(tk.END,
                                  f"Se movieron {movidos} archivos .avi repetidos"
                                  " a carpetas 'repeat'.\n")
            self.texto_avi.config(state="disabled")
        except tk.TclError:
            # Ignorar errores específicos de tkinter al actualizar el widget Text
            pass
        #messagebox.askokcancel("Resultado", f"Se movieron {movidos} archivos .avi repetidos.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalizadorVideosApp(root)
    root.mainloop()
