""" Busca archivos de texto en una carpeta y subcarpetas en busca de una palabra específica. """
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import difflib
import matplotlib.pyplot as plt

CARPETA_INICIO = 'C:/Users/Usuario/OneDrive/Escritorio/info_discos duros/sizes'
set_busquedas = set()

def carpeta_inicial():
    """ Establece la carpeta inicial para la búsqueda """
    carpeta = CARPETA_INICIO
    if carpeta:
        label_carpeta.config(text=CARPETA_INICIO)
        boton_buscar.config(state="normal")
        entrada_palabra.config(state="normal")
        label_carpeta.config(fg="gray40")

def seleccionar_carpeta():
    """ Abre un cuadro de diálogo para seleccionar una carpeta """
    carpeta = filedialog.askdirectory()
    if carpeta:
        label_carpeta.config(text=carpeta)
        boton_buscar.config(state="normal")
        entrada_palabra.config(state="normal")
        label_carpeta.config(fg="darkgreen")

# Diccionario para almacenar el estado de los checkbuttons de archivos
check_vars_archivos = {}

def buscar_palabra():
    """ Busca la palabra en los archivos de texto de la carpeta y
    subcarpetas (excluyendo comentarios.txt) """
    carpeta = label_carpeta.cget("text")
    palabra = entrada_palabra.get()
    if not os.path.isdir(carpeta):
        messagebox.showerror("Error", "La dirección de la carpeta no es válida.")
        return
    if not palabra:
        sin_palabra = messagebox.askokcancel("buscar palabra",
                                             "Debe ingresar una palabra para buscar.")
        if sin_palabra:
            entrada_palabra.focus()
        return

    results = []
    valores_por_archivo = {}
    nombres_en_archivos = set()

    for roota, _, files in os.walk(carpeta):
        for nombre_archivo in files:
            # Excluir comentarios.txt de la búsqueda
            if (nombre_archivo.endswith('.txt') and
                nombre_archivo.lower() != "comentarios.txt" and
                check_vars_archivos.get(nombre_archivo, tk.BooleanVar(value=True)).get()):
                ruta_archivo = os.path.join(roota, nombre_archivo)
                with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                    lineas = archivo.readlines()
                    ocurrencias = 0
                    valor_total = 0
                    for num_linea, linea in enumerate(lineas, 1):
                        nombre_linea = linea.strip().split()[0] if linea.strip() else ""
                        if nombre_linea:
                            nombres_en_archivos.add(nombre_linea.lower())
                        if palabra in linea:
                            results.append(f"{ruta_archivo} - Línea {num_linea}: {linea.strip()}")
                            ocurrencias += 1
                            ultimo_resultado = results[-1]
                            valor_resultado = ultimo_resultado.split(":")[-1].strip()
                            valor_resultado_limpio = valor_resultado.split("GB")[0].strip()
                            valor_alternativo = ultimo_resultado.split("-")[-1].strip()
                            valor_alternativo_limpio = valor_alternativo.split("GB")[0].strip()
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
                        valores_por_archivo[nombre_archivo] = valor_total
                        set_busquedas.add(f"{palabra}, {ocurrencias}, "
                                          f"{nombre_archivo.split('.')[0]}, "
                                          f" Valor Total: {valor_total:.2f} GB")

    if results:
        resultado_texto.delete(1.0, tk.END)
        for resultado in results:
            resultado_texto.insert(tk.END, resultado.split("/")[-1].strip() + "\n")
        # Solo mostrar la gráfica si el checkbutton está activado
        if var_mostrar_grafica.get():
            mostrar_grafico(valores_por_archivo)
    else:
        # ... (resto del código igual) ...
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
    mostrar_resultados_en_label()

def mostrar_grafico(valores_por_archivo):
    """ Muestra un gráfico de barras horizontal con los valores por archivo en modo gris """

    plt.style.use('grayscale')  # Estilo

    _, ax = plt.subplots(figsize=(10, max(6, len(valores_por_archivo) * 0.25)))
    fig = plt.gcf()
    fig.patch.set_facecolor("#e0e0e0")  # Fondo de la figura
    ax.set_facecolor("#cccccc")         # Fondo del subplot

    archivos, valores = zip(*sorted(valores_por_archivo.items(),
                                    key=lambda x: x[1], reverse=True))
    for i, v in enumerate(valores):
        plt.text(v, i, f"{v:.2f}", va='center', fontsize=9, color="#2C2929")  # Texto oscuro
    plt.barh(archivos, valores, color="#366381", alpha=0.6)  # Barras gris
    plt.ylabel('Archivos', color="#2C2929")
    plt.xlabel('Tamaño (GB)', color="#2C2929")
    plt.title(entrada_palabra.get(), color="#2C2929")
    plt.tight_layout()
    plt.show()

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
    """ Imprime los resultados del texto """
    lista_resultado_busquedas = list()
    for resultado in set_busquedas:
        lista_resultado_busquedas.append(resultado)
    lista_resultado_busquedas = sorted(lista_resultado_busquedas)
    for resultado in lista_resultado_busquedas:
        print(resultado)
    print(" ")

def abrir_ventana_comentario():
    """Abre una ventana emergente para escribir un comentario y guardarlo en comentarios.txt"""
    def guardar_comentario():
        palabra = entrada_palabra.get().strip()
        comentario = entry_comentario.get().strip()
        if palabra and comentario:
            carpeta = label_carpeta.cget("text")
            ruta_comentarios = os.path.join(carpeta, "comentarios.txt")
            with open(ruta_comentarios, "a", encoding="utf-8") as f:
                f.write(f"{palabra}: {comentario}\n")
            ventana_comentario.destroy()
            messagebox.showinfo("Comentario guardado", "Comentario guardado correctamente.")
        else:
            messagebox.showwarning("Faltan datos", "Debes escribir una palabra y un comentario.")

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
    label_comentarios.config(text="Comentarios")

