""" PERSONAJES """

import tkinter as tk
from tkinter import messagebox
from random import randint
from datetime import datetime
import os
from PIL import ImageTk, Image
import myth2_tools
import myth3_attaks
import myth4_acceso
import myth5_creator


now = datetime.now()
M1_VER = (1, 1)
M1 = M1_VER[0]
M2 = myth2_tools.M2_VER[0]
M3 = myth3_attaks.M3_VER[0]
M4 = myth4_acceso.M4_VER[0]
M5 = myth5_creator.M5_VER[0]
VERSION_LIST = f' {M1} . {M2} . {M3} . {M4} . {M5}'

def esp():
    """ dejar espacio """
    print(' ')


def ver_versiones():
    """ funcion para la visualizacion de las versiones """
    messagebox.showerror(message=VERSION_LIST, title='VERSION VIEWER')
    print(VERSION_LIST)


# tupla de simbolos
tuple_luz =             (0,3,0,0,2,1,0,0,2,0,0,0,0,1,1,0,0,0)
tuple_oscuridad =       (2,0,3,0,0,1,1,0,0,0,0,0,0,2,0,0,0,0)
tuple_sabiduria =       (0,0,0,2,3,0,0,0,1,0,0,2,1,1,1,0,0,1)
tuple_guerra =          (0,0,2,0,0,0,0,0,0,2,2,0,0,0,0,0,0,0)
tuple_caos =            (0,0,0,0,0,0,0,0,0,1,2,0,0,2,0,2,0,0)
tuple_tierra =          (1,0,0,0,0,0,2,2,0,2,0,0,0,0,0,0,0,0)
tuple_agua =            (1,0,0,0,0,2,0,3,0,0,0,0,0,0,2,1,0,0)
tuple_fuego =           (0,3,0,0,0,0,1,0,0,1,0,0,2,0,0,0,2,0)
tuple_muerte =          (2,0,0,0,0,0,0,0,0,2,1,0,0,0,0,0,0,2)
tuple_vida =            (0,0,0,0,0,0,2,1,2,0,0,0,0,0,0,0,0,2)
tuple_paz =             (0,0,0,3,1,0,0,0,0,0,0,3,3,0,0,1,1,0)
tuple_traicion =        (0,0,2,0,0,0,0,0,0,0,3,0,0,2,0,0,1,0)
tuple_venganza =        (0,0,0,0,0,0,0,0,0,0,0,2,0,0,2,0,2,0)
tuple_orden =           (0,2,0,3,2,0,0,0,1,0,0,1,0,0,0,0,0,1)
tuple_ignorancia =      (2,0,3,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0)
tuple_energia =         (0,2,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,2)
tuple_proteccion =      (0,0,0,2,2,0,0,0,0,0,0,0,2,0,0,0,0,0)
tuple_transformacion =  (2,0,0,0,0,0,0,0,2,2,0,0,0,0,0,0,0,0)

