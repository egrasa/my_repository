""" History Visualizer Module
This module provides functionality to visualize the history of file creation events
using charts and graphs. It integrates with the History Tracker module to retrieve
the necessary data.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from history_tracker import get_history, clear_history

# Importaciones opcionales para gráficos
#try:
 #   import matplotlib.pyplot as plt
  #  from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
   # import pandas as pd
    #MATPLOTLIB_AVAILABLE = True
#except ImportError:
 #   MATPLOTLIB_AVAILABLE = False

class HistoryViewer:
    """Clase para visualizar el historial de creación de archivos"""
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.filtered_data = []  # Inicializa como lista vacía
        self.table_frame = None
        self.chart_frame = None
        self.notebook = None
        self.filter_entry = None
        self.order_var = None
        self.order_combo = None

    def show_history_window(self):
        """Muestra la ventana del historial"""
        history_data = get_history()
        if not history_data:
            messagebox.showinfo("Historial", "No hay datos en el historial.")
            return

        self.filtered_data = history_data  # Actualiza el filtro actual

        self.window = tk.Toplevel(self.parent)
        self.window.title("Historial de Archivos Creados")
        self.window.geometry("1200x1000")
        self.window.configure(bg='lightgray')

        # --- Filtros y orden ---
        filter_frame = tk.Frame(self.window, bg='lightgray')
        filter_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(filter_frame, text="Filtrar por nombre:", bg='lightgray').pack(side='left')
        self.filter_entry = tk.Entry(filter_frame, width=20)
        self.filter_entry.pack(side='left', padx=5)

        tk.Label(filter_frame, text="Ordenar por:", bg='lightgray').pack(side='left', padx=(20,0))
        self.order_var = tk.StringVar(value='timestamp')
        order_options = ['timestamp', 'filename', 'file_count', 'total_size_gb']
        self.order_combo = ttk.Combobox(filter_frame, textvariable=self.order_var,
                                        values=order_options, state='readonly', width=15)
        self.order_combo.pack(side='left', padx=5)

        apply_btn = tk.Button(filter_frame, text="Aplicar", command=self.apply_filter_order,
                              bg='lightblue')
        apply_btn.pack(side='left', padx=10)

        # Frame principal con notebook
        main_frame = tk.Frame(self.window, bg='lightgray')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)

        self.table_frame = tk.Frame(self.notebook, bg='lightgray')
        self.notebook.add(self.table_frame, text='📋 Tabla de Datos')

        #if MATPLOTLIB_AVAILABLE:
        self.chart_frame = tk.Frame(self.notebook, bg='lightgray')
        self.notebook.add(self.chart_frame, text='📊 Gráficos')

        self.create_table(self.table_frame, self.filtered_data)
        #if MATPLOTLIB_AVAILABLE:
        self.create_charts(self.chart_frame, self.filtered_data)

        # Frame de botones
        button_frame = tk.Frame(self.window, bg='lightgray')
        button_frame.pack(fill='x', padx=10, pady=5)

        # Botón para limpiar historial
        clear_btn = tk.Button(filter_frame, text="🗑️ Limpiar Historial",
                             command=self.clear_history_confirm, bg='lightcoral')
        clear_btn.pack(side='left', padx=5)
        # Este botón llama a self.clear_history_confirm, que a su vez llama a clear_history()

        # Botón para exportar (solo si pandas está disponible)
        #if MATPLOTLIB_AVAILABLE:  # pandas viene con matplotlib
        export_btn = tk.Button(filter_frame, text="💾 Exportar CSV",
                               command=lambda: self.export_to_csv(history_data), bg='lightblue')
        export_btn.pack(side='left', padx=5)

        # Botón para cerrar
        close_btn = tk.Button(filter_frame, text="❌ Cerrar",
                             command=self.window.destroy, bg='lightgray')
        close_btn.pack(side='right', padx=5)

    def create_table(self, parent, history_data):
        """Crea la tabla con los datos del historial"""
        # Frame para la tabla
        table_frame = tk.Frame(parent, bg='lightgray')
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Crear Treeview
        columns = ('Fecha', 'Archivo', 'Carpetas', 'Archivos', 'Tamaño (GB)',
                   'Origen', 'Ruta Completa')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)

        # Configurar columnas
        tree.heading('Fecha', text='Fecha y Hora')
        tree.heading('Archivo', text='Archivo Creado')
        tree.heading('Carpetas', text='Carpetas Procesadas')
        tree.heading('Archivos', text='Archivos Procesados')
        tree.heading('Tamaño (GB)', text='Tamaño Total (GB)')
        tree.heading('Origen', text='Carpeta Origen')
        tree.heading('Ruta Completa', text='Ruta Completa')

        tree.column('Fecha', width=150)
        tree.column('Archivo', width=200)
        tree.column('Carpetas', width=120)
        tree.column('Archivos', width=120)
        tree.column('Tamaño (GB)', width=120)
        tree.column('Origen', width=200)
        tree.column('Ruta Completa', width=300)

        # Agregar datos
        for entry in reversed(history_data):  # Más recientes primero
            tree.insert('', 'end', values=(
                entry.get('fecha_legible', ''),
                entry.get('filename', ''),
                entry.get('carpetas_procesadas', entry.get('file_count', '')),
                entry.get('archivos_procesados', ''),
                entry.get('total_size_gb', ''),
                os.path.basename(entry.get('carpeta_origen', '')),
                entry.get('ruta_completa', '')
            ))

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def create_charts(self, parent, history_data):
        """Crea los gráficos de evolución"""
        #if not MATPLOTLIB_AVAILABLE:
         #   label = tk.Label(parent, text="Matplotlib no está disponible.\nInstala"
          #                   " con: pip install matplotlib pandas",
           #                bg='lightgray', font=('Arial', 12))
            #label.pack(expand=True)
            #return

        if len(history_data) < 2:
            label = tk.Label(parent, text="Se necesitan al menos 2 entradas para mostrar gráficos",
                           bg='lightgray', font=('Arial', 12))
            label.pack(expand=True)
            return

        # Convertir a DataFrame
        df = pd.DataFrame(history_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Crear figura con 3 subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
        fig.patch.set_facecolor('lightgray')

        # Gráfico 1: Evolución de cantidad de carpetas
        ax1.plot(df['timestamp'], df['carpetas_procesadas'].fillna(df['file_count']),
                 marker='o', linewidth=2, markersize=6)
        ax1.set_title('Evolución de Carpetas Procesadas', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Cantidad de Carpetas', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)

        # Gráfico 2: Evolución de archivos procesados
        ax2.plot(df['timestamp'], df['archivos_procesados'], marker='^', linewidth=2,
                 markersize=6, color='green')
        ax2.set_title('Evolución de Archivos Procesados', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Cantidad de Archivos', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)

        # Gráfico 3: Evolución de tamaño total
        ax3.plot(df['timestamp'], df['total_size_gb'], marker='s', linewidth=2,
                markersize=6, color='red')
        ax3.set_title('Evolución de Tamaño Total Procesado', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Tamaño Total (GB)', fontsize=12)
        ax3.set_xlabel('Fecha', fontsize=12)
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', rotation=45)

        plt.tight_layout()

        # Integrar gráfico en tkinter
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)

    def clear_history_confirm(self):
        """Confirma antes de limpiar el historial"""
        result = messagebox.askyesno("Confirmar",
                                   "¿Estás seguro de que quieres limpiar todo el historial?\n"
                                   "Esta acción no se puede deshacer.")
        if result:
            self.export_to_csv(get_history())  # Exportar antes de limpiar
            clear_history()
            messagebox.askokcancel("Historial", "Historial limpiado correctamente.")
            if self.window:
                self.window.destroy()

    def export_to_csv(self, history_data):
        """Exporta el historial a CSV"""
        # Intentar convertir a DataFrame y manejar errores de datos específicos
        try:
            df = pd.DataFrame(history_data)
        except (ValueError, TypeError) as e:
            messagebox.showerror("Error", f"Datos del historial inválidos: {e}")
            return

        # Guardar en la carpeta carpetizador
        carpetizador_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "carpetizador"
        )
        os.makedirs(carpetizador_dir, exist_ok=True)
        filename = os.path.join(
            carpetizador_dir,
            f"historial_carpetizador_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        # Intentar escribir el archivo y manejar errores de E/S específicos
        try:
            df.to_csv(filename, index=False, encoding='utf-8')
            messagebox.askokcancel("Exportar", f"Historial exportado como: {filename}")
        except (OSError, PermissionError) as e:
            messagebox.showerror("Error de E/S", f"No se pudo escribir el archivo: {e}")

    def apply_filter_order(self):
        """Filtra y ordena los datos según la entrada del usuario"""
        history_data = get_history()
        filtro = self.filter_entry.get().strip().lower()
        orden = self.order_var.get()

        # Filtrar por nombre de archivo
        if filtro:
            filtered = [h for h in history_data if filtro in h['filename'].lower()]
        else:
            filtered = history_data

        # Ordenar
        try:
            filtered = sorted(filtered, key=lambda h: h[orden])
        except (KeyError, TypeError, ValueError):
            messagebox.showwarning("Orden", "No se pudo ordenar por el campo seleccionado;"
                                   " verifica los datos y el criterio de ordenación.")
            # Dejar la lista sin ordenar si falla el ordenamiento

        self.filtered_data = filtered

        # Actualizar tabla y gráfico
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.create_table(self.table_frame, self.filtered_data)

        #if MATPLOTLIB_AVAILABLE:
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        self.create_charts(self.chart_frame, self.filtered_data)
