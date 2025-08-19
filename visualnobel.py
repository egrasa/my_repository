""" visual nobel project substation """
from __future__ import annotations
import math
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt

class Objeto:
    """ Clase para representar un objeto en el juego """
    def __init__(self, nombre: str, estado: str, location: tuple | None = None):
        self.nombre = nombre
        self.estado = estado  # (por ejemplo, "activo", "abierto", "cerrado")
        # Coordenadas actuales del objeto (x, y). Si está en una zona, coincide con la zona.
        self.location = location

    def cambio_estado(self, nuevo_estado: str):
        """ Cambia el estado del objeto """
        self.estado = nuevo_estado
        print(f"\nEl estado de '{self.nombre}' ha cambiado a '{self.estado}'.\n")

    def __str__(self):
        return self.nombre

class Zona:
    """ Clase para representar una zona en el juego """
    def __init__(self, numero: int, nombre: str, objetos: list[Objeto] = None,
                 estado: str = "disponible", llave_necesaria: str = None,
                 llave_necesaria2: str = None):
        self.numero = numero
        self.nombre = nombre
        self.objetos = objetos if objetos else []
        self.abierta = False
        self.estado = estado  # (por ejemplo, "disponible", "activo", etc.)
        self.llave_necesaria = llave_necesaria  # nombre del objeto necesario para abrir
        self.llave_necesaria2 = llave_necesaria2  # segunda llave necesaria, si aplica

    def abrir(self, inventario: list[Objeto]):
        """ Abre la zona si no está abierta y si se tiene la llave necesaria """
        if self.abierta:
            print(f"\nZona '{self.nombre}' ya estaba abierto.\n")
            return
        if self.llave_necesaria:
            if any(obj.nombre == self.llave_necesaria for obj in inventario):
                self.abierta = True
                print(f"\nHas usado '{self.llave_necesaria}'. Zona '{self.nombre}'"
                      " ahora está abierto.\n")
            else:
                print(f"\nNecesitas '{self.llave_necesaria}' para abrir '{self.nombre}'.\n")
        else:
            self.abierta = True
            print(f"\nZona '{self.nombre}' ahora está abierto.\n")

    def cerrar(self):
        """ Cierra la zona si está abierta """
        if self.abierta:
            self.abierta = False
            print(f"\nZona '{self.nombre}' ahora está cerrado.\n")
        else:
            print(f"\nZona '{self.nombre}' ya estaba cerrado.\n")

    def mostrar_objetos(self):
        """ Muestra los objetos en la zona """
        if self.objetos:
            print("Objetos en la zona:")
            for i, obj in enumerate(self.objetos, 1):
                print(f"{i}. {obj}")
        else:
            print("\nNo hay objetos en esta zona.\n")

    def coger_objeto(self, indice: int) -> Objeto | None:
        """ Coge un objeto de la zona por su índice """
        if 0 <= indice < len(self.objetos):
            return self.objetos.pop(indice)
        else:
            print("\nÍndice de objeto no válido.\n")
            return None

    def dejar_objeto(self, objeto: Objeto):
        """ Deja un objeto en la zona """
        self.objetos.append(objeto)
        print(f"\nHas dejado '{objeto}' en la zona '{self.nombre}'.\n")

    def usar_objeto(self, objeto: Objeto):
        """ Usa un objeto de la zona """
        if objeto in self.objetos:
            print(f"Has usado '{objeto}' en la zona '{self.nombre}'.")
            lista_objetos = [obj.nombre for obj in self.objetos]
            if objeto.nombre in lista_objetos:
                print("definir nuevo estado del objeto:\n")
                nuevo_estado = input(f"Introduce el nuevo estado para '{objeto.nombre}': \n")
                objeto.cambio_estado(nuevo_estado)
        else:
            print(f"\nEl objeto '{objeto}' no está en esta zona.\n")

