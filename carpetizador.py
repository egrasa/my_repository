""" carpetizador """
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import os
import csv
#from collections import deque
from history_tracker import log_file_creation
from history_visualizer import HistoryViewer

ENCODINGS = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

VERSION = 1.3

lista_carpetizados = []
lista_eventos = []

class ToolTip(object):
    """ Clase para crear tooltips en widgets de Tkinter """
    def __init__(self, widget, text, delay=600):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.delay = delay  # milisegundos
        self._after_id = None
        widget.bind("<Enter>", self.schedule_tip)
        widget.bind("<Leave>", self.hide_tip)

    def schedule_tip(self, event=None):
        """ Programa la aparición del tooltip """
        lista_eventos.append(event)
        self._after_id = self.widget.after(self.delay, self.show_tip)

    def show_tip(self, event=None):
        """ Muestra el tooltip """
        lista_eventos.append(event)
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 30
        y = y + cy + self.widget.winfo_rooty() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("Arial", 8))
        label.pack(ipadx=4, ipady=2)

    def hide_tip(self, event=None):
        """ Oculta el tooltip """
        lista_eventos.append(event)
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def actualizar_estado_boton_crear():
    """ fn actualizar estado del boton crear """
    carpeta = label_carpeta.cget("text")
    nombre = entrada_nombre.get()
    if carpeta and carpeta != "No se ha seleccionado ninguna carpeta" and nombre.strip():
        boton_crear.config(state='normal')
    else:
        boton_crear.config(state='disabled')

def seleccionar_carpeta():
    """ fn elegir ruta """
    carpeta = filedialog.askdirectory()
    boton_seagate.config(state='disabled', bg='lightgray')
    boton_old.config(state='disabled', bg='lightgray')
    boton_new.config(state='disabled', bg='lightgray')
    boton_last.config(state='disabled', bg='lightgray')
    boton_unionsine14.config(state='disabled', bg='lightgray')
    boton_beta5tb.config(state='disabled', bg='lightgray')
    boton_alpha4tb.config(state='disabled', bg='lightgray')
    boton_mpass2018.config(state='disabled', bg='lightgray')
    boton_easystore.config(state='disabled', bg='lightgray')
    boton_elem12.config(state='disabled', bg='lightgray')
    boton_newse.config(state='disabled', bg='lightgray')
    boton_base1.config(state='disabled', bg='lightgray')
    boton_mpassazul.config(state='disabled', bg='lightgray')
    boton_mpassblanco.config(state='disabled', bg='lightgray')
    boton_unionsine10.config(state='disabled', bg='lightgray')
    boton_mpassrojo.config(state='disabled', bg='lightgray')
    boton_secret.config(state='disabled', bg='lightgray')
    boton_expansion.config(state='disabled', bg='lightgray')
    label_carpeta.config(fg='darkblue')
    entrada_nombre.config(state='normal', fg='gray40')
    if carpeta:
        label_carpeta.config(text=carpeta)
        nombre_carpeta = carpeta.split('/')
        #print(nombre_carpeta)
        boton_crear.config(state='normal')
        entrada_nombre.config(state='normal')
        actualizar_estado_boton_crear()
        if "Elements14Tb_old" in nombre_carpeta:
            boton_old.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Elements14Tb_old")
        elif "Elements14Tb_new" in nombre_carpeta:
            boton_new.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Elements14Tb_new")
        elif "Elements18Tb_last" in nombre_carpeta:
            boton_last.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Elements18Tb_last")
        elif "Seagate8Tb_Desktop" in nombre_carpeta:
            boton_seagate.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Seagate8Tb_Desktop")
        elif "UnionSine14Tb" in nombre_carpeta:
            boton_unionsine14.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "UnionSine14Tb")
        elif "Elements5Tb_Beta" in nombre_carpeta:
            boton_beta5tb.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Elements5Tb_Beta")
        elif "Elements4Tb_Alpha" in nombre_carpeta:
            boton_alpha4tb.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Elements4Tb_Alpha")
        elif "MyPassport2018" in nombre_carpeta:
            boton_mpass2018.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "MyPassport2018")
        elif "Easystore8Tb" in nombre_carpeta:
            boton_easystore.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Easystore8Tb")
        elif "Elements12Tb" in nombre_carpeta:
            boton_elem12.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Elements12Tb")
        elif "Elements4Tb_newSE" in nombre_carpeta:
            boton_newse.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Elements4Tb_newSE")
        elif "Elements2Tb_Base1" in nombre_carpeta:
            boton_base1.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Elements2Tb_Base1")
        elif "MyPassport2Tb_azul" in nombre_carpeta:
            boton_mpassazul.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "MyPassport2Tb_azul")
        elif "MyPassport4Tb_blanco" in nombre_carpeta:
            boton_mpassblanco.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "MyPassport4Tb_blanco")
        elif "UnionSine10Tb" in nombre_carpeta:
            boton_unionsine10.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "UnionSine10Tb")
        elif "MyPassport2Tb_red" in nombre_carpeta:
            boton_mpassrojo.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "MyPassport2Tb_red")
        elif "Elements4Tb_SEcret" in nombre_carpeta:
            boton_secret.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Elements4Tb_SEcret")
        elif "Seagate10Tb_Expansion" in nombre_carpeta:
            boton_expansion.config(state='normal', bg='lightgreen', fg='blue')
            entrada_nombre.delete(0, tk.END)
            entrada_nombre.insert(0, "Seagate10Tb_Expansion")
        else:
            print("Carpeta no reconocida")
    else:
        label_carpeta.config(text="No se ha seleccionado ninguna carpeta")
        actualizar_estado_boton_crear()
    # Resetear barra y texto de estado al seleccionar carpeta
    progress['value'] = 0
    progress.config(style="gray.Horizontal.TProgressbar")
    label_estado.config(text="")

