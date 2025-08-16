""" Comparador de Archivos de Texto (CSV)
Este programa permite seleccionar dos archivos csv y comparar datos.
Muestra las palabras repetidas y las similares (70% o más) entre ambos archivos."""

import tkinter as tk
from tkinter import filedialog, messagebox
import csv
import os
from difflib import SequenceMatcher
import matplotlib.pyplot as plt
import numpy as np

# --- Tema oscuro (constantes) y control de palabras fijadas ---
DARK_BG = "#2b2b2b"
WIDGET_BG = "#3a3a3a"
FG_COLOR = "#e0e0e0"
ENTRY_BG = "#1e1e1e"
ENTRY_FG = "#e0e0e0"
TEXT_BG = "black"
TEXT_FG = "#06da06"
TEXT_FG_AZ = "#027fb9"
TEXT_FG_OR = "#f5b030"


# Diccionario global: palabra -> BooleanVar (True = no mover)
pinned_vars = {}

# Palabras predeterminadas para los Checkbuttons
DEFAULT_PINNED_WORDS = ["avi", "review", "errores", "xcut"]

def seleccionar_archivo1():
    """ Abre un cuadro de diálogo para seleccionar el primer archivo CSV """
    archivo = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
    if isinstance(archivo, tuple):
        archivo = archivo[0] if archivo else ""
    if archivo:
        label_archivo1.config(text=os.path.basename(archivo))
        label_archivo1.archivo_path = archivo
        actualizar_totales()

def seleccionar_archivo2():
    """ Abre un cuadro de diálogo para seleccionar el segundo archivo CSV """
    archivo = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
    if isinstance(archivo, tuple):
        archivo = archivo[0] if archivo else ""
    if archivo:
        label_archivo2.config(text=os.path.basename(archivo))
        label_archivo2.archivo_path = archivo
        actualizar_totales()

def analizar_archivos():
    """ Analiza los dos archivos CSV seleccionados y muestra las palabras repetidas y similares """
    archivo1 = getattr(label_archivo1, "archivo_path", "")
    archivo2 = getattr(label_archivo2, "archivo_path", "")
    # Asegurarse de que archivo1 y archivo2 sean cadenas, no tuplas
    if isinstance(archivo1, tuple):
        archivo1 = archivo1[0] if archivo1 else ""
    if isinstance(archivo2, tuple):
        archivo2 = archivo2[0] if archivo2 else ""
    if not archivo1 or not archivo2:
        messagebox.showerror("Error", "Debes seleccionar ambos archivos .csv.")
        return
    if not isinstance(archivo1,
                      str) or not isinstance(archivo2,
                                             str) or not archivo1.lower().endswith(
                                                 '.csv') or not archivo2.lower().endswith('.csv'):
        messagebox.showerror("Error", "Selecciona dos archivos .csv válidos.")
        return

    try:
        palabras1 = set()
        palabras2 = set()
        with open(archivo1, 'r', encoding='utf-8') as f1:
            reader1 = csv.reader(f1)
            for row in reader1:
                if row and row[0].strip():
                    palabras1.add(row[0].strip())
        with open(archivo2, 'r', encoding='utf-8') as f2:
            reader2 = csv.reader(f2)
            for row in reader2:
                if row and row[0].strip():
                    palabras2.add(row[0].strip())

        palabras_repetidas = palabras1 & palabras2

        palabras_similares = set()
        for p1 in palabras1:
            for p2 in palabras2:
                if p1 != p2 and SequenceMatcher(None, p1, p2).ratio() >= 0.7:
                    palabras_similares.add(f"{p1} <-> {p2}")

        resultado_texto.delete(1.0, tk.END)
        resultado_texto.insert(tk.END, "Nombres repetidos:\n")
        resultado_texto.insert(tk.END, ", ".join(sorted(palabras_repetidas)) + "\n\n")
        resultado_texto.insert(tk.END, "Nombres similares (>=70% coincidencia):\n")
        resultado_texto.insert(tk.END, "\n".join(sorted(palabras_similares)))

    except (OSError, csv.Error, UnicodeDecodeError) as e:
        messagebox.showerror("Error", f"No se pudo analizar los archivos:\n{e}")