class Simbolo():
    """ crear clase simbolo """
    def __init__(self, symbol_id, symbol_name, symbol_tuple, factor_fisico, factor_x, factor_ataque,
                 factor_defensa, factor_velocidad):
        self.symbol_id = symbol_id
        self.symbol_name = symbol_name
        self.symbol_tuple = symbol_tuple
        self.factor_fisico = factor_fisico
        self.factor_x = factor_x
        self.factor_ataque = factor_ataque
        self.factor_defensa = factor_defensa
        self.factor_velocidad = factor_velocidad


    def __str__(self):
        return self.symbol_name


    def ver_simbolo(self):
        """ ver datos de simbolo """
        print(self.symbol_name)
        print(self.symbol_tuple)


    def ver_damage(self):
        """ ver daños a todos los tipos """
        if int(self.symbol_tuple[0]) > 0:
            print(f'daño a tipo luz {self.symbol_tuple[0]}')
        if int(self.symbol_tuple[1]) > 0:
            print(f'daño a tipo oscuridad: {self.symbol_tuple[1]}')
        if int(self.symbol_tuple[2]) > 0:
            print(f'daño a tipo sabiduria: {self.symbol_tuple[2]}')
        if int(self.symbol_tuple[3]) > 0:
            print(f'daño a tipo guerra: {self.symbol_tuple[3]}')
        if int(self.symbol_tuple[4]) > 0:
            print(f'daño a tipo caos: {self.symbol_tuple[4]}')
        if int(self.symbol_tuple[5]) > 0:
            print(f'daño a tipo tierra: {self.symbol_tuple[5]}')
        if int(self.symbol_tuple[6]) > 0:
            print(f'daño a tipo agua: {self.symbol_tuple[6]}')
        if int(self.symbol_tuple[7]) > 0:
            print(f'daño a tipo fuego: {self.symbol_tuple[7]}')
        if int(self.symbol_tuple[8]) > 0:
            print(f'daño a tipo muerte: {self.symbol_tuple[8]}')
        if int(self.symbol_tuple[9]) > 0:
            print(f'daño a tipo vida: {self.symbol_tuple[9]}')
        if int(self.symbol_tuple[10]) > 0:
            print(f'daño a tipo paz: {self.symbol_tuple[10]}')
        if int(self.symbol_tuple[11]) > 0:
            print(f'daño a tipo traicion: {self.symbol_tuple[11]}')
        if int(self.symbol_tuple[12]) > 0:
            print(f'daño a tipo venganza: {self.symbol_tuple[12]}')
        if int(self.symbol_tuple[13]) > 0:
            print(f'daño a tipo orden: {self.symbol_tuple[13]}')
        if int(self.symbol_tuple[14]) > 0:
            print(f'daño a tipo ignorancia: {self.symbol_tuple[14]}')
        if int(self.symbol_tuple[15]) > 0:
            print(f'daño a tipo energia: {self.symbol_tuple[15]}')
        if int(self.symbol_tuple[16]) > 0:
            print(f'daño a tipo proteccion: {self.symbol_tuple[16]}')
        if int(self.symbol_tuple[17]) > 0:
            print(f'daño a tipo transformacion: {self.symbol_tuple[17]}')


# Instancia simbolo
luz =               Simbolo(0,  'luz',              tuple_luz,              1, 1, 0, 0, 2)
oscuridad =         Simbolo(1,  'oscuridad',        tuple_oscuridad,        0, 1, 0, 1, 1)
sabiduria =         Simbolo(2,  'sabiduria',        tuple_sabiduria,        0, 1, 0, 0, 2)
guerra =            Simbolo(3,  'guerra',           tuple_guerra,           0, 0, 1, 1, 0)
caos =              Simbolo(4,  'caos',             tuple_caos,             0, 2, 1, 1, 0)
tierra =            Simbolo(5,  'tierra',           tuple_tierra,           2, 0, 0, 1, 0)
agua =              Simbolo(6,  'agua',             tuple_agua,             1, 0, 0, 0, 0)
fuego =             Simbolo(7,  'fuego',            tuple_fuego,            1, 0, 1, 0, 0)
muerte =            Simbolo(8,  'muerte',           tuple_muerte,           1, 1, 0, 0, 0)
vida =              Simbolo(9,  'vida',             tuple_vida,             1, 0, 0, 1, 0)
paz =               Simbolo(10, 'paz',              tuple_paz,              0, 0, 0, 2, 0)
traicion =          Simbolo(11, 'traicion',         tuple_traicion,         0, 0, 1, 0, 1)
venganza =          Simbolo(12, 'venganza',         tuple_venganza,         1, 0, 1, 0, 0)
orden =             Simbolo(13, 'orden',            tuple_orden,            1, 1, 0, 1, 1)
ignorancia =        Simbolo(14, 'ignorancia',       tuple_ignorancia,       0, 1, 0, 0, 0)
energia =           Simbolo(15, 'energia',          tuple_energia,          2, 1, 1, 1, 1)
proteccion =        Simbolo(16, 'proteccion',       tuple_proteccion,       1, 0, 0, 2, 0)
transformacion =    Simbolo(17, 'transformacion',   tuple_transformacion,   1, 1, 0, 0, 1)

# Diccionario de símbolos
simbolos = {
    'luz': luz,
    'oscuridad': oscuridad,
    'sabiduria': sabiduria,
    'guerra': guerra,
    'caos': caos,
    'tierra': tierra,
    'agua': agua,
    'fuego': fuego,
    'muerte': muerte,
    'vida': vida,
    'paz': paz,
    'traicion': traicion,
    'venganza': venganza,
    'orden': orden,
    'ignorancia': ignorancia,
    'energia': energia,
    'proteccion': proteccion,
    'transformacion': transformacion
}