def salir_app():
    """ fn salir de la app """
    # Cerrar todas las ventanas hijas si existen
    for w in ventana.winfo_children():
        if isinstance(w, tk.Toplevel):
            try:
                w.destroy()
            except (tk.TclError, RuntimeError):
                # Exception ignored intentionally; consider adding logging if needed for debugging.
                pass
    try:
        ventana.quit()  # Detener el mainloop si está corriendo
        ventana.destroy()
    except (tk.TclError, RuntimeError, OSError):
        # Exception ignored intentionally; consider adding logging if needed for debugging.
        pass

def crear_archivo():
    """ fn crear archivo txt y csv """
    nombre_archivo = entrada_nombre.get()
    carpeta = label_carpeta.cget("text")
    print(carpeta)
    carpeta2 = "C:/Users/Usuario/OneDrive/Escritorio/info_discos duros"

    if nombre_archivo and carpeta:
        dirs_total = sum(len(dirs) for _, dirs, _ in os.walk(carpeta))
        files_total = sum(len(files) for _, _, files in os.walk(carpeta))
        progress['maximum'] = dirs_total if dirs_total > 0 else 1
        progress['value'] = 0
        progress.config(style="green.Horizontal.TProgressbar")
        ventana.update_idletasks()

        ruta_txt = os.path.join(carpeta, f"{nombre_archivo}.txt")
        ruta_txt2 = os.path.join(carpeta2, f"{nombre_archivo}.txt")
        ruta_csv = os.path.join(carpeta, f"{nombre_archivo}.csv")
        ruta_csv2 = os.path.join(carpeta2, f"{nombre_archivo}.csv")

        total_size_gb = 0
        file_count = 0

        with open(ruta_txt, 'w', encoding='utf-8') as archivo_txt, \
             open(ruta_csv, 'w', newline='', encoding='utf-8') as archivo_csv:

            csv_writer = csv.writer(archivo_csv)
            # Añadida columna NumFiles para indicar número de archivos en cada carpeta
            csv_writer.writerow(["Nombre", "Tamaño (GB)", "Origen", "NumFiles"])

            count = 0
            for root, dirs, _ in os.walk(carpeta):
                for diri in dirs:
                    dir_path = os.path.join(root, diri)
                    # calcular tamaño y número de archivos dentro de la carpeta
                    try:
                        file_list = [f for f in os.listdir(dir_path) if
                                     os.path.isfile(os.path.join(dir_path, f))]
                    except (PermissionError, FileNotFoundError):
                        file_list = []
                    size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in file_list)
                    size_gb = size / (1024 ** 3)
                    num_files = len(file_list)
                    total_size_gb += size_gb
                    archivo_txt.write(f"{diri}: {size_gb:.2f} GB\n")
                    csv_writer.writerow([diri, f"{size_gb:.2f}", dir_path.split('/')[1],
                                         str(num_files)])
                    count += 1
                    file_count += 1
                    progress['value'] = count
                    porcentaje = int((count / progress['maximum']) * 100)
                    label_estado.config(text=f"Procesando... {porcentaje}%")
                    ventana.update_idletasks()

        with open(ruta_txt2, 'w', encoding='utf-8') as archivo_txt, \
             open(ruta_csv2, 'w', newline='', encoding='utf-8') as archivo_csv:

            csv_writer = csv.writer(archivo_csv)
            # Añadida columna NumFiles en la segunda copia del CSV
            csv_writer.writerow(["Nombre", "Tamaño (GB)", "Origen", "NumFiles"])

            count = 0
            for root, dirs, _ in os.walk(carpeta):
                for diri in dirs:
                    dir_path = os.path.join(root, diri)
                    try:
                        file_list = [f for f in os.listdir(dir_path) if
                                     os.path.isfile(os.path.join(dir_path, f))]
                    except (PermissionError, FileNotFoundError):
                        file_list = []
                    size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in file_list)
                    size_gb = size / (1024 ** 3)
                    num_files = len(file_list)
                    archivo_txt.write(f"{diri}: {size_gb:.2f} GB\n")
                    csv_writer.writerow([diri, f"{size_gb:.2f}", dir_path.split('/')[1],
                                         str(num_files)])
                    count += 1
                    progress['value'] = count
                    porcentaje = int((count / progress['maximum']) * 100)
                    label_estado.config(text=f"Procesando... {porcentaje}%")
                    ventana.update_idletasks()

        progress['value'] = progress['maximum']
        label_estado.config(text="¡Procesamiento finalizado!")
        ventana.update_idletasks()

        # Registrar en el historial
        log_file_creation(
            nombre_archivo,
            file_count,
            total_size_gb,
            carpeta,
            ruta_completa=carpeta,
            carpetas_procesadas=dirs_total,
            archivos_procesados=files_total
        )

        boton_mostrar.config(state='normal')

