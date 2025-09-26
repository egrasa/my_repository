""" Analizador de vídeos contenidos en una carpeta """

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import time
import os
import shutil
import threading
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

lista_de_errores = list()  # Para almacenar errores únicos
lista_de_analizados = list()  # Para almacenar archivos analizados

def analizar_videos_en_carpeta(carpeta):
    """ Analiza los vídeos en la carpeta especificada y devuelve una lista de tuplas con nombre, 
    duración y peso """
    extensiones_video = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
    archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(extensiones_video)]
    resultados = []
    for archivo in archivos:
        ruta = os.path.join(carpeta, archivo)
        try:
            clip = VideoFileClip(ruta)
            duracion = clip.duration / 60  # minutos
            peso = os.path.getsize(ruta) / (1024 * 1024)  # MB
            resultados.append((archivo, duracion, peso))
            clip.close()
        except (OSError, ValueError) as e:
            lista_de_errores.append(archivo)
            lista_de_errores.append(str(e))
    return resultados

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
    """ Muestra un gráfico de dispersión de duración vs tamaño de los vídeos """
    if not resultados:
        messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
        return
    duraciones = [dur for _, dur, _ in resultados]
    pesos = [peso for _, _, peso in resultados]

    plt.style.use('grayscale')  # Estilo gris
    _, ax = plt.subplots(figsize=(10, max(6, len(resultados) * 0.25)))
    fig = plt.gcf()
    fig.patch.set_facecolor("#e0e0e0")  # Fondo de la figura
    ax.set_facecolor("#887f7f")         # Fondo del subplot

    # Colores: verde si cumple condición de review, azul si no
    colores = ['tab:green' if (dur > 30 and (peso/dur) < 80) else 'tab:blue'
               for dur, peso in zip(duraciones, pesos)]
    ax.scatter(duraciones, pesos, c=colores, s=60, edgecolor='k', alpha=0.6)

    # Etiquetas solo para los que cumplen la condición
    for i, (nombre, dur, peso) in enumerate(resultados):
        if dur > 15 and (peso/dur) < 80:
            ax.annotate(nombre, (dur, peso), fontsize=9, color='green', alpha=0.8)
        elif dur > 15 and (peso/dur) > 200:
            ax.annotate(nombre, (dur, peso), fontsize=9, color='blue', alpha=0.8)

    # Línea de tendencia (sin extremos)
    ratios = [(peso / dur if dur > 0 else 0, idx) for idx,
              (dur, peso) in enumerate(zip(duraciones, pesos))]
    ratios_ordenados = sorted(ratios, key=lambda x: x[0])
    # Solo descartar extremos si hay más de 20 vídeos
    if len(ratios) > 20:
        indices_a_descartar = {ratios_ordenados[0][1],
                               ratios_ordenados[1][1],
                               ratios_ordenados[-1][1],
                               ratios_ordenados[-2][1]}
    else:
        indices_a_descartar = set()
    duraciones_filtradas = [dur for i, dur in enumerate(duraciones) if i not in indices_a_descartar]
    pesos_filtrados = [peso for i, peso in enumerate(pesos) if i not in indices_a_descartar]
    if len(duraciones_filtradas) > 1:
        z = np.polyfit(duraciones_filtradas, pesos_filtrados, 1)
        p = np.poly1d(z)
        ax.plot(duraciones_filtradas, p(duraciones_filtradas),
                "r--", label="Tendencia (sin extremos)")

    # Línea de 80 MB/min
    if duraciones:
        x_vals = [min(duraciones), max(duraciones)]
        y_vals = [x * 80 for x in x_vals]
        ax.plot(x_vals, y_vals, "g-.", label="80 MB/min")

    ax.set_xlabel("Duración (minutos)")
    ax.set_ylabel("Tamaño (MB)")
    ax.set_title(os.path.basename(carpeta) if carpeta else "Duración vs Tamaño de vídeos")
    ax.legend()
    plt.tight_layout()
    plt.show()