class Personaje():
    """ crear clase personaje """
    def __init__(self, id_codez, genz, tituloz, sexoz, nombrez, symbolz, lifez,
                 locationz, hyst_descriptionz, padrez=None, madrez=None, imagen=None,
                 creacion_id=None):
        if not isinstance(symbolz, Simbolo):
            raise ValueError("symbolz debe ser una instancia de la clase Simbolo")
        self._id_code = id_codez
        self.gen = genz
        self.titulo = tituloz
        self._sexo = sexoz
        self.nombre = nombrez
        self.symbol = symbolz
        self._life = lifez
        self.location = locationz
        self.hyst_description = hyst_descriptionz
        self._padre = padrez
        self._madre = madrez
        self.imagen = imagen
        # CREA EL ID ÚNICO SOLO UNA VEZ
        if creacion_id is not None:
            self.creacion_id = creacion_id
        else:
            self.creacion_id = f"{self.nombre}_{self._id_code}{randint(0, 9)}"


    def asignar_stats(self):
        """ asignar stats al personaje """
        print(' ')
        print(self.symbol.symbol_name, self.symbol.symbol_tuple)
        # Usa nombre e id para un identificador único
        print(f'creacion id: {self.creacion_id}')

        fuerza_fisica = self._calcular_fuerza_fisica()
        fuerza_magica = self._calcular_fuerza_magica()
        defensa_fisica = self._calcular_defensa_fisica(fuerza_fisica)
        defensa_magica = self._calcular_defensa_magica(fuerza_magica)
        velocidad_fisica = self._calcular_velocidad_fisica(fuerza_fisica)
        velocidad_magica = self._calcular_velocidad_magica(fuerza_magica)

        print(f'fuerza fisica {fuerza_fisica}')
        print(f'fuerza magica {fuerza_magica}')
        print(f'defensa fisica {defensa_fisica}')
        print(f'defensa magica {defensa_magica}')
        print(f'velocidad fisica {velocidad_fisica}')
        print(f'velocidad_magica {velocidad_magica}')

        # ...resto igual...

    def _calcular_fuerza_fisica(self):
        """ calcular fuerza fisica """
        f = self.symbol.factor_fisico
        atk = self.symbol.factor_ataque
        return round((((randint((20+f), 30) - int(self.gen)) * 2) +
                      int(f) + int(atk) + round(int(self._life)/100, 2)), 2)

    def _calcular_fuerza_magica(self):
        """ calcular fuerza magica """
        x = self.symbol.factor_x
        atk = self.symbol.factor_ataque
        return round((((randint((22-int(self.gen)),
                                (32+x)) - int(self.gen) - randint(0, int(self.gen))) * 2) +
                      int(x) + int(atk)), 2)

    def _calcular_defensa_fisica(self, fuerza_fisica):
        f = self.symbol.factor_fisico
        defn = self.symbol.factor_defensa
        return round(((randint(4, 15) - 2*(int(self.gen)) +
                       round(((fuerza_fisica+f) / 2), 2)) +
                      int(f) + int(defn) + round(int(self._life)/100, 2)), 2)

    def _calcular_defensa_magica(self, fuerza_magica):
        x = self.symbol.factor_x
        defn = self.symbol.factor_defensa
        return round(((randint(6, 12) + (fuerza_magica / 2) + int(x)) + int(defn)), 2)

    def _calcular_velocidad_fisica(self, fuerza_fisica):
        f = self.symbol.factor_fisico
        vel = self.symbol.factor_velocidad
        return round((((randint((10+vel+f),
                                60) + ((int(fuerza_fisica)+int(f)+int(vel)) / 2)) / 10) +
                      int(f) + int(vel)), 2)

    def _calcular_velocidad_magica(self, fuerza_magica):
        x = self.symbol.factor_x
        vel = self.symbol.factor_velocidad
        return round((((randint((20+vel),
                                (50-int(self.gen))) + ((fuerza_magica+x+vel) / 2)) / 10) +
                      int(x) + int(vel)), 2)


    def mostrar_info(self):
        """Muestra la ventana de información del personaje."""
        self._imprimir_info()
        self._crear_ventana_info()

    def _imprimir_info(self):
        print(f'id code: {self._id_code}')
        print(self.symbol)
        self.symbol.ver_damage()

    def _crear_ventana_info(self):
        info_personaje_panel = tk.Toplevel()
        info_personaje_panel.title(f'{self.nombre}')
        info_personaje_panel.geometry('800x520+1200+200')

        self._crear_labels_info(info_personaje_panel)
        self._crear_botones_info(info_personaje_panel)

        info_personaje_panel.mainloop()

    def _crear_labels_info(self, panel):
        tk.Label(panel, text=f'{self.titulo} \n').pack()
        tk.Label(panel, font=('arial', 18), fg='blue',
                 text=f':::    {self.nombre}   :::  \n ').pack()
        if self._padre is not None:
            tk.Label(panel, text=f'\n padre: {self._padre}\n madre: {self._madre} \n \n').pack()
        info_historia_labelframe = tk.LabelFrame(panel, text='Historia:', padx=5, pady=5,
                                                 fg='gray50', borderwidth=0)
        info_historia_labelframe.pack()
        info_historia_text = tk.Text(info_historia_labelframe, wrap='word', font=('Arial', 12),
                                     width=70, height=8, bg='gray95', borderwidth=0)
        info_historia_text.insert(tk.END, f' \n{self.hyst_description} \n \n')
        info_historia_text.config(state=tk.DISABLED)
        info_historia_text.pack(fill='both', expand=True)

    def _crear_botones_info(self, panel):
        def cerrar_info():
            panel.destroy()

        def seleccionar_personaje():
            """ Selecciona el personaje y guarda la información """
            # Asegura que creacion_id tenga el valor correcto

            # Calcula los stats antes de guardar
            fuerza_fisica = self._calcular_fuerza_fisica()
            fuerza_magica = self._calcular_fuerza_magica()
            defensa_fisica = self._calcular_defensa_fisica(fuerza_fisica)
            defensa_magica = self._calcular_defensa_magica(fuerza_magica)
            velocidad_fisica = self._calcular_velocidad_fisica(fuerza_fisica)
            velocidad_magica = self._calcular_velocidad_magica(fuerza_magica)

            carpeta = 'project_2_myth/personajes'
            if not os.path.exists(carpeta):
                os.makedirs(carpeta)
            nombre_archivo = f"personaje_{self.creacion_id}.txt"
            ruta_archivo = os.path.join(carpeta, nombre_archivo)
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(f'\n{self.creacion_id}\n ')
                f.write(f'{fuerza_fisica}\n ')
                f.write(f'{fuerza_magica}\n ')
                f.write(f'{defensa_fisica}\n ')
                f.write(f'{defensa_magica}\n ')
                f.write(f'{velocidad_fisica}\n ')
                f.write(f'{velocidad_magica}\n')
                f.write(f'{self.symbol.symbol_name}\n')
                f.write(f'Título: {self.titulo}\n')
                f.write(f'Sexo: {self._sexo}\n')
                f.write(f'Nombre: {self.nombre}\n')
                f.write(f'Símbolo: {self.symbol.symbol_name}\n')
                f.write(f'Vida: {self._life}\n')
                f.write(f'Ubicación: {self.location}\n')
                f.write(f'Historia: {self.hyst_description}\n')
                f.write(f'Padre: {self._padre}\n')
                f.write(f'Madre: {self._madre}\n')
                f.write('\n--- STATS ---\n')
                f.write(f'Fuerza física: {fuerza_fisica}\n')
                f.write(f'Fuerza mágica: {fuerza_magica}\n')
                f.write(f'Defensa física: {defensa_fisica}\n')
                f.write(f'Defensa mágica: {defensa_magica}\n')
                f.write(f'Velocidad física: {velocidad_fisica}\n')
                f.write(f'Velocidad mágica: {velocidad_magica}\n')
            print(f'Personaje guardado en: {ruta_archivo}')

            # Guardar también como personaje seleccionado
            with open('project_2_myth/01_personaje.txt', 'w', encoding='UTF-8') as personaje:
                personaje.write(f'{self._id_code} \n{self.gen} \n{self.titulo} \n{self.nombre} \n')
            print('personaje creado:')
            panel.destroy()
            self.asignar_stats()

        boton_salir_info = tk.Button(panel, text='DESCARTAR', width=25, height=2,
                                     bg='gray80', command=cerrar_info)
        boton_seleccionar_personaje = tk.Button(panel, text='CREAR \nPERSONAJE',
                                                width=25, height=4, bg='lightblue',
                                                state='disabled', command=seleccionar_personaje)
        with open('project_2_myth/nivel.txt', 'r', encoding='UTF-8') as nivel_r:
            nivel_v = nivel_r.read()
        if nivel_v == '1':
            boton_seleccionar_personaje.config(state='normal')
        elif nivel_v == '2':
            boton_seleccionar_personaje.config(state='active')
        boton_seleccionar_personaje.pack()
        boton_salir_info.pack()


    def ubicar_posicion(self, x, y):
        """ fn ubicar en una posicion """
        print(f'{self.titulo} {self.nombre} en fila {x}, columna {y}')


    def ubicar_boton(self):
        """ fn informar cual es la funcion del boton """
        messagebox.showerror(message='este personaje aun no está creado',
                            title='error del sistema', )


