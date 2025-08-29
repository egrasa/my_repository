""" Agrupador de Nombres CSV
    Esta aplicación permite seleccionar una carpeta con archivos CSV """

import os
import csv
from collections import Counter, defaultdict
import itertools
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import difflib
import subprocess
import matplotlib.pyplot as plt
import numpy as np

VERSION = 1.1

class AgrupadorApp:
    """ Clase principal de la aplicación para agrupar nombres de archivos CSV """
    def __init__(self, master):
        """ Inicializa la aplicación y crea la interfaz gráfica """
        # Paleta de colores y fuente uniforme
        style = ttk.Style()
        style.theme_use('default')

        # Colores suaves
        color_bg = "#C8C8D6"         # Fondo general
        color_frame = "#acafb9"      # Fondo de frames
        color_accent = "#8ce7e2"     # Botones activos
        color_button = "#bbc7d6"     # Botones normales
        color_button2 = "#bae7d6"    # Botones secundarios
        color_text = "#1b1b4d"       # Texto principal
        color_entry_bg = "#c1dad1"  # Gris claro para cuando está activa

        # Fuente uniforme
        fuente = ("Segoe UI", 10)
        fuente2 = ("Segoe UI", 12)

        # Aplica estilos generales
        style.configure(".", font=fuente, background=color_bg, foreground=color_text)
        style.configure("TFrame", background=color_frame)
        style.configure("TLabel", background=color_frame, foreground=color_text, font=fuente)
        style.configure("TEntry", fieldbackground=color_bg, foreground=color_text, font=fuente2)
        style.configure("TButton", background=color_button, foreground=color_text,
                        font=fuente, padding=6)
        style.configure("alternative.TButton", background=color_button2, foreground=color_text,
                        font=fuente, padding=6)
        style.configure("TLabelframe", background=color_frame, foreground=color_text,
                        font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background=color_frame, foreground=color_text,
                        font=("Segoe UI", 10, "bold"))
        style.configure("Custom.TCheckbutton",
            background=color_frame,
            foreground=color_text,
            font=fuente2)
        style.map("TEntry", fieldbackground=[("disabled", color_bg), ("focus", color_entry_bg)],
                  foreground=[("focus", color_text)])
        style.map("TButton", background=[("active", color_accent), ("disabled", color_frame)])

        self.root = master
        self.root.configure(bg=color_bg)
        self.root.title(f"Agrupador definitivo de Nombres CSV - Versión {VERSION}")
        # Establecer la carpeta por defecto al iniciar
        self.directorio = tk.StringVar(
            value=r"C:\Users\Usuario\OneDrive\Escritorio\info_discos duros\csv")
        self.check_vars = {}
        self.frame_checks = None
        self.porcentaje_labels = {}
        self.nombres_descartar_vars = {}

        # Inicializar atributos usados fuera de __init__
        self._nombre_radar = None
        self._archivos_radar = []

        # Nombres a descartar (pueden ser activados por el usuario)
        self.models = ['dinstar', 'adel1n', 'miadevil', 'emiliaaa', 'dinstar_sp',
                       'dinstar_process', 'dinstar_original', 'dinstar_downloads',
                       'adel1n_sp', 'adel1n_original', 'emiliaaa_sp', 'miadevil_sp', 'Mia_']
        self.assort = ['forcut', 'review', 'variety', 'errores', 'avi_original', 'xcut']
        self.video_formats = ['avi', 'mp4', 'mkv', 'flv', 'mov', 'wmv']
        # Diccionario para agrupar los nombres a descartar por grupo
        self.nombres_descartar_grupos = {
            "Sp_Models": sorted(self.models),
            "Assort": sorted(self.assort),
            "VideoFormats": sorted(self.video_formats)
        }

        # Frame principal horizontal
        frame_main = ttk.Frame(self.root)
        frame_main.pack(fill="both", expand=True)

        # Frame izquierdo (selección de carpeta y archivos)
        frame_left = ttk.Frame(frame_main)
        frame_left.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # Frame derecho para los checkbuttons de nombres a descartar, agrupados por grupo
        self.frame_right = ttk.LabelFrame(frame_main,
                                     text="Nombres \n(activar para INCLUIR)", padding=10)
        # NO se hace .pack todavia, se mostrará al hacer clic en el botón

        # Selección de carpeta
        frame_dir = ttk.Frame(frame_left, padding=10)
        frame_dir.pack(fill="x")
        ttk.Label(frame_dir, text="Carpeta:").pack(side="left")
        # mostrar la carpeta seleccionada como Label (ligado a la misma StringVar)
        ttk.Label(frame_dir, textvariable=self.directorio, width=70,
                  anchor="w").pack(side="left", padx=5)
        self.boton_v = ttk.Button(frame_dir, text="✅", width=4,
                                  style="TButton",
                   command=self.confirmar_carpeta)
        #self.boton_v.pack(side="left", padx=2)

        # Separador visual entre la sección de carpeta y las opciones de CSV
        sep = ttk.Separator(frame_left, orient='horizontal')
        sep.pack(fill='x', padx=8, pady=(4,6))

        frame_csv_select = ttk.Frame(frame_left)
        frame_csv_select.pack(fill="x", pady=(0, 5))
        frame_csv_boton = ttk.Frame(frame_left)
        frame_csv_boton.pack(fill="x", pady=(0, 5))

        # Frame para los checkbuttons de archivos CSV
        self.frame_checks = ttk.LabelFrame(frame_left, text="Selecciona archivos CSV", padding=10)
        self.frame_checks.pack(fill="both", expand=True, padx=10, pady=5)

        # Botones seleccionar/deseleccionar todos los archivos CSV
        self.boton_csv_todos = ttk.Button(frame_left, text="✔️",
                                          width=3, style="alternative.TButton",
                                          command=self.seleccionar_todos_csv,
                                          state="disabled")
        self.boton_csv_todos.pack(side="left", padx=1)
        self.boton_csv_ninguno = ttk.Button(frame_left, text="⬜",
                                            width=3, style="alternative.TButton",
                                            command=self.deseleccionar_todos_csv,
                                            state="disabled")
        self.boton_csv_ninguno.pack(side="left", padx=1)

        # Botón para generar TXT y gráficas
        self.boton_grafica = ttk.Button(frame_left, text="📊 Gráfica",
                                        width=15,
                                        command=self.generar_todo,
                                        state="disabled")
        self.boton_grafica.pack(pady=5, side="left")

        # Botón para buscar nombres con peso 0 en archivos activos
        self.boton_vacias = ttk.Button(frame_left, text="🗂️ vacías",
                                       width=15,
                                       state="disabled",
                                       command=self.buscar_nombres_peso_cero)
        self.boton_vacias.pack(pady=5, side="left")

        # Botón para gráfica radar de pesos por nombre repetido
        self.boton_radar = ttk.Button(frame_left, text="📈 Radar pesos",
                                      width=15,
                                      command=self.graficar_radar_pesos,
                                      state="disabled")
        self.boton_radar.pack(pady=5, side="left")

        # Botón para abrir el archivo nombres_repetidos.txt
        self.boton_abrir_txt = ttk.Button(frame_left, text="📝 Abrir txt",
                                          width=15,
                                          command=self.abrir_txt,
                                          state="disabled")
        self.boton_abrir_txt.pack(pady=5, side="left")

        # Frame derecho para los checkbuttons de nombres a descartar, agrupados por grupo
        self.frame_right = ttk.LabelFrame(frame_main,
                                        text="Nombres \n(activar para INCLUIR)", padding=10)
        # NO se hace .pack todavía, se mostrará al hacer clic en el botón

        # Botones seleccionar/deseleccionar todos los nombres a descartar
        # (DENTRO de self.frame_right)
        frame_nombres_select = ttk.Frame(self.frame_right)
        frame_nombres_select.pack(fill="both", pady=(0, 5), anchor="n")
        self.boton_select_todos = ttk.Button(frame_nombres_select,
                                             text="✔️",
                                             style="alternative.TButton",
                                             width=3,
                                             command=self.seleccionar_todos_nombres,
                                             state="disabled", )
        self.boton_select_todos.pack(side="left", padx=1)
        self.boton_select_ninguno = ttk.Button(frame_nombres_select,
                                               text="⬜",
                                               style="alternative.TButton",
                                               command=self.deseleccionar_todos_nombres,
                                               state="disabled", width=3)
        self.boton_select_ninguno.pack(side="left", padx=1)

        # Crear los checkbuttons por grupo (DENTRO de self.frame_right)
        for grupo, nombres in self.nombres_descartar_grupos.items():
            grupo_frame = ttk.LabelFrame(self.frame_right, text=grupo, padding=5)
            grupo_frame.pack(fill="both", padx=4, pady=4, side="left", anchor="n", expand=True)
            for nombre in nombres:
                nombre_var = tk.BooleanVar(value=False)  # Por defecto desactivados
                chk = ttk.Checkbutton(grupo_frame, text=nombre, variable=nombre_var,
                                      style="Custom.TCheckbutton")
                chk.pack(anchor="w", pady=2)
                self.nombres_descartar_vars[nombre] = nombre_var

        # Entry y botón para buscar archivo CSV y habilitar su checkbutton
        frame_buscar_csv = ttk.Frame(frame_left)
        frame_buscar_csv.pack(fill="x", pady=(0, 5))
        self.label_buscar = ttk.Label(frame_csv_select, text="Buscar...")
        self.entry_buscar_csv = ttk.Entry(frame_csv_select, width=40,
                                          state="disabled", style="TEntry")

        # --- BOTÓN MOSTRAR/OCULTAR frame_right ---
        self.frame_right_visible = False  # Estado de visibilidad
        self.boton_toggle = ttk.Button(frame_csv_select, text="Opciones avanzadas ▶",
                                       command=self.toggle_frame_right, state="disabled")
        self.boton_toggle.pack(pady=5, padx=1, anchor="ne", side="right")

        # Botón limpiar (nuevo)
        self.boton_limpiar = ttk.Button(frame_csv_select, text="🧹", width=3, state="disabled",
                                        command=lambda: self.entry_buscar_csv.delete(0, tk.END))
        self.boton_limpiar.pack(side="right", padx=1)

        self.boton_activar = ttk.Button(frame_csv_select, text="🔍 ver ///", state="disabled",
                    command=self.buscar_y_activar_csv)
        self.boton_activar.pack(side="right", padx=1)
        self.entry_buscar_csv.pack(side="right", padx=5)
        self.label_buscar.pack(side="right", padx=1)

        # Permitir activar con Enter
        self.entry_buscar_csv.bind("<Return>", lambda event: self.buscar_y_activar_csv())
        self.label_peso = ttk.Label(frame_csv_select, text="Peso total: 0.0 GB")
        self.label_peso.pack(pady=5, padx=10, side="left")

        # Botón de ayuda y botón discreto para cambiar carpeta
        self.boton_carpeta = ttk.Button(frame_left, text="📂", width=3,
                                        command=self.seleccionar_carpeta)
        self.boton_carpeta.pack(pady=10, side="right")
        self.boton_ayuda = ttk.Button(frame_left, text="❓ Ayuda", command=self.mostrar_ayuda)
        self.boton_ayuda.pack(pady=10, side="right")

        # Cargar archivos CSV por defecto si la carpeta existe
        if os.path.isdir(self.directorio.get()):
            self.generar_checkbuttons()

    def mostrar_ayuda(self):
        """ Muestra un cuadro de diálogo con información sobre cómo usar la aplicación """
        ayuda_texto = (
            "Esta aplicación permite visualizar nombres de modelos contenidos en archivos CSV "
            "y generar gráficos indicando en que unidades de disco se encuentran esas modelos.\n\n"
            "Funciones principales:\n"
            "1. ✅: Confirma la carpeta por defecto donde se encuentran los archivos CSV\n"
            "2. 📂 Carpeta...: Permite seleccionar una carpeta con archivos "
            "CSV diferente a la predeterminada.\n"
            "3. Selecciona la unidad de disco: Marca las unidades de disco donde deseas buscar.\n"
            "4. 🔍 ver ///: Permite buscar un nombre específico entre todos los archivos.\n"
            "5. 📊 Gráfica: Genera gráficos indicando en que unidades de disco se encuentran "
            "repetidos nombres de modelos.\n"
            "6. 📈 Radar pesos: Muestra un gráfico tipo radar para un nombre específico que este "
            "repetido en al menos 3 unidades de disco diferentes.\n"
            "7. 📝 Abrir txt: Abre el archivo generado tras generar Gráfica con los nombres "
            "repetidos.\n"
            "8. 🗂️ Carpetas vacías: Busca carpetas vacías en los archivos seleccionados.\n"
            "9. ❓ Ayuda: Muestra esta ventana de ayuda.\n\n"
            "Nota: Usa los botones de selección para marcar o desmarcar todos los archivos "
            "o nombres.\n"
            "Puedes configurar mejor la búsqueda indicando nombres a descartar \n"
            "en opciones avanzadas"
        )
        messagebox.askokcancel("Ayuda - Agrupador de Nombres CSV", ayuda_texto)

    def buscar_nombres_peso_cero(self):
        """Busca en los archivos CSV activos todos los nombres 
        con peso 0 y los muestra en un print"""
        carpeta = self.directorio.get()
        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showwarning("Error", "Selecciona una carpeta válida.")
            return
        seleccionados = [archivo for archivo, var in self.check_vars.items() if var.get()]
        if not seleccionados:
            messagebox.askokcancel("Sin selección", "Selecciona al menos un archivo CSV.")
            return

        nombres_peso_cero = defaultdict(list)
        for archivo in seleccionados:
            ruta = os.path.join(carpeta, archivo)
            try:
                with open(ruta, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for fila in reader:
                        if len(fila) >= 2:
                            try:
                                peso = float(fila[1])
                                if peso == 0:
                                    nombres_peso_cero[archivo].append(fila[0])
                            except ValueError:
                                continue
            except (OSError, IOError, csv.Error) as e:
                print(f"Error leyendo {archivo}: {e}")
                messagebox.askokcancel("Error", f"No se pudo leer el archivo {archivo}.\n{e}")

        print("\n--- carpetas vacias ---")
        for archivo, nombres in nombres_peso_cero.items():
            print(f"{os.path.splitext(archivo)[0]}: {', '.join(nombres) if nombres else 'Ninguno'}")

    def confirmar_carpeta(self):
        """Confirma la dirección escrita en el entry y actualiza los checkbuttons"""
        carpeta = self.directorio.get()
        if carpeta and os.path.isdir(carpeta):
            self.generar_checkbuttons()
        else:
            messagebox.showerror("Error", "La carpeta escrita no es válida.")

    def toggle_frame_right(self):
        """ Alterna la visibilidad del frame derecho """
        if self.frame_right_visible:
            self.frame_right.pack_forget()
            self.boton_toggle.config(text="Mostrar avanzadas ▶")
            self.frame_right_visible = False
        else:
            self.frame_right.pack(side="right", fill="y", padx=5, pady=5)
            self.boton_toggle.config(text="Ocultar avanzadas ◀")
            self.frame_right_visible = True

    def buscar_y_activar_csv(self):
        """ Busca un archivo CSV por palabra y activa su checkbutton si lo encuentra """
        self.deseleccionar_todos_csv()
        palabra = self.entry_buscar_csv.get().strip().lower()
        if not palabra:
            self._mostrar_mensaje_buscar_palabra()
            return

        carpeta = self.directorio.get()
        if not carpeta or not os.path.isdir(carpeta):
            self._manejar_carpeta_invalida()
            return

        encontrado, suma_pesos_por_archivo, archivos_con_palabra = (
            self._procesar_archivos_csv(palabra, carpeta))
        self._actualizar_pesos_y_porcentajes(suma_pesos_por_archivo)
        self._mostrar_resultados_busqueda(palabra, encontrado, archivos_con_palabra)

    def _mostrar_mensaje_buscar_palabra(self):
        """ Muestra un mensaje si no se introduce una palabra para buscar """
        intro_palabra = messagebox.askokcancel("Buscar archivo",
                                               "Introduce una palabra para buscar.")
        if intro_palabra:
            print("Introduce una palabra para buscar...")
            self.entry_buscar_csv.focus_set()

    def _manejar_carpeta_invalida(self):
        """ Maneja el caso en que la carpeta seleccionada no es válida """
        error_carpeta = messagebox.askokcancel("Error",
                                               "Esta carpeta no es válida.\n¿Quieres "
                                               "seleccionar otra?")
        if error_carpeta:
            print("Carpeta no válida, quizás seleccionando otra...")
            self.seleccionar_carpeta()

    def _procesar_archivos_csv(self, palabra, carpeta):
        """ Procesa los archivos CSV para buscar la palabra y calcular pesos """
        encontrado = False
        suma_pesos_por_archivo = {}
        archivos_con_palabra = []
        lista_pesos = []

        for archivo, var in self.check_vars.items():
            ruta = os.path.join(carpeta, archivo)
            suma_peso, archivo_encontrado = self._procesar_archivo_individual(ruta, palabra, var)
            if archivo_encontrado:
                encontrado = True
                archivos_con_palabra.append(archivo)
            if suma_peso > 0:
                suma_pesos_por_archivo[archivo] = suma_peso
                lista_pesos.append(suma_peso)

        total_peso = sum(lista_pesos)
        self.label_peso.config(text=f" Peso total:   {round(total_peso, 2)} GB  ")
        return encontrado, suma_pesos_por_archivo, archivos_con_palabra

    def _procesar_archivo_individual(self, ruta, palabra, var):
        """ Procesa un archivo CSV individual para buscar la palabra y calcular su peso """
        suma_peso = 0.0
        archivo_encontrado = False
        try:
            with open(ruta, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                for fila in reader:
                    if fila and palabra == fila[0].strip().lower():
                        var.set(True)
                        archivo_encontrado = True
                        try:
                            peso = float(fila[1])
                            suma_peso += peso + 0.01
                        except (ValueError, TypeError):
                            pass
        except (OSError, IOError):
            var.set(False)
        return suma_peso, archivo_encontrado

    def _actualizar_pesos_y_porcentajes(self, suma_pesos_por_archivo):
        """ Actualiza los pesos y porcentajes en las etiquetas """
        total_peso = sum(suma_pesos_por_archivo.values())
        for archivo, lbl in self.porcentaje_labels.items():
            if archivo in suma_pesos_por_archivo and total_peso > 0:
                porcentaje = suma_pesos_por_archivo[archivo] * 100 / total_peso
                lbl.config(text=f"{porcentaje:.1f}%")
            elif archivo in self.check_vars and self.check_vars[archivo].get():
                lbl.config(text="0.0%")
            else:
                lbl.config(text="")

    def _mostrar_resultados_busqueda(self, palabra, encontrado, archivos_con_palabra):
        """ Muestra los resultados de la búsqueda en la consola y
        actualiza el estado del botón radar """
        if not encontrado:
            self._sugerir_palabras_similares(palabra)
        else:
            print(f"'{palabra}' encontrado en los archivos: {', '.join(archivos_con_palabra)}")

        if len(set(archivos_con_palabra)) > 2:
            self.boton_radar.config(state="normal")
            self._nombre_radar = palabra
            self._archivos_radar = list(set(archivos_con_palabra))
        else:
            self.boton_radar.config(state="disabled")
            self._nombre_radar = None
            self._archivos_radar = []

    def _sugerir_palabras_similares(self, palabra):
        """ Sugiere palabras similares si no se encuentra la palabra buscada """
        nombres_en_archivos = set()
        for archivo in self.check_vars:
            ruta = os.path.join(self.directorio.get(), archivo)
            try:
                with open(ruta, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for fila in reader:
                        if fila:
                            nombre = fila[0].strip().lower()
                            nombres_en_archivos.add(nombre)
            except (OSError, IOError, csv.Error, UnicodeDecodeError):
                continue
        similares = difflib.get_close_matches(palabra, nombres_en_archivos, n=10, cutoff=0.75)
        if similares:
            print(f"No se encontró '{palabra}'. Palabras parecidas (>75%): {', '.join(similares)}")
            parecida = messagebox.askokcancel("Buscar archivo",
                                              f"No se encontró ningún archivo CSV con '{palabra}'\n"
                                              f"¿Quizás quisiste decir [ {', '.join(similares)} ]?")
            if parecida:
                self.entry_buscar_csv.delete(0, tk.END)
                self.entry_buscar_csv.insert(0, similares[0])
        else:
            print(f"No se encontró '{palabra}' en ningún archivo CSV.")
            messagebox.askokcancel("Buscar archivo",
                                   f"No se encontró '{palabra}' en ningún archivo CSV "
                                   "ni tampoco palabras parecidas.")

    def seleccionar_todos_csv(self):
        """ Selecciona todos los archivos CSV marcando sus checkbuttons """
        for var in self.check_vars.values():
            var.set(True)

    def deseleccionar_todos_csv(self):
        """ Deselecciona todos los archivos CSV desmarcando sus checkbuttons """
        for var in self.check_vars.values():
            var.set(False)

    def seleccionar_todos_nombres(self):
        """ Selecciona todos los nombres a descartar marcando sus checkbuttons """
        for var in self.nombres_descartar_vars.values():
            var.set(True)

    def deseleccionar_todos_nombres(self):
        """ Deselecciona todos los nombres a descartar desmarcando sus checkbuttons """
        for var in self.nombres_descartar_vars.values():
            var.set(False)

    def seleccionar_carpeta(self):
        """ Abre un diálogo para seleccionar una carpeta y actualiza la variable de directorio """
        carpeta = filedialog.askdirectory()
        self.boton_v.config(state="disabled")
        if carpeta:
            self.directorio.set(carpeta)
            self.generar_checkbuttons()  # Actualiza los checkbuttons al seleccionar carpeta

    def generar_checkbuttons(self):
        """ Genera checkbuttons para cada archivo CSV en la carpeta seleccionada, 
        en 2 columnas y añade etiqueta de porcentaje de peso """
        for widget in self.frame_checks.winfo_children():
            widget.destroy()
        self.check_vars.clear()
        self.porcentaje_labels = {}  # Nuevo: guardar referencias a las etiquetas
        self.boton_vacias.config(state="normal")
        self.boton_grafica.config(state="normal")
        self.boton_csv_todos.config(state="normal")
        self.boton_csv_ninguno.config(state="normal")
        self.boton_select_todos.config(state="normal")
        self.boton_select_ninguno.config(state="normal")
        self.entry_buscar_csv.config(state="normal")
        self.boton_activar.config(state="normal")
        self.boton_toggle.config(state="normal")
        self.boton_limpiar.config(state="normal")
        carpeta = self.directorio.get()
        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showerror("Error", "Selecciona una carpeta válida.")
            return
        archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(".csv")]
        if not archivos:
            messagebox.showinfo("Sin archivos", "No se encontraron archivos CSV en la carpeta.")
            return

        col1 = ttk.Frame(self.frame_checks)
        col2 = ttk.Frame(self.frame_checks)
        col1.pack(side="left", fill="both", expand=True)
        col2.pack(side="left", fill="both", expand=True)

        mitad = (len(archivos) + 1) // 2
        for i, archivo in enumerate(archivos):
            frame_fila = ttk.Frame(col1 if i < mitad else col2)
            frame_fila.pack(fill="x", pady=2)
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(frame_fila, text=archivo.split('.')[0], variable=var,
                                   style="Custom.TCheckbutton")
            chk.pack(side="left", anchor="w")
            lbl = ttk.Label(frame_fila, text="")  # Etiqueta vacía al inicio
            lbl.pack(side="left", padx=5)
            self.check_vars[archivo] = var
            self.porcentaje_labels[archivo] = lbl

    def abrir_txt(self):
        """Abre el archivo nombres_repetidos.txt con el programa predeterminado"""
        carpeta = "C:\\Users\\Usuario\\OneDrive\\Escritorio\\info_discos duros\\listados"
        salida = os.path.join(carpeta, "nombres_repetidos.txt")
        if os.path.exists(salida):
            try:
                os.startfile(salida)  # Solo Windows
            except AttributeError:
                subprocess.call(['open', salida])  # Mac
            except OSError:
                subprocess.call(['xdg-open', salida])  # Linux
        else:
            messagebox.showerror("Error", "El archivo nombres_repetidos.txt no existe.")

    def graficar_radar_pesos(self):
        """Genera un gráfico radar solo para el nombre buscado si aparece en más de dos archivos"""
        carpeta = self.directorio.get()
        if not hasattr(self, "_nombre_radar") or not self._nombre_radar or not self._archivos_radar:
            messagebox.showinfo("Sin datos", "Busca un nombre que esté en más de dos archivos.")
            return
        nombre = self._nombre_radar
        archivos = sorted(self._archivos_radar)
        pesos = []
        for archivo in archivos:
            ruta = os.path.join(carpeta, archivo)
            peso = 0
            try:
                with open(ruta, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for fila in reader:
                        if len(fila) >= 2 and fila[0].strip().lower() == nombre:
                            try:
                                peso = float(fila[1])
                            except ValueError:
                                peso = 0
                            break
            except (OSError, IOError, csv.Error, ValueError):
                peso = 0
            pesos.append(peso)
        n1 = len(archivos)
        if n1 < 3:
            messagebox.showinfo("Sin datos", "El nombre debe estar en más de dos archivos.")
            return
        angles = np.linspace(0, 2 * np.pi, n1, endpoint=False).tolist()
        pesos += pesos[:1]
        angles += angles[:1]
        _, ax = plt.subplots(subplot_kw={'polar': True})
        ax.plot(angles, pesos, 'o-', linewidth=2, label=nombre)
        ax.fill(angles, pesos, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(archivos, fontsize=10)
        plt.style.use('seaborn-v0_8-darkgrid')  # Estilo
        plt.title(f"Pesos de '{nombre}' en archivos")
        plt.tight_layout()
        plt.show()

    def generar_todo(self):
        """ Agrupa nombres de archivos CSV, genera un TXT y muestra gráficas """
        carpeta = self.directorio.get()
        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showerror("Error", "Selecciona una carpeta válida.")
            return
        seleccionados = [archivo for archivo, var in self.check_vars.items() if var.get()]
        if not seleccionados:
            messagebox.askokcancel("Sin selección", "Selecciona al menos un archivo CSV.")
            return

        # --- Lógica de agrupación y graficado ---
        nombres_validos = []
        nombre_archivos = defaultdict(set)
        pesos_por_archivo = {}  # Nuevo: para guardar el peso total por archivo

        for archivo in seleccionados:
            ruta = os.path.join(carpeta, archivo)
            peso_total = 0.0  # Acumulador de peso para este archivo
            try:
                with open(ruta, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    filas = list(reader)
            except (OSError, IOError, csv.Error) as e:
                print(f"Error leyendo {archivo}: {e}")
                messagebox.showwarning("Archivo omitido", f"No se pudo leer {archivo}.\n{e}")
                continue
            if not filas:
                print(f"Archivo vacío: {archivo}")
                continue
            datos = filas[1:] if filas and not filas[0][0].isdigit() else filas
            for fila in datos:
                if len(fila) >= 2:
                    try:
                        peso = float(fila[1])
                        if peso >= 0:
                            nombre = fila[0]
                            nombres_validos.append(nombre)
                            nombre_archivos[nombre].add(archivo)
                            peso_total += peso  # Sumar peso
                    except ValueError:
                        continue
            pesos_por_archivo[archivo] = peso_total  # Guardar el peso total de este archivo

        # Imprimir el peso total de cada archivo en la terminal
        print("\n--- Peso total por archivo (TB) ---\n")
        for archivo, peso in pesos_por_archivo.items():
            print(f"{archivo.split('.')[0]}:     {round(peso/1000, 2)} TB")

        # Lista de nombres a descartar según los checkbuttons
        nombres_descartar = {nombre for nombre,
                             var in self.nombres_descartar_vars.items() if not var.get()}

        conteo = Counter(nombres_validos)
        repetidos = [
            nombre for nombre, count in conteo.items()
            if count > 1 and nombre.lower() not in nombres_descartar
        ]
        repetidos_info = [
            (nombre, sorted(nombre_archivos[nombre]))
            for nombre in repetidos
        ]
        repetidos_info.sort(key=lambda x: len(x[1]), reverse=True)

        # Guardar en TXT
        carpeta_salida = "C:\\Users\\Usuario\\OneDrive\\Escritorio\\info_discos duros\\listados"
        salida = os.path.join(carpeta_salida, "nombres_repetidos.txt")
        with open(salida, "w", encoding="utf-8") as f:
            for nombre, archivos in repetidos_info:
                f.write(f"{nombre} -> {', '.join(archivos)}\n")
        print(" ")
        print("TXT generado en: ", carpeta_salida)

        # Habilitar el botón para abrir el archivo
        self.boton_abrir_txt["state"] = "normal"

        # Graficar (una sola gráfica)
        archivos_unicos = sorted({archivo for _,
                                  archivos in repetidos_info for archivo in archivos})
        colores = plt.colormaps.get_cmap('tab10').resampled(len(archivos_unicos))
        marcadores = ['o', 's', '^', 'D', 'v', 'P', '*', 'X', 'h', '+', 'x', '1', '2', '3',
                      '4', '8', '<', '>', '|', '_']
        marcadores_ciclo = itertools.cycle(marcadores)
        archivo_estilo = {}
        for idx, archivo in enumerate(archivos_unicos):
            archivo_estilo[archivo] = {
                "color": colores(idx),
                "marker": next(marcadores_ciclo)
            }

        def scatter_por_nombres(repetidos_parte, estilos_archivo, titulo):
            """Genera un scatter plot de nombres repetidos en archivos CSV"""
            plt.style.use('seaborn-v0_8-darkgrid')  # Estilo
            plt.figure(figsize=(max(10, len(archivos_unicos) // 2), 8))
            for nombre_rep, archivos_rep in repetidos_parte:
                for archivo_rep in archivos_rep:
                    estilo = estilos_archivo[archivo_rep]
                    # Buscar el peso asociado a ese nombre en ese archivo
                    peso = None
                    ruta = os.path.join(carpeta, archivo_rep)
                    try:
                        with open(ruta, newline="", encoding="utf-8") as f:
                            reader = csv.reader(f)
                            for fila in reader:
                                if len(fila) >= 2 and fila[0] == nombre_rep:
                                    try:
                                        peso = float(fila[1])
                                    except (ValueError, TypeError):
                                        peso = None
                                    break
                    except (ValueError, TypeError):
                        peso = None
                    plt.scatter(
                        archivo_rep, nombre_rep,
                        color=estilo["color"],
                        marker=estilo["marker"],
                        label=(archivo_rep if archivo_rep not in
                               plt.gca().get_legend_handles_labels()[1] else "")
                    )
                    # Añadir etiqueta con el peso
                    if peso is not None:
                        plt.text(
                            archivo_rep, nombre_rep,
                            peso,
                            fontsize=8,
                            ha='left',
                            va='bottom'
                        )
            plt.xlabel("Archivo CSV")
            plt.ylabel("Nombre repetido")
            plt.title(titulo)
            plt.xticks(rotation=90)
            plt.tight_layout()
            plt.legend(title="Archivo", bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.show()

        if repetidos_info:
            scatter_por_nombres(repetidos_info, archivo_estilo,
                                "Nombres repetidos en archivos seleccionados")


if __name__ == "__main__":
    root = tk.Tk()
    app = AgrupadorApp(root)
    root.mainloop()