def graficar_csv(archivo, titulo):
    """ Genera un gráfico de barras horizontal a partir del archivo CSV seleccionado """
    print(archivo)
    print(titulo)
    if not archivo or not archivo.lower().endswith('.csv'):
        messagebox.showerror("Error", "Selecciona un archivo .csv válido.")
        return
    nombres = []
    tamanios = []
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    nombre = row[0].strip()
                    try:
                        tamanio = float(row[1])
                    except ValueError:
                        continue
                    nombres.append(nombre)
                    tamanios.append(tamanio)
        if not nombres or not tamanios:
            messagebox.showinfo("Sin datos", "No hay datos válidos para graficar.")
            return
        nombres, tamanios = zip(*sorted(zip(nombres, tamanios), reverse=True))
        plt.clf()
        plt.barh(nombres, tamanios, color='skyblue', alpha=0.7)
        #plt.xlabel('Tamaño')
        #plt.ylabel('Nombre')
        plt.title(archivo.split('/')[-1] + " - " + titulo)  # Título con el nombre del archivo
        plt.tight_layout()
        plt.show()
    except (OSError, csv.Error, UnicodeDecodeError) as e:
        messagebox.showerror("Error", f"No se pudo graficar el archivo:\n{e}")

def graficar_repetidos():
    """ Genera un gráfico de barras con los nombres repetidos entre los dos archivos CSV """
    archivo1 = getattr(label_archivo1, "archivo_path", "")
    archivo2 = getattr(label_archivo2, "archivo_path", "")
    # Asegurarse de que archivo1 y archivo2 sean cadenas, no tuplas
    if isinstance(archivo1, tuple):
        archivo1 = archivo1[0] if archivo1 else ""
    if isinstance(archivo2, tuple):
        archivo2 = archivo2[0] if archivo2 else ""
    if not archivo1 or not archivo2:
        messagebox.showerror("Error", "Debes seleccionar ambos archivos .csv.")
        return
    if not archivo1.lower().endswith('.csv') or not archivo2.lower().endswith('.csv'):
        messagebox.showerror("Error", "Selecciona dos archivos .csv válidos.")
        return

    try:
        # Obtener nombres repetidos
        valores1 = {}
        with open(archivo1, 'r', encoding='utf-8') as f1:
            reader1 = csv.reader(f1)
            for row in reader1:
                if len(row) >= 2:
                    nombre = row[0].strip()
                    try:
                        tamanio = float(row[1])
                    except ValueError:
                        continue
                    # Acumular si el nombre se repite
                    valores1[nombre] = valores1.get(nombre, 0.0) + tamanio

        valores2 = {}
        with open(archivo2, 'r', encoding='utf-8') as f2:
            reader2 = csv.reader(f2)
            for row in reader2:
                if len(row) >= 2:
                    nombre = row[0].strip()
                    try:
                        tamanio = float(row[1])
                    except ValueError:
                        continue
                    # Acumular si el nombre se repite
                    valores2[nombre] = valores2.get(nombre, 0.0) + tamanio

        repetidos = set(valores1.keys()) & set(valores2.keys())
        if not repetidos:
            messagebox.showinfo("Sin datos", "No hay coincidencias para graficar.")
            return

        nombres = sorted(repetidos)
        tamanios1 = [valores1[n] for n in nombres]
        tamanios2 = [valores2[n] for n in nombres]

        y = np.arange(len(nombres))
        plt.clf()
        plt.barh(y - 0.2, tamanios1, height=0.4, color='salmon',
                 alpha=0.8, label=archivo1.rsplit('/', maxsplit=1)[-1])
        plt.barh(y + 0.2, tamanios2, height=0.4, color='skyblue',
                 alpha=0.8, label=archivo2.rsplit('/', maxsplit=1)[-1])
        plt.yticks(y, nombres)
        #plt.xlabel('Tamaño')
        #plt.ylabel('Nombre (coincidente)')
        #plt.title('Gráfica de Nombres Repetidos (Ambos Archivos)')
        plt.legend()
        plt.tight_layout()
        plt.show()
    except (OSError, csv.Error, ValueError) as e:
        messagebox.showerror("Error", f"No se pudo graficar los repetidos:\n{e}")