def dar_nombre(nombre):
    """ fn dar nombre """
    #print(nombre)
    entrada_nombre.delete(0, tk.END)
    entrada_nombre.insert(0, nombre)
    crear_archivo()

def nombre_old():
    """ fn nombre Elements14Tb_old """
    nombre_archivo = "Elements14Tb_old"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_old.config(state='disabled', bg='lightgray')

def nombre_new():
    """ fn nombre Elements14Tb_new """
    nombre_archivo = "Elements14Tb_new"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_new.config(state='disabled', bg='lightgray')

def nombre_last():
    """ fn nombre Elements18Tb_last """
    nombre_archivo = "Elements18Tb_last"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_last.config(state='disabled', bg='lightgray')

def nombre_seagate():
    """ fn nombre Seagate8Tb_Desktop """
    nombre_archivo = "Seagate8Tb_Desktop"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_seagate.config(state='disabled', bg='lightgray')

def nombre_unionsine14():
    """ fn nombre UnionSine14Tb """
    nombre_archivo = "UnionSine14Tb"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_unionsine14.config(state='disabled', bg='lightgray')

def nombre_beta5tb():
    """ fn nombre Elements5Tb_Beta """
    nombre_archivo = "Elements5Tb_Beta"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_beta5tb.config(state='disabled', bg='lightgray')

def nombre_alpha4tb():
    """ fn nombre Elements4Tb_Alpha """
    nombre_archivo = "Elements4Tb_Alpha"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_alpha4tb.config(state='disabled', bg='lightgray')

def nombre_mpass2018():
    """ fn nombre MyPassport2018 """
    nombre_archivo = "MyPassport2018"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_mpass2018.config(state='disabled', bg='lightgray')

def nombre_easystore():
    """ fn nombre Easystore8Tb """
    nombre_archivo = "Easystore8Tb"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_easystore.config(state='disabled', bg='lightgray')

def nombre_elem12():
    """ fn nombre Elements12Tb """
    nombre_archivo = "Elements12Tb"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_elem12.config(state='disabled', bg='lightgray')

def nombre_newse():
    """ fn nombre Elements4Tb_newSE """
    nombre_archivo = "Elements4Tb_newSE"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_newse.config(state='disabled', bg='lightgray')

def nombre_secret():
    """ fn nombre Elements4Tb_SEcret """
    nombre_archivo = "Elements4Tb_SEcret"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_secret.config(state='disabled', bg='lightgray')

