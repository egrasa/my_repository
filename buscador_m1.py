""" Busca archivos de texto en una carpeta y subcarpetas en busca de una palabra específica. """
import os
import subprocess
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import difflib
import re
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Archivo JSON para historial de últimas búsquedas
HISTORY_FILE = Path(__file__).parent / "search_history.json"
# lista en memoria con el historial (most recent first)
search_history: list[str] = []

# Archivo JSON para palabras en múltiples archivos
MULTI_FILE_WORDS_FILE = Path(__file__).parent / "multi_file_words.json"
palabras_multiples = set()

CARPETA_INICIO = 'C:/Users/Usuario/OneDrive/Escritorio/info_discos duros/csv'

set_busquedas = set()

VERSION = 1.1

def load_history():
    """
    Carga el historial desde JSON (últimas búsquedas).
    Si el archivo no existe o el JSON es inválido, el historial se reinicia silenciosamente.
    """
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                # Actualizar la lista en sitio para evitar rebinding y no necesitar 'global'
                search_history.clear()
                # mantener hasta 10 entradas más recientes
                search_history.extend([str(x) for x in data][:10])
            else:
                search_history.clear()
        else:
            search_history.clear()
    except (OSError, json.JSONDecodeError):
        # Problemas de I/O o JSON inválido: iniciar historial vacío
        search_history.clear()