# --- NUEVO: gestión de palabras fijadas (no mover) ---
def agregar_palabras_fijadas():
    """
    Añade palabras (separadas por comas/espacios/; ) a la lista de 'no mover'
    y crea su Checkbutton para activar/desactivar la restricción.
    """
    raw = entry_fijar.get().strip()
    if not raw:
        return
    candidatos = [p.strip() for sep in [",", ";"] for p in raw.replace(sep, " ").split()]
    for palabra in candidatos:
        if not palabra:
            continue
        if palabra not in pinned_vars:
            var = tk.BooleanVar(value=True)  # True = fijado (no mover)
            pinned_vars[palabra] = var
            chk = tk.Checkbutton(
                frame_checks,
                text=palabra,
                variable=var,
                bg=DARK_BG,
                fg=FG_COLOR,
                activebackground=DARK_BG,
                activeforeground=FG_COLOR,
                selectcolor=DARK_BG,
                highlightthickness=0,
                anchor="w",
                padx=4
            )
            chk.pack(anchor="w", fill="x")
    entry_fijar.delete(0, tk.END)

def inicializar_palabras_fijadas():
    """Inicializa los Checkbuttons con las palabras predeterminadas."""
    for palabra in DEFAULT_PINNED_WORDS:
        if palabra not in pinned_vars:
            var = tk.BooleanVar(value=True)  # True = fijado (no mover)
            pinned_vars[palabra] = var
            chk = tk.Checkbutton(
                frame_checks,
                text=palabra,
                variable=var,
                bg=DARK_BG,
                fg=FG_COLOR,
                activebackground=DARK_BG,
                activeforeground=FG_COLOR,
                selectcolor=DARK_BG,
                highlightthickness=0,
                anchor="w",
                padx=4
            )
            chk.pack(anchor="w", fill="x")

def actualizar_totales():
    """Actualiza los labels de total para cada archivo CSV seleccionado."""
    archivo1 = getattr(label_archivo1, "archivo_path", "")
    archivo2 = getattr(label_archivo2, "archivo_path", "")
    # Asegurarse de que archivo1 y archivo2 sean cadenas, no tuplas
    if isinstance(archivo1, tuple):
        archivo1 = archivo1[0] if archivo1 else ""
    if isinstance(archivo2, tuple):
        archivo2 = archivo2[0] if archivo2 else ""
    total1 = 0
    total2 = 0
    # Sumar valores del primer archivo
    if isinstance(archivo1, str) and archivo1.lower().endswith('.csv') and os.path.exists(archivo1):
        try:
            with open(archivo1, 'r', encoding='utf-8') as f1:
                reader1 = csv.reader(f1)
                for row in reader1:
                    if len(row) >= 2:
                        try:
                            total1 += float(row[1])
                            #print(row[0], "\t", row[1])
                        except ValueError:
                            continue
        except (OSError, csv.Error, UnicodeDecodeError, ValueError):
            pass
    # Sumar valores del segundo archivo
    if isinstance(archivo2, str) and archivo2.lower().endswith('.csv') and os.path.exists(archivo2):
        try:
            with open(archivo2, 'r', encoding='utf-8') as f2:
                reader2 = csv.reader(f2)
                for row in reader2:
                    if len(row) >= 2:
                        try:
                            total2 += float(row[1])
                        except ValueError:
                            continue
        except (OSError, csv.Error, UnicodeDecodeError, ValueError):
            pass
    label_weight1_total.config(text=f"{total1:.2f} Gb")
    label_weight2_total.config(text=f"{total2:.2f} Gb")
    #peso_total_acumulado = total1 + total2
    #print(f"Peso total acumulado: {peso_total_acumulado:.2f} Gb")


def comprobar_integridad(originales1, originales2, propuesta1, propuesta2):
    """
    Comprueba que la suma de los pesos originales (archivo1 + archivo2)
    es igual a la suma de los pesos de las propuestas (propuesta1 + propuesta2).
    """
    suma_original = sum(originales1.values()) + sum(originales2.values())
    suma_propuesta = sum(propuesta1.values()) + sum(propuesta2.values())
    print(f"Suma original archivos: {suma_original:.2f} Gb")
    print(f"Suma propuesta archivos: {suma_propuesta:.2f} Gb")
    if abs(suma_original - suma_propuesta) < 1e-6:
        print("✅ Integridad OK: No se ha perdido ningún peso en la distribución.")
    else:
        print("⚠️ Integridad ERROR: Hay diferencia en la suma total de pesos.")