class Juego:
    """ Clase principal del juego """
    def __init__(self):
        """ Inicializa el juego con las zonas y el inventario """
        # Nueva zona inicial
        self.zona_inicio = Zona(0, "Zona inicio", [],
                                estado="inicio")
        self.zonas = [
            Zona(1, "Puesto del vigilante", [Objeto("llave", "disponible"),
                                             Objeto("boligrafo", "disponible")],
                 estado="disponible",
                 llave_necesaria="boligrafo"),
            Zona(2, "Llavero principal", [Objeto("llaveV8", "disponible"),
                                          Objeto("llaveV9", "disponible")],
                 estado="disponible",
                 llave_necesaria="llave"),
            Zona(3, "Via 8", [Objeto("guantes", "disponible"),
                              Objeto("gafas", "disponible")],
                 estado="disponible",
                 llave_necesaria="llaveV8"),
            Zona(4, "Via 9", [Objeto("guantes", "disponible"),
                              Objeto("gafas", "disponible")],
                 estado="disponible",
                 llave_necesaria="llaveV9"),
            Zona(5, "Subestacion", [Objeto("guantes", "disponible"),
                                    Objeto("actuador", "disponible")],
                 estado="disponible",
                 llave_necesaria="actuador",
                 llave_necesaria2="guantes"),
            Zona(6, "Sala de control", [Objeto("monitor", "disponible"),
                                        Objeto("teclado", "disponible")],
                 estado="disponible",
                 llave_necesaria=None,
                 llave_necesaria2=None),
        ]

        # Coordenadas de las zonas (x, y) en metros, zona inicio en el centro (0, 0)
        self.coordenadas_zonas = {
            "Zona inicio": (0, 0),
            "Puesto del vigilante": (0, 500),
            "Llavero principal": (1000, 200),
            "Via 8": (1000, 500),
            "Via 9": (1000, 0),
            "Subestacion": (1200, 800),
            "Sala de control": (1200, 900),
        }
        self.zona_actual = self.zona_inicio
        self.inventario: list[Objeto] = []
        self.ya_salio_de_inicio = False
        self.distancia_total = 0  # Acumulador de distancia recorrida

        # Estados de tensión para la interfaz de Sala de control
        # Keys: 'via8_25', 'via8_3', 'via9_25', 'via9_3' -> booleano (False=OFF, True=ON)
        self.via_states = {
            'via8_25': False,
            'via8_3': False,
            'via9_25': False,
            'via9_3': False,
        }

        # Referencias a labels de la GUI (se crean cuando se abre la interfaz)
        self._sc_info_label_v8 = None
        self._sc_info_label_v9 = None

        # Inicializar la propiedad location de cada objeto según la zona donde nace
        for zona in self.zonas:
            coords = self.coordenadas_zonas.get(zona.nombre)
            if coords:
                for obj in zona.objetos:
                    # asigna la coordenada de la zona como ubicación inicial del objeto
                    obj.location = coords

    def calcular_distancia(self, zona_origen, zona_destino):
        """Calcula la distancia entre dos zonas usando sus coordenadas."""
        x1, y1 = self.coordenadas_zonas[zona_origen]
        x2, y2 = self.coordenadas_zonas[zona_destino]
        return math.hypot(x2 - x1, y2 - y1)

    def mostrar_intro_inicio(self):
        """ Muestra la introducción de la zona de inicio """
        print("\n--- ZONA INICIO ---")
        print("Bienvenido/a. Todavía no tienes nada en tu inventario.")
        print("Debes dirigirte a una zona para empezar tu aventura.\n")
        print("En los distintos menús podrás realizar acciones como:")
        print(" - Abrir o cerrar secciones o zonas")
        print(" - Ver y coger objetos de la zona")
        print(" - Dejar objetos en la zona")
        print(" - Ver y usar tu inventario")
        print(" - Usar objetos en la zona")
        print(" - Ver el estado de la zona o cambiarlo")
        print(" - Ver el estado gráfico de todas las zonas\n")
        #print("Cuando salgas de esta zona de inicio, ya no podrás regresar.\n")

    def mostrar_menu_principal(self):
        """ Muestra el menú principal del juego """
        print("\n--- Elegir zona ---")
        print("Elige una zona")
        print("Opciones:")
        for zona in self.zonas:
            print(f"{zona.numero}. Ir a {zona.nombre}")
        print("9. Ver mapa")
        print("0. Salir\n")

    def mostrar_menu_zona(self):
        """ Muestra el menú de acciones disponibles en la zona actual """
        print(f"\n--- {self.zona_actual.nombre} ---")
        print("Acciones:")
        print("Desbloquear/abrir zona")
        print("Bloquear/cerrar zona")
        print("Ver objetos en la zona")
        print("Coger objeto")
        print("Dejar objeto")
        print("Ver inventario")
        print("Usar objeto")
        print("Ver estado de la zona")
        print("Cambiar estado de la zona")
        print("Ir a otra zona")
        print("Ver mapa\n")

    def ver_zona(self):
        """ Muestra la zona actual y sus objetos """
        print(f"\n--- Zona actual: {self.zona_actual.nombre} ---")

    def mostrar_estado_zonas_grafico(self):
        """ Muestra una ventana gráfica con el estado de todas las zonas """
        estado_colores = {
            "activado": "green",
            "desactivado": "red",
            "fallo": "yellow",
            "cerrada": "gray"
        }

        ventana = tk.Tk()
        ventana.title("Estado de las Zonas")
        ventana.geometry(f"{min(1200, 260*len(self.zonas))}x350")

        frame = ttk.Frame(ventana, padding=20)
        frame.pack(fill="both", expand=True)

        for i, zona in enumerate(self.zonas):
            # Determinar color según estado y si está abierta
            if not zona.abierta:
                color = estado_colores["cerrada"]
                estado = "cerrada"
            else:
                color = estado_colores.get(zona.estado, "gray")
                estado = zona.estado

            zona_frame = tk.Frame(frame, bg=color, width=220, height=220, relief="raised", bd=3)
            zona_frame.grid(row=0, column=i, padx=15, pady=15)
            zona_frame.grid_propagate(False)  # Mantener tamaño fijo

            tk.Label(zona_frame, text=zona.nombre, bg=color,
                     fg="black", font=("Arial", 14, "bold")).pack(pady=(12, 5))
            tk.Label(zona_frame, text=f"Estado: {estado}", bg=color,
                     fg="black", font=("Arial", 11)).pack(pady=(0, 8))

            # Mostrar objetos en la zona
            objetos_texto = "Objetos:\n"
            if zona.objetos:
                objetos_texto += "\n".join(f"- {obj.nombre}" for obj in zona.objetos)
            else:
                objetos_texto += "Ninguno"
            tk.Label(zona_frame, text=objetos_texto, bg=color,
                     fg="black", font=("Arial", 10), justify="left").pack(pady=(0, 5), anchor="w")

        ventana.mainloop()

    def mostrar_mapa(self):
        """Muestra un gráfico con la posición (x,y) de las zonas y etiquetas."""
        # Reúne coordenadas (incluyendo zona inicio)
        nombres = []
        xs = []
        ys = []
        colores = []
        # incluir zona_inicio si está en coordenadas
        for nombre, (x, y) in self.coordenadas_zonas.items():
            nombres.append(nombre)
            xs.append(x)
            ys.append(y)
            # color según si la zona está abierta/estado conocido
            zona_obj = next((z for z in self.zonas if z.nombre == nombre), None)
            if nombre == self.zona_inicio.nombre:
                colores.append('purple')
            elif zona_obj is None:
                colores.append('gray')
            else:
                if not zona_obj.abierta:
                    colores.append('gray')
                elif zona_obj.estado == "activado":
                    colores.append('green')
                elif zona_obj.estado == "fallo":
                    colores.append('orange')
                else:
                    colores.append('blue')

        plt.figure(figsize=(8, 6))
        # añadir label para que la leyenda pueda mostrarse
        plt.scatter(xs, ys, c=colores, s=120, edgecolors='k', label='Zonas')
        for xi, yi, lab in zip(xs, ys, nombres):
            plt.annotate(lab, (xi, yi), textcoords="offset points",
                         xytext=(5, 5), ha='left', fontsize=9)
        plt.title("Mapa de Zonas")
        plt.xlabel("X (m)")
        plt.ylabel("Y (m)")
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.tight_layout()
        # Mostrar leyenda por defecto en la esquina superior izquierda
        plt.legend(loc='upper left')
        plt.show()

    def mostrar_location_map(self):
        """Mapa de 'locations' — muestra zonas y la location actual de todos los objetos.
        Nota: esta función NO está ligada a los menús (no aparece como opción)."""
        # Zonas
        z_names, zx, zy, z_colors = [], [], [], []
        for nombre, (x, y) in self.coordenadas_zonas.items():
            z_names.append(nombre)
            zx.append(x)
            zy.append(y)
            zobj = next((z for z in self.zonas if z.nombre == nombre), None)
            if nombre == self.zona_inicio.nombre:
                z_colors.append('purple')
            elif zobj is None:
                z_colors.append('gray')
            else:
                if not zobj.abierta:
                    z_colors.append('gray')
                elif zobj.estado == "activado":
                    z_colors.append('green')
                elif zobj.estado == "fallo":
                    z_colors.append('orange')
                else:
                    z_colors.append('blue')

        # Objetos en zonas: AGRUPAR por coordenadas y crear etiqueta con lista separada por comas
        loc_map: dict[tuple, list[str]] = {}  # (x,y) -> [nombres de objetos]
        for zona in self.zonas:
            zone_coords = self.coordenadas_zonas.get(zona.nombre, (0, 0))
            for obj in zona.objetos:
                loc = tuple(obj.location if getattr(obj, "location", None) else zone_coords)
                loc_map.setdefault(loc, []).append(obj.nombre)

        obj_xs, obj_ys, obj_labels, obj_colors = [], [], [], []
        for (x, y), names in loc_map.items():
            obj_xs.append(x)
            obj_ys.append(y)
            # etiqueta combinada entre paréntesis, separada por comas
            obj_labels.append("(" + ", ".join(names) + ")")
            obj_colors.append('tab:blue')  # en zona

        # objetos en inventario (su location refleja la posición del jugador)
        inv_xs, inv_ys, inv_labels = [], [], []
        for obj in self.inventario:
            # si no tiene location asignada, usar ubicación de la zona actual
            loc = getattr(obj, "location", None) or self.coordenadas_zonas.get(
                self.zona_actual.nombre)
            inv_xs.append(loc[0])
            inv_ys.append(loc[1])
            inv_labels.append(obj.nombre + " (inv)")

        # Dibujado
        plt.figure(figsize=(9,7))
        # zonas como cuadrados grandes
        plt.scatter(zx, zy, marker='s', s=260, c=z_colors, edgecolors='k', label='Zonas')
        for xi, yi, lab in zip(zx, zy, z_names):
            plt.annotate(lab, (xi, yi), textcoords="offset points", xytext=(6,6),
                         fontsize=9, weight='bold')

        # objetos en zonas (agrupados)
        if obj_xs:
            plt.scatter(obj_xs, obj_ys, c=obj_colors, s=80, marker='o', edgecolors='k',
                        label='Objetos (en zona)')
            for xi, yi, lab in zip(obj_xs, obj_ys, obj_labels):
                # etiqueta ligeramente desplazada para no solaparse con la etiqueta de la zona
                plt.annotate(lab, (xi, yi), textcoords="offset points", xytext=(6,-10),
                             fontsize=8, color='navy')

        # objetos en inventario
        if inv_xs:
            plt.scatter(inv_xs, inv_ys, c='red', s=100, marker='*', edgecolors='k',
                        label='Objetos (inventario)')
            for xi, yi, lab in zip(inv_xs, inv_ys, inv_labels):
                plt.annotate(lab, (xi, yi), textcoords="offset points", xytext=(-8,8),
                             fontsize=8, color='darkred')

        plt.title("Mapa de Zonas y Locations de Objetos")
        plt.xlabel("X (m)")
        plt.ylabel("Y (m)")
        plt.grid(alpha=0.3, linestyle='--')
        plt.gca().set_aspect('equal', adjustable='box')
        # Mostrar leyenda por defecto en la esquina superior izquierda
        plt.legend(loc='upper left')
        plt.tight_layout()
        plt.show()

    def mostrar_interfaz_sala_control(self):
        """Abre una interfaz retro para la Sala de control con controles para Vía 8 y Vía 9."""
        root = tk.Tk()
        root.title("Sala de Control - Retro Panel")
        root.configure(bg="#0b0b0b")
        retro_bg = "#0b0b0b"
        panel_bg = "#14211b"
        accent = "#39ff14"  # verde retro
        error_color = "orange"
        font_title = ("Courier New", 11, "bold")
        font_btn = ("Courier New", 10, "bold")
        font_info = ("Courier New", 10)

        def _zones_open_for(via_name: str) -> bool:
            """Devuelve True si las zonas requeridas para activar tension en via_name
            están abiertas."""
            # para vía 8: 'Via 8' y 'Subestacion' deben estar abiertas
            # para vía 9: 'Via 9' y 'Subestacion' deben estar abiertas
            sub = next((z for z in self.zonas if z.nombre == "Subestacion"), None)
            via = next((z for z in self.zonas if z.nombre == via_name), None)
            return bool(sub and sub.abierta and via and via.abierta)

        def toggle(key, btn, other_key, other_btn):
            """Alterna key, valida zonas antes de activar y usa colores de error si fallo."""
            will_enable = not self.via_states[key]
            # si vamos a habilitar, validar condiciones de zonas
            if will_enable:
                via_name = "Via 8" if key.startswith("via8") else "Via 9"
                if not _zones_open_for(via_name):
                    # mostrar error y poner labels en naranja
                    messagebox.showerror("Error", f"No se puede activar tensión en {via_name}.\n"
                                                      "Asegúrate de que la zona y la Subestacion"
                                                      " estén abiertas.")
                    if self._sc_info_label_v8:
                        self._sc_info_label_v8.config(fg=error_color)
                    if self._sc_info_label_v9:
                        self._sc_info_label_v9.config(fg=error_color)
                    return  # no aplicar cambio

            # Si la validación pasa o se está apagando, aplicar cambio normal
            new_state = will_enable
            self.via_states[key] = new_state
            label_base = "25 kV" if "25" in key else "3 kV"
            btn.config(text=f"{label_base}: {'ON' if new_state else 'OFF'}",
                       bg=("#004400" if new_state else "#330000"),
                       fg=accent if new_state else "white")

            # Control mutuo: si activamos este, apagar y deshabilitar el otro;
            # si apagamos, habilitar el otro
            other_label_base = "25 kV" if "25" in other_key else "3 kV"
            if new_state:
                self.via_states[other_key] = False
                other_btn.config(text=f"{other_label_base}: OFF", bg="#330000",
                                 fg="white", state="disabled")
            else:
                other_btn.config(state="normal")

            # Restaurar color de info a verde por defecto y actualizar textos
            if self._sc_info_label_v8:
                self._sc_info_label_v8.config(fg=accent)
            if self._sc_info_label_v9:
                self._sc_info_label_v9.config(fg=accent)
            update_info()

        def update_info():
            # Actualiza labels de información con los estados actuales y asegura color por defecto
            v8_25 = "ON" if self.via_states['via8_25'] else "OFF"
            v8_3 = "ON" if self.via_states['via8_3'] else "OFF"
            v9_25 = "ON" if self.via_states['via9_25'] else "OFF"
            v9_3 = "ON" if self.via_states['via9_3'] else "OFF"
            if self._sc_info_label_v8:
                self._sc_info_label_v8.config(text=f"Vía 8\n25 kV: {v8_25}\n3 kV: {v8_3}",
                                              fg=accent)
            if self._sc_info_label_v9:
                self._sc_info_label_v9.config(text=f"Vía 9\n25 kV: {v9_25}\n3 kV: {v9_3}",
                                              fg=accent)

        # Frames para Vía 8, Vía 9 e Información
        frame_v8 = tk.Frame(root, bg=panel_bg, bd=3, relief="ridge", padx=12, pady=10)
        frame_v9 = tk.Frame(root, bg=panel_bg, bd=3, relief="ridge", padx=12, pady=10)
        frame_info = tk.Frame(root, bg=panel_bg, bd=3, relief="ridge", padx=12, pady=10)

        frame_v8.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        frame_v9.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        frame_info.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")

        # Título retro
        tk.Label(frame_v8, text="VÍA 8", bg=panel_bg, fg=accent, font=font_title).pack(pady=(0,8))
        tk.Label(frame_v9, text="VÍA 9", bg=panel_bg, fg=accent, font=font_title).pack(pady=(0,8))
        tk.Label(frame_info, text="ESTADO TENSION", bg=panel_bg, fg=accent,
                 font=font_title).pack(pady=(0,8))

        # Botones Vía 8
        btn_v8_25 = tk.Button(frame_v8, text="25 kV: OFF", width=12, font=font_btn,
                              bg="#330000", fg="white", relief="raised")
        btn_v8_3 = tk.Button(frame_v8, text="3 kV: OFF", width=12, font=font_btn,
                             bg="#330000", fg="white", relief="raised")
        btn_v8_25.pack(pady=6)
        btn_v8_3.pack(pady=6)
        # asignar comandos pasando el botón compañero para control mutuo
        btn_v8_25.config(command=lambda: toggle('via8_25', btn_v8_25, 'via8_3', btn_v8_3))
        btn_v8_3.config(command=lambda: toggle('via8_3', btn_v8_3, 'via8_25', btn_v8_25))

        # Botones Vía 9
        btn_v9_25 = tk.Button(frame_v9, text="25 kV: OFF", width=12, font=font_btn,
                              bg="#330000", fg="white", relief="raised")
        btn_v9_3 = tk.Button(frame_v9, text="3 kV: OFF", width=12, font=font_btn,
                             bg="#330000", fg="white", relief="raised")
        btn_v9_25.pack(pady=6)
        btn_v9_3.pack(pady=6)
        btn_v9_25.config(command=lambda: toggle('via9_25', btn_v9_25, 'via9_3', btn_v9_3))
        btn_v9_3.config(command=lambda: toggle('via9_3', btn_v9_3, 'via9_25', btn_v9_25))

        # --- sincronizar UI inicial con self.via_states ---
        def _apply_button_state(key, btn, other_key, other_btn):
            is_on = self.via_states.get(key, False)
            label_base = "25 kV" if "25" in key else "3 kV"
            btn.config(text=f"{label_base}: {'ON' if is_on else 'OFF'}",
                       bg=("#004400" if is_on else "#330000"),
                       fg=accent if is_on else "white")
            if is_on:
                # forzar off en el otro y deshabilitarlo
                self.via_states[other_key] = False
                other_btn.config(text=f"{'25 kV' if '25' in other_key else '3 kV'}: OFF",
                                  bg="#330000", fg="white", state="disabled")
            else:
                other_btn.config(state="normal")

        _apply_button_state('via8_25', btn_v8_25, 'via8_3', btn_v8_3)
        _apply_button_state('via8_3', btn_v8_3, 'via8_25', btn_v8_25)
        _apply_button_state('via9_25', btn_v9_25, 'via9_3', btn_v9_3)
        _apply_button_state('via9_3', btn_v9_3, 'via9_25', btn_v9_25)

        # Labels de info (se almacenan en self para actualizar desde toggle)
        self._sc_info_label_v8 = tk.Label(frame_info, text="", bg=panel_bg, fg=accent,
                                           font=font_info, justify="left")
        self._sc_info_label_v9 = tk.Label(frame_info, text="", bg=panel_bg, fg=accent,
                                           font=font_info, justify="left")
        self._sc_info_label_v8.pack(pady=(4,8), anchor="w")
        self._sc_info_label_v9.pack(pady=(4,8), anchor="w")

        # Botón de cerrar
        tk.Button(root, text="Cerrar", command=root.destroy,
                  bg=retro_bg, fg="white", font=font_btn).grid(row=1, column=0,
                                                                columnspan=3, pady=(6,12))

        # Inicializar texto de info con los estados actuales
        update_info()

        root.mainloop()

    def ejecutar(self):
        """ Ejecuta el juego, mostrando los menús y gestionando las acciones del jugador """
        if not self.ya_salio_de_inicio:
            self.mostrar_intro_inicio()
            self.mostrar_menu_principal()
            while True:
                texto_de_zona = set()
                elegir_zona = input("¿A qué zona quieres ir? "
                                    "(0 para salir): \n").strip().lower()
                # Acceso rápido al mapa: aceptar 'mapa', 'm' o '9'
                if elegir_zona in ("mapa", "m", "9", "map"):
                    self.mostrar_mapa()
                    # Volver a mostrar el menú principal
                    self.mostrar_menu_principal()
                    continue

                # OPCIÓN OCULTA: mostrar mapa de locations con "location" o "34"
                if elegir_zona in ("location", "34"):
                    self.mostrar_location_map()
                    # Volver a mostrar el menú principal (opción oculta no se imprime)
                    self.mostrar_menu_principal()
                    continue

                texto_de_zona.update(elegir_zona.split())
                if elegir_zona in ["salir", "0"]:
                    print("\n ¡Hasta luego!")
                    return
                opcion = None
                max_coincidencias = 0
                for zona in self.zonas:
                    palabras_zona = set(zona.nombre.lower().split())
                    coincidencias = len(texto_de_zona & palabras_zona)
                    if elegir_zona == str(zona.numero):
                        print(elegir_zona)
                        coincidencias += 1  # Prioriza coincidencia exacta por número
                    if coincidencias > max_coincidencias:
                        max_coincidencias = coincidencias
                        opcion = zona.numero
                        print("zona ", opcion)
                if opcion is not None and 1 <= opcion <= len(self.zonas):
                    zona_destino = self.zonas[opcion - 1]
                    # Nueva condición: no se puede ir a Sala de control
                    # si Subestacion no está abierta
                    if zona_destino.nombre == "Sala de control":
                        subestacion = next(z for z in self.zonas if z.nombre == "Subestacion")
                        if not subestacion.abierta:
                            print("No puedes ir a la Sala de control hasta que "
                                  "la Subestacion esté abierta.")
                            print("Estas en la zona Subestacion.\n")
                            zona_destino = subestacion
                    # Calcular distancia desde zona actual a la nueva zona
                    distancia = self.calcular_distancia(self.zona_actual.nombre,
                                                        zona_destino.nombre)
                    self.distancia_total += distancia
                    print(f"\nTe has movido a la zona: {zona_destino.nombre}")
                    print(f"Distancia recorrida en este trayecto: {distancia:.1f} metros")
                    print(f"Distancia total acumulada: {self.distancia_total:.1f} metros")
                    print(f"Objetos en tu inventario: {len(self.inventario)}\n")
                    self.zona_actual = zona_destino
                    # Actualizar la location de los objetos que llevamos en el inventario:
                    new_coords = self.coordenadas_zonas.get(self.zona_actual.nombre)
                    if new_coords:
                        for obj in self.inventario:
                            obj.location = new_coords
                    break
                else:
                    print("\nZona no válida. Elige un número de zona correcto o escribe 'salir'.\n")
        # A partir de aquí, el juego normal, ya no se puede volver a la zona de inicio
        while True:
            self.menu_zona()
            break

    def menu_zona(self):
        """ Muestra el menú de acciones en la zona actual y gestiona 
        las interacciones del jugador """
        self.ver_zona()
        numero_objetos = len(self.zona_actual.objetos)
        print(f"Objetos en la zona: {numero_objetos}")
        if numero_objetos == 0:
            print("No hay objetos en esta zona.")
        while True:
            accion = None
            elecciones = set()
            eleccion = input("realizar una accion: ").strip().lower()
            elecciones.update(eleccion.split())
            print(
                "\nAcciones disponibles: 0 Salir/Ir a zona | 1 Abrir | 2 Cerrar | 3 Ver objetos |"
                " 4 Coger | 5 Dejar | 6 Ver inventario | 7 Usar | 8 Ver estado gráfico |"
                " 9 Cambiar estado | 10 Ver mapa\n")
            # Diccionario de opciones: clave = número de acción, valor = lista de palabras clave
            opciones = {
                0: {"salir", "0", "terminar", "fin", "del", "juego", "exit", "ir"},
                1: {"abrir", "1", "desbloquear", "zona", "activar"},
                2: {"cerrar", "2", "bloquear", "zona", "desactivar"},
                3: {"objetos", "3", "examinar", "ver"},
                4: {"coger", "objeto", "4"},
                5: {"objeto", "5", "dejar"},
                6: {"ver", "6", "inventario"},
                7: {"objeto", "7", "usar", "firmar"},
                8: {"ver", "8", "estado"},
                9: {"estado", "9", "cambiar"},
                10: {"mapa", "m", "10", "ver", "map"},
                # OPCIÓN OCULTA: mostrar mapa de locations con "location" o "34"
                34: {"location", "34"}
            }

            # Nueva lógica: buscar la opción con más coincidencias de palabras
            max_coincidencias = 0
            mejor_accion = None
            for num_accion, palabras_opcion in opciones.items():
                coincidencias = len(elecciones & set(" ".join(palabras_opcion).split()))
                if coincidencias > max_coincidencias:
                    max_coincidencias = coincidencias
                    mejor_accion = num_accion

            accion = mejor_accion

            if accion == 0:
                # Elegir nueva zona
                while True:
                    # Usar las palabras ya escritas en elecciones para intentar seleccionar la zona
                    opcion = None
                    max_coincidencias = 0
                    for zona in self.zonas:
                        palabras_zona = set(zona.nombre.lower().split())
                        coincidencias = len(elecciones & palabras_zona)
                        # Si el número de la zona está en elecciones, prioriza
                        if str(zona.numero) in elecciones:
                            coincidencias += 1
                        if coincidencias > max_coincidencias:
                            max_coincidencias = coincidencias
                            opcion = zona.numero
                    # Si hay coincidencias suficientes, selecciona la zona automáticamente
                    if opcion is not None and 1 <= opcion <= len(self.zonas):
                        zona_destino = self.zonas[opcion - 1]
                        # Nueva condición: no se puede ir a Sala de control
                        # si Subestacion no está abierta
                        if zona_destino.nombre == "Sala de control":
                            subestacion = next(z for z in self.zonas if z.nombre == "Subestacion")
                            if not subestacion.abierta:
                                print("No puedes ir a la Sala de control hasta que "
                                      "la Subestacion esté abierta.")
                                print("Te llevamos automáticamente a la zona Subestacion.")
                                zona_destino = subestacion
                        distancia = self.calcular_distancia(self.zona_actual.nombre,
                                                            zona_destino.nombre)
                        self.distancia_total += distancia
                        print(f"\n Te has movido a la zona: {zona_destino.nombre}")
                        print(f"Distancia recorrida en este trayecto: {distancia:.1f} metros")
                        print(f"Distancia total acumulada: {self.distancia_total:.1f} metros")
                        print(f"Objetos en tu inventario: {len(self.inventario)}\n")
                        self.zona_actual = zona_destino
                        break
                    # Si no hay coincidencias, pide input como antes
                    elegir_zona = input("¿A qué zona quieres ir? "
                                        "( 0 para salir): \n").strip().lower()
                    if elegir_zona in ["salir", "0"]:
                        return
                    elecciones_zona = set(elegir_zona.split())
                    opcion = None
                    max_coincidencias = 0
                    for zona in self.zonas:
                        palabras_zona = set(zona.nombre.lower().split())
                        coincidencias = len(elecciones_zona & palabras_zona)
                        if elegir_zona == str(zona.numero):
                            coincidencias += 1
                        if coincidencias > max_coincidencias:
                            max_coincidencias = coincidencias
                            opcion = zona.numero
                    if opcion is not None and 1 <= opcion <= len(self.zonas):
                        zona_destino = self.zonas[opcion - 1]
                        distancia = self.calcular_distancia(self.zona_actual.nombre,
                                                            zona_destino.nombre)
                        self.distancia_total += distancia
                        print(f"\n Te has movido a la zona: {zona_destino.nombre}")
                        print(f"Distancia recorrida en este trayecto: {distancia:.1f} metros")
                        print(f"Distancia total acumulada: {self.distancia_total:.1f} metros")
                        print(f"Objetos en tu inventario: {len(self.inventario)}\n")
                        self.zona_actual = zona_destino
                        break
                    else:
                        print("\nZona no válida. Elige un número de zona correcto"
                              " o escribe 'salir'.\n")
                continue
            elif accion == 1:
                # ABRIR: solo si tienes el objeto necesario, se consume al usarlo
                llave = self.zona_actual.llave_necesaria
                llave2 = self.zona_actual.llave_necesaria2

                # Condición especial para Sala de control: monitor y teclado deben estar en la zona
                if self.zona_actual.nombre == "Sala de control":
                    nombres_objetos_zona = [obj.nombre.lower() for obj in self.zona_actual.objetos]
                    if (not "monitor" in nombres_objetos_zona and not
                        "teclado" in nombres_objetos_zona):
                        print("\nEl monitor y el teclado deben estar en la zona para "
                              "poder abrirla.\n")
                        continue
                # --- NUEVA CONDICIÓN PARA SUBESTACION ---
                if self.zona_actual.nombre == "Subestacion":
                    nombres_inventario = [obj.nombre.lower() for obj in self.inventario]
                    if "guantes" not in nombres_inventario:
                        print("\n-¡Peligro! No puedes trabajar en la subestacion sin guantes.-\n")
                        continue

                # Para abrir el llavero principal necesitas la llave del puesto del vigilante
                if self.zona_actual.nombre == "Llavero principal":
                    llave = "llave"
                tiene_llave = any(obj.nombre == llave for obj
                                  in self.inventario) if llave else True
                tiene_llave2 = any(obj.nombre == llave2 for obj
                                   in self.inventario) if llave2 else True

                if llave and not tiene_llave:
                    print(f"\nNo tienes '{llave}' en tu inventario. No puedes abrir esta zona.\n")
                else:
                    if llave:
                        idx_llave = next((i for i, obj in enumerate(self.inventario)
                                          if obj.nombre == llave), None)
                        if idx_llave is not None:
                            obj_llave = self.inventario[idx_llave]
                            print(f"\nNecesitas '{llave}' para abrir. Usando '{obj_llave}'...\n")
                            self.zona_actual.abrir(self.inventario)
                            print(f"Has usado '{obj_llave}' para abrir la zona."
                                  f"'{obj_llave}' ha sido consumido.\n")
                            self.inventario.pop(idx_llave)
                        else:
                            print(f"\n--No tienes '{llave}'. No puedes abrir esta zona.--\n")
                            continue
                    else:
                        self.zona_actual.abrir(self.inventario)

                    # Nueva mecánica: Si requiere llave_necesaria2 y no la tienes, estado = "fallo"
                    if llave2 and not tiene_llave2:
                        print(f"\nNo tienes '{llave2}'. El estado de la zona pasa a 'fallo'.\n")
                        self.zona_actual.estado = "fallo"
                    else:
                        # Preguntar por el estado tras abrir solo si no hay fallo
                        self.zona_actual.estado = "activado"
                    # Si acabamos de activar la Sala de control, abrir su interfaz gráfica
                    if (self.zona_actual.nombre == "Sala de control" and
                        self.zona_actual.estado == "activado"):
                        self.mostrar_interfaz_sala_control()
                    print(f"El estado de la zona '{self.zona_actual.nombre}'"
                          f" es ahora '{self.zona_actual.estado}'.\n")

            elif accion == 2:
                # devuelve el objeto necesario al inventario si la zona tiene llave_necesaria
                llave = self.zona_actual.llave_necesaria
                # --- NUEVA CONDICIÓN PARA SUBESTACION ---
                if self.zona_actual.nombre == "Subestacion":
                    nombres_inventario = [obj.nombre.lower() for obj in self.inventario]
                    if "guantes" not in nombres_inventario:
                        print("\n¡Peligro! No puedes trabajar en la subestacion sin guantes.\n")
                        continue
                # Condición especial: no se puede cerrar el puesto del vigilante
                # si la llave no está en la zona
                if self.zona_actual.nombre == "Puesto del vigilante":
                    nombres_objetos_zona = [obj.nombre.lower() for obj in self.zona_actual.objetos]
                    if "llave" not in nombres_objetos_zona:
                        print("\nNo puedes cerrar el Puesto del vigilante: "
                              "la llave debe estar disponible en la zona.\n")
                        continue
                if self.zona_actual.abierta:
                    self.zona_actual.cerrar()
                    if llave:
                        self.inventario.append(Objeto(llave, "disponible"))
                        print(f"'{llave}' ha sido devuelto a tu inventario tras cerrar la zona.\n")
                else:
                    print(f"La zona '{self.zona_actual.nombre}' ya está cerrada.\n")
            elif accion == 3:
                self.zona_actual.mostrar_objetos()
                if not self.zona_actual.objetos:
                    print("No hay objetos en esta zona.\n")
                    continue
            elif accion == 4:
                # COGER OBJETO: permite coger cualquier objeto disponible en la zona
                if not self.zona_actual.objetos:
                    print("No hay objetos en esta zona.\n")
                    continue
                self.zona_actual.mostrar_objetos()
                nombres_objetos = [obj.nombre.lower() for obj in self.zona_actual.objetos]
                # Buscar si alguna palabra de elecciones coincide con un objeto
                idx = None
                for palabra in elecciones:
                    if palabra in nombres_objetos:
                        idx = nombres_objetos.index(palabra)
                        break
                # Si no se encontró por elecciones, pedir input al usuario
                if idx is None:
                    eleccion_obj = input("¿Qué objeto quieres coger?: ").strip().lower()
                    # Intentar por número
                    if eleccion_obj.isdigit():
                        idx_num = int(eleccion_obj) - 1
                        if 0 <= idx_num < len(self.zona_actual.objetos):
                            idx = idx_num
                    # Intentar por nombre
                    if idx is None and eleccion_obj in nombres_objetos:
                        idx = nombres_objetos.index(eleccion_obj)
                if idx is not None and 0 <= idx < len(self.zona_actual.objetos):
                    obj = self.zona_actual.objetos[idx]
                    # No se puede coger la llave del puesto de vigilante hasta activar zona
                    if (self.zona_actual.nombre == "Puesto del vigilante"
                        and obj.nombre == "llave"
                        and not self.zona_actual.abierta):
                        print("No puedes coger la llave hasta que firmes el libro de registro.")
                        continue
                    # No se puede coger objetos del llavero hasta que esté activado
                    if (self.zona_actual.nombre == "Llavero principal"
                        and self.zona_actual.estado != "activado"):
                        print("No puedes coger la llave porque el llavero está cerrado.")
                        print("primero debes abrir el llavero principal.")
                        continue
                    obj = self.zona_actual.coger_objeto(idx)
                    if obj:
                        # agregar a inventario y actualizar su location
                        # a la posición actual del jugador
                        self.inventario.append(obj)
                        obj.location = self.coordenadas_zonas.get(self.zona_actual.nombre,
                                                                  obj.location)
                        print(f"Has cogido '{obj}'. (location actualizada a {obj.location})")
                else:
                    print("No se ha encontrado ese objeto o índice no válido.")
            elif accion == 5:
                if not self.inventario:
                    print("No tienes objetos en tu inventario.")
                    continue
                print("Inventario: \n")
                nombres_inventario = [obj.nombre.lower() for obj in self.inventario]
                for i, obj in enumerate(self.inventario, 1):
                    print(f"{i}. {obj}")
                idx = None
                # Buscar si alguna palabra de elecciones coincide con un objeto del inventario
                for palabra in elecciones:
                    if palabra in nombres_inventario:
                        idx = nombres_inventario.index(palabra)
                        break
                # Si no se encontró por elecciones, pedir input al usuario
                if idx is None:
                    eleccion_obj = input("\n¿Qué objeto quieres dejar? "
                                         "(nombre o número): \n").strip().lower()
                    # Intentar por número
                    if eleccion_obj.isdigit():
                        idx_num = int(eleccion_obj) - 1
                        if 0 <= idx_num < len(self.inventario):
                            idx = idx_num
                    # Intentar por nombre
                    if idx is None and eleccion_obj in nombres_inventario:
                        idx = nombres_inventario.index(eleccion_obj)
                if idx is not None and 0 <= idx < len(self.inventario):
                    obj = self.inventario.pop(idx)
                    # actualizar location del objeto a la zona donde se deja
                    zone_coords = self.coordenadas_zonas.get(self.zona_actual.nombre)
                    if zone_coords:
                        obj.location = zone_coords
                    self.zona_actual.dejar_objeto(obj)
                else:
                    print("\nNo se ha encontrado ese objeto o índice no válido.")
            elif accion == 6:
                if self.inventario:
                    print("Inventario: \n")
                    for obj in self.inventario:
                        print(f"- {obj}")
                else:
                    print("Tu inventario está vacío.\n")
            elif accion == 7:
                if not self.inventario:
                    print("No tienes objetos en tu inventario.\n")
                    continue
                print("Inventario: \n")
                nombres_inventario = [obj.nombre.lower() for obj in self.inventario]
                for i, obj in enumerate(self.inventario, 1):
                    print(f"{i}. {obj}\n")
                idx = None
                # Buscar si alguna palabra de elecciones coincide con un objeto del inventario
                for palabra in elecciones:
                    if palabra in nombres_inventario:
                        idx = nombres_inventario.index(palabra)
                        break
                # Si no se encontró por elecciones, pedir input al usuario
                if idx is None:
                    eleccion_obj = input("¿Qué objeto quieres usar? "
                                         "(nombre o número): ").strip().lower()
                    # Intentar por número
                    if eleccion_obj.isdigit():
                        idx_num = int(eleccion_obj) - 1
                        if 0 <= idx_num < len(self.inventario):
                            idx = idx_num
                    # Intentar por nombre
                    if idx is None and eleccion_obj in nombres_inventario:
                        idx = nombres_inventario.index(eleccion_obj)
                if idx is not None and 0 <= idx < len(self.inventario):
                    obj = self.inventario[idx]
                    print(f"Has seleccionado '{obj}'.\n")
                    if (self.zona_actual.llave_necesaria and
                        obj.nombre == self.zona_actual.llave_necesaria):
                        if not self.zona_actual.abierta:
                            self.zona_actual.abrir(self.inventario)
                        if obj.nombre == "boligrafo":
                            print(f"Has usado '{obj}' para firmar el libro de registro"
                                  f" '{self.zona_actual.nombre}'.\n")
                        else:
                            print(f"'{obj}' ha sido consumido y ya no está en tu inventario.\n")
                        # Consumir el objeto utilizado
                        self.inventario.pop(idx)
                        self.zona_actual.estado = "activado"
                        # Si acabamos de activar la Sala de control, abrir su interfaz gráfica
                        if self.zona_actual.nombre == "Sala de control":
                            self.mostrar_interfaz_sala_control()
                        print(f"El estado de la zona '{self.zona_actual.nombre}'"
                              f" es ahora '{self.zona_actual.estado}'.\n")
                    else:
                        print(f"No puedes usar '{obj}' aquí o no es útil en esta zona.\n")
                else:
                    print("No se ha encontrado ese objeto o índice no válido.\n")
            elif accion == 8:
                # Ver estado de las zonas (gráfico)
                print('\nen la ventana puedes ver el estado de las zonas')
                print('cierra la ventana para continuar\n')
                self.mostrar_estado_zonas_grafico()
            elif accion == 9:
                # Cambiar estado de la zona (solo si está abierta)
                if self.zona_actual.abierta:
                    nuevo_estado = ""
                    while nuevo_estado not in ["activado", "desactivado", "fallo"]:
                        nuevo_estado = input("¿Nuevo estado para la zona "
                                             "(activado/desactivado/fallo)?: ").strip().lower()
                    self.zona_actual.estado = nuevo_estado
                    print(f"El estado de la zona '{self.zona_actual.nombre}' "
                          f"es ahora '{self.zona_actual.estado}'.\n")
                else:
                    print("La zona debe estar abierta para cambiar su estado.\n")
            elif accion == 10:
                # Mostrar mapa desde el menú de zona
                self.mostrar_mapa()
                continue
            elif accion == 34:
                # OPCIÓN OCULTA: mostrar mapa con locations de objetos
                self.mostrar_location_map()
                continue
            else:
                print(" ")
                print('punto de control 1')
                #self.mostrar_menu_zona()

if __name__ == "__main__":
    Juego().ejecutar()
# This code is a simple text-based adventure game where the player can navigate
# through different zones,
# interact with objects, and manage an inventory.
# The game features zones that can be opened or closed,
# allows the player to pick up and drop objects,
# and provides a menu system for navigation and actions.
# The player can explore zones, collect items, and use them as needed,
# creating a basic interactive experience.
# The game is designed to be run in a console or terminal,
# and it uses simple text.
