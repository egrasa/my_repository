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

class AgrupadorApp:
    """ Clase principal de la aplicación para agrupar nombres de archivos CSV """
    def __init__(self, master):
        self.root = master
        self.root.title("Agrupador definitivo de Nombres CSV")
        # Establecer la carpeta por defecto al iniciar
        self.directorio = tk.StringVar(
            value=r"C:\Users\Usuario\OneDrive\Escritorio\info_discos duros\csv")
        self.check_vars = {}
        self.frame_checks = None
        self.porcentaje_labels = {}

        # Nombres a descartar (pueden ser activados por el usuario)
        self.models = ['dinstar', 'adel1n', 'miadevil', 'emiliaaa', 'dinstar_sp',
                       'dinstar_process', 'dinstar_original', 'dinstar_downloads',
                       'adel1n_sp', 'emiliaaa_sp', 'miadevil_sp', 'Mia_']
        self.assort = ['forcut', 'review', 'variety', 'errores', 'avi', 'mp4',
                       'mkv', 'flv', 'mov', 'wmv', 'avi_original', 'xcut']
        self.video_formats = []
        # Diccionario para agrupar los nombres a descartar por grupo
        self.nombres_descartar_grupos = {
            "Sp_Models": self.models,
            "Assort": self.assort,
            "Video Formats": self.video_formats
        }
        self.nombres_descartar_vars = {}

        # Frame principal horizontal
        frame_main = ttk.Frame(self.root)
        frame_main.pack(fill="both", expand=True)

        # Frame izquierdo (selección de carpeta y archivos)
        frame_left = ttk.Frame(frame_main)
        frame_left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Selección de carpeta
        frame_dir = ttk.Frame(frame_left, padding=10)
        frame_dir.pack(fill="x")
        ttk.Label(frame_dir, text="Carpeta:").pack(side="left")
        ttk.Entry(frame_dir, textvariable=self.directorio,
                  state="disabled", width=70).pack(side="left", padx=5)
        self.boton_v = ttk.Button(frame_dir, text="V", width=3, style="alternative.TButton",
                   command=self.confirmar_carpeta)
        self.boton_v.pack(side="left", padx=2)
        ttk.Button(frame_dir, text="Carpeta...", command=self.seleccionar_carpeta).pack(side="left")

        frame_csv_select = ttk.Frame(frame_left)
        frame_csv_select.pack(fill="x", pady=(0, 5))
        frame_csv_boton = ttk.Frame(frame_left)
        frame_csv_boton.pack(fill="x", pady=(0, 5))

        # Botón para leer archivos y generar checkbuttons
        #self.leer_csv = ttk.Button(frame_dir, text="Leer CSV", state="disabled",
                   #command=self.generar_checkbuttons)
        #self.leer_csv.pack(pady=5, side="left")

        # Frame para los checkbuttons de archivos CSV
        self.frame_checks = ttk.LabelFrame(frame_left, text="Selecciona archivos CSV", padding=10)
        self.frame_checks.pack(fill="both", expand=True, padx=10, pady=5)

        # Botones seleccionar/deseleccionar todos los archivos CSV
        self.boton_csv_todos = ttk.Button(frame_csv_boton, text="todos",
                   command=self.seleccionar_todos_csv, state="disabled")
        self.boton_csv_todos.pack(side="left", padx=1)
        self.boton_csv_ninguno = ttk.Button(frame_csv_boton, text="ninguno",
                   command=self.deseleccionar_todos_csv, state="disabled")
        self.boton_csv_ninguno.pack(side="left", padx=1)

        # Botón para generar TXT y gráficas
        self.boton_grafica = ttk.Button(frame_left, text="Gráfica",
                   command=self.generar_todo, state="normal")
        self.boton_grafica.pack(pady=10, side="left")

        # Botón para gráfica radar de pesos por nombre repetido
        self.boton_radar = ttk.Button(frame_left, text="Radar pesos",
                    command=self.graficar_radar_pesos, state="disabled")
        self.boton_radar.pack(pady=10, side="left")

        # Botón para abrir el archivo nombres_repetidos.txt
        self.boton_abrir_txt = ttk.Button(frame_left, text="Abrir txt",
                                          command=self.abrir_txt, state="disabled",)
        self.boton_abrir_txt.pack(pady=10, side="left")

        # Botón para buscar nombres con peso 0 en archivos activos
        self.boton_vacias = ttk.Button(frame_left, text="carpetas vacías", state="disabled",
                   command=self.buscar_nombres_peso_cero)
        self.boton_vacias.pack(pady=10, side="left")

        # Frame derecho para los checkbuttons de nombres a descartar, agrupados por grupo
        frame_right = ttk.LabelFrame(frame_main,
                                     text="Nombres \n(activar para INCLUIR)", padding=10)
        frame_right.pack(side="right", fill="y", padx=5, pady=5)

        # Botones seleccionar/deseleccionar todos los nombres a descartar
        frame_nombres_select = ttk.Frame(frame_right)
        frame_nombres_select.pack(fill="x", pady=(0, 5))
        self.boton_select_todos = ttk.Button(frame_nombres_select, text="todos",
                   command=self.seleccionar_todos_nombres, state="disabled")
        self.boton_select_todos.pack(side="left", padx=1)
        self.boton_select_ninguno = ttk.Button(frame_nombres_select, text="ninguno",
                   command=self.deseleccionar_todos_nombres, state="disabled")
        self.boton_select_ninguno.pack(side="left", padx=1)

        # Crear los checkbuttons por grupo
        for grupo, nombres in self.nombres_descartar_grupos.items():
            grupo_frame = ttk.LabelFrame(frame_right, text=grupo, padding=5)
            grupo_frame.pack(fill="x", padx=5, pady=5, side="left")
            for nombre in nombres:
                var = tk.BooleanVar(value=False)  # Por defecto desactivados
                chk = ttk.Checkbutton(grupo_frame, text=nombre, variable=var)
                chk.pack(anchor="w", pady=2)
                self.nombres_descartar_vars[nombre] = var

        # Entry y botón para buscar archivo CSV y habilitar su checkbutton
        frame_buscar_csv = ttk.Frame(frame_left)
        frame_buscar_csv.pack(fill="x", pady=(0, 5))
        self.label_buscar = ttk.Label(frame_csv_select, text="Buscar...")
        self.entry_buscar_csv = ttk.Entry(frame_csv_select, width=40, state="disabled")
        self.boton_activar = ttk.Button(frame_csv_select, text="activar", state="disabled",
                   command=self.buscar_y_activar_csv)
        self.boton_activar.pack(side="right", padx=10)
        self.entry_buscar_csv.pack(side="right", padx=5)
        self.label_buscar.pack(side="right", padx=5)

        # Permitir activar con Enter
        self.entry_buscar_csv.bind("<Return>", lambda event: self.buscar_y_activar_csv())
        self.label_peso = ttk.Label(frame_csv_boton, text="Peso total: 0.0 GB")
        self.label_peso.pack(pady=5, padx=10, side="right")

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
            print(f"{archivo.split('.')[0]}: {', '.join(nombres) if nombres else 'Ninguno'}")

    def confirmar_carpeta(self):
        """Confirma la dirección escrita en el entry y actualiza los checkbuttons"""
        carpeta = self.directorio.get()
        if carpeta and os.path.isdir(carpeta):
            self.generar_checkbuttons()
        else:
            messagebox.showerror("Error", "La carpeta escrita no es válida.")

    def buscar_y_activar_csv(self):
        """ Busca un archivo CSV por palabra y activa su checkbutton si lo encuentra """
        palabra = self.entry_buscar_csv.get().strip().lower()
        if not palabra:
            intro_palabra = messagebox.askokcancel("Buscar archivo",
                                                "Introduce una palabra para buscar.")
            if intro_palabra:
                print("Introduce una palabra para buscar...")
                self.entry_buscar_csv.focus_set()
            return
        carpeta = self.directorio.get()
        if not carpeta or not os.path.isdir(carpeta):
            error_carpeta = messagebox.askokcancel("Error", "Esta carpeta no es válida.\n"
                                                "quieres seleccionar otra?")
            if error_carpeta:
                print("Carpeta no válida, quizas seleccionando otra...")
                self.seleccionar_carpeta()
            return
        encontrado = False
        suma_pesos_por_archivo = {}
        lista_pesos = []
        nombres_en_archivos = set()
        archivos_con_palabra = []

        for archivo, var in self.check_vars.items():
            ruta = os.path.join(carpeta, archivo)
            suma_peso = 0.0
            try:
                with open(ruta, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for fila in reader:
                        if fila and fila[0]:
                            nombres_en_archivos.add(fila[0].strip().lower())
                        if fila and palabra == fila[0].strip().lower():
                            var.set(True)
                            encontrado = True
                            archivos_con_palabra.append(archivo)
                            try:
                                peso = float(fila[1])
                                suma_peso += peso + 0.01
                            except (ValueError, TypeError):
                                pass
                    if suma_peso == 0:
                        var.set(False)
                    elif suma_peso == 0.01:
                        respuesta = messagebox.askokcancel("Buscar archivo",
                                            f"La palabra {palabra} existe en el archivo {archivo}"
                                            ", pero parece no tener datos.\n"
                                            " ¿Deseas activar el checkbutton?")
                        if respuesta:
                            var.set(True)
                        else:
                            var.set(False)
                if suma_peso > 0.01:
                    suma_pesos_por_archivo[archivo] = suma_peso
                    lista_pesos.append(suma_peso)
            except (OSError, IOError):
                var.set(False)
        total_peso = sum(lista_pesos)
        self.label_peso.config(text=f" Peso total:   {round(total_peso, 2)} GB  ")
        for archivo, lbl in self.porcentaje_labels.items():
            if archivo in suma_pesos_por_archivo and total_peso > 0:
                porcentaje = suma_pesos_por_archivo[archivo] * 100 / total_peso
                lbl.config(text=f"{porcentaje:.1f}%")
            elif archivo in self.check_vars and self.check_vars[archivo].get():
                lbl.config(text="0.0%")
            else:
                lbl.config(text="")
        if suma_pesos_por_archivo:
            print(' ')
            for archivo, suma in suma_pesos_por_archivo.items():
                print(f"'{palabra}' en {archivo.split('.')[0]}:  "
                    f"{round(suma, 2)} GB -- {round(suma*100/total_peso, 1)} %")
        if not encontrado:
            similares = difflib.get_close_matches(palabra, nombres_en_archivos, n=10, cutoff=0.8)
            if similares:
                print(f"No se encontró '{palabra}'. "
                    f"Palabras parecidas (>80%): {', '.join(similares)}")
                parecida = messagebox.askokcancel("Buscar archivo",
                                f"No se encontró ningún archivo CSV con '{palabra}\n'"
                                f"quizas quisite decir [ {', '.join(similares)} ]")
                if parecida:
                    self.entry_buscar_csv.delete(0, tk.END)
                    self.entry_buscar_csv.insert(0, similares[0])
            else:
                print(f"No se encontró '{palabra}' en ningún archivo CSV.")
                messagebox.askokcancel("Buscar archivo",
                                    f"No se encontró '{palabra}' en ningún archivo CSV."
                                    " ni tampoco palabras parecidas.")

        # --- Activar o desactivar el botón radar según condición ---
        if len(set(archivos_con_palabra)) > 2:
            self.boton_radar.config(state="normal")
            self._nombre_radar = palabra  # Guardar el nombre buscado para el radar
            self._archivos_radar = list(set(archivos_con_palabra))
        else:
            self.boton_radar.config(state="disabled")
            self._nombre_radar = None
            self._archivos_radar = []

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
        self.boton_vacias.config(state="normal")  # Habilitar botón
        self.boton_grafica.config(state="normal")  # Habilitar botón
        self.boton_csv_todos.config(state="normal")  # Habilitar botón
        self.boton_csv_ninguno.config(state="normal")  # Habilitar botón
        self.boton_select_todos.config(state="normal")  # Habilitar botón
        self.boton_select_ninguno.config(state="normal")  # Habilitar botón
        self.entry_buscar_csv.config(state="normal")  # Habilitar entry
        self.boton_activar.config(state="normal")  # Habilitar botón
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
            chk = ttk.Checkbutton(frame_fila, text=archivo.split('.')[0], variable=var)
            chk.pack(side="left", anchor="w")
            lbl = ttk.Label(frame_fila, text="")  # Etiqueta vacía al inicio
            lbl.pack(side="left", padx=5)
            self.check_vars[archivo] = var
            self.porcentaje_labels[archivo] = lbl

    def abrir_txt(self):
        """Abre el archivo nombres_repetidos.txt con el programa predeterminado"""
        carpeta = self.directorio.get()
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