# Llama a esta función al final de propuesta_reparto, justo antes de mostrar resultados:
# comprobar_integridad(originales1, originales2, propuesta1, propuesta2)


def propuesta_reparto():
    """Calcula una propuesta de reparto óptimo de elementos entre ambos CSV.
    Para nombres repetidos se suma su peso (peso_csv1 + peso_csv2) y se asigna a un único CSV."""
    print(" ")
    archivo1 = getattr(label_archivo1, "archivo_path", "")
    archivo2 = getattr(label_archivo2, "archivo_path", "")
    if isinstance(archivo1, tuple):
        archivo1 = archivo1[0] if archivo1 else ""
    if isinstance(archivo2, tuple):
        archivo2 = archivo2[0] if archivo2 else ""
    if not archivo1 or not archivo2:
        messagebox.showerror("Error", "Debes seleccionar ambos archivos .csv.")
        return

    # Leer datos de ambos archivos preservando la fuente original
    originales1 = {}  # {nombre: peso}
    originales2 = {}
    suma_peso1 = 0
    suma_peso2 = 0
    try:
        with open(archivo1, 'r', encoding='utf-8') as f1:
            reader1 = csv.reader(f1)
            for row in reader1:
                if len(row) >= 2:
                    try:
                        nombre = row[0].strip()
                        peso = float(row[1])
                        # Acumular si el nombre se repite
                        originales1[nombre] = originales1.get(nombre, 0.0) + peso
                        suma_peso1 += peso
                        #print(nombre, "\t", peso)
                    except ValueError:
                        continue
        with open(archivo2, 'r', encoding='utf-8') as f2:
            reader2 = csv.reader(f2)
            for row in reader2:
                if len(row) >= 2:
                    try:
                        nombre = row[0].strip()
                        peso = float(row[1])
                        # Acumular si el nombre se repite
                        originales2[nombre] = originales2.get(nombre, 0.0) + peso
                        suma_peso2 += peso
                        #print(nombre)
                    except ValueError:
                        continue
    except (OSError, csv.Error, UnicodeDecodeError, ValueError) as e:
        messagebox.showerror("Error", f"No se pudo leer los archivos:\n{e}")
        return

    # Obtener límites de peso
    try:
        extra1 = float(entry_weight1.get()) if entry_weight1.get().strip() else 0
    except ValueError:
        extra1 = 0
    try:
        extra2 = float(entry_weight2.get()) if entry_weight2.get().strip() else 0
    except ValueError:
        extra2 = 0

    total1 = suma_peso1
    total2 = suma_peso2

    limite1 = total1 + extra1
    limite2 = total2 + extra2

    # Encontrar duplicados
    nombres1 = set(originales1.keys())
    nombres2 = set(originales2.keys())
    duplicados = nombres1.intersection(nombres2)

    # Palabras fijadas activas (no mover)
    fijados_activos = {k for k, v in pinned_vars.items() if v.get()}

    # Duplicados que SÍ se pueden combinar (excluye fijados)
    duplicados_movibles = duplicados - fijados_activos

    # contar solo los duplicados
    total_duplicados = sum(originales1[n] + originales2[n] for n in duplicados)
    total_duplicados1 = sum(originales1[n] for n in duplicados)
    total_duplicados2 = sum(originales2[n] for n in duplicados)
    print(f"Peso duplicados CSV1: {total_duplicados1:.2f} Gb")
    print(f"Peso duplicados CSV2: {total_duplicados2:.2f} Gb")
    print(f"peso duplicados: {total_duplicados:.2f} Gb")

    # Quitar duplicados de partida para construir pesos base sin ellos
    propuesta1 = {n: p for n, p in originales1.items() if n not in duplicados}
    propuesta2 = {n: p for n, p in originales2.items() if n not in duplicados}

    peso_actual1 = total1 - total_duplicados1
    peso_actual2 = total2 - total_duplicados2

    # 1) Reponer los duplicados FIJADOS en cada CSV (no se combinan ni se mueven)
    for nombre in sorted(duplicados & fijados_activos):
        p1 = originales1.get(nombre, 0.0)
        p2 = originales2.get(nombre, 0.0)
        if p1:
            propuesta1[nombre] = p1
            peso_actual1 += p1
        if p2:
            propuesta2[nombre] = p2
            peso_actual2 += p2

    # 2) Asignar duplicados MOVIBLES sumando pesos y eligiendo destino
    asignacion_duplicados = {}
    total_p1 = 0
    total_p2 = 0
    totales = 0
    for nombre in sorted(duplicados_movibles):
        p1 = originales1[nombre]
        total_p1 += p1
        p2 = originales2[nombre]
        total_p2 += p2
        peso_total = p1 + p2  # suma de ambos
        totales += peso_total

        cabe1 = (peso_actual1 + peso_total) <= limite1
        cabe2 = (peso_actual2 + peso_total) <= limite2
        if cabe1 and cabe2:
            ratio1 = (peso_actual1 + peso_total) / limite1 if limite1 > 0 else 1e9
            ratio2 = (peso_actual2 + peso_total) / limite2 if limite2 > 0 else 1e9
            destino = 1 if ratio1 <= ratio2 else 2
        elif cabe1:
            destino = 1
        elif cabe2:
            destino = 2
        else:
            exceso1 = (peso_actual1 + peso_total) - limite1
            exceso2 = (peso_actual2 + peso_total) - limite2
            destino = 1 if exceso1 <= exceso2 else 2

        asignacion_duplicados[nombre] = (peso_total, destino)
        if destino == 1:
            propuesta1[nombre] = peso_total
            peso_actual1 += peso_total
        else:
            propuesta2[nombre] = peso_total
            peso_actual2 += peso_total

    print("Peso total duplicados CSV1:", total_p1)
    print("Peso total duplicados CSV2:", total_p2)
    elementos_movidos = []

    # Rebalanceo (evitar mover fijados y duplicados ya combinados cuando no corresponda)
    if peso_actual1 > limite1 or peso_actual2 > limite2:
        # Mover duplicados combinados si hay exceso
        for nombre, (peso_total, destino_actual) in sorted(asignacion_duplicados.items(),
                                                           key=lambda x: -x[1][0]):
            if peso_actual1 <= limite1 and peso_actual2 <= limite2:
                break
            if destino_actual == 1 and peso_actual1 > limite1:
                if (peso_actual2 + peso_total) <= limite2 or (
                    (peso_actual1 - peso_total) - limite1 >
                    (peso_actual2 + peso_total - limite2)
                ):
                    del propuesta1[nombre]
                    propuesta2[nombre] = peso_total
                    peso_actual1 -= peso_total
                    peso_actual2 += peso_total
                    asignacion_duplicados[nombre] = (peso_total, 2)
                    elementos_movidos.append((nombre, "1->2"))
            elif destino_actual == 2 and peso_actual2 > limite2:
                if (peso_actual1 + peso_total) <= limite1 or (
                    (peso_actual2 - peso_total) - limite2 >
                    (peso_actual1 + peso_total - limite1)
                ):
                    del propuesta2[nombre]
                    propuesta1[nombre] = peso_total
                    peso_actual2 -= peso_total
                    peso_actual1 += peso_total
                    asignacion_duplicados[nombre] = (peso_total, 1)
                    elementos_movidos.append((nombre, "2->1"))

    # Segunda fase: mover elementos únicos si persiste exceso (EXCLUYENDO FIJADOS)
    if peso_actual1 > limite1:
        candidatos = [(n, p) for n, p in propuesta1.items()
                      if n not in asignacion_duplicados and n not in fijados_activos]
        candidatos.sort(key=lambda x: -x[1])
        for nombre, p in candidatos:
            if peso_actual1 <= limite1:
                break
            if (peso_actual2 + p) <= limite2:
                del propuesta1[nombre]
                propuesta2[nombre] = p
                peso_actual1 -= p
                peso_actual2 += p
                elementos_movidos.append((nombre, "1->2"))
    if peso_actual2 > limite2:
        candidatos = [(n, p) for n, p in propuesta2.items()
                      if n not in asignacion_duplicados and n not in fijados_activos]
        candidatos.sort(key=lambda x: -x[1])
        for nombre, p in candidatos:
            if peso_actual2 <= limite2:
                break
            if (peso_actual1 + p) <= limite1:
                del propuesta2[nombre]
                propuesta1[nombre] = p
                peso_actual2 -= p
                peso_actual1 += p
                elementos_movidos.append((nombre, "2->1"))

    es_valido = (peso_actual1 <= limite1 and peso_actual2 <= limite2)

    # Salida
    comprobar_integridad(originales1, originales2, propuesta1, propuesta2)
    resultado_texto.delete(1.0, tk.END)
    resultado_texto.insert(tk.END, "Propuesta de distribución (duplicados sumados):\n\n")
    resultado_texto.insert(
        tk.END, f"CSV 1 (límite: {limite1:.2f} Gb, propuesto: {peso_actual1:.2f} Gb)\n")

    for n, p in sorted(propuesta1.items()):
        marca = ""
        if n in duplicados_movibles:
            marca = " [DUP SUMADO]"
        elif n in fijados_activos:
            marca = " [FIJADO]"
        resultado_texto.insert(tk.END, f"  {n} ({p:.2f} Gb){marca}\n")

    resultado_texto.insert(
        tk.END, f"\nCSV 2 (límite: {limite2:.2f} Gb, propuesto: {peso_actual2:.2f} Gb)\n")
    for n, p in sorted(propuesta2.items()):
        marca = ""
        if n in duplicados_movibles:
            marca = " [DUP SUMADO]"
        elif n in fijados_activos:
            marca = " [FIJADO]"
        resultado_texto.insert(tk.END, f"  {n} ({p:.2f} Gb){marca}\n")

    if not es_valido:
        resultado_texto.insert(tk.END, "\n⚠️ No se pudo ajustar dentro de los límites.\n")
        resultado_texto.insert(tk.END, f"Exceso CSV1: {max(0, peso_actual1 - limite1):.2f} Gb\n")
        resultado_texto.insert(tk.END, f"Exceso CSV2: {max(0, peso_actual2 - limite2):.2f} Gb\n")
    elif elementos_movidos:
        resultado_texto.insert(tk.END, f"\nElementos movidos ({len(elementos_movidos)}):\n")
        for nombre, direc in elementos_movidos:
            resultado_texto.insert(tk.END, f"  {nombre} ({direc})\n")
        movidos_a_csv1 = [n for n, d in elementos_movidos if d == "2->1"]
        movidos_a_csv2 = [n for n, d in elementos_movidos if d == "1->2"]
        if movidos_a_csv1:
            resultado_texto.insert(tk.END, f"\nResumen movidos a CSV1 ({len(movidos_a_csv1)}):\n")
            for n in movidos_a_csv1:
                resultado_texto.insert(tk.END, f"  {n}\n")
        if movidos_a_csv2:
            resultado_texto.insert(tk.END, f"\nResumen movidos a CSV2 ({len(movidos_a_csv2)}):\n")
            for n in movidos_a_csv2:
                resultado_texto.insert(tk.END, f"  {n}\n")
    else:
        resultado_texto.insert(tk.END, "\n✓ No se requieren movimientos.\n")


