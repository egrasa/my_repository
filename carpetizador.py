""" carpetizador """
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import os
import csv

lista_carpetizados = []
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
    label_carpeta.config(fg='darkgreen')
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
        elif "Elements14Tb_new" in nombre_carpeta:
            boton_new.config(state='normal', bg='lightgreen', fg='blue')
        elif "Elements14Tb_last" in nombre_carpeta:
            boton_last.config(state='normal', bg='lightgreen', fg='blue')
        elif "SeagateDesktop8Tb" in nombre_carpeta:
            boton_seagate.config(state='normal', bg='lightgreen', fg='blue')
        elif "UnionSine14Tb" in nombre_carpeta:
            boton_unionsine14.config(state='normal', bg='lightgreen', fg='blue')
        elif "Elements5Tb_Beta" in nombre_carpeta:
            boton_beta5tb.config(state='normal', bg='lightgreen', fg='blue')
        elif "Elements4Tb_Alpha" in nombre_carpeta:
            boton_alpha4tb.config(state='normal', bg='lightgreen', fg='blue')
        elif "MyPassport2018" in nombre_carpeta:
            boton_mpass2018.config(state='normal', bg='lightgreen', fg='blue')
        elif "Easystore8Tb" in nombre_carpeta:
            boton_easystore.config(state='normal', bg='lightgreen', fg='blue')
        elif "Elements12Tb" in nombre_carpeta:
            boton_elem12.config(state='normal', bg='lightgreen', fg='blue')
        elif "Elements4Tb_newSE" in nombre_carpeta:
            boton_newse.config(state='normal', bg='lightgreen', fg='blue')
        elif "Elements2Tb_Base1" in nombre_carpeta:
            boton_base1.config(state='normal', bg='lightgreen', fg='blue')
        elif "MyPassport2Tb_azul" in nombre_carpeta:
            boton_mpassazul.config(state='normal', bg='lightgreen', fg='blue')
        elif "MyPassport4Tb_blanco" in nombre_carpeta:
            boton_mpassblanco.config(state='normal', bg='lightgreen', fg='blue')
        elif "UnionSine10Tb" in nombre_carpeta:
            boton_unionsine10.config(state='normal', bg='lightgreen', fg='blue')
        elif "MyPassport2Tb_red" in nombre_carpeta:
            boton_mpassrojo.config(state='normal', bg='lightgreen', fg='blue')
        elif "Elements4Tb_SEcret" in nombre_carpeta:
            boton_secret.config(state='normal', bg='lightgreen', fg='blue')
        elif "Seagate10Tb_Expansion" in nombre_carpeta:
            boton_expansion.config(state='normal', bg='lightgreen', fg='blue')
        else:
            print("Carpeta no reconocida")
    else:
        label_carpeta.config(text="No se ha seleccionado ninguna carpeta")
        actualizar_estado_boton_crear()