def nombre_base1():
    """ fn nombre Elements2Tb_base1 """
    nombre_archivo = "Elements2Tb_base1"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_base1.config(state='disabled', bg='lightgray')

def nombre_mpassazul():
    """ fn nombre MyPassport2Tb_azul """
    nombre_archivo = "MyPassport2Tb_azul"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_mpassazul.config(state='disabled', bg='lightgray')

def nombre_mpassblanco():
    """ fn nombre MyPassport4Tb_blanco """
    nombre_archivo = "MyPassport4Tb_blanco"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_mpassblanco.config(state='disabled', bg='lightgray')

def nombre_unionsine10():
    """ fn nombre UnionSine10Tb """
    nombre_archivo = "UnionSine10Tb"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_unionsine10.config(state='disabled', bg='lightgray')

def nombre_mpassrojo():
    """ fn nombre MyPassport2Tb_red """
    nombre_archivo = "MyPassport2Tb_red"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_mpassrojo.config(state='disabled', bg='lightgray')

def nombre_expansion():
    """ fn nombre Seagate10Tb_Expansion """
    nombre_archivo = "Seagate10Tb_Expansion"
    if nombre_archivo not in lista_carpetizados:
        lista_carpetizados.append(nombre_archivo)
        dar_nombre(nombre_archivo)
    else:
        messagebox.showinfo("Información", "El nombre ya ha sido utilizado.")
    boton_expansion.config(state='disabled', bg='lightgray')

def mostrar_archivos():
    """ fn mostrar archivos creados """
    print(" ")
    print(len(lista_carpetizados))
    if lista_carpetizados:
        archivos = "\n".join(lista_carpetizados)
        print(archivos)
    else:
        messagebox.askokcancel("Archivos Creados", "No se han creado archivos aún.")

def mostrar_ayuda():
    """Muestra una ventana emergente con la ayuda de la aplicación."""
    mensaje = (
        "Gestor de Archivos - Ayuda\n\n"
        "Esta aplicación crea archivos txt y csv a partir de una carpeta seleccionada."
        "\nEstos archivos txt y csv contienen información sobre los archivos y carpetas "
        "dentro de la carpeta seleccionada.\n\n -- Instrucciones --\n"
        "1. Selecciona una carpeta con el botón 'Seleccionar Carpeta'.\n"
        "2. Una vez seleccionada la carpeta, se habilitará el botón con el nombre sugerido "
        "para ese archivo.\n"
        "3. Pulsa ese botón para generar los archivos txt y csv.\n"
        "4. En acaso de querer otro nombre para el archivo, o no activarse ningun botón, "
        "edita el campo de texto y pulsa 'Crear Archivo'.\n"
        "5. Los botones de nombres rápidos se activan según la carpeta seleccionada.\n"
        "\n"
        "En la barra de progreso puedes ver el avance del procesamiento.\n"
    )
    # Mostrar el mensaje de ayuda al usuario
    messagebox.showinfo("Ayuda - Gestor de Archivos", mensaje)

def mostrar_historial():
    """
    Muestra el historial de archivos creados. 
    Si el módulo 'history_visualizer' está disponible,
    se utiliza para mostrar una ventana avanzada con el historial.
    Si no está disponible, se muestra un resumen simple de los archivos creados en la sesión actual.
    """
    try:
        history_viewer = HistoryViewer(ventana)
        history_viewer.show_history_window()
    except ImportError:
        if lista_carpetizados:
            archivos = "\n".join(lista_carpetizados)
            messagebox.showinfo("Historial (sesión)",
                                f"Archivos creados en esta sesión:\n\n{archivos}")
        else:
            messagebox.showinfo("Historial",
                                "No hay historial disponible.\n\nEsto significa que no se han"
                                " creado archivos en esta sesión.")

# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Gestor de Archivos")
ventana.geometry("600x340")
ventana.configure(bg='lightgray')

style = ttk.Style()
style.theme_use('default')
style.configure("gray.Horizontal.TProgressbar", troughcolor='lightgray', background='lightgray')
style.configure("green.Horizontal.TProgressbar", troughcolor='lightgray', background='green')

frame_top = tk.Frame(ventana, bg='lightgray')
frame_top.pack(pady=10)

# Botón para seleccionar carpeta
boton_seleccionar = tk.Button(frame_top, text="📂 Seleccionar Carpeta", width=30, fg='blue',
                              height=2, bg='lightblue', command=seleccionar_carpeta,
                              relief='groove')