def mostrar_resultados_en_label():
    """Busca la palabra solo en comentarios.txt en la ruta fija 
    y muestra el resultado en el label de comentarios, excluyendo 
    la palabra buscada en el texto mostrado"""
    palabra = entrada_palabra.get().strip().lower()
    ruta_comentarios = (r"C:\Users\Usuario\OneDrive\Escritorio\info_discos duros\sizes"
                        r"\comentarios.txt")
    if os.path.exists(ruta_comentarios):
        resultados = []
        with open(ruta_comentarios, "r", encoding="utf-8") as f:
            for linea in f:
                if palabra and palabra in linea.lower():
                    # Excluye la palabra buscada del texto mostrado
                    texto_filtrado = linea.lower().replace(palabra, "").strip(" :\t-")
                    if texto_filtrado:
                        resultados.append(texto_filtrado.strip())
        if resultados:
            texto = "\t".join(resultados)
        else:
            texto = palabra
        label_comentarios.config(text=texto)
    else:
        label_comentarios.config(text="No existe comentarios.txt en la ruta fija.")

# Crear la ventana principal
root = tk.Tk()
root.title("Buscar Modelo")
root.geometry("600x300+1000+200")

# Crear y colocar los widgets
main_frame = tk.Frame(root, borderwidth=0)
main_frame.pack(pady=5, expand=True, fill=tk.BOTH)

beta_frame = tk.Frame(root, borderwidth=0)
beta_frame.pack(pady=2, expand=True, fill=tk.BOTH)

gamma_frame = tk.Frame(root, borderwidth=0)
gamma_frame.pack(pady=2, expand=True, fill=tk.BOTH)

var_mostrar_grafica = tk.BooleanVar(value=False)

boton_seleccionar = tk.Button(main_frame, text="Seleccionar", borderwidth=0, fg="gray40",
                              width=10, command=seleccionar_carpeta)
boton_seleccionar.pack(side=tk.LEFT)

boton_carpeta_inicio = tk.Button(main_frame, text="carpeta sizes", width=10, borderwidth=0,
                                 fg="gray50", command=carpeta_inicial)
boton_carpeta_inicio.pack(side=tk.LEFT)

label_carpeta = tk.Label(main_frame, text="No se ha seleccionado carpeta",
                         fg="gray50", width=45, anchor="w")
label_carpeta.pack(padx=2, side=tk.LEFT)

check_mostrar_grafica = tk.Checkbutton(main_frame, text="gráfica",
                                       variable=var_mostrar_grafica,
                                       bg="#9292A0", fg="#353B4D", selectcolor="#C4C4CC")
check_mostrar_grafica.pack(pady=5, padx=2, side=tk.RIGHT)

entrada_palabra = tk.Entry(beta_frame, width=20, state="disabled", font=("Courier New", 12))
entrada_palabra.bind("<Return>", lambda event: boton_buscar.invoke())

boton_buscar = ttk.Button(beta_frame, text="Buscar ...", style="Dark.TButton",
                         state="disabled", command=buscar_palabra)
boton_buscar.pack(pady=5, padx=10, side=tk.RIGHT)
entrada_palabra.pack(pady=5, side=tk.RIGHT, padx=5)

boton_print = tk.Button(beta_frame, text="print", command=print_resultados,
                        borderwidth=1, width=10, relief="ridge")
boton_print.pack(pady=5, padx=(5, 2), side=tk.LEFT)

boton_comentario = tk.Button(beta_frame, text="Comentario",
                             command=abrir_ventana_comentario,
                             borderwidth=1, width=10, relief="ridge")
boton_comentario.pack(pady=5, padx=2, side=tk.LEFT)

boton_limpiar = tk.Button(beta_frame, text="Limpiar", command=limpiar_campos,
                          borderwidth=1, width=10, relief="ridge")
boton_limpiar.pack(pady=5, padx=(5, 2), side=tk.LEFT)

label_comentarios = tk.Label(gamma_frame, text=" ", width=40,
                            anchor="w", font=("Courier New", 12))
label_comentarios.pack(pady=5, padx=2, side=tk.LEFT)

resultado_texto = tk.Text(root, width=90, height=40, fg="darkblue")

root.configure(bg="#9292A0")
main_frame.configure(bg="#9292A0")
beta_frame.configure(bg="#9292A0")
gamma_frame.configure(bg="#9292A0")
boton_seleccionar.configure(bg="#9292A0", fg="#13161F")
boton_carpeta_inicio.configure(bg="#9292A0", fg="#13161F")
label_carpeta.configure(bg="#9292A0", fg="#13161F")
label_comentarios.configure(bg="#9292A0", fg="#9F10D8")
entrada_palabra.configure(bg="#C4C4CC", fg="#1A223B", insertbackground="#aa9696")
boton_print.configure(bg="#909099", fg="#353B4D")
boton_comentario.configure(bg="#909099", fg="#353B4D")
boton_limpiar.configure(bg="#909099", fg="#30478D")
resultado_texto.configure(bg="#3a3939", fg="#03A12B", insertbackground="#8d8686")

boton_buscar.configure(style="Gray.TButton")

# Si usas ttk.Button, puedes definir un estilo:
style = ttk.Style()
style.theme_use('clam')
style.configure("Dark.TButton", background="#909099", foreground="#9F10D8", relief="flat")

resultado_texto.pack(pady=0)

carpeta_inicial()

root.mainloop()
