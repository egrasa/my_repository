""" Programa para leer elementos de un archivo CSV de la tabla periódica."""

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import IntVar, Checkbutton
import csv
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# --- Clase Tooltip ---
class ToolTip:
    """ Clase para crear tooltips en widgets de Tkinter """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        """ Muestra el tooltip en la posición del cursor """
        if self.tipwindow or not self.text:
            return
        eventos = []
        eventos.append(event)
        x, y, cx, cy = self.widget.bbox("insert") if self.widget.winfo_ismapped() else (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 40 + cx
        y = y + self.widget.winfo_rooty() + 20 + cy
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#e2e2d8", relief='solid', borderwidth=1,
                         font=("courier new", 12), fg="#052A8D")
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        """ Oculta el tooltip """
        eventos = []
        eventos.append(event)
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class Elemento:
    """ Clase para representar un elemento de la tabla periódica """
    def __init__(
        self,
        atomic_number,
        element,
        symbol,
        atomic_mass,
        number_of_neutrons,
        number_of_protons,
        number_of_electrons,
        period,
        group,
        phase,
        radioactive,
        natural,
        metal,
        nonmetal,
        metalloid,
        type_,
        atomic_radius,
        electronegativity,
        first_ionization,
        density,
        melting_point,
        boiling_point,
        number_of_isotopes,
        discoverer,
        year,
        specific_heat,
        number_of_shells,
        number_of_valence
    ):
        self.atomic_number = atomic_number
        self.element = element
        self.symbol = symbol
        self.atomic_mass = atomic_mass
        self.number_of_neutrons = number_of_neutrons
        self.number_of_protons = number_of_protons
        self.number_of_electrons = number_of_electrons
        self.period = period
        self.group = group
        self.phase = phase
        self.radioactive = radioactive
        self.natural = natural
        self.metal = metal
        self.nonmetal = nonmetal
        self.metalloid = metalloid
        self.type_ = type_
        self.atomic_radius = atomic_radius
        self.electronegativity = electronegativity
        self.first_ionization = first_ionization
        self.density = density
        self.melting_point = melting_point
        self.boiling_point = boiling_point
        self.number_of_isotopes = number_of_isotopes
        self.discoverer = discoverer
        self.year = year
        self.specific_heat = specific_heat
        self.number_of_shells = number_of_shells
        self.number_of_valence = number_of_valence

    def __repr__(self):
        return f"{self.element} ({self.symbol}), Z={self.atomic_number}"

# Lista global para almacenar los elementos leídos
elementos = []
boton_seleccionado = [None]