def save_history():
    """Guarda el historial actual (lista) a JSON."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            # persistir hasta 10 entradas más recientes
            json.dump(search_history[:10], f, ensure_ascii=False, indent=2)
    except OSError:
        # No se pudo escribir el archivo de historial; ignorar silenciosamente
        pass

def update_history(new_word: str):
    """Inserta/mueve new_word al frente del historial y lo persiste."""
    # Normalizar (mantener original pero evitar duplicados por mayúsculas)
    w = str(new_word)
    # Conservar el primer encuentro exacto si existe (ignorando mayúsculas/minúsculas)
    existing = next((x for x in search_history if x.lower() == w.lower()), None)
    if existing:
        search_history.remove(existing)
    # Insertar al frente
    search_history.insert(0, w)
    # Mantener como máximo 10 elementos
    del search_history[10:]
    # Persistir en disco
    save_history()
    # Evitar atrapar excepciones generales comprobando existencia y tipo del widget.
    if 'history_combobox' in globals() and isinstance(history_combobox, ttk.Combobox):
        try:
            history_combobox['values'] = search_history
        except tk.TclError:
            # Si el widget está en un estado inválido (por ejemplo, UI cerrada), ignorar
            pass

def update_history_combobox():
    """Actualiza el Combobox de historial con los valores actuales de
    search_history si el widget existe (muestra hasta 10 entradas)."""
    # Comprobar que el widget existe y es del tipo correcto antes de intentar modificarlo
    if 'history_combobox' in globals() and isinstance(history_combobox, ttk.Combobox):
        try:
            history_combobox['values'] = search_history
        except tk.TclError:
            # Si el widget está en un estado inválido (por ejemplo, UI cerrada),
            # ignorar silenciosamente
            pass

def load_multi_file_words():
    """Carga palabras en múltiples archivos desde JSON."""
    try:
        if MULTI_FILE_WORDS_FILE.exists():
            with open(MULTI_FILE_WORDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                palabras_multiples.clear()
                palabras_multiples.update(data)
    except (OSError, json.JSONDecodeError):
        palabras_multiples.clear()

def save_multi_file_words():
    """Guarda palabras en múltiples archivos a JSON."""
    try:
        with open(MULTI_FILE_WORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(palabras_multiples), f, ensure_ascii=False, indent=2)
    except OSError:
        pass

def carpeta_inicial():
    """ Establece la carpeta inicial para la búsqueda """
    carpeta = CARPETA_INICIO
    if carpeta:
        label_carpeta.config(text=CARPETA_INICIO)
        boton_buscar.config(state="normal")
        entrada_palabra.config(state="normal")
        label_carpeta.config(fg="gray40")
        # cargar historial al activar la UI (si no se ha cargado)
        load_history()
        update_history_combobox()
        load_multi_file_words()
        # poner foco en la entrada de búsqueda al iniciar
        try:
            entrada_palabra.focus_set()
        except Exception:
            pass

def seleccionar_carpeta():
    """ Abre un cuadro de diálogo para seleccionar una carpeta """
    carpeta = filedialog.askdirectory()
    if carpeta:
        label_carpeta.config(text=carpeta)
        boton_buscar.config(state="normal")
        entrada_palabra.config(state="normal")
        label_carpeta.config(fg="darkgreen")
        # dar foco al entry tras seleccionar carpeta
        try:
            entrada_palabra.focus_set()
        except Exception:
            pass

# Diccionario para almacenar el estado de los checkbuttons de archivos
check_vars_archivos = {}

# Diccionario para almacenar los valores por archivo de forma global
valores_por_archivo = {}
# Nuevo: almacenar total de NumFiles por archivo (cuando exista esa columna en los CSV)
archivos_num_files = {}

def buscar_palabra():
    """ Busca la palabra en los archivos de texto de la carpeta y
    subcarpetas (excluyendo comentarios.txt) """
    carpeta = label_carpeta.cget("text")
    palabra = entrada_palabra.get()
    modo = modo_var.get()  # "txt" o "csv"
    if not os.path.isdir(carpeta):
        messagebox.showerror("Error", "La dirección de la carpeta no es válida.")
        return
    if not palabra:
        sin_palabra = messagebox.askokcancel("buscar palabra",
                                             "Debe ingresar una palabra para buscar.")
        if sin_palabra:
            entrada_palabra.focus()
        return
    # registrar búsqueda en historial (mover al frente, mantener max 5)
    update_history(palabra)
    update_history_combobox()

    results = []
    valores_por_archivo.clear()  # Limpiar antes de cada búsqueda
    nombres_en_archivos = set()
    resultados_encontrados = 0
    archivos_con_palabra = set()

    if modo == "txt":
        # Búsqueda en archivos .txt (lógica original)
        for roota, _, files in os.walk(carpeta):
            for nombre_archivo in files:
                # Excluir comentarios.txt de la búsqueda
                if (nombre_archivo.endswith('.txt') and
                    nombre_archivo.lower() != "comentarios.txt" and
                    check_vars_archivos.get(nombre_archivo, tk.BooleanVar(value=True)).get()):
                    ruta_archivo = os.path.join(roota, nombre_archivo)
                    try:
                        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                            lineas = archivo.readlines()
                            ocurrencias = 0
                            valor_total = 0
                            for num_linea, linea in enumerate(lineas, 1):
                                nombre_linea = linea.strip().split()[0] if linea.strip() else ""
                                if nombre_linea:
                                    nombres_en_archivos.add(nombre_linea.lower())
                                if palabra in linea:
                                    results.append(f"{ruta_archivo} -"
                                                   f" Línea {num_linea}: {linea.strip()}")
                                    ocurrencias += 1
                                    ultimo_resultado = results[-1]
                                    valor_resultado = ultimo_resultado.split(":")[-1].strip()
                                    valor_resultado_limpio = valor_resultado.split("GB")[0].strip()
                                    valor_alternativo = ultimo_resultado.split("-")[-1].strip()
                                    valor_alternativo_limpio = valor_alternativo.split(
                                        "GB")[0].strip()
                                    try:
                                        valor_numerico = float(valor_resultado_limpio)
                                        valor_total += valor_numerico
                                    except ValueError:
                                        try:
                                            valor_numerico2 = float(valor_alternativo_limpio)
                                            valor_total += valor_numerico2
                                        except ValueError:
                                            pass
                            if ocurrencias > 0:
                                boton_grafico.config(state="normal")
                                valores_por_archivo[nombre_archivo] = valor_total
                                set_busquedas.add(f"{palabra}, {ocurrencias}, "
                                                  f"{nombre_archivo.split('.')[0]}, "
                                                  f" Valor Total: {valor_total:.2f} GB")
                                resultados_encontrados += 1
                                archivos_con_palabra.add(ruta_archivo)
                    except (UnicodeDecodeError, IOError) as e:
                        print(f"Error leyendo {ruta_archivo}: {e}")
    elif modo == "csv":
        # Búsqueda en archivos .csv
        for roota, _, files in os.walk(carpeta):
            for nombre_archivo in files:
                if (nombre_archivo.endswith('.csv') and
                    check_vars_archivos.get(nombre_archivo, tk.BooleanVar(value=True)).get()):
                    ruta_archivo = os.path.join(roota, nombre_archivo)
                    try:
                        df = pd.read_csv(ruta_archivo, encoding='utf-8')
                        df = df.reset_index(drop=True)  # Asegurar índices 0-based

                        # identificar columna de NumFiles (si existe)
                        num_col_idx = None
                        cols = list(df.columns)
                        # búsqueda por nombre (contiene 'num' y 'file')
                        for i, col in enumerate(cols):
                            cname = str(col).strip().lower()
                            if 'num' in cname and 'file' in cname:
                                num_col_idx = i
                                break
                        # fallback por nombres comunes
                        if num_col_idx is None:
                            for i, col in enumerate(cols):
                                cname = str(col).strip().lower()
                                if cname in ('numfiles', 'num_files', 'nfiles', 'num',
                                             'numero', 'cantidad'):
                                    num_col_idx = i
                                    break
                        # último fallback: si hay al menos 4 columnas,
                        # asumir la 4ª es NumFiles (índice 3)
                        if num_col_idx is None and len(cols) >= 4:
                            num_col_idx = 3

                        # Buscar solo en la primera columna (índice 0)
                        if len(df.columns) > 0:
                            mask = df[df.columns[0]].astype(str).str.contains(palabra,
                                                                             case=False,
                                                                             na=False)
                            filas_coincidentes = df[mask]
                            ocurrencias = len(filas_coincidentes)
                            if ocurrencias > 0:
                                # acumuladores por archivo
                                valor_total = 0.0
                                total_numfiles_for_file = 0
                                for idx, row in filas_coincidentes.iterrows():
                                    # Extraer valor_gb de la segunda columna (índice 1) usando regex
                                    valor_gb = 0.0
                                    if len(df.columns) > 1:
                                        val_str = str(row[df.columns[1]])
                                        match = re.search(r'(\d+\.?\d*)', val_str)
                                        n_buscado = str(row[df.columns[0]])
                                        if match:
                                            try:
                                                valor_gb = float(match.group(1))
                                            except ValueError:
                                                valor_gb = 0.0
                                    # Extraer numero de archivos si hay columna detectada
                                    num_files = 0
                                    if num_col_idx is not None and num_col_idx < len(df.columns):
                                        try:
                                            val_nf = row[df.columns[num_col_idx]]
                                            # intentar convertir a int
                                            # (puede venir como "5" o "5.0")
                                            if pd.isna(val_nf):
                                                num_files = 0
                                            else:
                                                if isinstance(val_nf, (int, float)):
                                                    num_files = int(val_nf)
                                                else:
                                                    num_files = int(float(str(val_nf).strip()))
                                        except (ValueError, TypeError, OverflowError):
                                            # Errores esperables al convertir el valor a número:
                                            # - ValueError: texto no convertible
                                            # - TypeError: valor None u objeto inesperado
                                            # - OverflowError: número fuera de rango al convertir
                                            num_files = 0
                                    total_numfiles_for_file += num_files
                                    # Mostrar resultado claro (índice 1-based para usuario) e
                                    # incluir NumFiles si existe
                                    if num_files:
                                        results.append(f"{os.path.basename(ruta_archivo)} - "
                                                       f"Fila {idx + 1} {n_buscado} - Tamaño:"
                                                       f" {valor_gb:.2f} GB - Files: {num_files}")
                                    else:
                                        results.append(f"{os.path.basename(ruta_archivo)} - "
                                                       f"Fila {idx + 1} {n_buscado} - Tamaño:"
                                                       f" {valor_gb:.2f} GB")
                                    # Agregar a nombres_en_archivos para sugerencias
                                    for val in row.values:
                                        if isinstance(val, str):
                                            nombres_en_archivos.add(val.lower())
                                    valor_total += valor_gb

                                # almacenar totales para este archivo
                                if valor_total > 0:
                                    valores_por_archivo[nombre_archivo] = valor_total
                                if total_numfiles_for_file > 0:
                                    archivos_num_files[nombre_archivo] = total_numfiles_for_file

                                set_busquedas.add(f"{palabra}, {ocurrencias}, "
                                                  f"{nombre_archivo.split('.')[0]}, "
                                                  f" Valor Total: {valor_total:.2f} GB")
                                resultados_encontrados += 1
                                boton_grafico.config(state="normal")
                                archivos_con_palabra.add(ruta_archivo)
                    except (UnicodeDecodeError, pd.errors.ParserError, IOError) as e:
                        print(f"Error leyendo {ruta_archivo}: {e}")

    if results:
        resultado_texto.delete(1.0, tk.END)
        for resultado in results:
            resultado_texto.insert(tk.END, resultado.split("/")[-1].strip() + "\n")
    else:
        similares = difflib.get_close_matches(palabra, nombres_en_archivos, n=10, cutoff=0.8)
        if similares:
            print(f"No se encontró '{palabra}'. Palabras parecidas (>80%): {', '.join(similares)}")
            palabras_parecidas = messagebox.askokcancel("Buscar archivo",
                                    f"No se encontró '{palabra}'. "
                                    f"Quizás quisiste decir: {', '.join(similares)}")
            if palabras_parecidas:
                entrada_palabra.delete(0, tk.END)
                entrada_palabra.insert(0, similares[0])
                buscar_palabra()
        else:
            print(f"No se encontró '{palabra}' ni palabras parecidas en los archivos.")
            messagebox.askokcancel("Buscar archivo",
                                   f"No se encontró '{palabra}' en los archivos ni \n"
                                   "palabras parecidas."
                                   " Intenta con otra \npalabra o verifica"
                                   " la carpeta seleccionada.")
    if resultados_encontrados >= 3:
        boton_grafico_radar.config(state="normal")
    else:
        boton_grafico_radar.config(state="disabled")
    mostrar_resultados_en_label()
    # Después de los loops, después de if results:
    if len(archivos_con_palabra) > 1:
        palabras_multiples.add(palabra.lower())
    else:
        palabras_multiples.discard(palabra.lower())
    save_multi_file_words()

def mostrar_grafico():
    """ Muestra un gráfico de barras horizontal para TXT o de pie para CSV """
    if not valores_por_archivo:
        messagebox.showinfo("Sin datos",
                            "No hay datos para graficar. Realiza una búsqueda primero.")
        return
    modo = modo_var.get()
    if modo == "txt":
        # Gráfico de barras horizontal para TXT
        plt.style.use('grayscale')
        _, ax = plt.subplots(figsize=(10, max(6, len(valores_por_archivo) * 0.25)))
        fig = plt.gcf()
        fig.patch.set_facecolor("#e0e0e0")
        ax.set_facecolor("#cccccc")
        archivos, valores = zip(*sorted(valores_por_archivo.items(), key=lambda x: x[1],
                                        reverse=True))
        for i, v in enumerate(valores):
            plt.text(v, i, f"{v:.2f}", va='center', fontsize=9, color="#2C2929")
        plt.barh(archivos, valores, color="#366381", alpha=0.6)
        plt.ylabel('Archivos', color="#2C2929")
        plt.xlabel('Tamaño (GB)', color="#2C2929")
        plt.title(f"Barras TXT: {entrada_palabra.get()}", color="#2C2929")
        plt.tight_layout()
        plt.show()
    elif modo == "csv":
        # Gráfico de pie para CSV
        archivos, valores = zip(*valores_por_archivo.items())
        plt.figure(figsize=(8, 8))
        plt.pie(valores, labels=archivos, autopct='%1.1f%%', startangle=140)
        plt.title(f"Pie CSV: {entrada_palabra.get()}")
        plt.axis('equal')
        plt.show()

def mostrar_grafico_radar():
    """ Muestra un gráfico radar con los valores por archivo si hay al menos 3 resultados """
    if not valores_por_archivo or len(valores_por_archivo) < 3:
        messagebox.showinfo("Sin datos suficientes",
                            "Se requieren al menos 3 resultados para el radar.")
        return
    archivos, valores = zip(*sorted(valores_por_archivo.items(), key=lambda x: x[1], reverse=True))
    etiquetas = list(archivos)
    datos = list(valores)
    # Radar requiere cerrar el círculo
    datos += datos[:1]
    etiquetas += etiquetas[:1]
    n1 = len(etiquetas)
    angles = np.linspace(0, 2 * np.pi, n1, endpoint=True)
    _, ax = plt.subplots(subplot_kw={'polar': True})
    ax.plot(angles, datos, 'o-', linewidth=2, color="#366381")
    ax.fill(angles, datos, color="#366381", alpha=0.25)
    ax.set_xticks(angles)
    ax.set_xticklabels(etiquetas, fontsize=10)
    plt.title("Radar: " + entrada_palabra.get(), color="#2C2929")
    plt.tight_layout()
    plt.show()

def mostrar_estadisticas():
    """Muestra estadísticas en formato tabla para TXT o con emojis para CSV."""
    if not valores_por_archivo:
        resultado_texto.insert(tk.END, "No hay datos para estadísticas.\n")
        return
    total = sum(valores_por_archivo.values())
    num_archivos = len(valores_por_archivo)
    modo = modo_var.get()
    if modo == "txt":
        texto = "\n--- Estadísticas TXT ---\n"
        texto += f"{'Archivos:':<20} {num_archivos}\n"
        texto += f"{'Total:':<20} {total:.2f} GB\n"
        archivos_ordenados = sorted(valores_por_archivo.items(), key=lambda x: x[1], reverse=True)
        for archivo, valor in archivos_ordenados:
            porcentaje = (valor / total * 100) if total > 0 else 0
            texto += f"{archivo:<20} {porcentaje:.2f}% ({valor:.2f} GB)\n"
    elif modo == "csv":
        texto = "\n--- Estadísticas CSV 📊 ---\n"
        texto += f"📁 Archivos: {num_archivos}\n"
        texto += f"💾 Total: {total:.2f} GB\n"
        archivos_ordenados = sorted(valores_por_archivo.items(), key=lambda x: x[1], reverse=True)
        for archivo, valor in archivos_ordenados:
            porcentaje = (valor / total * 100) if total > 0 else 0
            texto += f"📄 {archivo}: {porcentaje:.2f}% ({valor:.2f} GB)\n"
    resultado_texto.insert(tk.END, texto)

def abrir_modulo_definitivo():
    """Abre el módulo definitivo.py en una nueva ventana"""
    ruta = os.path.join(os.path.dirname(__file__), "../project_gamma/definitivo.py")
    ruta = os.path.abspath(ruta)
    try:
        os.startfile(ruta)  # Solo Windows
    except AttributeError:
        subprocess.call(['open', ruta])  # Mac
    except OSError:
        subprocess.call(['xdg-open', ruta])  # Linux

def print_resultados():
    """ Imprime los resultados del texto y la lista de palabras en múltiples archivos """
    lista_resultado_busquedas = list()
    for resultado in set_busquedas:
        lista_resultado_busquedas.append(resultado)
    lista_resultado_busquedas = sorted(lista_resultado_busquedas)
    for resultado in lista_resultado_busquedas:
        print(resultado)
    print(" ")
    print("Palabras en múltiples archivos:")
    if palabras_multiples:
        for palabra in sorted(palabras_multiples):
            print(f"- {palabra}")
    else:
        print("Ninguna")
    print(" ")

def abrir_ventana_comentario():
    """Abre una ventana emergente para escribir un comentario y guardarlo en comentarios.txt"""
    def guardar_comentario():
        palabra = entrada_palabra.get().strip()
        comentario = entry_comentario.get().strip()
        if palabra and comentario:
            carpeta = label_carpeta.cget("text")
            ruta_comentarios = os.path.join(carpeta, "comentarios.txt")
            print(ruta_comentarios)
            with open(ruta_comentarios, "a", encoding="utf-8") as f:
                f.write(f"{palabra}: {comentario}\n")
            ventana_comentario.destroy()
            messagebox.askokcancel("Comentario guardado", "Comentario guardado correctamente.")
        else:
            messagebox.askokcancel("Faltan datos", "Debes escribir una palabra y un comentario.")

    ventana_comentario = tk.Toplevel(root)
    ventana_comentario.title("Añadir comentario")
    ventana_comentario.geometry("350x120")
    tk.Label(ventana_comentario, text="Comentario para la palabra buscada:").pack(pady=8)
    entry_comentario = tk.Entry(ventana_comentario, width=40)
    entry_comentario.pack(pady=5)
    entry_comentario.bind("<Return>", lambda event: guardar_comentario())
    boton_aceptar = tk.Button(ventana_comentario, text="Aceptar", command=guardar_comentario)
    boton_aceptar.pack(pady=8)

def limpiar_campos():
    """Limpia el campo de búsqueda, los resultados y los comentarios."""
    entrada_palabra.delete(0, tk.END)
    resultado_texto.delete(1.0, tk.END)
    boton_grafico.config(state="disabled")
    # limpiar cualquier cabecera de comentarios dentro del Text
    try:
        # si existe tag 'comment_header', eliminar su rango
        ranges = resultado_texto.tag_ranges('comment_header')
        if ranges:
            resultado_texto.delete(ranges[0], ranges[1])
    except (tk.TclError, AttributeError):
        # Capturar errores específicos relacionados con el widget de Tkinter
        pass

def mostrar_resultados_en_label():
    """Busca la palabra solo en comentarios.txt en la ruta fija 
    y muestra el resultado como cabecera en resultado_texto (se excluye
    la palabra buscada en el texto mostrado)."""
    palabra = entrada_palabra.get().strip().lower()
    ruta_comentarios = os.path.join(CARPETA_INICIO, "comentarios.txt")
    texto = ""
    if os.path.exists(ruta_comentarios):
        resultados = []
        with open(ruta_comentarios, "r", encoding="utf-8") as f:
            for linea in f:
                linea_l = linea.lower()
                # Si se buscó una palabra y está en la línea, procesarla
                if palabra and palabra in linea_l:
                    # Extraer el comentario después del primer ':' si existe
                    partes = linea_l.split(":", 1)
                    if len(partes) == 2:
                        comentario = partes[1].strip()
                    else:
                        comentario = partes[0].strip()
                    # Excluir la palabra buscada del comentario mostrado
                    comentario = comentario.replace(palabra, "").strip(" :\t-")
                    if comentario:
                        resultados.append(comentario)
        # Construir el texto a mostrar: unir con tabulador si hay varios resultados
        if resultados:
            texto = "\t".join(resultados)
        else:
            texto = palabra or ""
    else:
        texto = "No existe comentarios.txt en la ruta fija."

    # insertar/actualizar la cabecera dentro del Text resultado_texto
    header = f"Comentarios: {texto}\n\n" if texto else ""
    try:
        # asegurarnos de que el Text existe
        if resultado_texto.winfo_exists():
            # habilitar temporalmente si está en modo disabled
            prev_state = resultado_texto.cget("state")
            if prev_state == "disabled":
                resultado_texto.configure(state="normal")
            # eliminar cabecera previa si existe
            try:
                prev_ranges = resultado_texto.tag_ranges('comment_header')
                if prev_ranges:
                    resultado_texto.delete(prev_ranges[0], prev_ranges[1])
            except tk.TclError:
                # error relacionado con el widget/text tags: ignorar silenciosamente
                pass
            if header:
                # insertar al principio
                resultado_texto.insert("1.0", header)
                # configurar estilo de la cabecera (si no está configurado)
                try:
                    resultado_texto.tag_configure('comment_header',
                                                  foreground=COLOR_LABEL_COMENT_FG,
                                                  font=("Courier New", 10, "italic"))
                except tk.TclError:
                    # si falla la configuración del tag, no interrumpir
                    pass
                # marcar rango insertado
                end_index = f"1.0 + {len(header)} chars"
                try:
                    resultado_texto.tag_add('comment_header', '1.0', end_index)
                except tk.TclError:
                    # problemas con tag_add: ignorar silenciosamente
                    pass
            # restaurar estado previo
            if prev_state == "disabled":
                resultado_texto.configure(state="disabled")
    except (tk.TclError, AttributeError):
        # en caso de que el widget no esté listo o haya error relacionado con tkinter,
        # fallback: mantener label_comentarios (comportamiento silencioso como antes)
        pass

# Paleta de colores centralizada
COLOR_BG = "#9292A0"
COLOR_BTN_BG = "#909099"
COLOR_BTN_FG = "#353B4D"
COLOR_BTN_LIMPIAR_FG = "#30478D"
COLOR_BTN_SEL_FG = "#13161F"
COLOR_LABEL_BG = "#9292A0"
COLOR_LABEL_FG = "#13161F"
COLOR_LABEL_COMENT_FG = "#D8BA10"
COLOR_ENTRY_BG = "#C4C4CC"
COLOR_ENTRY_FG = "#1A223B"
COLOR_ENTRY_INS = "#aa9696"
COLOR_RESULT_BG = "#3a3939"
COLOR_RESULT_FG = "#03A12B"
COLOR_RESULT_INS = "#8d8686"

# Crear la ventana principal
root = tk.Tk()
root.title("Buscar Modelo")
root.geometry("700x500+1000+200")

# Crear y colocar los widgets
main_frame = tk.Frame(root, borderwidth=0)
main_frame.pack(pady=5, expand=True, fill=tk.BOTH)

beta_frame = tk.Frame(root, borderwidth=0)
beta_frame.pack(pady=2, expand=True, fill=tk.BOTH)

gamma_frame = tk.Frame(root, borderwidth=0)
gamma_frame.pack(pady=2, expand=True, fill=tk.BOTH)

boton_seleccionar = tk.Button(main_frame, text="📂 Seleccionar", borderwidth=0, fg=COLOR_BTN_SEL_FG,
                              width=12, command=seleccionar_carpeta, bg=COLOR_BG)
boton_seleccionar.pack(side=tk.LEFT)

boton_carpeta_inicio = tk.Button(main_frame, text="📁 carpeta sizes", width=14, borderwidth=0,
                                 fg=COLOR_BTN_SEL_FG, command=carpeta_inicial, bg=COLOR_BG)
boton_carpeta_inicio.pack(side=tk.LEFT)

label_carpeta = tk.Label(main_frame, text="No se ha seleccionado carpeta",
                         fg=COLOR_LABEL_FG, width=45, anchor="w", bg=COLOR_LABEL_BG)
label_carpeta.pack(padx=2, side=tk.LEFT)

# Combobox para historial de búsquedas (últimas 5)
history_var = tk.StringVar()
history_combobox = ttk.Combobox(beta_frame, textvariable=history_var, values=[],
                                state="readonly", width=20)
history_combobox.bind("<<ComboboxSelected>>",
                      lambda e: entrada_palabra.delete(0, tk.END) or entrada_palabra.insert(
                          0, history_var.get()))
history_combobox.pack(pady=5, side=tk.LEFT, padx=(4,2))
history_combobox.bind("<Return>", lambda event: boton_buscar.invoke())

# Radiobuttons para seleccionar modo: TXT o CSV
# Cambiado: por defecto CSV en lugar de TXT
modo_var = tk.StringVar(value="csv")
rb_txt = tk.Radiobutton(beta_frame, text="TXT", variable=modo_var, value="txt",
                        bg=COLOR_BG, fg=COLOR_BTN_SEL_FG)
rb_csv = tk.Radiobutton(beta_frame, text="CSV", variable=modo_var, value="csv",
                        bg=COLOR_BG, fg=COLOR_BTN_SEL_FG)
rb_txt.pack(pady=5, side=tk.LEFT, padx=(5,2))
rb_csv.pack(pady=5, side=tk.LEFT, padx=(2,5))

entrada_palabra = tk.Entry(beta_frame, width=30, state="disabled", font=("Courier New", 12),
                           bg=COLOR_ENTRY_BG, fg=COLOR_ENTRY_FG, insertbackground=COLOR_ENTRY_INS)
entrada_palabra.bind("<Return>", lambda event: boton_buscar.invoke())

boton_buscar = ttk.Button(beta_frame, text="🔍 Buscar ...", style="Dark.TButton",
                         state="disabled", command=buscar_palabra)
boton_buscar.pack(pady=5, padx=10, side=tk.RIGHT)
entrada_palabra.pack(pady=5, side=tk.RIGHT, padx=5)

boton_print = tk.Button(gamma_frame, text="🖨️ print", command=print_resultados,
                        borderwidth=1, width=10, relief="solid",
                        bg=COLOR_BTN_BG, fg=COLOR_BTN_FG)
boton_print.pack(pady=5, padx=5, side=tk.LEFT)

boton_comentario = tk.Button(gamma_frame, text="💬 Coment",
                             command=abrir_ventana_comentario,
                             borderwidth=1, width=10, relief="solid",
                             bg=COLOR_BTN_BG, fg=COLOR_BTN_FG)
boton_comentario.pack(pady=5, padx=2, side=tk.LEFT)

boton_limpiar = tk.Button(gamma_frame, text="🧹 Limpiar", command=limpiar_campos,
                          borderwidth=1, width=10, relief="solid",
                          bg=COLOR_BTN_BG, fg=COLOR_BTN_LIMPIAR_FG)
boton_limpiar.pack(pady=5, padx=5, side=tk.LEFT)

boton_grafico = tk.Button(gamma_frame, text="📊 gráfica", command=mostrar_grafico,
                          borderwidth=1, width=10, relief="ridge", state="disabled",
                          bg=COLOR_BTN_BG, fg=COLOR_BTN_FG)
boton_grafico.pack(pady=2, padx=5, side=tk.RIGHT)

boton_grafico_radar = tk.Button(gamma_frame, text="🕸️ Radar", command=mostrar_grafico_radar,
                                borderwidth=1, width=10, relief="ridge", state="disabled",
                                bg=COLOR_BTN_BG, fg=COLOR_BTN_FG)
boton_grafico_radar.pack(pady=2, padx=5, side=tk.RIGHT)

boton_estadisticas = tk.Button(gamma_frame, text="📈 Stats", command=mostrar_estadisticas,
                               borderwidth=1, width=10, relief="ridge",
                               bg=COLOR_BTN_BG, fg=COLOR_BTN_FG)
boton_estadisticas.pack(pady=2, padx=5, side=tk.RIGHT)

resultado_texto = tk.Text(root, width=90, height=40, fg=COLOR_RESULT_FG,
                          bg=COLOR_RESULT_BG, insertbackground=COLOR_RESULT_INS)

# ------------- línea divisoria azul entre controles y panel de texto -------------
divider = tk.Frame(root, height=2, bg="darkblue")
divider.pack(fill=tk.X, padx=8, pady=(6,6))

# Etiqueta de versión discreta en la esquina inferior derecha
# usa el mismo fondo de la ventana para integrarse, color de texto sutil
version_label = tk.Label(root, text=f"v{VERSION}", bg=COLOR_RESULT_BG, fg="black",
                         font=("Segoe UI", 8))
# Colocarla con place para que no interfiera con el pack/geometry del resto
version_label.place(relx=1.0, rely=1.0, x=-6, y=-6, anchor="se")
# --------------------------------------------------------------------------------

root.configure(bg=COLOR_BG)
main_frame.configure(bg=COLOR_BG)
beta_frame.configure(bg=COLOR_BG)
gamma_frame.configure(bg=COLOR_BG)
# Los botones y labels ya tienen el color asignado arriba

boton_buscar.configure(style="Dark.TButton")

# Si usas ttk.Button, puedes definir un estilo:
style = ttk.Style()
style.theme_use('clam')
style.configure("Dark.TButton", background=COLOR_BTN_BG, foreground=COLOR_BTN_FG,
                relief="raised", borderwidth=2)

resultado_texto.pack(pady=0)

carpeta_inicial()

root.mainloop()