root = tk.Tk()
root.title("Comparador de Archivos CSV")
root.geometry("800x600")
# Aplicar tema oscuro por defecto a widgets nuevos
root.configure(bg=DARK_BG)
root.option_add("*Button.background", WIDGET_BG)
root.option_add("*Button.foreground", FG_COLOR)
root.option_add("*Label.background", DARK_BG)
root.option_add("*Label.foreground", FG_COLOR)
root.option_add("*Entry.background", ENTRY_BG)
root.option_add("*Entry.foreground", ENTRY_FG)
root.option_add("*Checkbutton.background", DARK_BG)
root.option_add("*Checkbutton.foreground", FG_COLOR)

# Marco superior para selección de archivos
frame_top = tk.Frame(root, bg=DARK_BG)
frame_top.pack(pady=10, fill="x")

btn_archivo1 = tk.Button(frame_top, text="Archivo 1 (CSV)", bg=WIDGET_BG,
                         command=seleccionar_archivo1)
btn_archivo1.grid(row=0, column=0, padx=5)
label_archivo1 = tk.Label(frame_top, text="No seleccionado", width=30, anchor="w")
label_archivo1.grid(row=0, column=1, padx=5)

label_weight1 = tk.Label(frame_top, text="espacio libre (Gb):", anchor="w")
label_weight1.grid(row=0, column=4, padx=5)
entry_weight1 = tk.Entry(frame_top, width=8)
entry_weight1.grid(row=0, column=5, padx=5)
label_weight1_total = tk.Label(frame_top, text=" 0 Gb", anchor="w")
label_weight1_total.grid(row=0, column=2, padx=5)