def graficar_generico(x, y, titulo, xlabel, ylabel, color='#4682B4', etiquetas=None):
    """Genera una gráfica genérica de barras o líneas según el tipo seleccionado."""
    tipo = tipo_grafica.get()
    plt.style.use('ggplot')
    etiquetas_x = etiquetas if etiquetas is not None else x
    if tipo == "barras":
        plt.figure(figsize=(14,6))
        bars = plt.bar(etiquetas_x, y, color=color)
        plt.title(titulo)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation=90)
        for barras1, valor in zip(bars, y):
            plt.text(barras1.get_x() + barras1.get_width()/2, barras1.get_height(), f"{valor:.2f}",
                     ha='center', va='bottom', fontsize=9, color='black')
        plt.tight_layout()
        plt.show()
    elif tipo == "lineas":
        plt.figure(figsize=(14,6))
        plt.plot(x, y, marker='o', color=color)
        plt.title(titulo)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.show()
    elif tipo == "radar":
        if len(x) < 3:
            messagebox.askokcancel("Atención",
                                   "Se necesitan al menos 3 valores para una gráfica radar.")
            return
        valores = y + [y[0]]
        etiquetas = x + [x[0]]
        n1 = len(x)
        angles = np.linspace(0, 2 * np.pi, n1 + 1, endpoint=True)
        plt.figure(figsize=(7, 7))
        ax = plt.subplot(111, polar=True)
        ax.plot(angles, valores, linewidth=2, linestyle='solid', color=color)
        ax.fill(angles, valores, color=color, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(x, fontsize=10)
        plt.title(titulo, y=1.08)
        plt.tight_layout()
        plt.show()

def leer_elementos():
    """ Lee los elementos de un archivo CSV, los instancia en la clase Elemento 
    y los muestra en un Text widget """
    ruta = os.path.join(os.path.dirname(__file__), "tabla_periodica2.csv")
    elementos.clear()
    try:
        with open(ruta, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                elemento = Elemento(
                    row.get("AtomicNumber", ""),
                    row.get("Element", ""),
                    row.get("Symbol", ""),
                    row.get("AtomicMass", ""),
                    row.get("NumberofNeutrons", ""),
                    row.get("NumberofProtons", ""),
                    row.get("NumberofElectrons", ""),
                    row.get("Period", ""),
                    row.get("Group", ""),
                    row.get("Phase", ""),
                    row.get("Radioactive", ""),
                    row.get("Natural", ""),
                    row.get("Metal", ""),
                    row.get("Nonmetal", ""),
                    row.get("Metalloid", ""),
                    row.get("Type", ""),
                    row.get("AtomicRadius", ""),
                    row.get("Electronegativity", ""),
                    row.get("FirstIonization", ""),
                    row.get("Density", ""),
                    row.get("MeltingPoint", ""),
                    row.get("BoilingPoint", ""),
                    row.get("NumberOfIsotopes", ""),
                    row.get("Discoverer", ""),
                    row.get("Year", ""),
                    row.get("SpecificHeat", ""),
                    row.get("NumberofShells", ""),
                    row.get("NumberofValence", "")
                )
                elementos.append(elemento)
    except (FileNotFoundError, csv.Error, OSError) as e:
        messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
        return

    # Limpiar el texto antes de mostrar
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    if elementos:
        for elemento in elementos:
            linea = ", ".join(f"{k}: {v}" for k, v in vars(elemento).items())
            texto_resultado.insert(tk.END, linea + "\n")
    else:
        texto_resultado.insert(tk.END, "No se encontraron elementos en el archivo.")
    texto_resultado.config(state="disabled")

def buscar_elemento():
    """Busca un elemento por nombre o número atómico y muestra su información
    en el panel de texto y en los labels principales"""
    busqueda = entry_buscar.get().strip().lower()
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    if not busqueda:
        messagebox.askokcancel("Atención", "Introduce un nombre o número atómico para buscar.")
        return

    encontrado = None
    for elem8 in elementos:
        if elem8.element.lower() == busqueda or elem8.atomic_number == busqueda:
            encontrado = elem8
            break
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    if encontrado:
        # Actualiza los labels
        label_z.config(text=f" {encontrado.atomic_number} ")
        label_nombre.config(text=f" {encontrado.element}")
        label_simbolo.config(text=f" {encontrado.symbol}")
        mostrar_elemento_en_columnas_tab(encontrado)
    else:
        label_z.config(text="Z ")
        label_nombre.config(text="Nombre: ")
        label_simbolo.config(text="Símbolo: ")
        texto_resultado.insert(tk.END, "Elemento no encontrado.")
    texto_resultado.config(state="disabled")

def seleccionar_por_z(z):
    """Selecciona un elemento por su número atómico (Z) y actualiza los labels 
    y el relief del botón"""
    entry_buscar.delete(0, tk.END)
    entry_buscar.insert(0, str(z))
    buscar_elemento()

    # Cambiar relief del botón seleccionado y restaurar el anterior
    if boton_seleccionado[0] is not None:
        try:
            boton_seleccionado[0].config(relief="raised", borderwidth=1)
        except (tk.TclError, AttributeError):
            messagebox.showerror("Error", "No se pudo restaurar el botón.")
    btn = botones_por_z.get(str(z))
    if btn:
        btn.config(relief="sunken", borderwidth=2)
        boton_seleccionado[0] = btn

def mostrar_metales():
    """Muestra un listado de elementos que tienen 'yes' en el parámetro Metal
    y cambia color de sus botones"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    metales = [e for e in elementos if str(e.metal).strip().lower() == "yes"]
    # Cambiar color de los botones de metales
    #for boton in botones_por_z.values():
        #boton.config(bg="SystemButtonFace")  # Restaurar color por defecto
    for elem7 in metales:
        z = str(elem7.atomic_number)
        if z in botones_por_z:
            botones_por_z[z].config(bg="#586370")
    if metales:
        for elem7 in metales:
            texto_resultado.insert(
                tk.END, f"{elem7.atomic_number}: {elem7.element} ({elem7.symbol})\n")
    else:
        texto_resultado.insert(tk.END, "No se encontraron elementos metálicos.")
    texto_resultado.config(state="disabled")

def mostrar_gases():
    """Muestra un listado de elementos que tienen 'Gas' en el parámetro Phase
    y cambia color de sus botones"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    gases = [e for e in elementos if str(e.phase).strip().lower() == "gas"]
    # Cambiar color de los botones de gases
    #for btn in botones_por_z.values():
        #btn.config(bg="SystemButtonFace")  # Restaurar color por defecto
    for elem6 in gases:
        z = str(elem6.atomic_number)
        if z in botones_por_z:
            botones_por_z[z].config(bg="#87CEEB")  # Azul claro
    if gases:
        for elem6 in gases:
            texto_resultado.insert(
                tk.END, f"{elem6.atomic_number}: {elem6.element} ({elem6.symbol})\n")
    else:
        texto_resultado.insert(tk.END, "No se encontraron elementos en fase gas.")
    texto_resultado.config(state="disabled")

def mostrar_gases_nobles():
    """Muestra un listado de elementos que tienen 'Noble Gas' en el parámetro Type
    y cambia color de sus botones"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    gases_nobles = [e for e in elementos if str(e.type_).strip() == "Noble Gas"]
    # Cambiar color de los botones de gases nobles
    #for boton_gas in botones_por_z.values():
        #boton_gas.config(bg="SystemButtonFace")  # Restaurar color por defecto
    for elem5 in gases_nobles:
        z = str(elem5.atomic_number)
        if z in botones_por_z:
            botones_por_z[z].config(bg="#A020F0")  # Morado
    if gases_nobles:
        for elem5 in gases_nobles:
            texto_resultado.insert(
                tk.END, f"{elem5.atomic_number}: {elem5.element} ({elem5.symbol})\n")
    else:
        texto_resultado.insert(tk.END, "No se encontraron gases nobles.")
    texto_resultado.config(state="disabled")

def mostrar_actinidos():
    """Muestra un listado de elementos que tienen 'Actinide' en el parámetro Type
    y cambia color de sus botones"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    actinidos = [e for e in elementos if str(e.type_).strip() == "Actinide"]
    # Cambiar color de los botones de actínidos
    #for boton_actinido in botones_por_z.values():
        #boton_actinido.config(bg="SystemButtonFace")  # Restaurar color por defecto
    for elem4 in actinidos:
        z = str(elem4.atomic_number)
        if z in botones_por_z:
            botones_por_z[z].config(bg="#704D19")  # Naranja oscuro
    if actinidos:
        for elem4 in actinidos:
            texto_resultado.insert(
                tk.END, f"{elem4.atomic_number}: {elem4.element} ({elem4.symbol})\n")
    else:
        texto_resultado.insert(tk.END, "No se encontraron actínidos.")
    texto_resultado.config(state="disabled")

def mostrar_lantanidos():
    """Muestra un listado de elementos que tienen 'Lanthanide' en el parámetro Type
    y cambia color de sus botones"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    lantanidos = [e for e in elementos if str(e.type_).strip() == "Lanthanide"]
    # Cambiar color de los botones de lantánidos
    #for boton_lantanido in botones_por_z.values():
        #boton_lantanido.config(bg="SystemButtonFace")  # Restaurar color por defecto
    for elem3 in lantanidos:
        z = str(elem3.atomic_number)
        if z in botones_por_z:
            botones_por_z[z].config(bg="#BB9F03")  # Dorado
    if lantanidos:
        for elem3 in lantanidos:
            texto_resultado.insert(
                tk.END, f"{elem3.atomic_number}: {elem3.element} ({elem3.symbol})\n")
    else:
        texto_resultado.insert(tk.END, "No se encontraron lantánidos.")
    texto_resultado.config(state="disabled")

def mostrar_radiactivos_fg_verde():
    """Cambia el color del texto (fg) de los botones de los elementos radiactivos a verde"""
    for elem_r in elementos:
        if str(elem_r.radioactive).strip().lower() == "yes":
            z = str(elem_r.atomic_number)
            if z in botones_por_z:
                botones_por_z[z].config(fg="#1CAD1C")
        else:
            z = str(elem_r.atomic_number)
            if z in botones_por_z:
                botones_por_z[z].config(fg="black")  # Restaurar color por defecto

def resetear():
    """Restaura la interfaz al estado inicial"""
    # Restaurar labels
    label_z.config(text="Z ")
    label_nombre.config(text="Nombre: ")
    label_simbolo.config(text="Símbolo: ")
    # Restaurar cuadro de texto
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    texto_resultado.config(state="disabled")
    # Restaurar color de los botones
    for btn in botones_por_z.values():
        btn.config(bg="SystemButtonFace")
    # Restaurar campo de búsqueda
    entry_buscar.delete(0, tk.END)
    entry_buscar.insert(0, "Hydrogen")
    mostrar_metales()
    mostrar_gases()
    mostrar_gases_nobles()
    mostrar_actinidos()
    mostrar_lantanidos()

def mostrar_elemento_en_columnas_tab(elemento):
    """Muestra los atributos del elemento en un Text widget en formato de columnas"""
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    texto_resultado.insert(tk.END, "Atributo\t\t\t Valor\n")
    texto_resultado.insert(tk.END, "---------\t\t\t-------\n")
    for k, v in vars(elemento).items():
        texto_resultado.insert(tk.END, f"{k}\t\t\t  {v}\n")
    texto_resultado.config(state="disabled")

def mostrar_grafica_elemento():
    """Muestra una gráfica de barras con los parámetros seleccionados del elemento"""
    busqueda = entry_buscar.get().strip().lower()
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    if not busqueda:
        messagebox.askokcancel("Atención", "Introduce un nombre o número atómico para buscar.")
        return

    encontrado = None
    for elem2 in elementos:
        if elem2.element.lower() == busqueda or elem2.atomic_number == busqueda:
            encontrado = elem2
            break

    if not encontrado:
        messagebox.askokcancel("Elemento no encontrado", "No se encontró el elemento buscado.")
        return

    try:
        protones = int(encontrado.number_of_protons)
        neutrones = int(encontrado.number_of_neutrons)
        electrones = int(encontrado.number_of_electrons)
        #total = protones + neutrones + electrones
        #proton_a = protones / total * 10 if total else 0
        #neutro_a = neutrones / total * 10 if total else 0
        #electron_a = electrones / total * 10 if total else 0
        radio = float(
            encontrado.atomic_radius) if encontrado.atomic_radius not in ("", None) else 0
        electroneg = float(
            encontrado.electronegativity) if encontrado.electronegativity not in ("", None) else 0
        isotopos = int(
            encontrado.number_of_isotopes) if encontrado.number_of_isotopes not in ("", None) else 0
        shells = int(
            encontrado.number_of_shells) if encontrado.number_of_shells not in ("", None) else 0
        valencia = int(
            encontrado.number_of_valence) if encontrado.number_of_valence not in ("", None) else 0
        densidad = float(
            encontrado.density) if encontrado.density not in ("", None) else 0
        punto_fusion = float(
            encontrado.melting_point) if encontrado.melting_point not in ("", None) else 0
        punto_ebullicion = float(
            encontrado.boiling_point) if encontrado.boiling_point not in ("", None) else 0
    except (ValueError, TypeError):
        messagebox.showerror("Error", "No se pudo obtener la información numérica del elemento.")
        return

    # Diccionario para acceder a los valores por clave
    valores_dict = {
        "protones": protones,
        "neutrones": neutrones,
        "electrones": electrones,
        "radio": radio,
        "electroneg": electroneg,
        "isotopos": isotopos,
        "shells": shells,
        "valencia": valencia,
        "densidad": densidad,
        "punto_fusion": punto_fusion,
        "punto_ebullicion": punto_ebullicion,
    }

    etiquetas = []
    valores = []
    colores = [
        '#FF6347', '#4682B4', '#32CD32', '#FFD700', '#8A2BE2', '#A0522D',
        '#00CED1', '#FF1493', '#8A2BE2', '#FF8C00', '#00BFFF', '#FF4500',
        '#2E8B57','#D2691E', '#FF69B4', '#8B4513', '#7FFF00', '#DC143C'
        ]
    colores_usados = []

    for idx, (texto_graf, clave_graf) in enumerate(parametros_grafica):
        if vars_grafica[clave_graf].get():
            etiquetas.append(texto_graf)
            valores.append(valores_dict[clave_graf])
            colores_usados.append(colores[idx])

    if not etiquetas:
        messagebox.askokcancel("Atención", "Selecciona al menos un parámetro para la gráfica.")
        return

    plt.figure(figsize=(13,5))
    bars = plt.bar(etiquetas, valores, color=colores_usados)
    plt.title(f"{encontrado.element} ({encontrado.symbol}) - Z={encontrado.atomic_number}")
    plt.ylabel("Valor")
    plt.xticks(rotation=45)

    for bar1, valor in zip(bars, valores):
        plt.text(bar1.get_x() + bar1.get_width()/2, bar1.get_height(), f"{valor:.2f}",
                 ha='center', va='bottom', fontsize=9, color='black')

    plt.tight_layout()
    plt.show()

def mostrar_grafica_radio_atomico():
    """Muestra una gráfica de barras con los valores de radio atómico de todos los elementos"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    nombres = []
    radios = []
    for elemento in elementos:
        try:
            radio = float(
                elemento.atomic_radius) if elemento.atomic_radius not in ("", None) else None
        except ValueError:
            radio = None
        if radio is not None:
            nombres.append(f"{elemento.symbol} ({elemento.atomic_number})")
            radios.append(radio)
    if not radios:
        messagebox.askokcancel("Sin datos", "No hay valores de radio atómico disponibles.")
        return
    graficar_generico(nombres, radios, "Radio Atómico de los Elementos",
                      "Elemento (Símbolo y Z)", "Radio Atómico", color='#4682B4')

def mostrar_grafica_melting_point():
    """Muestra una gráfica de barras con los valores de punto de fusión de todos los elementos"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    nombres = []
    melting_points = []
    for elem1 in elementos:
        try:
            mp = float(elem1.melting_point) if elem1.melting_point not in ("", None) else None
        except ValueError:
            mp = None
        if mp is not None:
            nombres.append(f"{elem1.symbol} ({elem1.atomic_number})")
            melting_points.append(mp)
    if not melting_points:
        messagebox.askokcancel("Sin datos", "No hay valores de punto de fusión disponibles.")
        return
    graficar_generico(nombres, melting_points, "Punto de Fusión de los Elementos",
                      "Elemento (Símbolo y Z)", "Punto de Fusión (K)", color='#FF6347')

def mostrar_grafica_boiling_point():
    """Muestra una gráfica de barras con los valores de punto de ebullición 
    de todos los elementos"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    nombres = []
    boiling_points = []
    for elem_boiling in elementos:
        try:
            bp = float(
                elem_boiling.boiling_point) if elem_boiling.boiling_point not in ("",
                                                                                  None) else None
        except ValueError:
            bp = None
        if bp is not None:
            nombres.append(f"{elem_boiling.symbol} ({elem_boiling.atomic_number})")
            boiling_points.append(bp)
    if not boiling_points:
        messagebox.askokcancel("Sin datos", "No hay valores de punto de ebullición disponibles.")
        return
    graficar_generico(nombres, boiling_points, "Punto de Ebullición de los Elementos",
                      "Elemento (Símbolo y Z)", "Punto de Ebullición (K)", color='#008080')

def mostrar_grafica_densidad():
    """Muestra una gráfica de barras con los valores de densidad de todos los elementos"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    nombres = []
    densidades = []
    for elemento_densidad in elementos:
        try:
            densidad = float(
                elemento_densidad.density) if elemento_densidad.density not in ("", None) else None
        except ValueError:
            densidad = None
        if densidad is not None:
            nombres.append(f"{elemento_densidad.symbol} ({elemento_densidad.atomic_number})")
            densidades.append(densidad)
    if not densidades:
        messagebox.askokcancel("Sin datos", "No hay valores de densidad disponibles.")
        return
    graficar_generico(nombres, densidades, "Densidad de los Elementos", "Elemento (Símbolo y Z)",
                      "Densidad (g/cm³)", color='#8A2BE2')

def mostrar_grafica_specific_heat():
    """Muestra una gráfica de barras con los valores de specific_heat de todos los elementos"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    nombres = []
    specific_heats = []
    for elem0 in elementos:
        try:
            sh = float(elem0.specific_heat) if elem0.specific_heat not in ("", None) else None
        except ValueError:
            sh = None
        if sh is not None:
            nombres.append(f"{elem0.symbol} ({elem0.atomic_number})")
            specific_heats.append(sh)
    if len(specific_heats) < 1:
        messagebox.askokcancel("Sin datos",
                               "No hay valores de specific_heat disponibles para graficar.")
        return
    graficar_generico(nombres, specific_heats, "Specific Heat de todos los elementos",
                      "Elemento (Símbolo y Z)", "Specific Heat", color='#FF8C00')

def mostrar_busqueda_avanzada():
    """Ventana para búsqueda avanzada por propiedades"""
    resetear()
    mostrar_metales()
    mostrar_gases()
    mostrar_gases_nobles()
    mostrar_actinidos()
    mostrar_lantanidos()
    def buscar():
        prop = combo_prop.get()
        op = combo_op.get()
        valor = entry_valor.get().strip()
        if not prop or not op or not valor:
            messagebox.askokcancel("Atención", "Completa todos los campos.")
            return
        resultados = []
        for e in elementos:
            v = getattr(e, prop, "")
            try:
                # Convertir a float si es posible
                v_num = float(v)
                valor_num = float(valor)
                if op == "=" and v_num == valor_num:
                    resultados.append(e)
                elif op == ">" and v_num > valor_num:
                    resultados.append(e)
                elif op == "<" and v_num < valor_num:
                    resultados.append(e)
                elif op == ">=" and v_num >= valor_num:
                    resultados.append(e)
                elif op == "<=" and v_num <= valor_num:
                    resultados.append(e)
            except (ValueError, TypeError):
                # Comparación de texto
                if op == "=" and str(v).lower() == valor.lower():
                    resultados.append(e)
        texto_resultado.config(state="normal")
        texto_resultado.delete(1.0, tk.END)
        texto_resultado.insert(tk.END, f"Resultados para {prop} {op} {valor}:\n")
        if resultados:
            for elem9 in resultados:
                texto_resultado.insert(tk.END,
                                       f"{elem9.atomic_number}: {elem9.element} ({elem9.symbol})\n")
                botones_por_z[str(elem9.atomic_number)].config(bg='lightgreen', borderwidth=2)
        else:
            texto_resultado.insert(tk.END, "No se encontraron elementos con esos criterios.")
        texto_resultado.config(state="disabled")
        win.destroy()

    win = tk.Toplevel(root)
    win.title("Búsqueda avanzada")
    win.geometry("400x150")
    tk.Label(win, text="Propiedad:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5)
    tk.Label(win, text="Operador:", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady=5)
    tk.Label(win, text="Valor:", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=5)

    # Lista de propiedades numéricas y de texto útiles
    propiedades = [
        ("atomic_number", "Z"),
        ("element", "Nombre"),
        ("symbol", "Símbolo"),
        ("atomic_mass", "Masa"),
        ("number_of_neutrons", "Neutrones"),
        ("number_of_protons", "Protones"),
        ("number_of_electrons", "Electrones"),
        ("period", "Periodo"),
        ("group", "Grupo"),
        ("phase", "Fase"),
        ("radioactive", "Radiactivo"),
        ("metal", "Metal"),
        ("nonmetal", "No metal"),
        ("metalloid", "Metaloide"),
        ("type_", "Tipo"),
        ("atomic_radius", "Radio atómico"),
        ("electronegativity", "Electronegatividad"),
        ("density", "Densidad"),
        ("melting_point", "Fusión"),
        ("boiling_point", "Ebullición"),
        ("specific_heat", "Specific Heat"),
        ("number_of_isotopes", "Isótopos"),
        ("discoverer", "Descubridor"),
        ("year", "Año"),
        ("number_of_shells", "Shells"),
        ("number_of_valence", "Valencia")
    ]

    combo_prop = ttk.Combobox(win, values=[p[0] for p in propiedades], width=20)
    combo_prop.grid(row=0, column=1, padx=5, pady=5)
    combo_op = ttk.Combobox(win, values=["=", ">", "<", ">=", "<="], width=5)
    combo_op.set("=")  # Valor por defecto
    combo_op.grid(row=1, column=1, padx=5, pady=5)
    entry_valor = ttk.Entry(win, width=20)
    entry_valor.grid(row=2, column=1, padx=5, pady=5)

    boton_buscar_inside = ttk.Button(win, text="Buscar", command=buscar)
    boton_buscar_inside.bind("<Return>", lambda event: buscar())
    boton_buscar_inside.grid(row=3, column=1, columnspan=2, pady=5)

def representar_atomo():
    """Representa gráficamente el átomo seleccionado (modelo Bohr simplificado 
    y colores por subniveles)"""
    busqueda = entry_buscar.get().strip().lower()
    if not elementos:
        messagebox.showinfo("Atención", "Primero debes leer los elementos.")
        return
    if not busqueda:
        messagebox.showinfo("Atención", "Introduce un nombre o número atómico para buscar.")
        return

    encontrado = None
    for elemh1 in elementos:
        if elemh1.element.lower() == busqueda or elemh1.atomic_number == busqueda:
            encontrado = elemh1
            break

    if not encontrado:
        messagebox.showinfo("Elemento no encontrado", "No se encontró el elemento buscado.")
        return

    try:
        protones = int(encontrado.number_of_protons)
        neutrones = int(encontrado.number_of_neutrons)
        electrones = int(encontrado.number_of_electrons)
        # Niveles electrónicos: lista con número de electrones por nivel
        niveles = []
        if encontrado.number_of_shells and encontrado.number_of_electrons:
            total_shells = int(encontrado.number_of_shells)
            total_e = int(encontrado.number_of_electrons)
            distribucion = [2, 8, 18, 32, 32, 18, 8]
            e_restantes = total_e
            for max_e in distribucion[:total_shells]:
                if e_restantes > max_e:
                    niveles.append(max_e)
                    e_restantes -= max_e
                else:
                    niveles.append(e_restantes)
                    break
        else:
            niveles = [electrones]  # fallback

    except (ValueError, TypeError):
        messagebox.showerror("Error", "No se pudo obtener la información numérica del elemento.")
        return

    # --- Dibujo ---
    _, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.axis('off')

    # Núcleo
    ax.add_patch(plt.Circle((0, 0), 1.5, color='lightblue', label='Núcleo'))
    ax.text(0, 0.5, f'P: {protones}', ha='center', fontsize=6)
    ax.text(0, -0.5, f'N: {neutrones}', ha='center', fontsize=6)

    # Colores por subnivel
    colores = ['#1E90FF', '#32CD32', '#FFA500', '#FF3030']  # azul, verde, naranja, rojo

    radio_base = 4
    nucleo = protones + neutrones
    for i, num_e in enumerate(niveles):
        radio = radio_base + i * ((2 + protones + electrones) / nucleo)
        ax.add_patch(plt.Circle((0, 0), radio, fill=False, linestyle='dotted'))
        # Asignar colores según la posición del electrón en el nivel
        for j in range(num_e):
            # Determinar color según la posición
            if j < 2:
                color = colores[0]  # azul
            elif j < 8:
                color = colores[1]  # verde
            elif j < 18:
                color = colores[2]  # naranja
            else:
                color = colores[3]  # rojo
            angle = 2 * np.pi * j / num_e
            x = radio * np.cos(angle)
            y = radio * np.sin(angle)
            ax.plot(x, y, 'o', color=color, markersize=6)

    # Leyenda para los subniveles
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label="Grupo 's'",
               markerfacecolor=colores[0], markersize=8),
        Line2D([0], [0], marker='o', color='w', label="Grupo 'p'",
               markerfacecolor=colores[1], markersize=8),
        Line2D([0], [0], marker='o', color='w', label="Grupo 'd'",
               markerfacecolor=colores[2], markersize=8),
        Line2D([0], [0], marker='o', color='w', label="Grupo 'f'",
               markerfacecolor=colores[3], markersize=8),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8, frameon=False)

    plt.title(f'{encontrado.element} (Modelo Bohr)')
    plt.show()

def mostrar_protones_igual_neutrones():
    """Muestra un listado de elementos que tienen el mismo número de protones que de neutrones"""
    if not elementos:
        messagebox.askokcancel("Atención", "Primero debes leer los elementos.")
        return
    texto_resultado.config(state="normal")
    texto_resultado.delete(1.0, tk.END)
    iguales = []
    for e in elementos:
        try:
            protones = int(e.number_of_protons)
            neutrones = int(e.number_of_neutrons)
            if protones == neutrones:
                iguales.append(e)
        except ValueError:
            continue
    if iguales:
        for igual_elem in iguales:
            texto_resultado.insert(tk.END,
                                   f"{igual_elem.atomic_number}: {igual_elem.element}"
                                   f" ({igual_elem.symbol})\n")
    else:
        texto_resultado.insert(tk.END,
                               "No se encontraron elementos con igual número de protones"
                               "y neutrones.")
    texto_resultado.config(state="disabled")

root = tk.Tk()
root.title("Tabla Periódica de los Elementos")
root.geometry("1100x1000")  # Ventana más grande

tipo_grafica = tk.StringVar(value="barras")

frame_top = tk.Frame(root)
frame_top.pack(pady=5)

# Añade estos labels después de crear frame_top y antes del Text
frame_labels = tk.Frame(root)
frame_labels.pack(pady=5)

# Crear un frame para los botones de los elementos
frame_botones = tk.Frame(root)
frame_botones.pack(pady=5)

frame_graficas = tk.LabelFrame(root, text="Gráficas", font=("Arial", 12), borderwidth=0)
frame_graficas.pack(pady=5, padx=15, expand=True, fill=tk.X)

frame_tipo_grafica = tk.Frame(frame_graficas)
frame_tipo_grafica.pack(side="right", padx=10)

frame_checks = tk.Frame(root)
frame_checks.pack(side="right", padx=10, pady=10, anchor="n")

label_z = tk.Label(frame_labels, text=" ", font=("Arial", 20, "bold"), width=10,
                   anchor="w")
label_z.pack(side=tk.LEFT, padx=5)
label_nombre = tk.Label(frame_labels, text="Elemento ", font=("Arial", 16, "bold"),
                        width=20, anchor="w")
label_nombre.pack(side=tk.LEFT, padx=5)
label_simbolo = tk.Button(frame_labels, text=" ", font=("Arial", 20, "bold"), bg="lightgray",
                         width=4, anchor="w", command= mostrar_grafica_elemento)
label_simbolo.pack(side=tk.LEFT, padx=5)

#tk.Label(frame_tipo_grafica, text="Tipo de gráfica:", font=("Arial", 10, "bold")).pack(anchor="w")
tk.Radiobutton(frame_tipo_grafica, text="Barras", variable=tipo_grafica, value="barras",
               font=("Arial", 10)).pack(anchor="w", side="left")
tk.Radiobutton(frame_tipo_grafica, text="Líneas", variable=tipo_grafica, value="lineas",
               font=("Arial", 10)).pack(anchor="w", side="left")
tk.Radiobutton(frame_tipo_grafica, text="Radar", variable=tipo_grafica, value="radar",
               font=("Arial", 10)).pack(anchor="w", side="left")

#boton_leer = tk.Button(frame_top, text="Leer elementos", command=leer_elementos,
                       #font=("Arial", 12))
#boton_leer.pack(side=tk.LEFT, padx=5)

parametros_grafica = [
    ("Protones", "protones"),
    ("Neutrones", "neutrones"),
    ("Electrones", "electrones"),
    ("Radio Atómico", "radio"),
    ("Electronegatividad", "electroneg"),
    ("Isótopos", "isotopos"),
    ("Shells", "shells"),
    ("Valencia", "valencia"),
    ("Densidad", "densidad"),
    ("Fusión (K)", "punto_fusion"),
    ("Ebullición (K)", "punto_ebullicion"),
]

vars_grafica = {}

def marcar_todos():
    """Marca todos los parámetros de la gráfica"""
    for v in vars_grafica.values():
        v.set(1)

def desmarcar_todos():
    """Desmarca todos los parámetros de la gráfica"""
    for v in vars_grafica.values():
        v.set(0)

boton_marcar_todos = tk.Button(frame_checks, text="todos", width=10, bg="lightgray",
                               command=marcar_todos, font=("Arial", 9), relief="groove")
boton_marcar_todos.pack(side="top", pady=(0, 2), anchor="w")

boton_desmarcar_todos = tk.Button(frame_checks, text="ninguno", width=10, bg="lightgray",
                                  command=desmarcar_todos, font=("Arial", 9), relief="groove")
boton_desmarcar_todos.pack(side="top", pady=(0, 2), anchor="w")

for texto, clave in parametros_grafica:
    var = IntVar(value=1)  # Por defecto activados
    chk = Checkbutton(frame_checks,
                      text=texto,
                      variable=var,
                      font=("Arial", 10),
                      anchor="w",
                      width=18)
    chk.pack(side="top", pady=1, anchor="w")  # De arriba a abajo
    vars_grafica[clave] = var

entry_buscar = tk.Entry(frame_top, font=("Arial", 12), width=20)
entry_buscar.pack(side=tk.LEFT, padx=5)
entry_buscar.insert(0, "Hydrogen")  # Valor por defecto

boton_buscar = tk.Button(frame_top, text="Buscar", command=buscar_elemento,
                          font=("Arial", 10))
entry_buscar.bind("<Return>", lambda event: buscar_elemento())
boton_buscar.pack(side=tk.LEFT, padx=5)

boton_busqueda_avanzada = tk.Button(frame_top, text="Búsqueda avanzada",
                                    command=mostrar_busqueda_avanzada, font=("Arial", 10))
boton_busqueda_avanzada.pack(side=tk.LEFT, padx=5)

boton_atomo = tk.Button(frame_top, text="Átomo (Bohr)", command=representar_atomo,
                        font=("Arial", 10), bg="lightgray")
boton_atomo.pack(side=tk.LEFT, padx=5)

boton_metal = tk.Button(frame_top, text="Metal", borderwidth=0,
                        command=mostrar_metales, font=("new courier", 8))
boton_metal.pack(side=tk.LEFT, padx=5)

boton_gas = tk.Button(frame_top, text="Gas", borderwidth=0,
                      command=mostrar_gases, font=("new courier", 8))
boton_gas.pack(side=tk.LEFT, padx=5)

boton_gas_noble = tk.Button(frame_top, text="Gas Noble", borderwidth=0,
                            command=mostrar_gases_nobles, font=("new courier", 8))
boton_gas_noble.pack(side=tk.LEFT, padx=5)

boton_lantanido = tk.Button(frame_top, text="Lantánido", borderwidth=0,
                            command=mostrar_lantanidos, font=("new courier", 8))
boton_lantanido.pack(side=tk.LEFT, padx=5)

boton_actinido = tk.Button(frame_top, text="Actínido", borderwidth=0,
                           command=mostrar_actinidos, font=("new courier", 8))
boton_actinido.pack(side=tk.LEFT, padx=5)

#boton_x = tk.Button(frame_top, text="X", command=mostrar_protones_igual_neutrones,
                    #font=("new courier", 8))
#boton_x.pack(side=tk.LEFT, padx=5)

boton_reset = tk.Button(frame_top, text="Resetear", command=resetear, font=("new courier", 8))
boton_reset.pack(side=tk.LEFT, padx=5)

boton_grafica = tk.Button(frame_graficas, text="radios atomicos", height=1, width=12,
                          relief="ridge", command=mostrar_grafica_radio_atomico,
                          font=("Arial", 10))
boton_grafica.pack(pady=2, side="left")

boton_grafica_melting = tk.Button(frame_graficas, text="fusión", height=1, width=12,
                                  relief="ridge", command=mostrar_grafica_melting_point,
                                  font=("Arial", 10))
boton_grafica_melting.pack(pady=2, side="left")

boton_grafica_boiling = tk.Button(frame_graficas, text="ebullición", height=1, width=12,
                                  relief="ridge", command=mostrar_grafica_boiling_point,
                                  font=("Arial", 10))
boton_grafica_boiling.pack(pady=2, side="left")

boton_grafica_densidad = tk.Button(frame_graficas, text="densidad", height=1, width=12,
                                   relief="ridge", command=mostrar_grafica_densidad,
                                   font=("Arial", 10))
boton_grafica_densidad.pack(pady=2, side="left")

boton_grafica_radar_sh = tk.Button(
    frame_graficas,
    text="Specific Heat",
    height=1,
    width=18,
    relief="ridge",
    command=mostrar_grafica_specific_heat,
    font=("Arial", 10)
)
boton_grafica_radar_sh.pack(pady=2, side="left")

texto_resultado = tk.Text(root, width=600, height=32,
                          font=("Consolas", 10), bg="#222222", fg="#00FF00")
texto_resultado.pack(padx=10, pady=10, side="left")
texto_resultado.config(state="disabled")

leer_elementos()  # Cargar los elementos al iniciar

botones_por_z = {}

for elem in elementos:
    try:
        fila = int(elem.period) if str(elem.period).isdigit() else 0
        columna = int(elem.group) if str(elem.group).isdigit() else 0
    except ValueError:
        fila, columna = 0, 0

    btn_elemento = tk.Button(
        frame_botones,
        text=str(elem.symbol),
        width=4,
        font=("Arial", 12),
        command=lambda z=elem.atomic_number: seleccionar_por_z(z)
    )
    # Tooltip con nombre, número atómico y tipo de material
    TOOLTIP_TEXT = f"{elem.element}  {elem.atomic_number}  \n{elem.type_}  \n{elem.phase}"
    ToolTip(btn_elemento, TOOLTIP_TEXT)

    if fila > 0 and columna > 0:
        btn_elemento.grid(row=fila, column=columna, padx=1, pady=1)
    else:
        btn_elemento.grid(row=8, column=int(elem.atomic_number) % 18, padx=1, pady=1)
    botones_por_z[str(elem.atomic_number)] = btn_elemento

mostrar_metales()
mostrar_gases()
mostrar_gases_nobles()
mostrar_actinidos()
mostrar_lantanidos()
mostrar_radiactivos_fg_verde()

root.mainloop()