class ToolTip:
    """Tooltip para widgets de Tkinter"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        """Muestra el tooltip"""
        lista_de_errores.append(event.widget)
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

    def hide_tip(self, event=None):
        """Oculta el tooltip"""
        lista_de_errores.remove(event.widget)
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
        self.carpeta = None  # Inicializar el atributo carpeta
        self._parar_analisis = False  # Control de parada

        self.root.configure(bg=COLOR_BG)

        # Frame principal para selección de carpeta y análisis
        self.frame_principal = ttk.Frame(master, padding=5)
        self.frame_principal.pack(fill="x", pady=5)

        # --- Fila para selección de carpeta y mostrar ruta ---
        frame_dir = tk.Frame(self.frame_principal, bg=COLOR_FRAME)
        frame_dir.pack(fill="x", pady=2)

        self.boton = tk.Button(frame_dir, text="Carpeta...", width=15,
                               command=self.seleccionar_carpeta, height=2,
                               bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                               activebackground=COLOR_PROGRESS)
        self.boton.pack(side="left", padx=(0, 5))

        self.carpeta_var = tk.StringVar()
        self.label_carpeta = tk.Label(frame_dir, textvariable=self.carpeta_var,
                                      width=60, anchor="w", bg=COLOR_FRAME, fg=COLOR_LABEL)
        self.label_carpeta.pack(side="left", padx=(0, 5), fill="x", expand=True)
        self.label_carpeta.config(text="")  # Inicialmente vacío

        # Botón para iniciar el análisis (se crea aquí, pero se mostrará en la pestaña Resultados)
        self.boton_analizar = tk.Button(frame_dir, text="Analizar", command=self.analizar_carpeta,
                                        bg=COLOR_BUTTON, fg=COLOR_LABEL, width=10,
                                        activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_analizar["state"] = "disabled"

        # Sistema de pestañas
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Pestaña para archivos AVI
        self.frame_avi = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_avi, text="Archivos AVI")

        # Pestaña para gráficos
        self.frame_graficos = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_graficos, text="Gráficos")

        # Pestaña principal con resultados
        self.frame_resultados = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(self.frame_resultados, text="Resultados")

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

        # Botón para ver carpetas vacías
        self.boton_ver_vacias = tk.Button(avi_buttons_frame, text="Ver Vacías", width=15,
                                          command=self.ver_carpetas_vacias, state="disabled",
                                          bg=COLOR_FRAME, fg=COLOR_TEXT,
                                          activebackground=COLOR_PROGRESS)
        self.boton_ver_vacias.pack(side="left", padx=5)

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

        # --- CONTENIDO PESTAÑA GRÁFICOS ---
        graficos_buttons_frame = tk.Frame(self.frame_graficos, bg=COLOR_FRAME)
        graficos_buttons_frame.pack(fill="x", pady=10)

        self.boton_grafico = tk.Button(graficos_buttons_frame, text="Gráfico", relief="ridge",
                                       command=self.mostrar_grafico, width=15,
                                       bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                       activebackground=COLOR_PROGRESS)
        self.boton_grafico.pack(side="left", padx=5)

        self.boton_histograma = tk.Button(graficos_buttons_frame, text="Histograma", width=15,
                                  command=self.mostrar_histograma_duraciones,
                                  bg=COLOR_BUTTON, fg=COLOR_TEXT, relief="ridge",
                                  activebackground=COLOR_PROGRESS, state="disabled")
        self.boton_histograma.pack(side="left", padx=5)

        self.boton_visual = tk.Button(graficos_buttons_frame, text="Visual", width=15,
                                    command=lambda: mostrar_grafico_visual(self.resultados,
                                                                           self.carpeta),
                                    bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                    activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_visual.pack(side="left", padx=5)

        # Nuevo botón: Boxplot de la relación Peso/Duración (MB/min)
        self.boton_boxplot = tk.Button(graficos_buttons_frame, text="Boxplot ratio", width=15,
                                       command=self.mostrar_boxplot_ratio,
                                       bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                       activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_boxplot.pack(side="left", padx=5)

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

        # Botón para abrir la carpeta review
        self.boton_review = tk.Button(carpetas_frame, text="REVIEW", borderwidth=1,
                                      command=self.abrir_review, width=10, relief="flat",
                                      bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT, state="disabled",
                                      activebackground=COLOR_PROGRESS)
        self.boton_review.pack(side="left", padx=5)

        # Botón para abrir la carpeta xcut
        self.boton_xcut = tk.Button(carpetas_frame, text="XCUT", borderwidth=1,
                                    command=self.abrir_xcut, width=10, relief="flat",
                                    bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT, state="disabled",
                                    activebackground=COLOR_PROGRESS)
        self.boton_xcut.pack(side="left", padx=5)

        # Botón para abrir la carpeta errores
        self.boton_abrir_errores = tk.Button(carpetas_frame, text="ERRORES", borderwidth=1,
                                             command=self.abrir_errores, width=10, relief="flat",
                                             bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                                             activebackground=COLOR_PROGRESS, state="disabled")
        self.boton_abrir_errores.pack(side="left", padx=5)

        # Frame para botones adicionales
        extras_frame = tk.Frame(self.frame_resultados, bg=COLOR_FRAME)
        extras_frame.pack(fill="x", pady=5)

        # Botón para búsqueda avanzada
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
                  foreground=[("selected", "#FFFFFF")])
        style.configure("TProgressbar", troughcolor=COLOR_BG,
                        background=COLOR_PROGRESS, bordercolor=COLOR_FRAME,
                        lightcolor=COLOR_PROGRESS, darkcolor=COLOR_PROGRESS)
        style.configure("TLabel", background=COLOR_FRAME, foreground=COLOR_LABEL)
        style.configure("TButton", background=COLOR_BUTTON, foreground=COLOR_BUTTON_TEXT)

    def mostrar_grafico(self):
        """ Llama a la función global mostrar_grafico con los resultados actuales """
        mostrar_grafico(self.resultados, self.carpeta)

    def abrir_review(self):
        """ Abre la carpeta 'review' dentro de la carpeta seleccionada """
        if self.carpeta:
            review_dir = os.path.join(self.carpeta, "review")
            if os.path.exists(review_dir):
                os.startfile(review_dir)
            else:
                messagebox.askokcancel("Info", "La carpeta 'review' no existe aún.")

    def abrir_xcut(self):
        """ Abre la carpeta 'xcut' dentro de la carpeta seleccionada """
        if self.carpeta:
            xcut_dir = os.path.join(self.carpeta, "xcut")
            if os.path.exists(xcut_dir):
                os.startfile(xcut_dir)
            else:
                messagebox.askokcancel("Info", "La carpeta 'xcut' no existe aún.")

    def abrir_errores(self):
        """ Abre la carpeta 'errores' dentro de la carpeta seleccionada """
        if self.carpeta:
            errores_dir = os.path.join(self.carpeta, "errores")
            if os.path.exists(errores_dir):
                os.startfile(errores_dir)
            else:
                messagebox.askokcancel("Info", "La carpeta 'errores' no existe aún.")

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
            self.texto_archivos.insert(tk.END, "Carpetas vacías:\n")
            for carpeta in vacias:
                self.texto_archivos.insert(tk.END, carpeta + "\n")
        else:
            self.texto_archivos.insert(tk.END, "No hay carpetas vacías.\n")
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
            self.boton_review["state"] = "normal"
            self.boton_xcut["state"] = "normal"
            self.boton_avi["state"] = "normal"
            self.boton_print_errores["state"] = "normal"
            self.boton_abrir_errores["state"] = "normal"
            threading.Thread(target=self._analizar_videos_thread, args=(self.carpeta,),
                             daemon=True).start()
        else:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")

    def seleccionar_carpeta(self):
        """ Abre un diálogo para seleccionar una carpeta """
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.carpeta = carpeta
            self.carpeta_var.set(carpeta)
            self.boton["state"] = "normal"
            self.boton_analizar["state"] = "normal"
            self.boton_grafico["state"] = "disabled"
            self.boton_review["state"] = "disabled"
            self.boton_xcut["state"] = "disabled"
            self.boton_avi["state"] = "normal"
            self.boton_ver_vacias["state"] = "normal"
        else:
            self.boton_analizar["state"] = "disabled"
            self.boton_avi["state"] = "disabled"
            self.boton_review["state"] = "disabled"

    def contar_avis_en_subcarpetas(self):
        """Cuenta todos los archivos .avi en la carpeta seleccionada y sus subcarpetas"""
        if not self.carpeta:
            self.label_resultado.config(text="Primero selecciona una carpeta.")
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
        self.label_resultado.config(text=f"Total - {total_avis} - archivos .avi  en "
                                        f"{total_roots} carpetas de ({len(root_list)})")
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
            self.texto_archivos.insert(tk.END, "Carpetas con archivos .avi:\n")
            for carpeta in carpetas_con_avis:
                self.texto_archivos.insert(tk.END, carpeta + "\n")
        else:
            self.texto_archivos.insert(tk.END, "No se encontraron carpetas con archivos .avi.\n")
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

    def mostrar_histograma_duraciones(self):
        """Muestra un histograma de la distribución de duraciones de los vídeos analizados."""
        if not self.resultados:
            messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
            return
        duraciones = [dur for _, dur, _ in self.resultados]
        plt.style.use('ggplot')
        plt.figure(figsize=(10, 6))
        plt.hist(duraciones, bins=20, color='#7289da', edgecolor='black', alpha=0.8)
        plt.xlabel("Duración (minutos)")
        plt.ylabel("Cantidad de vídeos")
        plt.title("Distribución de duraciones de vídeos")
        plt.tight_layout()
        plt.show()

    def mostrar_boxplot_ratio(self):
        """Genera un boxplot de la relación Peso/Duración (MB/min)
        con puntos y outliers anotados. La caja central es semitransparente
        para que se vean todos los puntos debajo / encima."""
        if not self.resultados:
            messagebox.showinfo("Sin datos", "No hay vídeos válidos para graficar.")
            return
        # calcular ratios y mantener nombres para anotaciones
        ratios = []
        labels = []
        for nombre, dur, peso in self.resultados:
            if dur and dur > 0:
                ratio = peso / dur
                ratios.append(ratio)
                labels.append((nombre, ratio))
        if not ratios:
            messagebox.showinfo("Sin datos", "No hay ratios válidos (duración 0).")
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

        # Boxplot con puntos jitter
        _, ax = plt.subplots(figsize=(10, 6))
        # Hacemos la caja semitransparente (alpha) y usamos patch_artist para que se aplique
        box = ax.boxplot(ratios, vert=True, patch_artist=True, showfliers=True,
						 boxprops=dict(facecolor='#9fb3c8', color='#2b5f78', alpha=0.35),
						 medianprops=dict(color='red', linewidth=2),
						 whiskerprops=dict(color='#2B6D8B'),
						 capprops=dict(color='#2B6D8B'),
						 flierprops=dict(marker='D', markerfacecolor='#E76F51', markersize=6,
                       alpha=0.9, markeredgecolor='k'))

        # añadir puntos jitter por encima (zorder alto) para mayor visibilidad
        x = np.random.normal(1, 0.04, size=len(ratios))
        ax.scatter(x, ratios, alpha=0.85, color='#264653', edgecolor='black', s=50, zorder=5)

        ax.set_xticks([1])
        ax.set_xticklabels(['Peso/Duración (MB/min)'])
        ax.set_ylabel('MB por minuto')
        ax.set_title('Boxplot: distribución de Peso/Duración')

        # Si el backend/versión no aplica alpha desde boxprops, aseguramos set_alpha en los patches
        try:
            for patch in box.get('boxes', []):
                patch.set_alpha(0.35)
        except (AttributeError, TypeError) as e:
            # No interrumpir si algo falla al ajustar patches; registrar para depuración
            print(f"Ignoring patch alpha set error: {e}")

        # detectar outliers por IQR y anotarlos
        q1 = np.percentile(ratios, 25)
        q3 = np.percentile(ratios, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = [(n, r) for n, r in labels if r < lower or r > upper]
        if outliers:
            for name, val in outliers:
                ax.annotate(name, (1.02, val), xytext=(8, 0), textcoords='offset points',
							va='center', fontsize=8, color='darkred')

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
                self.texto_archivos.insert(tk.END, "Resultados de búsqueda avanzada:\n")
                for nombre, dur, peso in encontrados:
                    self.texto_archivos.insert(tk.END, f"{nombre}\t{dur:.2f} min\t{peso:.2f} MB\n")
            else:
                self.texto_archivos.insert(tk.END,
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

    def _analizar_videos_thread(self, carpeta):
        """ Función que se ejecuta en un hilo para analizar los vídeos en carpeta y subcarpetas """
        tiempo_inicio = time.time()
        extensiones_video = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
        archivos = []
        rutas_archivos = []
        carpetas_archivos = []
        # Recorrer carpeta y subcarpetas
        for root_dir, _, files in os.walk(carpeta):
            for f in files:
                if f.lower().endswith(extensiones_video):
                    archivos.append(f)
                    rutas_archivos.append(os.path.join(root_dir, f))
                    carpetas_archivos.append(root_dir)
        total = len(rutas_archivos)
        resultados = []
        self.texto_archivos.delete(1.0, tk.END)

        def crear_barra():
            """ Crea la barra de progreso """
            self.progress = ttk.Progressbar(self.frame3, length=800,
                                            mode="determinate", maximum=total)
            self.progress.pack(pady=2)
            self.label_porcentaje.config(text="0%")
            self.frame3.update_idletasks()
        self.root.after(0, crear_barra)

        for idx, (
            archivo, ruta, carpeta_actual
            ) in enumerate(zip(archivos, rutas_archivos, carpetas_archivos), 1):
            if self._parar_analisis:
                break  # Sale del bucle si se pulsó "Parar"
            carpetita = os.path.basename(os.path.dirname(ruta))
            lista_de_analizados.append(archivo)
            self.texto_archivos.config(state="normal")
            self.texto_archivos.insert(tk.END, f"Analizando archivo: {len(lista_de_analizados)} "
                                       f"\n{carpetita} - {archivo}\n")
            #self.texto_archivos.see(tk.END)
            try:
                clip = VideoFileClip(ruta)
                duracion = clip.duration / 60  # minutos
                peso = os.path.getsize(ruta) / (1024 * 1024)  # MB
                if duracion > 0:
                    resultados.append((archivo, duracion, peso, ruta, carpeta_actual))
                clip.close()
                self.texto_archivos.delete(1.0, tk.END)
            except (OSError, ValueError) as e:
                # Si el archivo ya está dentro de una carpeta llamada "errores", no crear ni mover
                parent_basename = os.path.basename(os.path.dirname(ruta)).lower()
                err_msg = str(e)
                # Mostrar/registrar el error en el Text (usar cadena)
                try:
                    self.texto_archivos.insert(tk.END, err_msg + "\n")
                except tk.TclError:
                    # Si no se puede insertar en el Text, seguir sin interrumpir
                    pass
                # Registrar en la lista de errores
                lista_de_errores.append(carpetita)
                lista_de_errores.append(archivo)

                if parent_basename == "errores":
                    # Ya está en la carpeta de errores -> no crear ni mover
                    print(f"Archivo ya en 'errores', no se mueve: {ruta}")
                else:
                    errores_dir = os.path.join(os.path.dirname(ruta), "errores")
                    # Crear la carpeta de errores solo si no existe
                    if not os.path.exists(errores_dir):
                        try:
                            os.makedirs(errores_dir)
                        except (OSError, shutil.Error) as e_mkdir:
                            print(f"No se pudo crear la carpeta 'errores': {e_mkdir}")
                            # No intentar mover si no se puede crear la carpeta
                            continue
                    # Mover el archivo a la carpeta de errores
                    origen_error = ruta
                    destino_error = os.path.join(errores_dir, archivo)
                    try:
                        shutil.move(origen_error, destino_error)
                    except (OSError, shutil.Error) as e2:
                        print(f"Error al mover {archivo} a la carpeta de errores: {e2}")
            porcentaje = int((idx / total) * 100)
            self.root.after(0, lambda val=idx, pct=porcentaje: self._actualizar_progreso(val, pct))
            self.texto_archivos.config(state="disabled")
            if idx % 5 == 0:
                self.root.after(0, self.frame3.update_idletasks)
        self.boton_parar["state"] = "disabled"

        # --- Mover archivos que cumplen la condición a la carpeta "review"
        # o "xcut" en su subcarpeta ---
        for nombre, duracion, peso, ruta, carpeta_actual in resultados:
            # Evita crear review/xcut dentro de review/xcut
            basename_actual = os.path.basename(carpeta_actual).lower()
            if duracion > 15 and (peso / duracion) < 25:
                if basename_actual != "xcut":
                    xcut_dir = os.path.join(carpeta_actual, "xcut")
                else:
                    xcut_dir = carpeta_actual
                if not os.path.exists(xcut_dir):
                    os.makedirs(xcut_dir)
                destino = os.path.join(xcut_dir, nombre)
                try:
                    shutil.move(ruta, destino)
                except (OSError, shutil.Error) as e:
                    print(f"No se pudo mover {nombre}: {e}")
            elif duracion > 30 and (peso / duracion) < 80:
                if basename_actual != "review":
                    review_dir = os.path.join(carpeta_actual, "review")
                else:
                    review_dir = carpeta_actual
                if not os.path.exists(review_dir):
                    os.makedirs(review_dir)
                destino = os.path.join(review_dir, nombre)
                try:
                    shutil.move(ruta, destino)
                except (OSError, shutil.Error) as e:
                    print(f"No se pudo mover {nombre}: {e}")

        def destruir_barra():
            if self.progress is not None:
                lista_de_analizados.clear()
                self.progress.destroy()

        self.root.after(0, lambda: self._actualizar_progreso(total, 100))
        self.root.after(0, destruir_barra)
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
            print(len(resultados_text))
            self.boton_grafico["state"] = "normal"
            self.boton_histograma["state"] = "normal"
            self.boton["state"] = "normal"

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
            # Mostrar solo archivos de más de 15 min y < 80 MB/min
            self.texto_archivos.config(state="normal")
            self.texto_archivos.delete(1.0, tk.END)
            encontrados = False
            for nombre, duracion, peso in self.resultados:
                if duracion > 15 and (peso / duracion) < 80:
                    self.texto_archivos.insert(tk.END,
                                               f"- {nombre}\t \t{peso/duracion:.2f} MB/min\n")
                    encontrados = True
            if not encontrados:
                self.texto_archivos.insert(tk.END,
                                        "No hay archivos de más de 15 min menores de 80 MB/min.")
            self.texto_archivos.config(state="disabled")

        self.root.after(0, actualizar_interfaz)

    def _actualizar_progreso(self, valor, porcentaje):
        try:
            if self.progress:
                self.progress.config(value=valor)
        except tk.TclError:
            pass  # La barra ya no existe, ignora el error
        self.label_porcentaje.config(text=f"{porcentaje}%")

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