btn_archivo2 = tk.Button(frame_top, text="Archivo 2 (CSV)", bg=WIDGET_BG,
                         command=seleccionar_archivo2)
btn_archivo2.grid(row=1, column=0, padx=5)
label_archivo2 = tk.Label(frame_top, text="No seleccionado", width=30, anchor="w")
label_archivo2.grid(row=1, column=1, padx=5)

label_weight2 = tk.Label(frame_top, text="espacio libre (Gb):", anchor="w")
label_weight2.grid(row=1, column=4, padx=5)
entry_weight2 = tk.Entry(frame_top, width=8)
entry_weight2.grid(row=1, column=5, padx=5)
label_weight2_total = tk.Label(frame_top, text=" 0 Gb", anchor="w")
label_weight2_total.grid(row=1, column=2, padx=5)

btn_grafica1 = tk.Button(frame_top, text="Gráfica 1", bg=WIDGET_BG,
                         command=lambda: graficar_csv(getattr(label_archivo1,
                                                              "archivo_path", ""),
                                                      "Archivo 1"))
btn_grafica1.grid(row=0, column=3, padx=5, pady=5)

btn_grafica2 = tk.Button(frame_top, text="Gráfica 2", bg=WIDGET_BG,
                         command=lambda: graficar_csv(getattr(label_archivo2,
                                                              "archivo_path", ""),
                                                      "Archivo 2"))