def crear_archivo():
    """ fn crear archivo txt y csv """
    nombre_archivo = entrada_nombre.get()
    carpeta = label_carpeta.cget("text")
    carpeta2 = "C:/Users/Usuario/OneDrive/Escritorio/info_discos duros"

    if nombre_archivo and carpeta:
        ruta_txt = os.path.join(carpeta, f"{nombre_archivo}.txt")
        ruta_txt2 = os.path.join(carpeta2, f"{nombre_archivo}.txt")
        ruta_csv = os.path.join(carpeta, f"{nombre_archivo}.csv")
        ruta_csv2 = os.path.join(carpeta2, f"{nombre_archivo}.csv")

        with open(ruta_txt, 'w', encoding='utf-8') as archivo_txt, \
             open(ruta_csv, 'w', newline='', encoding='utf-8') as archivo_csv:

            csv_writer = csv.writer(archivo_csv)
            csv_writer.writerow(["Nombre", "Tamaño (GB)", "Origen"])

            for root, dirs, _ in os.walk(carpeta):
                for diri in dirs:
                    dir_path = os.path.join(root, diri)
                    #print(dir_path.split('/')[1])
                    size = sum(os.path.getsize(os.path.join(dir_path, f))
                               for f in os.listdir(dir_path)
                               if os.path.isfile(os.path.join(dir_path, f)))
                    size_gb = size / (1024 ** 3)
                    archivo_txt.write(f"{diri}: {size_gb:.2f} GB\n")
                    csv_writer.writerow([diri, f"{size_gb:.2f}", dir_path.split('/')[1]])
            print("archivo txt creado:", ruta_txt2)

        with open(ruta_txt2, 'w', encoding='utf-8') as archivo_txt, \
             open(ruta_csv2, 'w', newline='', encoding='utf-8') as archivo_csv:

            csv_writer = csv.writer(archivo_csv)
            csv_writer.writerow(["Nombre", "Tamaño (GB)", "Origen"])

            for root, dirs, _ in os.walk(carpeta):
                for diri in dirs:
                    dir_path = os.path.join(root, diri)
                    size = sum(os.path.getsize(os.path.join(dir_path, f))
                               for f in os.listdir(dir_path)
                               if os.path.isfile(os.path.join(dir_path, f)))
                    size_gb = size / (1024 ** 3)
                    archivo_txt.write(f"{diri}: {size_gb:.2f} GB\n")
                    csv_writer.writerow([diri, f"{size_gb:.2f}", dir_path.split('/')[1]])
            print("archivo csv creado:", ruta_csv2)

        #label_estado.config(text=f"Archivos creados: {ruta_txt}\n")

def dar_nombre(nombre):
    """ fn dar nombre """
    #print(nombre)
    entrada_nombre.delete(0, tk.END)
    entrada_nombre.insert(0, nombre)
    crear_archivo()

def nombre_old():
    """ fn nombre old """
    nombre_archivo = "Elements14Tb_old"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_old.config(state='disabled', bg='lightgray')

def nombre_new():
    """ fn nombre new """
    nombre_archivo = "Elements14Tb_new"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_new.config(state='disabled', bg='lightgray')

def nombre_last():
    """ fn nombre last """
    nombre_archivo = "Elements14Tb_last"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_last.config(state='disabled', bg='lightgray')

def nombre_seagate():
    """ fn nombre seagate """
    nombre_archivo = "SeagateDesktop8Tb"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_seagate.config(state='disabled', bg='lightgray')

def nombre_unionsine14():
    """ fn nombre unionsine14 """
    nombre_archivo = "UnionSine14Tb"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_unionsine14.config(state='disabled', bg='lightgray')

def nombre_beta5tb():
    """ fn nombre beta5tb """
    nombre_archivo = "Elements5Tb_Beta"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_beta5tb.config(state='disabled', bg='lightgray')

def nombre_alpha4tb():
    """ fn nombre alpha4tb """
    nombre_archivo = "Elements4Tb_Alpha"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_alpha4tb.config(state='disabled', bg='lightgray')

def nombre_mpass2018():
    """ fn nombre mpass2018 """
    nombre_archivo = "MyPassport2018"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_mpass2018.config(state='disabled', bg='lightgray')

def nombre_easystore():
    """ fn nombre easystore """
    nombre_archivo = "Easystore8Tb"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_easystore.config(state='disabled', bg='lightgray')

def nombre_elem12():
    """ fn nombre elem12 """
    nombre_archivo = "Elements12Tb"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_elem12.config(state='disabled', bg='lightgray')

def nombre_newse():
    """ fn nombre newse """
    nombre_archivo = "Elements4Tb_newSE"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_newse.config(state='disabled', bg='lightgray')

def nombre_secret():
    """ fn nombre secret """
    nombre_archivo = "Elements4Tb_SEcret"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_secret.config(state='disabled', bg='lightgray')

def nombre_base1():
    """ fn nombre base1 """
    nombre_archivo = "Elements2Tb_base1"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_base1.config(state='disabled', bg='lightgray')

def nombre_mpassazul():
    """ fn nombre mpassazul """
    nombre_archivo = "MyPassport2Tb_azul"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_mpassazul.config(state='disabled', bg='lightgray')