boton_seleccionar.pack(pady=2, side='left')

# Botón para salir de la aplicación
boton_salir = tk.Button(frame_top, text="❌ Salir", width=10, bg='lightblue', fg='darkblue',
                        command=salir_app, relief='groove', height=2)
boton_salir.pack(pady=2, side='left')

# frames
frame_opciones = tk.Frame(ventana, bg='lightgray')
frame_opciones.pack(pady=0)

frame_botones = tk.Frame(ventana, bg='lightgray')
frame_botones.pack(pady=0)

frame_barra = tk.Frame(ventana, bg='lightgray')
frame_barra.pack(padx=25, pady=10, expand=True, fill='x')

frame_lower = tk.Frame(ventana, bg='darkred', height=2)
frame_lower.pack(pady=0, fill='x', expand=True)

frame_help = tk.Frame(ventana, bg='lightgray')
frame_help.pack(pady=0, fill='both', expand=True)

# Label para mostrar la carpeta seleccionada
label_carpeta = tk.Label(frame_barra, text="No se ha seleccionado ninguna carpeta",
                         fg='darkblue', width=40, bg='lightgray', font=('new courier', 8))
label_carpeta.pack(pady=0, side='left')

# Entrada para el nombre del archivo
entrada_nombre = tk.Entry(frame_opciones, width=30, fg='gray60', state='normal',
                          bg='lightgray', font=('new courier', 10), background='lightgray')
entrada_nombre.pack(padx=10, pady=5, side='left')
entrada_nombre.insert(0, "Nombre")
entrada_nombre.bind("<KeyRelease>", lambda event: actualizar_estado_boton_crear())

# Botón para crear el archivo
boton_crear = tk.Button(frame_opciones, text="Crear Archivo", height=2, width=10, bg='lightgray',
                        command=crear_archivo, state='disabled', borderwidth=0)
boton_crear.pack(padx=2, pady=5, side='left')

boton_ayuda = tk.Button(frame_help, text="❓ Ayuda", command=mostrar_ayuda,
                        bg="#8BC7A9", fg='black', relief='groove')
boton_ayuda.pack(padx=5, pady=5, anchor='ne', side='right')
ToolTip(boton_ayuda, "Muestra información de ayuda sobre el uso de la aplicación")

# Botones para seleccionar nombres
boton_old = tk.Button(frame_botones, text="Elements14Tb_old", width=20, command=nombre_old,
                      state='disabled', bg='lightgray')
boton_old.grid(pady=0, row=0, column=0)

boton_new = tk.Button(frame_botones, text="Elements14Tb_new", width=20, command=nombre_new,
                      state='disabled', bg='lightgray')
boton_new.grid(pady=0, row=0, column=1)

boton_last = tk.Button(frame_botones, text="Elements18Tb_last", width=20, command=nombre_last,
                       state='disabled', bg='lightgray')
boton_last.grid(pady=0, row=0, column=2)

boton_seagate = tk.Button(frame_botones, text="Seagate8Tb_Desktop", width=20,
                          command=nombre_seagate, state='disabled', bg='lightgray')
boton_seagate.grid(pady=0, row=1, column=0)

boton_unionsine14 = tk.Button(frame_botones, text="UnionSine14Tb", width=20,
                              command=nombre_unionsine14, state='disabled', bg='lightgray')
boton_unionsine14.grid(pady=0, row=1, column=1)

boton_beta5tb = tk.Button(frame_botones, text="Elements5Tb_Beta", width=20, command=nombre_beta5tb,
                          state='disabled', bg='lightgray')
boton_beta5tb.grid(pady=0, row=1, column=2)

boton_alpha4tb = tk.Button(frame_botones, text="Elements4Tb_Alpha", width=20,
                           command=nombre_alpha4tb, state='disabled', bg='lightgray')
boton_alpha4tb.grid(pady=0, row=2, column=0)

boton_mpass2018 = tk.Button(frame_botones, text="MyPassport2018", width=20,
                            command=nombre_mpass2018, state='disabled', bg='lightgray')
boton_mpass2018.grid(pady=0, row=2, column=1)

boton_easystore = tk.Button(frame_botones, text="Easystore8Tb", width=20, command=nombre_easystore,
                            state='disabled', bg='lightgray')
boton_easystore.grid(pady=0, row=2, column=2)

