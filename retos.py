""" retos.py """

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

# Configuración de colores (Tema Oscuro)
COLOR_BG = "#1e1e1e"
COLOR_FRAME = "#2d2d2d"
COLOR_TEXT_BG = "#3c3c3c"
COLOR_LABEL = "#e0e0e0"
COLOR_BUTTON = "#4a4a4a"
COLOR_BUTTON_TEXT = "#ffffff"
COLOR_ACCENT = "#007acc"
COLOR_COMPLETED = "#4caf50"
COLOR_PENDING = "#ff9800"

class GestorRetos:
    """ clase para gestionar retos almacenados en un archivo JSON """
    def __init__(self, archivo=None):
        if archivo is None:
            # Obtener la ruta del directorio donde se encuentra este script
            directorio_actual = os.path.dirname(os.path.abspath(__file__))
            self.archivo = os.path.join(directorio_actual, "retos.json")
        else:
            self.archivo = archivo
        self.retos = self._cargar_retos()

    def _cargar_retos(self):
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def guardar_retos(self):
        """ guardar retos en el archivo JSON """
        with open(self.archivo, "w", encoding="utf-8") as f:
            json.dump(self.retos, f, indent=4, ensure_ascii=False)

    def agregar_reto(self, reto_id, titulo, subtareas):
        """ agregar un nuevo reto """
        nuevo_reto = {
            "id": reto_id,
            "titulo": titulo,
            "subtareas": subtareas, # Lista de dicts
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        self.retos.append(nuevo_reto)
        self.guardar_retos()

    def eliminar_reto(self, reto_id):
        """ eliminar un reto por su ID """
        self.retos = [r for r in self.retos if r["id"] != reto_id]
        self.guardar_retos()

    def actualizar_reto(self, old_id, nuevo_id, titulo, subtareas):
        """ actualizar un reto existente """
        for reto in self.retos:
            if reto["id"] == old_id:
                reto["id"] = nuevo_id
                reto["titulo"] = titulo
                reto["subtareas"] = subtareas
                break
        self.guardar_retos()

    def obtener_retos_ordenados(self):
        """ obtener lista de retos ordenados por ID """
        return sorted(self.retos, key=lambda x: x.get("id", 0))

    def calcular_puntuacion_total(self):
        """ calcular la puntuación total de todos los retos """
        total = 0
        for reto in self.retos:
            for sub in reto["subtareas"]:
                if sub.get("completada", False):
                    total += sub.get("valor", 0)
        return total

class VentanaNuevoReto(tk.Toplevel):
    """ clase para la ventana de creación/edición de retos """
    def __init__(self, parent, gestor, callback_actualizar, reto_a_editar=None):
        super().__init__(parent)
        self.reto_a_editar = reto_a_editar
        self.title("Editar Reto" if reto_a_editar else "Nuevo Reto")
        self.geometry("850x650")
        self.configure(bg=COLOR_BG)
        self.gestor = gestor
        self.callback_actualizar = callback_actualizar
        self.subtareas_widgets = []

        # Frame para ID y Título
        header_input = tk.Frame(self, bg=COLOR_BG)
        header_input.pack(fill="x", padx=10, pady=5)

        # ID
        tk.Label(header_input, text="ID:", bg=COLOR_BG, fg=COLOR_LABEL,
                 font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.entry_id = tk.Entry(header_input, bg=COLOR_TEXT_BG, fg=COLOR_LABEL,
                                font=("Arial", 10), insertbackground=COLOR_LABEL, width=5)
        self.entry_id.pack(side="left", padx=5)

        if reto_a_editar:
            self.entry_id.insert(0, str(reto_a_editar["id"]))
        else:
            # Sugerir el siguiente ID
            max_id = max([r.get("id", 0) for r in self.gestor.retos]) if self.gestor.retos else 0
            self.entry_id.insert(0, str(max_id + 1))

        # Título
        tk.Label(header_input, text="Título:", bg=COLOR_BG, fg=COLOR_LABEL,
                 font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.entry_titulo = tk.Entry(header_input, bg=COLOR_TEXT_BG, fg=COLOR_LABEL,
                                     font=("Arial", 10),
                                    insertbackground=COLOR_LABEL, width=70)
        self.entry_titulo.pack(side="left", padx=5, fill="x", expand=True)
        if reto_a_editar:
            self.entry_titulo.insert(0, reto_a_editar["titulo"])

        # Contenedor de subtareas
        tk.Label(self, text="Subtareas:", bg=COLOR_BG, fg=COLOR_LABEL,
                 font=("Arial", 10, "bold")).pack(pady=5)

        self.canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.frame_subtareas = tk.Frame(self.canvas, bg=COLOR_BG)

        self.canvas.create_window((0, 0), window=self.frame_subtareas, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.scrollbar.pack(side="right", fill="y")

        self.frame_subtareas.bind("<Configure>",
                                  lambda e: self.canvas.configure(
                                      scrollregion=self.canvas.bbox("all")))

        # Frame inferior fijo para botones de guardar/eliminar
        self.frame_inferior = tk.Frame(self, bg=COLOR_BG, bd=1, relief="sunken")
        self.frame_inferior.pack(side="bottom", fill="x", pady=5)

        if reto_a_editar:
            tk.Button(self.frame_inferior, text="🗑️ ELIMINAR", command=self._eliminar,
                      bg="#c62828", fg=COLOR_BUTTON_TEXT, font=("Arial", 10, "bold"),
                      padx=10, pady=5).pack(side="left", padx=10, pady=5)

        tk.Button(self.frame_inferior, text="💾 GUARDAR" if reto_a_editar else "💾 GUARDAR TODO",
                  command=self._guardar,
                  bg=COLOR_COMPLETED, fg=COLOR_BUTTON_TEXT, font=("Arial", 10, "bold"),
                  padx=10, pady=5).pack(side="right", padx=10, pady=5)

        # Botón para añadir subtarea (este se queda arriba con las tareas)
        btn_add_frame = tk.Frame(self, bg=COLOR_BG)
        btn_add_frame.pack(fill="x", pady=2)
        tk.Button(btn_add_frame, text="+ Añadir Subtarea", command=self._agregar_subtarea_ui,
                  bg=COLOR_ACCENT, fg=COLOR_BUTTON_TEXT,
                  font=("Arial", 9, "bold")).pack(side="left", padx=10)

        # Cargar subtareas existentes o añadir una inicial
        if reto_a_editar:
            for sub in reto_a_editar["subtareas"]:
                self._agregar_subtarea_ui(sub)
        else:
            self._agregar_subtarea_ui()

    def _agregar_subtarea_ui(self, datos_subtarea=None):
        frame = tk.Frame(self.frame_subtareas, bg=COLOR_FRAME, pady=2)
        frame.pack(fill="x", pady=2)

        # Descripción
        tk.Label(frame, text="Descripción:", bg=COLOR_FRAME, fg=COLOR_LABEL,
                 font=("Arial", 9)).pack(anchor="w", padx=5)
        entry_desc = tk.Entry(frame, bg=COLOR_TEXT_BG, fg=COLOR_LABEL, font=("Arial", 9),
                             insertbackground=COLOR_LABEL, width=100)
        entry_desc.pack(padx=5, pady=1)
        if datos_subtarea:
            entry_desc.insert(0, datos_subtarea["desc"])

        # Valor
        tk.Label(frame, text="Puntos:", bg=COLOR_FRAME, fg=COLOR_LABEL,
                 font=("Arial", 9)).pack(anchor="w", padx=5)
        entry_valor = tk.Entry(frame, bg=COLOR_TEXT_BG, fg=COLOR_LABEL,
                               font=("Arial", 9), insertbackground=COLOR_LABEL, width=8)
        entry_valor.pack(anchor="w", padx=5, pady=1)
        if datos_subtarea:
            entry_valor.delete(0, tk.END)
            entry_valor.insert(0, str(datos_subtarea["valor"]))
        else:
            entry_valor.insert(0, "10")

        self.subtareas_widgets.append({
            "frame": frame, 
            "desc": entry_desc, 
            "valor": entry_valor,
            "completada": datos_subtarea["completada"] if datos_subtarea else False
        })

    def _eliminar(self):
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que quieres eliminar este reto?"):
            self.gestor.eliminar_reto(self.reto_a_editar["id"])
            self.callback_actualizar()
            self.destroy()

    def _guardar(self):
        titulo = self.entry_titulo.get().strip()
        id_str = self.entry_id.get().strip()

        if not titulo:
            messagebox.showwarning("Error", "El reto debe tener un título")
            return

        try:
            nuevo_id = int(id_str)
        except ValueError:
            messagebox.showwarning("Error", "El ID debe ser un número entero")
            return

        # Verificar si el ID ya existe (si estamos creando o cambiando el ID)
        if not self.reto_a_editar or (self.reto_a_editar and self.reto_a_editar["id"] != nuevo_id):
            if any(r["id"] == nuevo_id for r in self.gestor.retos):
                messagebox.showwarning("Error", f"El ID {nuevo_id} ya está en uso")
                return

        subtareas = []
        for w in self.subtareas_widgets:
            desc = w["desc"].get().strip()
            valor_str = w["valor"].get().strip()
            if desc:
                try:
                    valor = int(valor_str)
                    subtareas.append({
                        "desc": desc, 
                        "valor": valor, 
                        "completada": w["completada"]
                    })
                except ValueError:
                    continue

        if not subtareas:
            messagebox.showwarning("Error", "Añade al menos una subtarea válida")
            return

        if self.reto_a_editar:
            self.gestor.actualizar_reto(self.reto_a_editar["id"], nuevo_id, titulo, subtareas)
        else:
            self.gestor.agregar_reto(nuevo_id, titulo, subtareas)

        self.callback_actualizar()
        self.destroy()

class AppRetos:
    """ clase principal de la aplicación de retos """
    def __init__(self, root1):
        self.root = root1
        self.root.title("Gestor de Retos y Puntuación")
        self.root.geometry("900x700")
        self.root.configure(bg=COLOR_BG)

        self.gestor = GestorRetos()
        self.criterio_orden = tk.StringVar(value="id")

        # Header con Puntuación Global
        self.header = tk.Frame(self.root, bg=COLOR_ACCENT, height=60)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.label_puntos = tk.Label(self.header, text="🏆 Puntuación Total: 0",
                                    bg=COLOR_ACCENT, fg="white", font=("Arial", 18, "bold"))
        self.label_puntos.pack(expand=True)

        # Cuerpo principal
        self.main_frame = tk.Frame(self.root, bg=COLOR_BG)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame superior para controles
        self.controles_frame = tk.Frame(self.main_frame, bg=COLOR_BG)
        self.controles_frame.pack(fill="x", pady=5)

        # Botón Nuevo Reto
        tk.Button(self.controles_frame, text="➕ Nuevo Reto", command=self._abrir_nuevo_reto,
                  bg=COLOR_COMPLETED, fg="white", font=("Arial", 10, "bold"),
                  padx=10, pady=5).pack(side="left")

        # Lista de Retos (Scrollable)
        self.canvas = tk.Canvas(self.main_frame, bg=COLOR_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical",
                                       command=self.canvas.yview)
        self.frame_lista = tk.Frame(self.canvas, bg=COLOR_BG)

        self.canvas.create_window((0, 0), window=self.frame_lista, anchor="nw", width=850)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.frame_lista.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))

        self.actualizar_ui()

    def actualizar_ui(self):
        """ actualizar la interfaz de usuario con la lista de retos """
        # Limpiar lista
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        # Actualizar puntos
        puntos = self.gestor.calcular_puntuacion_total()
        self.label_puntos.config(text=f"🏆 Puntuación Total: {puntos}")

        # Obtener retos ordenados por ID
        retos = self.gestor.obtener_retos_ordenados()

        # Mostrar retos
        for reto in retos:
            self._crear_card_reto(reto)

    def _crear_card_reto(self, reto):
        # Lista de colores más suaves y profesionales para las tarjetas
        colores_suaves = ["#415a72", "#808136", "#a5554e", "#7b4a8f", "#ad6f45", "#418791"]
        color_card = colores_suaves[reto.get("id", 0) % len(colores_suaves)]

        # Contenedor para la card y el botón de editar fuera
        container = tk.Frame(self.frame_lista, bg=COLOR_BG)
        container.pack(fill="x", pady=5, padx=5)

        # Card principal (donde van las tareas)
        card = tk.Frame(container, bg=color_card, bd=2, relief="groove")
        card.pack(side="left", fill="x", expand=True)

        # Botón editar fuera de la card
        tk.Button(container, text="✏️", command=lambda r=reto: self._abrir_editar_reto(r),
                  bg=COLOR_BUTTON, fg="white", font=("Arial", 9, "bold"),
                  width=4).pack(side="right", padx=(5, 0), pady=5)

        # Título dentro de la card
        top_frame = tk.Frame(card, bg=color_card)
        top_frame.pack(fill="x", padx=5, pady=2)

        # Mostrar ID y Título
        texto_titulo = f"#{reto.get('id', 0)} - {reto['titulo']}"
        tk.Label(top_frame, text=texto_titulo, bg=color_card, fg="white",
                 font=("Arial", 11, "bold")).pack(side="left")

        # Subtareas
        for i, sub in enumerate(reto["subtareas"]):
            is_completed = sub.get("completada", False)
            # Color de fondo de la subtarea: verde suave si está completada
            bg_subtarea = "#27ae60" if is_completed else color_card
            fg_subtarea = "#ffffff" if is_completed else COLOR_LABEL

            sub_frame = tk.Frame(card, bg=bg_subtarea)
            sub_frame.pack(fill="x", padx=5, pady=1)

            var = tk.BooleanVar(value=is_completed)

            # Checkbox
            cb = tk.Checkbutton(sub_frame, variable=var, bg=bg_subtarea,
                                activebackground=bg_subtarea,
                               selectcolor=COLOR_TEXT_BG, command=lambda r=reto, idx=i,
                               v=var: self._toggle_subtarea(r, idx, v))
            cb.pack(side="left")

            # Texto subtarea
            texto = f"{sub['desc']} ({sub['valor']} pts)"
            if is_completed:
                texto = "✅ " + texto

            lbl = tk.Label(sub_frame, text=texto, bg=bg_subtarea, fg=fg_subtarea,
                          font=("Arial", 9, "bold" if is_completed else "normal"),
                          justify="left", wraplength=750, anchor="w")
            lbl.pack(side="left", padx=2, fill="x", expand=True)
            lbl.pack(side="left", padx=2, fill="x", expand=True)

    def _toggle_subtarea(self, reto, idx, var):
        reto["subtareas"][idx]["completada"] = var.get()
        self.gestor.guardar_retos()
        self.actualizar_ui()

    def _eliminar_reto(self, reto_id):
        if messagebox.askyesno("Confirmar", "¿Eliminar este reto?"):
            self.gestor.eliminar_reto(reto_id)
            self.actualizar_ui()

    def _abrir_nuevo_reto(self):
        VentanaNuevoReto(self.root, self.gestor, self.actualizar_ui)

    def _abrir_editar_reto(self, reto):
        VentanaNuevoReto(self.root, self.gestor, self.actualizar_ui, reto_a_editar=reto)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppRetos(root)
    root.mainloop()