def nombre_mpassblanco():
    """ fn nombre mpassblanco """
    nombre_archivo = "MyPassport4Tb_blanco"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_mpassblanco.config(state='disabled', bg='lightgray')

def nombre_unionsine10():
    """ fn nombre unionsine10 """
    nombre_archivo = "UnionSine10Tb"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_unionsine10.config(state='disabled', bg='lightgray')

def nombre_mpassrojo():
    """ fn nombre mpassrojo """
    nombre_archivo = "MyPassport2Tb_red"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
    boton_mpassrojo.config(state='disabled', bg='lightgray')

def nombre_expansion():
    """ fn nombre expansion """
    nombre_archivo = "Seagate10Tb_Expansion"
    dar_nombre(nombre_archivo)
    lista_carpetizados.append(nombre_archivo)
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

# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Gestor de Archivos")
ventana.geometry("600x320")

# Botón para seleccionar carpeta
boton_seleccionar = tk.Button(ventana, text="Seleccionar Carpeta", width=30, fg='blue',
                              height=3, bg='lightblue', command=seleccionar_carpeta)
boton_seleccionar.pack(pady=5)

# Label para mostrar la carpeta seleccionada
label_carpeta = tk.Label(ventana, text="No se ha seleccionado ninguna carpeta",
                         fg='gray60', width=50)
label_carpeta.pack(pady=5)

# frame botones
frame_botones = tk.Frame(ventana)
frame_botones.pack(pady=5)

# Botones para seleccionar nombres
boton_old = tk.Button(frame_botones, text="Elements14Tb_old", width=20, command=nombre_old,
                      state='disabled', bg='lightgray')
boton_old.grid(pady=0, row=0, column=0)

boton_new = tk.Button(frame_botones, text="Elements14Tb_new", width=20, command=nombre_new,
                      state='disabled', bg='lightgray')
boton_new.grid(pady=0, row=0, column=1)

boton_last = tk.Button(frame_botones, text="Elements14Tb_last", width=20, command=nombre_last,
                       state='disabled', bg='lightgray')
boton_last.grid(pady=0, row=0, column=2)

boton_seagate = tk.Button(frame_botones, text="SeagateDesktop8Tb", width=20, command=nombre_seagate,
                          state='disabled', bg='lightgray')
boton_seagate.grid(pady=0, row=1, column=0)

boton_unionsine14 = tk.Button(frame_botones, text="UnionSine14Tb", width=20,
                              command=nombre_unionsine14, state='disabled', bg='lightgray')
boton_unionsine14.grid(pady=0, row=1, column=1)

boton_beta5tb = tk.Button(frame_botones, text="Elements5Tb_Beta", width=20, command=nombre_beta5tb,
                          state='disabled', bg='lightgray')
boton_beta5tb.grid(pady=0, row=1, column=2)

boton_alpha4tb = tk.Button(frame_botones, text="ElementsAlpha4Tb", width=20,
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

boton_newse = tk.Button(frame_botones, text="Elements_newSE", width=20, command=nombre_newse,
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

# Entrada para el nombre del archivo
entrada_nombre = tk.Entry(ventana, width=40, fg='gray60', state='disabled')
entrada_nombre.pack(padx=20, pady=5, side='left')
entrada_nombre.insert(0, "Nombre")
entrada_nombre.bind("<KeyRelease>", lambda event: actualizar_estado_boton_crear())


# Botón para crear el archivo
boton_crear = tk.Button(ventana, text="Crear Archivo", height=3, width=15,
                        command=crear_archivo, state='disabled', borderwidth=0)
boton_crear.pack(padx=0, pady=5, side='left')

# Botón para mostrar los archivos creados
boton_mostrar = tk.Button(ventana, text="Mostrar Archivos", height=3, width=15,
                          command=mostrar_archivos, state='normal', borderwidth=0)
boton_mostrar.pack(padx=0, pady=5, side='left')

# Label para mostrar el estado
label_estado = tk.Label(ventana, text="")
label_estado.pack(pady=5, side='bottom')

# Iniciar el bucle principal de la interfaz
ventana.mainloop()