boton_elem12 = tk.Button(frame_botones, text="Elements12Tb", width=20, command=nombre_elem12,
                         state='disabled', bg='lightgray')
boton_elem12.grid(pady=0, row=3, column=0)

boton_newse = tk.Button(frame_botones, text="Elements4Tb_newSE", width=20, command=nombre_newse,
                        state='disabled', bg='lightgray')
boton_newse.grid(pady=0, row=3, column=1)

boton_base1 = tk.Button(frame_botones, text="Elements2Tb_base1", width=20, command=nombre_base1,
                        state='disabled', bg='lightgray')
boton_base1.grid(pady=0, row=3, column=2)

boton_mpassazul = tk.Button(frame_botones, text="MyPassport2Tb_azul", width=20,
                            command=nombre_mpassazul, state='disabled', bg='lightgray')
boton_mpassazul.grid(pady=0, row=4, column=0)

boton_mpassblanco = tk.Button(frame_botones, text="MyPassport4Tb_blanco", width=20,
                              command=nombre_mpassblanco, state='disabled', bg='lightgray')
boton_mpassblanco.grid(pady=0, row=4, column=1)

boton_unionsine10 = tk.Button(frame_botones, text="UnionSine10Tb", width=20,
                              command=nombre_unionsine10, state='disabled', bg='lightgray')
boton_unionsine10.grid(pady=0, row=4, column=2)

boton_mpassrojo = tk.Button(frame_botones, text="MyPassport2Tb_red", width=20,
                              command=nombre_mpassrojo, state='disabled', bg='lightgray')
boton_mpassrojo.grid(pady=0, row=5, column=0)

boton_secret = tk.Button(frame_botones, text="Elements4Tb_SEcret", width=20,
                        command=nombre_secret, state='disabled', bg='lightgray')
boton_secret.grid(pady=0, row=5, column=1)

boton_expansion = tk.Button(frame_botones, text="Seagate10Tb_Expansion", width=20,
                        command=nombre_expansion, state='disabled', bg='lightgray')
boton_expansion.grid(pady=0, row=5, column=2)

# Botón para mostrar los archivos creados
boton_mostrar = tk.Button(frame_opciones, text="Ver Creados", height=2, width=15,
                          command=mostrar_archivos, state='disabled', borderwidth=0, bg='lightgray')
boton_mostrar.pack(padx=2, pady=5, side='left')

# Botón para mostrar el historial
boton_historial = tk.Button(frame_opciones, text="📊 Historial", height=2, width=15,
                           command=mostrar_historial, borderwidth=0, fg='green', bg='lightgray')
boton_historial.pack(padx=2, pady=5, side='left')

# Label para mostrar el estado
label_estado = tk.Label(frame_barra, text="", font=("Arial", 8), bg='lightgray', fg='darkgreen')

# Barra de progreso desactivada al inicio
progress = ttk.Progressbar(frame_barra, orient='horizontal', length=100, mode='determinate',
                           style="gray.Horizontal.TProgressbar", name="progressbar")
progress.pack(padx=5, pady=0, side='right', fill='x', anchor='w')
label_estado.pack(padx=2, pady=2, side='right', anchor='w')

label_version = tk.Label(frame_help, text=f"Versión: {VERSION}", bg='lightgray', fg='darkred',
                        font=('new courier', 8))
label_version.pack(padx=10, pady=5, side='left', anchor='e')

# Tooltip para botones
ToolTip(boton_seleccionar, "Permite seleccionar la carpeta que quieras procesar")
ToolTip(boton_crear, "Crea un archivo txt y csv con el nombre que hayas elegido")
ToolTip(boton_mostrar, "Permite ver los archivos creados en esta sesion")
ToolTip(entrada_nombre, "Introduce el nombre del archivo que quieres crear")
ToolTip(label_carpeta, "Carpeta seleccionada para procesar")
ToolTip(progress, "Barra de progreso de creación de archivos")
ToolTip(label_version, f"Versión actual: {VERSION}")
ToolTip(boton_historial, "Muestra el historial de archivos creados y gráficos de evolución")

# Iniciar el bucle principal de la interfaz
try:
    ventana.mainloop()
except (tk.TclError, KeyboardInterrupt):
    try:
        if hasattr(ventana, "tk"):
            if ventana.winfo_exists():
                ventana.quit()
                ventana.destroy()
    except tk.TclError:
        # Exception ignored intentionally; consider adding logging if needed for debugging.
        pass