btn_grafica2.grid(row=1, column=3, padx=5, pady=5)

# Marco central para botones de acción
frame_middle = tk.Frame(root, bg=DARK_BG)
frame_middle.pack(pady=10, fill="x")

btn_analizar = tk.Button(frame_middle, text=" ///\tAnalizar",
                         command=analizar_archivos, bg=WIDGET_BG, fg=TEXT_FG_AZ, width=20)
btn_analizar.pack(pady=10, side="left", padx=5)

btn_propuesta = tk.Button(frame_middle, text=" ///\tPropuesta", command=propuesta_reparto,
                          bg=WIDGET_BG, fg=TEXT_FG_OR, width=20)
btn_propuesta.pack(pady=10, side="left")

btn_grafica_repetidos = tk.Button(frame_middle, text=" ///\tGráfica",
                                  command=graficar_repetidos, width=20, bg=WIDGET_BG, fg=FG_COLOR)
btn_grafica_repetidos.pack(pady=5, side="left", padx=5)

# Marco inferior para palabras fijadas y panel de resultados
frame_bottom = tk.Frame(root, bg=DARK_BG)
frame_bottom.pack(pady=10, fill="both", expand=True)

# Submarco izquierdo para Checkbuttons
frame_checks_container = tk.Frame(frame_bottom, bg=DARK_BG)
frame_checks_container.pack(side="left", fill="y", padx=10)

lbl_fijar = tk.Label(frame_checks_container, text="Palabras fijadas \n [para no mover]:")
lbl_fijar.pack(anchor="w", padx=5)
entry_fijar = tk.Entry(frame_checks_container, width=20)
entry_fijar.pack(anchor="w", padx=5, pady=5)
btn_fijar = tk.Button(frame_checks_container, text="Añadir",
                      command=agregar_palabras_fijadas, width=10)
btn_fijar.pack(anchor="w", padx=5, pady=5)

frame_checks = tk.Frame(frame_checks_container, bg=DARK_BG)
frame_checks.pack(fill="both", expand=True, pady=5)

# Submarco derecho para el panel de resultados
frame_text = tk.Frame(frame_bottom, bg=DARK_BG)
frame_text.pack(side="right", fill="both", expand=True, padx=10)

resultado_texto = tk.Text(frame_text, width=80, height=35, bg=TEXT_BG,
                          fg=TEXT_FG, wrap=tk.WORD, insertbackground=TEXT_FG, font=("Consolas", 10))
resultado_texto.pack(fill="both", expand=True, pady=10)

# Inicializar palabras fijadas predeterminadas
inicializar_palabras_fijadas()

root.mainloop()
