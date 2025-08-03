""" creador de personaje """

import os
import tkinter as tkc
from tkinter import ttk
from tkinter import messagebox
#from tkinter import PhotoImage
from PIL import ImageTk, Image
import numpy as np
import matplotlib.pyplot as plt

M5_VER = (1, 3)
MODULE_LIST = ('myth1_characters', 'myth2_tools', 'myth3_attaks', 'myth4_acceso',
               'myth5_creator')

CARPETA = 'project_2_myth/personajes'

def seleccionador():
    """ funcion creadora de la pantalla de seleccion de personaje """
    contenido_personajes = []
    lista_personajes = []
    lista_detalles = []
    lista_nombres = []
    lista_fuerzas = []
    lista_fuerzas_x = []
    lista_fuerzas_total = []
    lista_defensas_total = []
    lista_defensas = []
    lista_defensas_x = []
    lista_velocidades = []
    lista_velocidades_x = []
    lista_fisicos = []
    lista_especiales = []
    lista_rangos = []
    lista_rango_s = []
    lista_rango_a = []
    lista_rango_b = []
    lista_rango_c = []
    lista_rango_e = []
    # Iterar sobre los archivos en la CARPETA
    for nombre_archivo in os.listdir(CARPETA):
        if nombre_archivo.startswith('personaje') and nombre_archivo.endswith('.txt'):
            ruta_archivo = os.path.join(CARPETA, nombre_archivo)
            lista_personajes.append(nombre_archivo)
            with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                contenido_personajes.append(archivo.readlines(1))


    # Crear la ventana principal
    root = tkc.Tk()
    root.title("Selector de personajes creados")
    root.geometry("1200x800+1000+200")

    root.iconbitmap('project_2_myth/imagenes/design2.ico')

    #imagenes
    imagen1 = Image.open('project_2_myth/imagenes/Ophion4a.png')
    imagen1_sz = imagen1.resize((80, 60))
    imagen1_tk = ImageTk.PhotoImage(imagen1_sz)

    imagen_global = Image.open('project_2_myth/imagenes/sencillo1.png')
    imagen_global_sz = imagen_global.resize((240, 100))
    imagen_global_tk = ImageTk.PhotoImage(imagen_global_sz)

    imagen_area1 = Image.open('project_2_myth/imagenes/area1.png')
    imagen_area1_sz = imagen_area1.resize((240, 150))
    imagen_area1_tk = ImageTk.PhotoImage(imagen_area1_sz)

    imagen_zeus1 = Image.open('project_2_myth/imagenes/Zeus1.png')
    imagen_zeus1_sz = imagen_zeus1.resize((240, 150))
    imagen_zeus1_tk = ImageTk.PhotoImage(imagen_zeus1_sz)

    imagen_ptono2 = Image.open('project_2_myth/imagenes/Ptono2.png')
    imagen_ptono2_sz = imagen_ptono2.resize((240, 150))
    imagen_ptono2_tk = ImageTk.PhotoImage(imagen_ptono2_sz)

    # crear frames
    frame_exp_superior = tkc.Frame(root)
    frame_exp_superior.pack(fill='both', expand=True)

    frame_selector = tkc.Frame(root)
    frame_selector.pack(fill='both', expand=True, pady=10)

    frame_inferior = tkc.Frame(root, height=20, bg='gray60')
    frame_inferior.pack(side='bottom', fill='x', expand=True)

    # Crear una lista de opciones
    opciones = lista_personajes

    # Crear etiquetas
    selector_label = tkc.Label(frame_exp_superior,
                               font=('arial', 14),
                               text='selecciona 3 personajes de la lista para incluir en tu equipo')
    selector_label.pack(side='left', pady=10, padx=5)

    version_label = tkc.Label(frame_inferior, image=None,
                              text=f'version {M5_VER[0]} . {M5_VER[1]}',
                              font=('arial',8), bg='gray60')
    version_label.pack(side='bottom', padx=4)

    tabla_comp_label = tkc.Label(frame_inferior, text='tabla de comparacion para dev nivel 2',
                                 bg='gray60', fg='gray30')
    tabla_comp_label.pack(side='top')


    # tabla
    estilo = ttk.Style()
    estilo.configure('Treeview.Heading', font=('arial', 10, 'bold'))

    columns = ('Nombre', 'Fu', 'Fu x', 'Def', 'Def x', 'Vel', 'Vel x', 'Habilidad')
    tabla = ttk.Treeview(frame_selector, columns=columns, show='headings')
    for col in columns:
        tabla.column(col, width=60)
        tabla.heading(col, text=col)

    tabla.pack(fill='both', expand=True, side='right', padx=40)

    # tabla comparacion
    tabla_comparar = ttk.Treeview(frame_inferior,
                                  columns=columns,
                                  show='headings')
    for a in columns:
        tabla_comparar.column(a, width=50)
        tabla_comparar.heading(a, text=a)

    tabla_comparar.pack(fill='both', expand=True, side='right', padx=40)

    # Crear el Combobox
    combobox = ttk.Combobox(frame_selector, values=opciones, state="readonly",
                            width=40, justify='left',)
    combobox.pack(pady=10, padx=10, side='top')

    # sets
    set_fuerzas = []
    set_defensas = []
    set_velocidades = []
    set_fisico = []
    set_special = []
    set_fisico.append(2)
    set_special.append(2)

    # Funciones
    def add_all_items(nivel=0):
        """ fn añadir todos los personajes """
        set_fuerzas.append(84)
        set_defensas.append(51)
        set_velocidades.append(12.8)
        print(' ')
        # ver stats maximos y minimos
        if len(set_fuerzas) < 1 or len(set_defensas) < 1 or len(set_velocidades) < 1:
            print('lista fuerzas, defesa o velocidades vacia')
        elif not set_fisico or not set_special:
            print('lista fisico o special vacia')
        else:
            print(round(max(set_fuerzas),1), round(min(set_fuerzas),1))
            print(round(max(set_defensas),1), round(min(set_defensas),1))
            print(round(max(set_velocidades),1), round(min(set_velocidades),1))
            print(f'{round(max(set_fisico),1)}, {round(max(set_special),1)}  '
                f'[{round(min((min(set_fisico), min(set_special))),1)}]')

        longitud_lista = len(set_fuerzas)
        print(f'numero datos en lista = {longitud_lista}')
        if nivel == 3:
            tops = 'top_stats.txt'
            ruta_tops = os.path.join(CARPETA, tops)
            with open(ruta_tops, 'w', encoding='utf-8') as top:
                top.write(f'{round(max(set_fuerzas),2)} \n'
                        f'{round(min(set_fuerzas),2)} \n'
                        f'{round(max(set_defensas),2)} \n'
                        f'{round(min(set_defensas),2)} \n'
                        f'{round(max(set_velocidades),2)} \n'
                        f'{round(min(set_velocidades),2)} \n')
                if set_fisico and set_special:
                    top.write(f'{round(max(set_fisico),2)} \n'
                            f'{round(max(set_special),2)} \n')
                else:
                    top.write('0.0 \n0.0 \n')
                print('dato grabado')
        elif nivel == 2:
            # Comprobación extra de integridad de datos y advertencias
            advertencias = []
            std_fuerza = np.std(set_fuerzas) if len(set_fuerzas) > 1 else 0
            std_defensa = np.std(set_defensas) if len(set_defensas) > 1 else 0
            std_velocidad = np.std(set_velocidades) if len(set_velocidades) > 1 else 0

            rango_fuerza = max(set_fuerzas) - min(set_fuerzas)
            rango_defensa = max(set_defensas) - min(set_defensas)
            rango_velocidad = max(set_velocidades) - min(set_velocidades)
            factor_multiplicador = 4

            # Usar factor_multiplicador*desviación estándar como umbral dinámico
            if std_fuerza > 0 and rango_fuerza > factor_multiplicador * std_fuerza:
                advertencias.append("¡Advertencia: Gran dispersión en fuerza!"
                                    f"({rango_fuerza:.2f} > {factor_multiplicador*std_fuerza:.2f})")
            if std_defensa > 0 and rango_defensa > factor_multiplicador * std_defensa:
                advertencias.append("¡Advertencia: Gran dispersión en defensa! "
                                    f"({rango_defensa:.2f} > {factor_multiplicador*
                                    std_defensa:.2f})")
            if std_velocidad > 0 and rango_velocidad > factor_multiplicador * std_velocidad:
                advertencias.append(f"¡Advertencia: Gran dispersión en velocidad! "
                                    f"({rango_velocidad:.2f} > {factor_multiplicador*
                                    std_velocidad:.2f})")

            if advertencias:
                print("--- ADVERTENCIAS DE INTEGRIDAD DE DATOS --- (umbral dinámico):")
                for adv in advertencias:
                    print(adv)
                messagebox.askokcancel("Integridad de datos", "\n".join(advertencias))
            # Guardar los stats actuales como antes
            analizar_dispersion()
        mostrar_maximos_minimos()

    def ataque(f1, d2, f2, d1):
        """ fn ataque y contraataque """
        damage = d2 - f1
        damage = round(min(damage, 0), 1)
        contra_damage = d1 - f2
        contra_damage = round(min(contra_damage, 0), 1)
        return (damage, contra_damage)

    def calcular_limites_rangos(min_val, max_val):
        """Devuelve los límites para S, A, B, C, e en base a min y max."""
        paso = (max_val - min_val) / 5
        return {
            'S': max_val - paso,
            'A': max_val - 2*paso,
            'B': max_val - 3*paso,
            'C': max_val - 4*paso,
            'e': min_val
        }

    def analizar_dispersion():
        """Calcula la desviación estándar y compara con los umbrales fijos."""
        if len(set_fuerzas) > 1 and len(set_defensas) > 1 and len(set_velocidades) > 1:
            std_fuerza = np.std(set_fuerzas)
            std_defensa = np.std(set_defensas)
            std_velocidad = np.std(set_velocidades)
            rango_fuerza = max(set_fuerzas) - min(set_fuerzas)
            rango_defensa = max(set_defensas) - min(set_defensas)
            rango_velocidad = max(set_velocidades) - min(set_velocidades)
            print("\n--- Análisis de dispersión ---")
            print(f"Fuerza: std={std_fuerza:.2f}, rango={rango_fuerza:.2f}, umbral fijo=100")
            print(f"Defensa: std={std_defensa:.2f}, rango={rango_defensa:.2f}, umbral fijo=80")
            print(f"Velocidad: std={std_velocidad:.2f}, "
                  f"rango={rango_velocidad:.2f}, umbral fijo=15")
            if rango_fuerza > 100:
                print("¡Advertencia: Gran dispersión en fuerza (rango > 100)!")
            if rango_defensa > 80:
                print("¡Advertencia: Gran dispersión en defensa (rango > 80)!")
            if rango_velocidad > 15:
                print("¡Advertencia: Gran dispersión en velocidad (rango > 15)!")
            print("Puedes considerar ajustar los umbrales o hacerlos "
                  "dinámicos usando la desviación estándar.\n")
        else:
            print("No hay suficientes datos para analizar la dispersión.")

    def incluir_comparacion():
        """ incluir items en la tabla de comparacion """
        sel_item = tabla.selection()
        if len(sel_item) > 0:
            item = tabla.item(sel_item[0])
            item_values = item['values']
            tabla_comparar.insert('', 'end', values=item_values)


    def mostrar_seleccion():
        """ fn mostar en consola opcion seleccionada """
        full_tabla = tabla.get_children()
        len_tabla = len(full_tabla)
        seleccion = combobox.get()
        importar = False
        if len(seleccion) > 0:
            #print(len_tabla)
            if len_tabla == 2:
                boton_import.config(state='normal')
                importar = True
            else:
                boton_import.config(state='disabled')
            if len_tabla >= 5:
                #boton_incluir.config(state='disabled', text='MAXIMO \n ALCANZADO')
                boton_quitar.config(state='normal', bg='gray90', borderwidth=0)
            ruta_seleccion = os.path.join(CARPETA, seleccion)
            with open(ruta_seleccion, 'r', encoding='utf-8') as datos_seleccion:
                data_p = datos_seleccion.read()
                #print(data_p)
                tabla.insert('', 'end', values=data_p)
                if importar:
                    import_tabla(0)
                #messagebox.showinfo(message=data_p, title=seleccion)
        else:
            messagebox.showerror(message='seleccione un personaje de la lista desplegable',
                                 title='Nada seleccionado')


    def quitar():
        """ fn quitar elemento de la tabla """
        full_tabla = tabla.get_children()
        len_tabla = len(full_tabla)
        ver_sel = tabla.selection()
        if len(ver_sel) > 0:
            item_tabla = tabla.item(tabla.selection()[0])
            item_eliminado = item_tabla['values'][0]
            sel_tabla = tabla.selection()[0]
            tabla.delete(sel_tabla)
            print(f'{item_eliminado} eliminado')
            #print(f'items en tabla {len_tabla}')
            if len_tabla == 0:
                boton_incluir.config(state='normal')
            if len_tabla == 4:
                boton_import.config(state='normal')
                boton_quitar.config(state='disabled')
                import_tabla(0)
            else:
                boton_import.config(state='disabled')
        else:
            print('no hay nada seleccionado')


    def relativo(n1, n2):
        """ fn devolver el porcentaje relativo superior """
        diferencia = n1 - n2
        valor100 = (n1 + n2) / 2
        relatividad = diferencia * 100 / valor100
        return round(relatividad, 2)


    def comparar_valores(a1, a2):
        """ comparar valores genericos """
        ver_tabla_comp = tabla_comparar.get_children()
        n_items_tabla = len(ver_tabla_comp)
        nombre1 = 0
        nombre2 = 0
        if n_items_tabla == 2:
            boton_select1.config(state='disabled')
            item1 = ver_tabla_comp[0]
            item2 = ver_tabla_comp[1]
            valores1 = tabla_comparar.item(item1)['values']
            valores2 = tabla_comparar.item(item2)['values']
            #print(valores1)
            #print(valores2)
            nombre1 = valores1[0]
            nombre2 = valores2[0]
        if a1 > a2:
            dato_relativo = relativo(a1, a2)
            return (dato_relativo, nombre1)
        elif a1 < a2:
            dato_relativo = relativo(a2, a1)
            return (dato_relativo, nombre2)
        else:
            dato_relativo = 'empate'
            return (dato_relativo, 'nadie')


    def borrar_plot():
        """ fn borrar las listas de plots """
        #  resetear listas
        nonlocal lista_detalles
        nonlocal lista_nombres
        nonlocal lista_fuerzas
        nonlocal lista_fuerzas_x
        nonlocal lista_fuerzas_total
        nonlocal lista_defensas
        nonlocal lista_defensas_x
        nonlocal lista_velocidades
        nonlocal lista_velocidades_x
        nonlocal lista_fisicos
        nonlocal lista_especiales
        lista_detalles = []
        lista_nombres = []
        lista_fuerzas = []
        lista_fuerzas_x = []
        lista_fuerzas_total = []
        lista_defensas = []
        lista_defensas_x = []
        lista_velocidades = []
        lista_velocidades_x = []
        lista_fisicos = []
        lista_especiales = []
        lista_enumerate_index = []

        tabla_vacia = len(tabla.get_children())
        if tabla_vacia == 0:
            for index, opcion in enumerate(opciones):
                #print(index, opcion)
                ruta_opciones = os.path.join(CARPETA, opcion)
                lista_enumerate_index.append(index)
                with open(ruta_opciones, 'r', encoding='utf-8') as per_stats:
                    estadisticas = per_stats.read()
                    #print(index, estadisticas)
                    tabla.insert('', 'end', values=estadisticas)
        else:
            print('listas borradas')

    def analisis_datos_equilibrio_porcentual():
        """Clasifica personajes según el porcentaje de fuerza, defensa y velocidad
        respecto a sus máximos y mínimos."""
        if not (set_fuerzas and set_defensas and set_velocidades):
            print("No hay datos suficientes para analizar el equilibrio porcentual.")
            return

        max_f, min_f = max(set_fuerzas), min(set_fuerzas)
        max_d, min_d = max(set_defensas), min(set_defensas)
        max_v, min_v = max(set_velocidades), min(set_velocidades)

        lim_f = calcular_limites_rangos(min_f, max_f)
        lim_d = calcular_limites_rangos(min_d, max_d)
        lim_v = calcular_limites_rangos(min_v, max_v)

        tabla_completa = tabla.get_children()
        n_personajes = len(tabla_completa)

        muy_equilibrados = []
        equilibrados = []
        desbalanceados = []

        print(" ")
        print("NOMBRE \t\tFuerza\t\tDefensa\t\tVelocidad \tΔ%\t\tRango")
        for personaje in range(n_personajes):
            personajes = tabla_completa[personaje]
            values = tabla.item(personajes)['values']
            nombre = values[0]
            fuerza = float(values[1]) + float(values[2])
            defensa = float(values[3]) + float(values[4])
            velocidad = float(values[5]) + float(values[6])

            # Porcentaje de cada stat respecto a su rango
            perc_f = 100 * (fuerza - min_f) / (max_f - min_f) if max_f != min_f else 100
            perc_d = 100 * (defensa - min_d) / (max_d - min_d) if max_d != min_d else 100
            perc_v = 100 * (velocidad - min_v) / (max_v - min_v) if max_v != min_v else 100

            # Diferencia máxima entre porcentajes
            max_perc = max(perc_f, perc_d, perc_v)
            min_perc = min(perc_f, perc_d, perc_v)
            diff = max_perc - min_perc

            # rango
            rank = dar_rango_dinamico(nombre, fuerza, defensa, velocidad, lim_f, lim_d, lim_v)

            print(f"{nombre}:\t{perc_f:.0f}%, \t\t{perc_d:.0f}%, "
                  f" \t\t{perc_v:.0f}%, \t\tΔ={diff:.2f}%, \tRango={rank}")

            # Criterios de equilibrio
            if diff <= 10:
                muy_equilibrados.append(nombre)
            elif diff <= 25:
                equilibrados.append(nombre)
            else:
                desbalanceados.append(nombre)

        print(f"\nMuy equilibrados (Δ ≤ 10%): {muy_equilibrados}\n")
        print(f"Equilibrados (Δ ≤ 25%): {equilibrados}\n\n")
        #print(f"Desbalanceados (Δ > 25%): {desbalanceados}\n")

        return {
            'muy_equilibrados': muy_equilibrados,
            'equilibrados': equilibrados,
            'desbalanceados': desbalanceados
        }

    def mostrar_maximos_minimos():
        """Muestra los máximos y mínimos de fuerza, defensa y velocidad."""
        if set_fuerzas and set_defensas and set_velocidades:
            max_f = max(set_fuerzas)
            min_f = min(set_fuerzas)
            max_d = max(set_defensas)
            min_d = min(set_defensas)
            max_v = max(set_velocidades)
            min_v = min(set_velocidades)
            print(f"Fuerza:   min={min_f:.2f}   max={max_f:.2f}")
            print(f"Defensa:  min={min_d:.2f}   max={max_d:.2f}")
            print(f"Velocidad:min={min_v:.2f}   max={max_v:.2f}")
        else:
            print("No hay datos suficientes para calcular máximos y mínimos.")

    def ver_graficos():
        """ fn ver graficos con estadisticas, 
        resumen: los personajes incluidos en la banda superior tienen caracteristicas defensivas 
            potenciadas respecto a su fuerza.
        tarea 1: realizar listado de personajes en banda superior.
        tarea 2: realizar ensayo con grafica defensa - fuerza para determinar banda superior de 
            personajes con caracteristicas potenciadas de fuerza respecto a su defensa.
        nota: estudiar si es viable hacer estudio respecto a velocidad. """

        plt.clf()  # Limpiar el gráfico anterior

        nonlocal lista_detalles
        nonlocal lista_nombres
        nonlocal lista_fuerzas
        nonlocal lista_fuerzas_x
        nonlocal lista_fuerzas_total
        nonlocal lista_defensas_total
        nonlocal lista_defensas
        nonlocal lista_defensas_x
        nonlocal lista_velocidades
        nonlocal lista_velocidades_x
        nonlocal lista_fisicos
        nonlocal lista_especiales
        nonlocal set_fuerzas
        nonlocal set_defensas
        nonlocal set_velocidades
        nonlocal set_fisico
        nonlocal set_special
        #listado_rango = []
        lista_detalles = []
        lista_nombres = []
        lista_fuerzas = []
        lista_fuerzas_x = []
        lista_fuerzas_total = []
        lista_defensas_total = []
        lista_defensas = []
        lista_defensas_x = []
        lista_velocidades = []
        lista_velocidades_x = []
        lista_fisicos = []
        lista_especiales = []

        set_fuerzas = []
        set_defensas = []
        set_velocidades = []
        set_fisico = []
        set_special = []

        tabla_completa = tabla.get_children()
        n_personajes = len(tabla_completa)

        # Llenar las listas con los datos de la tabla
        for personaje in range(n_personajes):
            personajes = tabla_completa[personaje]
            values = tabla.item(personajes)['values']
            fuerza = float(values[1]) + float(values[2])
            defensa = float(values[3]) + float(values[4])
            velocidad = float(values[5]) + float(values[6])
            set_fuerzas.append(fuerza)
            set_defensas.append(defensa)
            set_velocidades.append(velocidad)
            lista_fuerzas.append(fuerza)
            lista_defensas.append(defensa)
            lista_velocidades.append(velocidad)
            lista_nombres.append(values[0])
            lista_fuerzas_total.append(fuerza)
            lista_defensas_total.append(defensa)

            # Calcular y añadir valores para set_fisico y set_special
            fisico = float(values[1]) + float(values[3]) + float(values[5])
            especial = float(values[2]) + float(values[4]) + float(values[6])
            if fisico > especial:
                porcentaje = round((fisico - especial) / fisico * 100, 2) if fisico != 0 else 0
                set_fisico.append(porcentaje)
            elif especial > fisico:
                porcentaje2 = round((especial - fisico) / especial * 100, 2) if especial != 0 else 0
                set_special.append(porcentaje2)

        # Ahora sí puedes calcular min y max y asignar rangos
        if set_fuerzas and set_defensas and set_velocidades:
            min_f, max_f = min(set_fuerzas), max(set_fuerzas)
            min_d, max_d = min(set_defensas), max(set_defensas)
            min_v, max_v = min(set_velocidades), max(set_velocidades)

            lim_f = calcular_limites_rangos(min_f, max_f)
            lim_d = calcular_limites_rangos(min_d, max_d)
            lim_v = calcular_limites_rangos(min_v, max_v)

            # Asignar rangos a cada personaje
            for personaje in range(n_personajes):
                personajes = tabla_completa[personaje]
                values = tabla.item(personajes)['values']
                nombre = values[0]
                fuerza = float(values[1]) + float(values[2])
                defensa = float(values[3]) + float(values[4])
                velocidad = float(values[5]) + float(values[6])
                dar_rango_dinamico(nombre, fuerza, defensa, velocidad, lim_f, lim_d, lim_v)
        else:
            print("No hay datos suficientes para calcular máximos y mínimos.")

        if not lista_fuerzas or not lista_defensas:
            print("No hay datos suficientes para graficar fuerza vs defensa.")
            return

        print(f'\n rango S: {len(lista_rango_s)}')
        print(f' rango A: {len(lista_rango_a)}')
        print(f' rango B: {len(lista_rango_b)}')
        print(f' rango C: {len(lista_rango_c)}')
        print(f' sin rango: {len(lista_rango_e)}')
        print(' ')

        #plt.style.use('dark_background')
        #fig, ax = plt.subplots()
        #fig.patch.set_facecolor('gray')
        #ax.set_facecolor('gray')
        #print(listado_rango)
        plt.subplot(3, 1, 1)
        plt.bar(lista_nombres, lista_fuerzas_total, width=0.5, color='#434646', alpha=0.5)
        plt.xticks(rotation=90)
        plt.plot(lista_fuerzas, color='blue', label='Fuerza')
        plt.plot(lista_fuerzas_x, color='red', label='Fuerza x')
        plt.title('Fuerza Total')
        plt.ylabel('Fuerzas')
        plt.xlabel('personajes')
        plt.legend()
        plt.grid(axis='y')
        #plt.subplot(2, 1, 2)
        #plt.bar(lista_nombres, lista_defensas_total, width=0.5, color='#434646', alpha=0.5)
        #plt.plot(lista_defensas, color='orange', label='defensa')
        #plt.plot(lista_defensas_x, color='green', label='defensa x')
        #plt.title('Defensa')
        #plt.plot(lista_velocidades, color='blue')
        #plt.plot(lista_velocidades_x, color='black')
        #plt.legend()

        plt.subplot(3, 1, 3)
        #plt.scatter(lista_fisicos, lista_especiales)
        plt.scatter(lista_fuerzas, lista_defensas, lista_velocidades)
        #plt.scatter(lista_fuerzas_x, lista_defensas_x)
        plt.title('diagrama Fuerza vs Defensa')
        plt.xlabel('fuerza')
        plt.ylabel('Defensa')

        # Activar las marcas menores
        plt.minorticks_on()

        # Configurar las líneas de cuadrícula
        plt.grid(which='both')
        plt.grid(which='minor', linestyle=':', linewidth='0.5', color='gray')

        # linea tendencia y banda error
        coeficientes = np.polyfit(lista_fuerzas, lista_defensas, 2)
        coeficientes2 = np.polyfit(lista_fuerzas, lista_defensas, 3)
        polinomio = np.poly1d(coeficientes)
        polinomio2 = np.poly1d(coeficientes2)
        linea_fuerza = np.linspace(min(lista_fuerzas), max(lista_fuerzas), 100)
        linea_defensa = polinomio(linea_fuerza)
        linea_defensa2 = polinomio2(linea_fuerza)
        y_pred = polinomio(lista_fuerzas)
        y_pred2 = polinomio2(lista_fuerzas)
        error = lista_defensas - y_pred
        error2 = lista_defensas - y_pred2
        std_error = np.std(error)
        std_error2 = np.std(error2)
        correccion = 5
        linea_defensa_sup = linea_defensa + std_error
        linea_defensa_inf = linea_defensa - std_error
        linea_defensa_sup2 = linea_defensa2 + (std_error2/correccion)
        linea_defensa_inf2 = linea_defensa2 - (std_error2/correccion)
        #linea_defensa_sup3 = linea_defensa2 + (std_error2*correccion)
        #linea_defensa_inf3 = linea_defensa2 - (std_error2*correccion)

        #plt.plot(linea_fuerza, linea_defensa, color='red', linestyle='--')
        #plt.plot(linea_fuerza, linea_defensa2, color='blue', linestyle=':')
        # Dibujar la banda de confianza

        plt.fill_between(linea_fuerza,
                         linea_defensa_inf,  # cambiando linea_defensa_inf por linea_fuerza
                         linea_defensa_sup, # para ver solo banda superior
                         color='orange',
                         alpha=0.2)
        plt.fill_between(linea_fuerza,
                         linea_defensa_inf2,
                         linea_defensa_sup2,
                         color='black',
                         alpha=0.2)
        #plt.fill_between(linea_fuerza,
                         #linea_defensa_inf3,
                         #linea_defensa_sup3,
                         #color='purple',
                         #alpha=0.1)

        # Filtrar los valores que están dentro de la banda de confianza
        valores_dentro_banda = [(f, d) for f, d in zip(lista_fuerzas, lista_defensas)
                                if (polinomio(f) - std_error) <= d <= (polinomio(f) + std_error)]

        valores_ultrabanda = [(uf, ud) for uf, ud in zip(lista_fuerzas, lista_defensas)
                              if (polinomio2(uf) - std_error2/correccion) <= ud <= (polinomio2(uf) +
                                                                           std_error2/correccion)]
        #valores_megabanda = [(uf, ud) for uf, ud in zip(lista_fuerzas, lista_defensas)
                              #if (polinomio2(uf) - std_error2*correccion) <= ud <=
                              #(polinomio2(uf) + std_error2*correccion)]
        valores_megabanda_superior = [(uf, ud) for uf, ud in zip(lista_fuerzas, lista_defensas)
                                      if ud >= (polinomio2(uf) + std_error2)]
        # Imprimir los valores que están dentro de la banda de confianza
        lista_dentro_banda = []
        lista_ultrabanda = []
        #lista_megabanda = []
        lista_megabanda_superior = []
        add_all_items(3)
        for valor in valores_dentro_banda:
            lista_dentro_banda.append(valor)
        analisis_datos_equilibrio_porcentual()

        for nuevo_valor in valores_ultrabanda:
            lista_ultrabanda.append(nuevo_valor)
        #analisis_datos_equilibrio_porcentual()

        for gran_valor_superior in valores_megabanda_superior:
            lista_megabanda_superior.append(gran_valor_superior)
        #analisis_datos(lista_megabanda_superior, 3)     # determinar personajes defensivos

        #plt.hist(set_defensas)
        #plt.hist(set_velocidades)
        #ax.bar(lista_nombres, lista_fisicos, color='#8bc34a', alpha=0.5)
        #ax.scatter(lista_especiales, lista_nombres, color='red', s=200, alpha=0.5)
        #plt.scatter(lista_nombres, lista_fisicos, color='#8bc34a')
        #plt.plot(lista_velocidades_x, color='black')
        #ax.legend({'especial':'rojo', 'fisico':'verde'})
        plt.show()


    def comparar():
        """ funcion comparar stats de personajes para su evaluacion """
        print(' ')
        ver_tabla_comp = tabla_comparar.get_children()
        n_items_tabla = len(ver_tabla_comp)
        if n_items_tabla == 2:
            boton_select1.config(state='disabled')
            item1 = ver_tabla_comp[0]
            item2 = ver_tabla_comp[1]
            valores1 = tabla_comparar.item(item1)['values']
            valores2 = tabla_comparar.item(item2)['values']

            nombre1, nombre2 = valores1[0], valores2[0]
            fuerza1, fuerza2 = float(valores1[1]), float(valores2[1])
            fuerza_m1, fuerza_m2 = float(valores1[2]), float(valores2[2])
            defensa1, defensa2 = float(valores1[3]), float(valores2[3])
            def_m1, def_m2 = float(valores1[4]), float(valores2[4])
            velocidad1, velocidad2 = float(valores1[5]), float(valores2[5])
            vel_m1, vel_m2 = float(valores1[6]), float(valores2[6])

            relativo_fuerza = comparar_valores(fuerza1, fuerza2)
            print(f'{relativo_fuerza[1]}    gana por {relativo_fuerza[0]} % en Fuerza')

            relativo_fuerzax = comparar_valores(fuerza_m1, fuerza_m2)
            print(f'{relativo_fuerzax[1]}   gana por {relativo_fuerzax[0]} % en Fuerza_x')

            relativo_defensa = comparar_valores(defensa1, defensa2)
            print(f'{relativo_defensa[1]}   gana por {relativo_defensa[0]} % en Defensa')

            relativo_defensax = comparar_valores(def_m1, def_m2)
            print(f'{relativo_defensax[1]}  gana por {relativo_defensax[0]} % en Defensa_x')

            relativo_velocidad = comparar_valores(velocidad1, velocidad2)
            print(f'{relativo_velocidad[1]}     gana por {relativo_velocidad[0]} % en Velocidad')

            relativo_velocidadx = comparar_valores(vel_m1, vel_m2)
            print(f'{relativo_velocidadx[1]}    gana por {relativo_velocidadx[0]} % en Velocidad_x')
            print(' ')

            if velocidad1 > velocidad2:
                damages_f = ataque(fuerza1, defensa2, fuerza2, defensa1)
                print(f'daño fisico     {nombre1}   {damages_f}     {nombre2}')
            elif velocidad1 < velocidad2:
                damages_f = ataque(fuerza2, defensa1, fuerza1, defensa2)
                print(f'daño fisico     {nombre2}   {damages_f}     {nombre1}')
            else:
                if velocidad1 + vel_m1 > velocidad2 + vel_m2:
                    damages_f = ataque(fuerza1, defensa2, fuerza2, defensa1)
                    print(f'daño fisico     {nombre1}   {damages_f}     {nombre2} ')
                elif velocidad1 + vel_m1 < velocidad2 + vel_m2:
                    damages_f = ataque(fuerza2, defensa1, fuerza1, defensa2)
                    print(f'daño fisico     {nombre2}   {damages_f}     {nombre1} ')
                else:
                    print('igualados en velocidad')

            if vel_m1 > vel_m2:
                damages_f = ataque(fuerza_m1, def_m2, fuerza_m2, def_m1)
                print(f'daño especial   {nombre1}   {damages_f}     {nombre2}')
            elif vel_m1 < vel_m2:
                damages_f = ataque(fuerza_m2, def_m1, fuerza_m1, def_m2)
                print(f'daño especial   {nombre2}   {damages_f}     {nombre1} ')
            else:
                if velocidad1 + vel_m1 > velocidad2 + vel_m2:
                    damages_f = ataque(fuerza_m1, def_m2, fuerza_m2, def_m1)
                    print(f'daño especial   {nombre1}   {damages_f}     {nombre2} ')
                elif velocidad1 + vel_m1 < velocidad2 + vel_m2:
                    damages_f = ataque(fuerza_m2, def_m1, fuerza_m1, def_m2)
                    print(f'daño especial   {nombre2}   {damages_f}     {nombre1} ')
                else:
                    print('igualados en velocidad_x')
        else:
            boton_select1.config(state='normal')


    def deselect():
        """ fn quitar item de la comparacion """
        ver_seleccion = tabla_comparar.selection()
        if len(ver_seleccion) > 0:
            tabla_comparar.delete(ver_seleccion)


    def import_tabla(code=1):
        """ fn importar toda la tabla """
        equipo = 'equipo.txt'
        ruta_tabla = os.path.join(CARPETA, equipo)
        full_tabla = tabla.get_children()
        len_tabla = len(full_tabla)
        lista_equipo = []
        for i in range(len_tabla):
            details = tabla.item(full_tabla[i])
            inside_details = details['values']
            for j in range(8):
                lista_equipo.append(inside_details[j])
        with open(ruta_tabla, 'w', encoding='utf-8') as equipo1:
            for valor in enumerate(lista_equipo):
                equipo1.write(f', {valor}\n')
        if code == 1:
            root.destroy()


    def dar_rango_dinamico(nombre, f, d, v, lim_f, lim_d, lim_v):
        """Asigna un rango dinámico según los límites calculados."""
        nonlocal lista_rangos
        if f >= lim_f['S'] and d >= lim_d['S'] and v >= lim_v['S']:
            #print('[   S   ]')
            lista_rangos.append('S')
            lista_rango_s.append(nombre)
            return '[ S ]'
        elif f >= lim_f['A'] and d >= lim_d['A'] and v >= lim_v['A']:
            #print('[   A   ]')
            lista_rangos.append('A')
            lista_rango_a.append(nombre)
            return '[ A ]'
        elif f >= lim_f['B'] and d >= lim_d['B'] and v >= lim_v['B']:
            #print('[   B   ]')
            lista_rangos.append('B')
            lista_rango_b.append(nombre)
            return '[ B ]'
        elif f >= lim_f['C'] and d >= lim_d['C'] and v >= lim_v['C']:
            #print('[   C   ]')
            lista_rangos.append('C')
            lista_rango_c.append(nombre)
            return '[ C ]'
        else:
            #print('sin Rango')
            lista_rangos.append('e')
            lista_rango_e.append(nombre)
            return '[ - ]'


    def grafico_sectores(detalles):
        """ mostrar grafico de sectores circulares """
        # Limpiar el gráfico anterior
        plt.clf()  # Limpia la figura actual

        y = np.array([float(detalles[1]), float(detalles[3]), float(detalles[5]),
                      float(detalles[2]), float(detalles[4]), float(detalles[6])])
        etiquetas = [' ', 'fisico', ' ',' ',  'special',  ' ']

        # Definir colores con transparencia (RGBA)
        mis_colores = [
            (1, 0, 0, 0.5),
            (0.85, 0, 0.05, 0.5),
            (0.90, 0.05, 0, 0.5),
            (0.65, 0.85, 0.9, 0.5),
            (0.75, 0.80, 0.9, 0.5),
            (0.70, 0.85, 0.8, 0.5),
            ]

        plt.subplot(3, 1, 2)
        plt.pie(y, startangle=0, labels=etiquetas,
                colors=mis_colores)
        plt.text(0, -1.5, detalles[0], ha='center', va='top', fontsize=12)
        plt.show()

    def leer_limites_stats(filepath):
        with open(filepath, 'r', encoding='utf-8') as top_stats:
            top_values = [float(line.strip()) for line in top_stats.readlines()]
        return {
            'top_x': top_values[0], 'low_x': top_values[1],
            'top_y': top_values[2], 'low_y': top_values[3],
            'top_z': top_values[4], 'low_z': top_values[5],
            'top_fi': top_values[6], 'top_sp': top_values[7]
        }

    def ajustar_limite(valor, minimo, maximo, nombre=''):
        if minimo <= valor <= maximo:
            return valor
        else:
            print(f'{nombre} ajustado dinámicamente')
            return maximo if valor > maximo else minimo

    def calcular_umbrales(top, low):
        m = 100 / (top - low)
        c = -(100 * low) / (top - low)
        y90 = (90 - c) / m
        y10 = (10 - c) / m
        alto = round(((top + low) / 2 + top) / 2, 2)
        bajo = round(((top + low) / 2 + low) / 2, 2)
        return y90, y10, alto, bajo

    def mostrar_nivel_stat(valor, y90, y10, alto, bajo, label, porcentaje):
        if valor >= alto:
            if valor >= y90:
                print(f'{porcentaje}  {label}      * * * * *')
            else:
                print(f'{porcentaje}  {label}      * * * ')
        elif valor <= bajo:
            if valor <= y10:
                print(f'{porcentaje}  {label}      .')
            else:
                print(f'{porcentaje}  {label}      * ')
        else:
            print(f'{porcentaje}  {label}      * * ')

    def evaluar_fisico_especial(fisico, especial, top_fis, top_sp, set_fisico, set_special):
        if fisico > especial:
            porcentaje = round((fisico - especial) / fisico * 100, 2) if fisico != 0 else 0
            set_fisico.append(porcentaje)
            print("fisico")
            if porcentaje >= top_fis:
                print('Físico destacado')
        elif especial > fisico:
            porcentaje2 = round((especial - fisico) / especial * 100, 2) if especial != 0 else 0
            set_special.append(porcentaje2)
            print("especial")
            if porcentaje2 >= top_sp:
                print('Especial destacado')
        elif fisico == especial:
            print(' # PERFECT # ')
        else:
            print('error de comparacion')

    def select():
        nonlocal set_fuerzas, set_defensas, set_velocidades, set_fisico, set_special

        # 1. Leer límites
        limites = leer_limites_stats('project_2_myth/personajes/top_stats.txt')

        # 2. Obtener personaje seleccionado
        item_select = tabla.selection()[0]
        pick_item = tabla.item(item_select)
        detail = pick_item['values']
        print(' ')
        print(f'# {detail[0]}')
        print(f' -{detail[7]}-')

        # 3. Ajustar límites dinámicamente
        if set_fuerzas:
            min_f, max_f = min(set_fuerzas), max(set_fuerzas)
            top_x = ajustar_limite(limites['top_x'], min_f, max_f, 'top x')
            low_x = ajustar_limite(limites['low_x'], min_f, max_f, 'low x')
        else:
            top_x, low_x = limites['top_x'], limites['low_x']

        m_x = 100/(top_x-low_x)
        c_x = -(100*low_x)/(top_x-low_x)
        y90x = (90-c_x)/m_x
        y10x = (10-c_x)/m_x
        x = round(((top_x+low_x)/2+top_x)/2, 0)     # valor estimado de mucha fuerza
        xr = round(((top_x+low_x)/2+low_x)/2, 0)    # valor estimado poca fuerza

        if set_defensas:
            min_y, max_y = min(set_defensas), max(set_defensas)
            top_y = ajustar_limite(limites['top_y'], min_y, max_y, 'top y')
            low_y = ajustar_limite(limites['low_y'], min_y, max_y, 'low y')
        else:
            top_y, low_y = limites['top_y'], limites['low_y']

        m_y = 100/(top_y-low_y)
        c_y = -(100*low_y)/(top_y-low_y)
        y90y = (90-c_y)/m_y
        y10y = (10-c_y)/m_y
        y = round(((top_y+low_y)/2+top_y)/2, 0)     # valor estimado de mucha defensa
        yr = round(((top_y+low_y)/2+low_y)/2, 0)    # valor estimado poca defensa

        if set_velocidades:
            min_z, max_z = min(set_velocidades), max(set_velocidades)
            top_z = ajustar_limite(limites['top_z'], min_z, max_z, 'top z')
            low_z = ajustar_limite(limites['low_z'], min_z, max_z, 'low z')
        else:
            top_z, low_z = limites['top_z'], limites['low_z']

        m_z = 100/(top_z-low_z)
        c_z = -(100*low_z)/(top_z-low_z)
        y90z = (90-c_z)/m_z
        y10z = (10-c_z)/m_z
        z = round(((top_z+low_z)/2+top_z)/2, 2)     # valor estimado de mucha velocidad
        zr = round(((top_z+low_z)/2+low_z)/2, 2)    # valor estimado de poca velocidad

        if set_fisico:
            min_fis, max_fis = min(set_fisico), max(set_fisico)
            top_fis = ajustar_limite(limites['top_fi'], min_fis, max_fis, 'top fis')
        else:
            top_fis = limites['top_fi']

        if set_special:
            min_sp, max_sp = min(set_special), max(set_special)
            top_sp = ajustar_limite(limites['top_sp'], min_sp, max_sp, 'top sp')
        else:
            top_sp = limites['top_sp']

        # 4. Calcular umbrales
        y90x, y10x, x, xr = calcular_umbrales(top_x, low_x)
        y90y, y10y, y, yr = calcular_umbrales(top_y, low_y)
        y90z, y10z, z, zr = calcular_umbrales(top_z, low_z)

        # 5. Evaluar stats y mostrar niveles
        fuerza_util = float(detail[1]) + float(detail[2])
        fuerza_util_r = round(fuerza_util * 100 / top_x, 1)
        fur = int(fuerza_util_r / 11)
        set_fuerzas.append(fuerza_util)
        mostrar_nivel_stat(fuerza_util, y90x, y10x, x, xr, 'F', fur)

        defensa_util = float(detail[3]) + float(detail[4])
        defensa_util_r = round(defensa_util * 100 / top_y, 1)
        dur = int(defensa_util_r / 11)
        set_defensas.append(defensa_util)
        mostrar_nivel_stat(defensa_util, y90y, y10y, y, yr, 'D', dur)

        velocidad_util = float(detail[5]) + float(detail[6])
        velocidad_util_r = round(velocidad_util * 100 / top_z, 1)
        vur = int(velocidad_util_r / 11)
        set_velocidades.append(velocidad_util)
        mostrar_nivel_stat(velocidad_util, y90z, y10z, z, zr, 'V', vur)

        # 6. Evaluar físico/especial
        fisico = float(detail[1]) + float(detail[3]) + float(detail[5])
        especial = float(detail[2]) + float(detail[4]) + float(detail[6])
        evaluar_fisico_especial(fisico, especial, top_fis, top_sp, set_fisico, set_special)

        # 7. Calcular límites y rango dinámico
        lim_f = calcular_limites_rangos(low_x, top_x)
        lim_d = calcular_limites_rangos(low_y, top_y)
        lim_v = calcular_limites_rangos(low_z, top_z)
        dar_rango_dinamico(detail[0], fuerza_util, defensa_util, velocidad_util,
                           lim_f, lim_d, lim_v)

        # 8. Mostrar gráfico de sectores
        grafico_sectores(detail)

    # Botón para mostrar la selección
    rojo = '#F44336'
    verde = '#00C853'
    #azul = '#4DD0E1'

    boton_todo = tkc.Button(frame_selector, text='ver listado', borderwidth=0,
                            image=imagen1_tk, compound='top', command=add_all_items)
    boton_todo.pack()

    boton_incluir = tkc.Button(frame_selector,
                       borderwidth=0,
                       #height=10,
                       #width=30,
                       bg=verde,
                       image=imagen_zeus1_tk,
                       compound='center',
                       font=('arial', 10, 'bold'),
                       relief='raised',
                       text="\n \n \n  === > ",
                       command=mostrar_seleccion)
    boton_incluir.pack(pady=20, padx=30, side='top')

    boton_import = tkc.Button(frame_exp_superior,
                              width=220,
                              height=80,
                              font=('arial', 12, 'bold'),
                              bg=None,
                              borderwidth=0,
                              image=imagen_area1_tk,
                              state='disabled',
                              compound='top',
                              text='IMPORTAR \n EQUIPO',
                              command=import_tabla)
    boton_import.pack(side='right', padx=40)

    boton_quitar = tkc.Button(frame_selector,
                              borderwidth=0,
                              #height=10,
                              #width=30,
                              image=imagen_ptono2_tk,
                              compound='center',
                              font=('arial', 10, 'bold'),
                              bg='white',
                              relief='flat',
                              border=0,
                              state='disabled',
                              text='\n \n \n < === ',
                              command=quitar)
    boton_quitar.pack(pady=20, padx=30, side='top')

    boton_ver_stats = tkc.Button(frame_selector, text=' ver stats ', width=32, height=2,
                                bg='gray50', borderwidth=1, command=select)
    boton_ver_stats.pack(side='bottom', padx=2, pady=5)

    boton_graficos = tkc.Button(frame_exp_superior, text='ver plot', width=225, height=50,
                                command=ver_graficos, image=imagen_global_tk, compound='center',
                                bg='#dcedc8', borderwidth=0)
    boton_graficos.pack(side='top', padx=10)

    boton_borrar_graficos = tkc.Button(frame_exp_superior, text='reset plot', width=32, height=1,
                                       command=borrar_plot, bg=None, borderwidth=0, fg='gray60')
    boton_borrar_graficos.pack(side='top', padx=10)

    boton_select1 = tkc.Button(frame_inferior, text='incluir a \n comparacion', width=12,
                               height=2, bg=verde, borderwidth=1, command=incluir_comparacion)

    boton_comparar = tkc.Button(frame_inferior, text='comparar', width=12, height=2,
                                bg='gray80', borderwidth=1, fg='blue', command=comparar)

    boton_deselect1 = tkc.Button(frame_inferior, text='quitar de \n comparacion', width=12,
                                 bg=rojo, borderwidth=1, command=deselect)

    boton_comparar.pack(side='right', padx=10)
    boton_select1.pack(side='right', padx=5)
    boton_deselect1.pack(side='right', padx=10)


    #boton_extra = tkc.Button(frame_inferior, text='extra', width=12, height=2,
                             #bg='gray60', borderwidth=1)
    #boton_extra.pack(side='right')



    # Ejecutar la aplicación
    root.mainloop()


if __name__ == "__main__":
    seleccionador()