# Instancia Personajes
personajes = []

with open('project_2_myth/personaje_instancia.txt', 'r', encoding='utf-8') as archivo:
    for linea in archivo:
        (id_code, gen, titulo, sexo, nombre, simbolo_name, life, location,
         hyst_description, padre, madre) = linea.strip().split(',')
        symbol = simbolos.get(simbolo_name.strip())
        #print(f'simbolo_name: {simbolo_name}')
        if symbol is None:
            raise ValueError(f'Simbolo {simbolo_name} no encontrado en el diccionariode simbolos')

        persona = Personaje(id_code, gen, titulo, sexo, nombre, symbol, life, location,
                          hyst_description, padre, madre)
        personajes.append(persona)

personaje01 = personajes[0]
personaje02 = personajes[1]
personaje03 = personajes[2]
personaje04 = personajes[3]
personaje05 = personajes[4]
personaje06 = personajes[5]
personaje07 = personajes[6]
personaje08 = personajes[7]
personaje09 = personajes[8]
personaje10 = personajes[9]
personaje11 = personajes[10]
personaje12 = personajes[11]
personaje13 = personajes[12]
personaje14 = personajes[13]
personaje15 = personajes[14]
personaje16 = personajes[15]
personaje17 = personajes[16]
personaje18 = personajes[17]
personaje19 = personajes[18]
personaje20 = personajes[19]
personaje21 = personajes[20]
personaje22 = personajes[21]
personaje23 = personajes[22]
personaje24 = personajes[23]
personaje25 = personajes[24]
personaje26 = personajes[25]
personaje27 = personajes[26]
personaje28 = personajes[27]
personaje29 = personajes[28]
personaje30 = personajes[29]
personaje31 = personajes[30]
personaje32 = personajes[31]
personaje33 = personajes[32]
personaje34 = personajes[33]
personaje35 = personajes[34]
personaje36 = personajes[35]
personaje37 = personajes[36]
personaje38 = personajes[37]
personaje39 = personajes[38]
personaje40 = personajes[39]
personaje41 = personajes[40]
personaje42 = personajes[41]
personaje43 = personajes[42]
personaje44 = personajes[43]
personaje45 = personajes[44]
personaje46 = personajes[45]
personaje47 = personajes[46]
personaje48 = personajes[47]
personaje49 = personajes[48]
personaje50 = personajes[49]
personaje51 = personajes[50]
personaje52 = personajes[51]
personaje53 = personajes[52]
personaje54 = personajes[53]
personaje55 = personajes[54]
personaje56 = personajes[55]
personaje57 = personajes[56]
personaje58 = personajes[57]
personaje59 = personajes[58]
personaje60 = personajes[59]
personaje61 = personajes[60]
personaje62 = personajes[61]
personaje63 = personajes[62]
personaje64 = personajes[63]
personaje65 = personajes[64]


def crear_ventana():
    """ creacion ventana principal """
    main_panel = tk.Tk()
    main_panel.title('CREACION DE PERSONAJES')
    #main_panel.geometry('780x500+1200+200')
    main_panel.iconbitmap('project_2_myth/imagenes/design2.ico')


    def salir():
        """ fn salir """
        main_panel.destroy()
        myth5_creator.seleccionador()


    def ver_version():
        """ consultar version y salir """
        messagebox.showerror(message=f'version {M1_VER} \n \n \n'
                            'si aceptas... la ventana se autodestruira\n gracias por la visita!',
                            title='Version')
        main_panel.iconify()
        ver_versiones()
        main_panel.after(1000, salir)

    def acceder():
        """ fn solicitar acceso """
        with open('project_2_myth/nivel.txt', 'r', encoding='UTF-8') as nivel_r:
            nivel_v = nivel_r.read()
            nivel_n = int(nivel_v)
        if nivel_n >= 1:
            messagebox.showerror(message=f'ya tienes acceso de nivel {nivel_v}')
            boton_acceso.config(state='disabled', text=f'nivel {nivel_v}')
        elif nivel_n == 2:
            boton_acceso.config('Nivel Dios')
        else:
            myth4_acceso.ventana_solicitud()


    # frames
    frame_logo = tk.Frame(main_panel, bg='gray10')
    frame_logo.pack(fill='both', expand=True)

    frame_encabezado = tk.Frame(main_panel, bg='gray60', height=1, relief='solid')
    frame_encabezado.pack(fill='x', expand=True, pady=4)

    frame_superior = tk.Frame(main_panel, bg='gray60', height=10)
    frame_superior.pack(fill='x', expand=True)

    frame_principal = tk.Frame(main_panel, bg='gray80')
    frame_principal.pack(fill='both', expand=True)

    for i in range(5):
        frame_principal.grid_columnconfigure(i, weight=20)

    for i in range(10):
        frame_principal.grid_rowconfigure(i, weight=20)

    frame_inferior = tk.Frame(main_panel, height=2, bg='darkred')
    frame_inferior.pack(fill='x', expand=True, pady=2)

    # imagen
    ophion = Image.open('project_2_myth/imagenes/Ophion3r.png')
    ophion_sz = ophion.resize((900, 500))
    ophion_tk = ImageTk.PhotoImage(ophion_sz)

    caos1 = Image.open('project_2_myth/imagenes/sencillo1.png')
    caos1_sz = caos1.resize((142, 30))
    caos1_tk = ImageTk.PhotoImage(caos1_sz)

    cronos = Image.open('project_2_myth/imagenes/Cronos1a.png')
    cronos_sz = cronos.resize((80, 50))
    cronos_tk = ImageTk.PhotoImage(cronos_sz)

    zeus = Image.open('project_2_myth/imagenes/Zeus1.png')
    zeus_sz = zeus.resize((80, 40))
    zeus_tk = ImageTk.PhotoImage(zeus_sz)

    #salida = Image.open('project_2_myth/imagenes/exit1.png')
    #salida_sz = salida.resize((80, 40))
    #salida_tk = ImageTk.PhotoImage(salida_sz)

    # label
    credits_label = tk.Label(text='developed by egrasa', fg='gray35')
    credits_label.pack(side='right', padx=10)

    names_label = tk.Label(frame_encabezado, text=None, bg='gray60',
                           fg='blue', image=cronos_tk, compound='center')
    names_label.pack(side='right', padx=5)
    ophion_label = tk.Label(frame_logo, image=ophion_tk)
    ophion_label.pack()

    # botones
    boton_salir = tk.Button(frame_encabezado,
                        text='SALIR',
                        #width=20,
                        #height=1,
                        image=zeus_tk,
                        compound='center',
                        bd=1,
                        borderwidth=0,
                        state='normal',
                        bg='gray60',
                        fg='gray10',
                        command=salir)
    boton_salir.pack(side='left')

    boton_acceso = tk.Button(frame_encabezado, text='log in',
                            width=10,
                            height=1,
                            bd=2,
                            image=None,
                            compound='top',
                            borderwidth=0,
                            state='disabled',
                            bg='gray60',
                            fg='gray40',
                            command=acceder)
    boton_acceso.pack(side='right')

    # Crear y posicionar los botones de personaje dinámicamente
    max_cols = 6  # Número de columnas por fila
    for idx, personaje in enumerate(personajes):
        fila = 1 + idx // max_cols
        columna = idx % max_cols
        boton = tk.Button(
            frame_principal,
            text=personaje.nombre,
            image=caos1_tk,
            compound='center',
            bd=2,
            state='normal',
            bg='gray80',
            command=personaje.mostrar_info
        )
        boton.grid(row=fila, column=columna)

    with open('project_2_myth/nivel.txt', 'r', encoding='UTF-8') as nivel_r:
        nivel_v = nivel_r.read()
        nivel_n = int(nivel_v)
        if nivel_n >= 1:
            boton_acceso.config(state='disabled', text=f'nivel {nivel_v}')
        else:
            boton_acceso.config(state='normal')

    boton_version = tk.Button(text=f'version {M1_VER[0]}.{M1_VER[1]}',
                               borderwidth=0, bg='gray95',
                               command=ver_version)
    boton_version.pack(side='left')

    main_panel.mainloop()

if __name__ == "__main__":
    crear_ventana()

esp()
#personaje01.mostrar_info()
#personaje01.ubicar_posicion(4, 7)
esp()
#personaje02.mostrar_info()
#personaje02.ubicar_posicion(5, 7)
with open('project_2_myth/nivel.txt', 'w', encoding='UTF-8') as nivel:
    nivel.write('0')


print('fin')
