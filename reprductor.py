""" Gestor de videos - Organizar, clasificar y reproducir videos """

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sqlite3
from pathlib import Path
try:
    # When package-installed or used as a module
    from .version import get_version
except Exception:
    # Fallback when running as a script (tests running from tests/)
    try:
        from version import get_version
    except Exception:
        def get_version():
            return '0.0.0'
from datetime import datetime
import math
from PIL import Image, ImageTk
import cv2
import vlc


VLC_AVAILABLE = True


class ProgressDialog:
    """Ventana de diálogo con barra de progreso"""
    def __init__(self, parent, title, message, total):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x120")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        # Centrar ventana
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (120 // 2)
        self.window.geometry(f"+{x}+{y}")

        # Mensaje
        self.label = ttk.Label(self.window, text=message, font=('Arial', 10))
        self.label.pack(pady=10)

        # Barra de progreso
        self.progress = ttk.Progressbar(self.window, length=360, mode='determinate', maximum=total)
        self.progress.pack(pady=10)

        # Etiqueta de estado
        self.status_label = ttk.Label(self.window, text=f"0 / {total}", font=('Arial', 9))
        self.status_label.pack(pady=5)

        self.total = total
        self.current = 0

    def update(self, current, status_text=""):
        """Actualiza la barra de progreso"""
        self.current = current
        self.progress['value'] = current
        self.status_label.config(text=f"{current} / {self.total} - {status_text}")
        self.window.update()

    def close(self):
        """Cierra la ventana de progreso"""
        self.window.grab_release()
        self.window.destroy()


# Constantes de colores
BG_COLOR = '#f0f0f0'
SIDEBAR_BG = '#2c3e50'
SIDEBAR_FG = '#ecf0f1'
ACCENT_COLOR = '#3498db'
HOVER_COLOR = '#2980b9'

class VideoDatabase:
    """Gestiona la base de datos de videos"""

    def __init__(self, db_path='videos.db'):
        self.db_path = db_path
        self.conn = None
        self.init_db()

    def init_db(self):
        """Inicializa la base de datos y crea las tablas"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Tabla de videos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                category TEXT,
                tags TEXT,
                rating INTEGER DEFAULT 0,
                duration REAL,
                added_date TEXT,
                last_played TEXT,
                play_count INTEGER DEFAULT 0,
                notes TEXT,
                thumbnail_path TEXT
            )
        ''')

        # Migración: añadir columna thumbnail_path si no existe
        cursor.execute("PRAGMA table_info(videos)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'thumbnail_path' not in columns:
            cursor.execute('ALTER TABLE videos ADD COLUMN thumbnail_path TEXT')

        # Tabla de categorías
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT
            )
        ''')

        # Insertar categorías predefinidas si no existen
        predefined_categories = [
            ('public', '#3498db'),    # Azul
            ('private', '#e74c3c'),   # Rojo
            ('ticket', '#f39c12'),    # Naranja
            ('password', '#9b59b6'),  # Morado
            ('clip', '#2ecc71'),      # Verde
            ('special', '#e67e22')    # Naranja oscuro
        ]

        for cat_name, cat_color in predefined_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)
            ''', (cat_name, cat_color))

        self.conn.commit()

    def add_video(self, filepath, category='public', tags=''):
        """Añade un video a la base de datos"""
        cursor = self.conn.cursor()
        filename = os.path.basename(filepath)
        added_date = datetime.now().isoformat()

        try:
            cursor.execute('''
                INSERT INTO videos (filepath, filename, category, tags, added_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (filepath, filename, category, tags, added_date))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Video ya existe

    def get_all_videos(self, category=None, search_term=None):
        """Obtiene todos los videos, opcionalmente filtrados"""
        cursor = self.conn.cursor()

        query = 'SELECT * FROM videos WHERE 1=1'
        params = []

        if category and category != 'Todos':
            query += ' AND category = ?'
            params.append(category)

        if search_term:
            query += ' AND (filename LIKE ? OR tags LIKE ? OR notes LIKE ?)'
            search_pattern = f'%{search_term}%'
            params.extend([search_pattern, search_pattern, search_pattern])

        query += ' ORDER BY added_date DESC'

        cursor.execute(query, params)
        return cursor.fetchall()

    def get_categories(self):
        """Obtiene todas las categorías predefinidas"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM categories ORDER BY name')
        return [row[0] for row in cursor.fetchall()]

    def update_video(self, video_id, **kwargs):
        """Actualiza campos de un video"""
        if not kwargs:
            return  # No hay campos para actualizar

        cursor = self.conn.cursor()

        # Lista blanca de columnas permitidas para actualizar
        allowed_columns = {
            'filepath', 'filename', 'category', 'tags', 'rating', 'duration', 'notes', 'thumbnail_path'}

        # Filtrar solo claves válidas
        safe_kwargs = {k: v for k, v in kwargs.items() if k in allowed_columns}
        if not safe_kwargs:
            return  # No hay campos válidos para actualizar
        set_clause = ', '.join([f'{key} = ?' for key in safe_kwargs.keys()])
        values = list(safe_kwargs.values()) + [video_id]


        cursor.execute(f'UPDATE videos SET {set_clause} WHERE id = ?', values)
        if cursor.rowcount > 0:
            self.conn.commit()
        else:
            # No se encontró el video; registrar advertencia pero no fallar
            print(f"Warning: No video found with id {video_id} to update.")

    def delete_video(self, video_id):
        """Elimina un video de la base de datos"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))
        self.conn.commit()

    def increment_play_count(self, video_id):
        """Incrementa el contador de reproducciones"""
        cursor = self.conn.cursor()
        last_played = datetime.now().isoformat()
        cursor.execute('''
            UPDATE videos 
            SET play_count = play_count + 1, last_played = ?
            WHERE id = ?
        ''', (last_played, video_id))
        self.conn.commit()

    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.conn:
            self.conn.close()


class VideoManagerApp:
    """Aplicación principal de gestión de videos"""

    def __init__(self, root):
        self.root = root
        # Mostrar versión en el título
        version = get_version()
        self.root.title(f"Gestor de Videos v{version}")
        self.root.geometry("1200x700")

        # Base de datos
        self.db = VideoDatabase()
        self.search_var = None
        self.category_var = None
        self.category_combo = None
        self.video_tree = None
        self.context_menu = None
        self.preview_canvas = None
        self.preview_label = None
        self.play_btn = None
        self.generate_timeline_btn = None
        self.preview_inner_frame = None
        self.preview_canvas_window = None
        self.preview_default_label = None
        self.timeline_images = []
        self.video_panel = None
        self.time_label = None
        self.progress_var = None
        self.volume_var = None
        self.progress_scale = None
        self.duration_label = None
        self.name_label = None
        self.detail_category_var = None
        self.detail_category_combo = None
        self.tags_entry = None
        self.rating_var = None
        self.notes_text = None


        # Directorio para miniaturas
        self.thumbnail_dir = Path('thumbnails')
        self.thumbnail_dir.mkdir(exist_ok=True)

        # Reproductor VLC (con logging silenciado para evitar spam de errores)
        if VLC_AVAILABLE:
            # Silenciar mensajes de error de VLC
            self.instance = vlc.Instance('--quiet', '--no-xlib')
            self.player = self.instance.media_player_new()
        else:
            self.player = None
            messagebox.showwarning("VLC no disponible",
                                 "python-vlc no está instalado."
                                 "La reproducción no estará disponible.")

        self.current_video = None
        self.current_thumbnail = None
        # Flag para indicar que el usuario está arrastrando la barra de progreso
        self.seeking = False
        self._was_playing = False

        # Construir UI
        self.build_ui()

        # Cargar videos
        self.refresh_video_list()

    def get_video_duration(self, filepath):
        """Obtiene la duración del video en segundos usando OpenCV"""
        try:
            cap = cv2.VideoCapture(filepath)  # type: ignore
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)  # type: ignore
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)  # type: ignore
                cap.release()

                if fps > 0:
                    duration = frame_count / fps
                    return int(duration)
            return 0
        except (cv2.error, OSError, ValueError, AttributeError):
            return 0

    @staticmethod
    def format_duration(seconds):
        """Formatea la duración en segundos a formato HH:MM:SS o MM:SS"""
        if seconds is None or seconds == 0:
            return "00:00"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def format_time_ms(milliseconds):
        """Formatea el tiempo en milisegundos a formato HH:MM:SS o MM:SS"""
        if milliseconds is None or milliseconds < 0:
            return "00:00"

        total_seconds = milliseconds / 1000
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        secs = int(total_seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def build_ui(self):
        """Construye la interfaz de usuario"""
        # Menu con About (muestra versión)
        try:
            menubar = tk.Menu(self.root)
            help_menu = tk.Menu(menubar, tearoff=0)
            help_menu.add_command(label=f"About (v{get_version()})", command=self.show_about)
            menubar.add_cascade(label="Help", menu=help_menu)
            self.root.config(menu=menubar)
        except Exception:
            pass
        # Panel principal dividido
        self.paned = ttk.PanedWindow(self.root, orient='horizontal')
        self.paned.pack(fill='both', expand=True)

        # Panel izquierdo (biblioteca)
        self.build_library_panel()

        # Panel derecho (reproductor y detalles)
        self.build_player_panel()

    def build_library_panel(self):
        """Construye el panel de biblioteca de videos"""
        library_frame = ttk.Frame(self.paned, width=400)
        self.paned.add(library_frame, weight=1)

        # Barra de herramientas
        toolbar = ttk.Frame(library_frame)
        toolbar.pack(side='top', fill='x', padx=5, pady=5)

        ttk.Button(toolbar, text="➕ Añadir Video",
                  command=self.add_video).pack(side='left', padx=2)
        ttk.Button(toolbar, text="📁 Añadir Carpeta",
                  command=self.add_folder).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🔄 Actualizar",
                  command=self.refresh_video_list).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🖼️ Miniaturas",
                  command=self.regenerate_all_thumbnails).pack(side='left', padx=2)
        ttk.Button(toolbar, text="⏱️ Duraciones",
                  command=self.calculate_all_durations).pack(side='left', padx=2)

        # Búsqueda
        search_frame = ttk.Frame(library_frame)
        search_frame.pack(side='top', fill='x', padx=5, pady=5)

        ttk.Label(search_frame, text="Buscar:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.refresh_video_list())
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side='left', fill='x',
                                                                   expand=True, padx=5)

        # Filtro por categoría
        filter_frame = ttk.Frame(library_frame)
        filter_frame.pack(side='top', fill='x', padx=5, pady=5)

        ttk.Label(filter_frame, text="Categoría:").pack(side='left')
        self.category_var = tk.StringVar(value='Todos')
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var,
                                           state='readonly')
        self.category_combo.pack(side='left', fill='x', expand=True, padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_video_list())

        # Lista de videos (Treeview)
        list_frame = ttk.Frame(library_frame)
        list_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        # Treeview
        self.video_tree = ttk.Treeview(list_frame, columns=('filename', 'duration',
                                                            'category', 'rating'),
                                       show='tree headings', yscrollcommand=scrollbar.set)
        self.video_tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.video_tree.yview)

        # Columnas
        # Make headings clickable to sort columns
        self.video_tree.heading('#0', text='ID', command=lambda: self.sort_treeview('#0'))
        self.video_tree.heading('filename', text='Nombre', command=lambda: self.sort_treeview(
            'filename'))
        self.video_tree.heading('duration', text='Duración', command=lambda: self.sort_treeview(
            'duration'))
        self.video_tree.heading('category', text='Categoría', command=lambda: self.sort_treeview(
            'category'))
        self.video_tree.heading('rating', text='Rating ⭐', command=lambda: self.sort_treeview(
            'rating'))

        self.video_tree.column('#0', width=50)
        self.video_tree.column('filename', width=200)
        self.video_tree.column('duration', width=80)
        self.video_tree.column('category', width=100)
        self.video_tree.column('rating', width=50)

        # Eventos
        self.video_tree.bind('<Double-Button-1>', self.on_video_double_click)
        self.video_tree.bind('<<TreeviewSelect>>', self.on_video_select)

        # Menú contextual
        self.context_menu = tk.Menu(self.video_tree, tearoff=0)
        self.context_menu.add_command(label="Reproducir", command=self.play_selected_video)
        self.context_menu.add_command(label="Editar", command=self.edit_selected_video)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Eliminar", command=self.delete_selected_video)

        self.video_tree.bind('<Button-3>', self.show_context_menu)

        # Keep track of sort order per column
        self._treeview_sort_state = {}
        # Store base heading labels so we can append ▲/▼ indicators
        self._treeview_heading_labels = {
            '#0': 'ID',
            'filename': 'Nombre',
            'duration': 'Duración',
            'category': 'Categoría',
            'rating': 'Rating ⭐'
        }

        # Frame para preview/thumbnail (en la parte inferior del panel de biblioteca)
        preview_frame = ttk.LabelFrame(library_frame, text="Vista Previa")
        preview_frame.pack(side='bottom', fill='both', expand=True, padx=5, pady=5)

        # Botón para generar timeline de miniaturas
        self.generate_timeline_btn = ttk.Button(preview_frame,
                                               text="📸 Generar Timeline de Miniaturas",
                                               command=self.generate_timeline_thumbnails,
                                               state='disabled')
        self.generate_timeline_btn.pack(side='top', pady=5)

        # Botón para añadir 4 miniaturas adicionales (si duración > 15 minutos)
        self.add_four_btn = ttk.Button(preview_frame,
                                       text="➕ Añadir 4 miniaturas (si >15min)",
                                       command=self.add_four_more_thumbnails_if_long,
                                       state='disabled')
        self.add_four_btn.pack(side='top', pady=2)

        # Canvas con scrollbar para miniaturas múltiples
        canvas_frame = ttk.Frame(preview_frame)
        canvas_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        self.preview_canvas = tk.Canvas(canvas_frame, bg='#2c3e50', height=350)
        scrollbar_preview = ttk.Scrollbar(canvas_frame, orient='vertical',
                                         command=self.preview_canvas.yview)
        self.preview_canvas.configure(yscrollcommand=scrollbar_preview.set)

        scrollbar_preview.pack(side='right', fill='y')
        self.preview_canvas.pack(side='left', fill='both', expand=True)

        # Frame interior del canvas para las miniaturas
        self.preview_inner_frame = tk.Frame(self.preview_canvas, bg='#2c3e50')
        self.preview_canvas_window = self.preview_canvas.create_window(
            0, 0, window=self.preview_inner_frame, anchor='nw')

        # Bind para actualizar el scrollregion
        self.preview_inner_frame.bind('<Configure>',
                                     lambda e: self.preview_canvas.configure(
                                         scrollregion=self.preview_canvas.bbox('all')))

        # Bind mouse wheel scrolling for the preview area (Windows, Linux, macOS)
        # Windows and macOS: <MouseWheel> with event.delta; Linux: Button-4/5
        self.preview_canvas.bind('<MouseWheel>', self._on_preview_mousewheel)
        self.preview_inner_frame.bind('<MouseWheel>', self._on_preview_mousewheel)
        self.preview_canvas.bind('<Button-4>', self._on_preview_mousewheel)
        self.preview_canvas.bind('<Button-5>', self._on_preview_mousewheel)
        self.preview_inner_frame.bind('<Button-4>', self._on_preview_mousewheel)
        self.preview_inner_frame.bind('<Button-5>', self._on_preview_mousewheel)

        # Label por defecto (se mostrará cuando no hay miniaturas)
        self.preview_default_label = tk.Label(self.preview_inner_frame,
                                             text="Selecciona un video\ny haz clic en el botón\n"
                                             "para generar miniaturas",
                                             bg='#2c3e50', fg='white', font=('Arial', 12))
        # Use grid inside preview_inner_frame to avoid mixing with grid-used thumbnails
        self.preview_default_label.grid(row=0, column=0, sticky='nsew', pady=50)
        # Keep a persistent reference used by load_thumbnail
        self.preview_label = self.preview_default_label
        # Ensure the inner frame expands the single cell so the label centers
        self.preview_inner_frame.grid_rowconfigure(0, weight=1)
        self.preview_inner_frame.grid_columnconfigure(0, weight=1)

        # Lista para guardar referencias a las imágenes
        self.timeline_images = []

    def build_player_panel(self):
        """Construye el panel del reproductor"""
        player_frame = ttk.Frame(self.paned)
        self.paned.add(player_frame, weight=2)

        # Frame del video
        video_frame = ttk.LabelFrame(player_frame, text="Reproductor")
        video_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        if VLC_AVAILABLE:
            self.video_panel = tk.Frame(video_frame, bg='black')
            self.video_panel.pack(fill='both', expand=True)
        else:
            ttk.Label(video_frame, text="Reproductor no disponible\nInstala python-vlc",
                     justify='center').pack(fill='both', expand=True)

        # Controles de reproducción
        controls_frame = ttk.Frame(player_frame)
        controls_frame.pack(side='top', fill='x', padx=5, pady=5)

        self.play_btn = ttk.Button(controls_frame, text="▶ Play", command=self.play_pause)
        self.play_btn.pack(side='left', padx=2)

        # Seek buttons: retroceder/avanzar 10 segundos
        ttk.Button(controls_frame, text="⏪ -10s", command=lambda: self.seek_relative(
            -10)).pack(side='left', padx=2)
        ttk.Button(controls_frame, text="⏩ +10s", command=lambda: self.seek_relative(
            10)).pack(side='left', padx=2)

        ttk.Button(controls_frame, text="⏹ Stop", command=self.stop_video).pack(side='left', padx=2)

        # Etiqueta de tiempo actual
        self.time_label = ttk.Label(controls_frame, text="00:00", width=8, anchor='e')
        self.time_label.pack(side='left', padx=(10, 5))

        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_scale = ttk.Scale(controls_frame, from_=0, to=100,
                                       variable=self.progress_var, orient='horizontal')
        self.progress_scale.pack(side='left', fill='x', expand=True, padx=5)
        # Bind press/move/release to support dragging the slider to seek
        self.progress_scale.bind('<ButtonPress-1>', self.on_progress_press)
        self.progress_scale.bind('<B1-Motion>', self.on_progress_move)
        self.progress_scale.bind('<ButtonRelease-1>', self.on_progress_release)
        # Also support simple clicks on the scale
        self.progress_scale.bind('<Button-1>', self.on_progress_click)

        # Etiqueta de duración total
        self.duration_label = ttk.Label(controls_frame, text="00:00", width=8, anchor='w')
        self.duration_label.pack(side='left', padx=(5, 10))

        # Volumen
        ttk.Label(controls_frame, text="🔊").pack(side='left')
        self.volume_var = tk.IntVar(value=50)
        volume_scale = ttk.Scale(controls_frame, from_=0, to=100,
                                variable=self.volume_var, orient='horizontal',
                                command=self.set_volume, length=100)
        volume_scale.pack(side='left', padx=2)

        # Keyboard shortcuts using Ctrl modifier:
        # Ctrl+J -> retroceder 10s, Ctrl+K or Ctrl+Space -> play/pause, Ctrl+L -> avanzar 10s
        try:
            # Use Control-<key> bindings so modifiers are required
            self.root.bind('<Control-j>', lambda e: self.seek_relative(-10))
            self.root.bind('<Control-J>', lambda e: self.seek_relative(-10))
            self.root.bind('<Control-k>', lambda e: self.play_pause())
            self.root.bind('<Control-K>', lambda e: self.play_pause())
            # Allow Ctrl+Space as an alternative to toggle play/pause
            self.root.bind('<Control-space>', lambda e: self.play_pause())
            self.root.bind('<Control-l>', lambda e: self.seek_relative(10))
            self.root.bind('<Control-L>', lambda e: self.seek_relative(10))
        except Exception:
            # If binding fails, don't block the UI
            pass

        # Panel de detalles
        details_frame = ttk.LabelFrame(player_frame, text="Detalles del Video")
        details_frame.pack(side='top', fill='both', padx=5, pady=5)

        # Grid para detalles
        ttk.Label(details_frame, text="Nombre:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.name_label = ttk.Label(details_frame, text="-")
        self.name_label.grid(row=0, column=1, sticky='w', padx=5, pady=2)

        ttk.Label(details_frame, text="Categoría:").grid(row=1, column=0, sticky='w',
                                                         padx=5, pady=2)
        self.detail_category_var = tk.StringVar()
        self.detail_category_combo = ttk.Combobox(details_frame,
                                                  textvariable=self.detail_category_var)
        self.detail_category_combo.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        self.detail_category_combo.bind('<<ComboboxSelected>>', self.update_current_video_category)

        ttk.Label(details_frame, text="Tags:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.tags_entry = ttk.Entry(details_frame)
        self.tags_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        self.tags_entry.bind('<FocusOut>', self.update_current_video_tags)

        ttk.Label(details_frame, text="Rating:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.rating_var = tk.IntVar(value=0)
        rating_frame = ttk.Frame(details_frame)
        rating_frame.grid(row=3, column=1, sticky='w', padx=5, pady=2)
        for i in range(5):
            ttk.Radiobutton(rating_frame, text=f"{'⭐' * (i+1)}",
                          variable=self.rating_var, value=i+1,
                          command=self.update_current_video_rating).pack(side='left')

        ttk.Label(details_frame, text="Notas:").grid(row=4, column=0, sticky='nw', padx=5, pady=2)
        self.notes_text = tk.Text(details_frame, height=4, width=40)
        self.notes_text.grid(row=4, column=1, sticky='ew', padx=5, pady=2)
        self.notes_text.bind('<FocusOut>', self.update_current_video_notes)

        details_frame.columnconfigure(1, weight=1)

    def add_video(self):
        """Añade un video a la biblioteca"""
        filepath = filedialog.askopenfilename(
            title="Seleccionar video",
            filetypes=[
                ("Videos", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filepath:
            video_id = self.db.add_video(filepath)
            if video_id:
                # Obtener y actualizar duración
                duration = self.get_video_duration(filepath)
                if duration > 0:
                    self.db.update_video(video_id, duration=duration)

                # Generar miniatura
                self.generate_thumbnail(filepath, video_id)
                messagebox.askokcancel("Éxito", f"Video añadido: {os.path.basename(filepath)}")
                self.refresh_video_list()
            else:
                messagebox.showwarning("Advertencia", "Este video ya está en la biblioteca")

    def add_folder(self):
        """Añade todos los videos de una carpeta"""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de videos")

        if folder:
            video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}

            # Primero contar todos los videos
            video_files = []
            for root, _dirs, files in os.walk(folder):
                for file in files:
                    if Path(file).suffix.lower() in video_extensions:
                        filepath = os.path.join(root, file)
                        video_files.append(filepath)

            total = len(video_files)

            if total == 0:
                messagebox.askokcancel("Info", "No se encontraron videos en la carpeta")
                return

            # Crear ventana de progreso
            progress_dialog = ProgressDialog(self.root, "Añadiendo Videos",
                                            "Procesando videos de la carpeta...", total)
            added_count = 0

            for idx, filepath in enumerate(video_files, 1):
                filename = os.path.basename(filepath)
                video_id = self.db.add_video(filepath)
                if video_id:
                    # Obtener y actualizar duración
                    duration = self.get_video_duration(filepath)
                    if duration > 0:
                        self.db.update_video(video_id, duration=duration)

                    # Generar miniatura
                    self.generate_thumbnail(filepath, video_id)
                    added_count += 1
                    progress_dialog.update(idx, f"Añadido: {filename[:30]}...")
                else:
                    progress_dialog.update(idx, f"Ya existe: {filename[:30]}...")

            # Cerrar ventana de progreso
            progress_dialog.close()

            messagebox.askokcancel("Éxito", f"Se añadieron {added_count} videos de {total}")
            self.refresh_video_list()

    def refresh_video_list(self):
        """Actualiza la lista de videos"""
        # Limpiar tree
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)

        # Actualizar categorías
        categories = ['Todos'] + self.db.get_categories()
        self.category_combo['values'] = categories
        self.detail_category_combo['values'] = self.db.get_categories()

        # Obtener videos filtrados
        search_term = self.search_var.get()
        category = self.category_var.get()

        videos = self.db.get_all_videos(
            category=category if category != 'Todos' else None,
            search_term=search_term if search_term else None
        )

        # Poblar tree
        for video in videos:
            video_id, _filepath, filename, category, _tags, rating, duration, *_ = video
            duration_str = self.format_duration(duration)
            self.video_tree.insert('', 'end', iid=str(video_id),
                                  text=str(video_id),
                                  values=(filename, duration_str, category or 'public',
                                          '⭐' * rating))

    def on_video_select(self, _event):
        """Maneja la selección de un video"""
        selection = self.video_tree.selection()
        if not selection:
            self.generate_timeline_btn.config(state='disabled')
            return

        video_id = int(selection[0])
        videos = self.db.get_all_videos()

        for video in videos:
            if video[0] == video_id:
                self.current_video = video
                self.load_video_details(video)
                # Habilitar botón de timeline
                self.generate_timeline_btn.config(state='normal')
                break

    def load_video_details(self, video):
        """Carga los detalles de un video en el panel de detalles"""
        # Manejar tanto videos con 11 campos (viejos) como 12 campos (nuevos)
        if len(video) == 11:
            (_video_id, _filepath, filename, category, tags, rating, _duration, _added_date,
             _last_played, _play_count, notes) = video
            _thumbnail_path = None
        else:
            (_video_id, _filepath, filename, category, tags, rating, _duration, _added_date,
             _last_played, _play_count, notes, _thumbnail_path) = video

        self.name_label.config(text=filename)
        self.detail_category_var.set(category or 'public')
        self.tags_entry.delete(0, 'end')
        self.tags_entry.insert(0, tags or '')
        self.rating_var.set(rating or 0)
        self.notes_text.delete('1.0', 'end')
        self.notes_text.insert('1.0', notes or '')

        # Limpiar vista previa anterior
        self.clear_timeline_preview()

    def on_video_double_click(self, _event):
        """Maneja el doble clic en un video"""
        self.play_selected_video()

    def play_selected_video(self):
        """Reproduce el video seleccionado"""
        if not self.current_video or not VLC_AVAILABLE:
            return

        video_id, filepath, *_ = self.current_video

        if not os.path.exists(filepath):
            messagebox.showerror("Error", "El archivo de video no existe")
            return

        # Incrementar contador
        self.db.increment_play_count(video_id)

        # Reproducir
        media = self.instance.media_new(filepath)
        self.player.set_media(media)
        self.player.set_hwnd(self.video_panel.winfo_id())
        self.player.play()
        self.play_btn.config(text="⏸ Pause")

        # Resetear etiquetas de tiempo
        self.time_label.config(text="00:00")
        self.duration_label.config(text="00:00")
        self.progress_var.set(0)

        # Dar tiempo a VLC para cargar el video y luego actualizar
        self.root.after(100, self.update_progress)

    def play_pause(self):
        """Alterna entre play y pause"""
        if not VLC_AVAILABLE or not self.player:
            return
        if self.player.is_playing():
            # Pausar el video
            self.player.pause()
            self.play_btn.config(text="▶ Play")
            # Actualizar una última vez para mantener los tiempos visibles
            self.update_progress_once()
            return

        # Si llegamos aquí, queremos reproducir o reanudar
        # Si no hay video seleccionado, nada que hacer
        if not self.current_video:
            return

        selected_filepath = self.current_video[1]

        # Si no existe el archivo seleccionado, mostrar error
        if not os.path.exists(selected_filepath):
            messagebox.showerror("Error", "El archivo de video no existe")
            return

        # Obtener media actualmente cargado en el player (si existe)
        current_media = self.player.get_media()
        try:
            current_mrl = current_media.get_mrl() if current_media is not None else None
        except (AttributeError, TypeError):
            current_mrl = None

        # URI del archivo seleccionado
        try:
            selected_mrl = Path(selected_filepath).as_uri()
        except (ValueError, OSError):
            selected_mrl = None

        # Si el media cargado corresponde al seleccionado, simplemente reanudar
        if current_mrl and selected_mrl and current_mrl == selected_mrl:
            self.player.play()
            self.play_btn.config(text="⏸ Pause")
            self.root.after(100, self.update_progress)
            return

        # Si el media cargado es distinto, cargar y reproducir el seleccionado
        self.play_selected_video()

    def stop_video(self):
        """Detiene la reproducción"""
        if VLC_AVAILABLE and self.player:
            self.player.stop()
            self.play_btn.config(text="▶ Play")
            self.progress_var.set(0)
            self.time_label.config(text="00:00")
            # La duración se mantiene visible

    def seek_relative(self, seconds):
        """Seek relativo (segundos) desde la posición actual. Positive -> avanzar, negative -> retroceder."""
        if not VLC_AVAILABLE or not self.player:
            return
        try:
            total_ms = self.player.get_length()
            if total_ms <= 0:
                return

            current_ms = self.player.get_time()
            if current_ms < 0:
                current_ms = 0

            new_ms = int(current_ms + (seconds * 1000))
            new_ms = max(0, min(new_ms, int(total_ms)))

            # Marcar seeking para evitar race con update_progress
            self.seeking = True
            # Realizar seek
            try:
                self.player.set_time(new_ms)
            except Exception:
                # Fallback a set_position si set_time no está disponible
                try:
                    pos = float(new_ms) / float(total_ms)
                    self.player.set_position(pos)
                except Exception:
                    pass

            # Actualizar UI inmediatamente
            self.update_progress_once()
        finally:
            self.seeking = False

    def set_volume(self, value):
        """Establece el volumen"""
        if VLC_AVAILABLE and self.player:
            self.player.audio_set_volume(int(float(value)))

    def on_progress_click(self, _event):
        """Maneja el clic en la barra de progreso"""
        if not VLC_AVAILABLE or not self.player:
            return

        # Calcular posición
        length = self.player.get_length()
        if length > 0:
            position = self.progress_var.get() / 100.0
            self.player.set_position(position)
            # Forzar actualización inmediata
            self.root.after(100, self.update_progress)

    def on_progress_press(self, _event):
        """Usuario inició la interacción con la barra (presionó)."""
        if not VLC_AVAILABLE or not self.player:
            return
        # Marcar que estamos en modo 'seeking'
        self.seeking = True
        try:
            self._was_playing = bool(self.player.is_playing())
        except Exception:
            self._was_playing = False
        # Pausar actualización automática mientras el usuario arrastra

    def on_progress_move(self, _event):
        """Actualizar posición visual mientras el usuario arrastra."""
        if not VLC_AVAILABLE or not self.player:
            return
        # Solo actualizar la etiqueta de tiempo mientras arrastra
        try:
            length = self.player.get_length()
            if length > 0:
                position = self.progress_var.get() / 100.0
                ms = int(position * length)
                self.time_label.config(text=self.format_time_ms(ms))
        except Exception:
            pass

    def on_progress_release(self, _event):
        """El usuario soltó el slider; hacer seek y reanudar si era necesario."""
        if not VLC_AVAILABLE or not self.player:
            self.seeking = False
            return

        try:
            length = self.player.get_length()
            if length > 0:
                position = self.progress_var.get() / 100.0
                # Realizar el seek en VLC
                self.player.set_position(position)
                # Si estaba reproduciendo antes del seek, reanudar
                if self._was_playing:
                    # small delay to let VLC process the set_position
                    self.root.after(100, command=self.player.play)
                    self.play_btn.config(text="⏸ Pause")
                else:
                    # Force update once to reflect the newly selected position
                    self.update_progress_once()
        except Exception:
            pass
        finally:
            # salir del modo seeking y reanudar las actualizaciones automáticas
            self.seeking = False
            # Reanudar la actualización periódica si está reproduciendo
            try:
                if self.player.get_state() == vlc.State.Playing:  # type: ignore
                    self.root.after(500, self.update_progress)
            except Exception:
                pass

    def update_progress(self):
        """Actualiza la barra de progreso y los tiempos"""
        if VLC_AVAILABLE and self.player:
            # Obtener estado del reproductor
            state = self.player.get_state()

            # Actualizar si está reproduciendo o en pausa
            if state in (vlc.State.Playing, vlc.State.Paused):  # type: ignore
                # Actualizar posición
                position = self.player.get_position()
                if position >= 0:
                    self.progress_var.set(position * 100)

                # Actualizar tiempos
                current_time = self.player.get_time()  # En milisegundos
                total_time = self.player.get_length()  # En milisegundos

                if current_time >= 0:
                    self.time_label.config(text=self.format_time_ms(current_time))

                if total_time > 0:
                    self.duration_label.config(text=self.format_time_ms(total_time))

                # Continuar actualizando solo si está reproduciendo
                if state == vlc.State.Playing:  # type: ignore
                    self.root.after(500, self.update_progress)
            elif state == vlc.State.Playing:  # type: ignore
                # Si está intentando reproducir, seguir intentando
                self.root.after(500, self.update_progress)

    def update_progress_once(self):
        """Actualiza la barra de progreso y los tiempos una sola vez (para cuando está pausado)"""
        if VLC_AVAILABLE and self.player:
            # Actualizar posición
            position = self.player.get_position()
            if position >= 0:
                self.progress_var.set(position * 100)

            # Actualizar tiempos
            current_time = self.player.get_time()  # En milisegundos
            total_time = self.player.get_length()  # En milisegundos

            if current_time >= 0:
                self.time_label.config(text=self.format_time_ms(current_time))

            if total_time > 0:
                self.duration_label.config(text=self.format_time_ms(total_time))


    def update_current_video_category(self, _event=None):
        """Actualiza la categoría del video actual"""
        if self.current_video:
            video_id = self.current_video[0]
            category = self.detail_category_var.get()
            self.db.update_video(video_id, category=category)
            self.refresh_video_list()

    def update_current_video_tags(self, _event=None):
        """Actualiza los tags del video actual"""
        if self.current_video:
            video_id = self.current_video[0]
            tags = self.tags_entry.get()
            self.db.update_video(video_id, tags=tags)

    def update_current_video_rating(self):
        """Actualiza el rating del video actual"""
        if self.current_video:
            video_id = self.current_video[0]
            rating = self.rating_var.get()
            self.db.update_video(video_id, rating=rating)
            self.refresh_video_list()

    def update_current_video_notes(self, _event=None):
        """Actualiza las notas del video actual"""
        if self.current_video:
            video_id = self.current_video[0]
            notes = self.notes_text.get('1.0', 'end-1c')
            self.db.update_video(video_id, notes=notes)

    def edit_selected_video(self):
        """Edita el video seleccionado (enfoca el panel de detalles)"""
        if self.current_video:
            self.detail_category_combo.focus()

    def delete_selected_video(self):
        """Elimina el video seleccionado de la biblioteca"""
        if not self.current_video:
            return

        video_id, _filepath, filename, *_ = self.current_video

        if messagebox.askyesno("Confirmar", f"¿Eliminar '{filename}' de la biblioteca?\n"
                               "(El archivo no se borrará del disco)"):
            self.db.delete_video(video_id)
            self.current_video = None
            self.refresh_video_list()
            messagebox.askokcancel("Éxito", "Video eliminado de la biblioteca")

    def show_context_menu(self, event):
        """Muestra el menú contextual"""
        item = self.video_tree.identify_row(event.y)
        if item:
            self.video_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def sort_treeview(self, col):
        """Ordena la Treeview por la columna `col`, alternando asc/desc."""
        try:
            # Obtener items actuales
            items = [(self.video_tree.set(k, col) if col != '#0' else k, k) for k in self.video_tree.get_children('')]

            # Detectar si la columna es numérica (duration o rating or id)
            def try_float(v):
                try:
                    return float(v)
                except Exception:
                    return None

            parsed = []
            for val, k in items:
                if col == '#0':
                    # id is from item id (string), try int
                    try:
                        parsed.append((int(val), k))
                    except Exception:
                        parsed.append((val, k))
                else:
                    # remove non-digit chars for duration like 00:03:12 -> compute seconds
                    if col == 'duration':
                        # Try to parse duration format HH:MM:SS or MM:SS
                        try:
                            parts = val.split(':')
                            parts = [int(p) for p in parts]
                            seconds = 0
                            if len(parts) == 3:
                                seconds = parts[0]*3600 + parts[1]*60 + parts[2]
                            elif len(parts) == 2:
                                seconds = parts[0]*60 + parts[1]
                            else:
                                seconds = int(val)
                            parsed.append((seconds, k))
                        except Exception:
                            parsed.append((val, k))
                    else:
                        f = try_float(val)
                        if f is not None:
                            parsed.append((f, k))
                        else:
                            parsed.append((val.lower() if isinstance(val, str) else val, k))

            # Determine current sort order and toggle
            asc = self._treeview_sort_state.get(col, True)
            parsed.sort(key=lambda x: x[0], reverse=not asc)

            # Reorder items
            for index, (_v, k) in enumerate(parsed):
                self.video_tree.move(k, '', index)

            # Update header indicators (▲ for asc, ▼ for desc)
            try:
                self._update_treeview_header_indicators(col, asc)
            except Exception:
                pass

            # Toggle for next click
            self._treeview_sort_state[col] = not asc
        except Exception:
            # If any problem, quietly ignore (do not crash UI)
            pass

    def _update_treeview_header_indicators(self, active_col, asc):
        """Update the column headers to show ▲/▼ for the active sorted column."""
        try:
            for c, base_label in self._treeview_heading_labels.items():
                if c == active_col:
                    indicator = '▲' if asc else '▼'
                    text = f"{base_label} {indicator}"
                else:
                    text = base_label
                # For the tree column '#0', heading expects text arg
                self.video_tree.heading(c, text=text)
        except Exception:
            pass

    def generate_thumbnail(self, video_path, video_id):
        """Genera una miniatura del video usando OpenCV (más confiable que VLC)"""
        try:
            # Abrir video con OpenCV
            cap = cv2.VideoCapture(video_path)  # type: ignore

            if not cap.isOpened():
                # Silencioso: algunos videos pueden no ser compatibles
                return None

            # Obtener el frame del medio del video
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # type: ignore

            # Intentar múltiples frames si el primero falla
            frames_to_try = []
            if total_frames > 0:
                frames_to_try = [
                    total_frames // 2,      # Frame del medio
                    total_frames // 4,      # Frame al 25%
                    total_frames // 10,     # Frame al 10%
                    min(100, total_frames)  # Frame 100 o el último
                ]
            else:
                frames_to_try = [0]  # Intentar el primer frame

            frame_rgb = None
            for frame_pos in frames_to_try:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)  # type: ignore
                ret, frame = cap.read()

                if ret and frame is not None:
                    try:
                        # Convertir de BGR (OpenCV) a RGB (PIL)
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # type: ignore
                        break  # Éxito, salir del bucle
                    except (ValueError, TypeError, AttributeError):
                        # Ignorar frames problemáticos y probar el siguiente
                        continue  # Intentar siguiente frame

            cap.release()

            if frame_rgb is not None:
                # Crear imagen PIL
                img = Image.fromarray(frame_rgb)

                # Asegurar relación de aspecto 3:2 mediante crop centrado y redimensionado
                try:
                    target_aspect = 3.0 / 2.0
                    width, height = img.size
                    current_aspect = width / height if height else 1

                    if current_aspect > target_aspect:
                        # imagen demasiado ancha -> recortar ancho
                        new_width = int(target_aspect * height)
                        left = (width - new_width) // 2
                        img = img.crop((left, 0, left + new_width, height))
                    else:
                        # imagen demasiado alta -> recortar alto
                        new_height = int(width / target_aspect)
                        top = (height - new_height) // 2
                        img = img.crop((0, top, width, top + new_height))

                    # Redimensionar a 300x200 (3:2)
                    img = img.resize((300, 200), Image.Resampling.LANCZOS)

                    # Guardar miniatura
                    thumbnail_path = self.thumbnail_dir / f"thumb_{video_id}.jpg"
                    img.save(thumbnail_path, "JPEG", quality=85)
                except (OSError, ValueError, AttributeError):
                    # Fallback: intentar guardar la imagen tal cual en caso de errores esperados
                    thumbnail_path = self.thumbnail_dir / f"thumb_{video_id}.jpg"
                    img.save(thumbnail_path, "JPEG", quality=85)

                # Actualizar base de datos
                self.db.update_video(video_id, thumbnail_path=str(thumbnail_path))

                return str(thumbnail_path)
            else:
                # Silencioso: el video puede estar corrupto
                return None

        except (cv2.error, OSError, ValueError) as e:
            # Manejo robusto de errores específicos (OpenCV, archivos, valores)
            print(f"Error generando miniatura: {e}")
            return None

    def load_thumbnail(self, video_id, thumbnail_path, video_path):
        """Carga y muestra la miniatura del video en formato cuadrado"""
        try:
            # Si no hay miniatura, intentar generarla
            if not thumbnail_path or not os.path.exists(thumbnail_path):
                thumbnail_path = self.generate_thumbnail(video_path, video_id)

            if thumbnail_path and os.path.exists(thumbnail_path):
                # Cargar imagen
                img = Image.open(thumbnail_path)

                # Crear imagen con relación 3:2 (300x200) con crop centrado
                try:
                    target_aspect = 3.0 / 2.0
                    width, height = img.size
                    current_aspect = width / height if height else 1

                    if current_aspect > target_aspect:
                        # demasiado ancha -> recortar ancho
                        new_width = int(target_aspect * height)
                        left = (width - new_width) // 2
                        img_cropped = img.crop((left, 0, left + new_width, height))
                    else:
                        # demasiado alta -> recortar alto
                        new_height = int(width / target_aspect)
                        top = (height - new_height) // 2
                        img_cropped = img.crop((0, top, width, top + new_height))

                    img_resized = img_cropped.resize((300, 200), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img_resized)
                except (OSError, ValueError, AttributeError):
                    # Fallback to original resize centered
                    img.thumbnail((300, 200), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)

                # Mostrar en label
                self.preview_label.config(image=photo, text="")
                self.preview_label.image = photo  # Mantener referencia
                self.current_thumbnail = photo
            else:
                # Mostrar placeholder
                self.preview_label.config(image="", text="Vista previa\nno disponible",
                                        bg='#2c3e50', fg='white')
                self.current_thumbnail = None
        except (OSError, tk.TclError) as e:
            # Manejar errores relacionados con archivos de imagen y Tkinter
            print(f"Error cargando miniatura: {e}")
            self.preview_label.config(image="", text="Error cargando\nvista previa",
                                    bg='#2c3e50', fg='white')
            self.current_thumbnail = None

    def regenerate_all_thumbnails(self):
        """Regenera todas las miniaturas de los videos en la biblioteca"""
        if not messagebox.askyesno("Confirmar",
                                   "¿Generar miniaturas para todos los videos?\n"
                                   "Esto puede tomar unos minutos."):
            return

        videos = self.db.get_all_videos()
        total = len(videos)

        if total == 0:
            messagebox.askokcancel("Info", "No hay videos en la biblioteca")
            return

        # Crear ventana de progreso
        progress_dialog = ProgressDialog(self.root, "Generando Miniaturas",
                                        "Procesando videos...", total)
        generated = 0

        for idx, video in enumerate(videos, 1):
            video_id = video[0]
            filepath = video[1]
            filename = video[2]

            if os.path.exists(filepath):
                if self.generate_thumbnail(filepath, video_id):
                    generated += 1
                progress_dialog.update(idx, f"Procesado: {filename[:30]}...")
            else:
                progress_dialog.update(idx, f"No encontrado: {filename[:30]}...")

        # Cerrar ventana de progreso
        progress_dialog.close()

        messagebox.askokcancel("Completado",
                               f"Se generaron {generated} miniaturas de {total} videos")
        self.refresh_video_list()

        # Recargar la miniatura del video actual si hay uno seleccionado
        if self.current_video:
            self.load_video_details(self.current_video)

    def calculate_all_durations(self):
        """Calcula la duración de todos los videos que no la tengan"""
        if not messagebox.askyesno("Confirmar",
                                   "¿Calcular duración para todos los videos?\n"
                                   "Esto puede tomar unos minutos."):
            return

        videos = self.db.get_all_videos()

        # Filtrar solo videos sin duración
        videos_to_process = []
        for video in videos:
            video_id = video[0]
            filepath = video[1]
            current_duration = video[6] if len(video) > 6 else 0

            if (current_duration is None or current_duration == 0) and os.path.exists(filepath):
                videos_to_process.append(video)

        total = len(videos_to_process)

        if total == 0:
            messagebox.askokcancel("Info", "Todos los videos ya tienen duración calculada")
            return

        # Crear ventana de progreso
        progress_dialog = ProgressDialog(self.root, "Calculando Duraciones",
                                        "Procesando videos...", total)
        calculated = 0

        for idx, video in enumerate(videos_to_process, 1):
            video_id = video[0]
            filepath = video[1]
            filename = video[2]

            duration = self.get_video_duration(filepath)
            if duration > 0:
                self.db.update_video(video_id, duration=duration)
                calculated += 1
                progress_dialog.update(idx, f"Calculado: {filename[:30]}..."
                                       f" ({self.format_duration(duration)})")
            else:
                progress_dialog.update(idx, f"Error: {filename[:30]}...")

        # Cerrar ventana de progreso
        progress_dialog.close()

        messagebox.askokcancel("Completado",
                               f"Se calcularon {calculated} duraciones de {total} videos")
        self.refresh_video_list()

    def clear_timeline_preview(self):
        """Limpia la vista previa de timeline"""
        # Limpiar widgets del frame interior
        for widget in self.preview_inner_frame.winfo_children():
            widget.destroy()

        # Limpiar referencias a imágenes
        self.timeline_images.clear()
        self.preview_default_label = tk.Label(self.preview_inner_frame,
                                             text="Selecciona un video\ny haz clic en el botón\n"
                                             "para generar miniaturas",
                                             bg='#2c3e50', fg='white', font=('Arial', 12))
        # Use grid to match thumbnail grid placement
        self.preview_default_label.grid(row=0, column=0, sticky='nsew', pady=50)
        # Ensure the inner frame expands the single cell so the label centers
        self.preview_inner_frame.grid_rowconfigure(0, weight=1)
        self.preview_inner_frame.grid_columnconfigure(0, weight=1)
        # Keep a persistent reference used by load_thumbnail (recreated when clearing)
        self.preview_label = self.preview_default_label
        self.preview_inner_frame.grid_rowconfigure(0, weight=1)
        self.preview_inner_frame.grid_columnconfigure(0, weight=1)

    def generate_timeline_thumbnails(self):
        """Genera múltiples miniaturas del video a lo largo de su duración"""
        if not self.current_video:
            return

        _video_id = self.current_video[0]
        filepath = self.current_video[1]
        _filename = self.current_video[2]

        if not os.path.exists(filepath):
            messagebox.showerror("Error", "El archivo de video no existe")
            return

        try:
            # Obtener duración del video
            cap = cv2.VideoCapture(filepath)  # type: ignore

            if not cap.isOpened():
                messagebox.showerror("Error", "No se pudo abrir el video")
                return

            fps = cap.get(cv2.CAP_PROP_FPS)  # type: ignore
            total_frames_f = cap.get(cv2.CAP_PROP_FRAME_COUNT)  # type: ignore
            try:
                total_frames = int(total_frames_f)
            except (TypeError, ValueError):
                total_frames = 0

            # Validar fps y frame count
            if not (math.isfinite(fps) and fps > 0) or total_frames <= 0:
                cap.release()
                messagebox.showerror("Error", f"No se pudo obtener información"
                                     f" del video (fps={fps}, frames={total_frames_f})")
                print(f"Error: fps={fps}, total_frames={total_frames_f}")
                return

            duration_seconds = total_frames / fps
            duration_hours = duration_seconds / 3600

            # Calcular número de miniaturas (6 por hora, mínimo 4)
            num_thumbnails = max(4, int(duration_hours * 6))
            # Duplicar la cantidad solicitada (según petición) y capear a 48
            num_thumbnails = min(num_thumbnails * 2, 48)

            # Limpiar vista previa anterior
            self.clear_timeline_preview()

            # Crear contenedor temporal para el progreso (permite usar pack dentro)
            # Mostramos el progreso en toda la anchura prevista (n columnas)
            ncols = 4
            progress_container = tk.Frame(self.preview_inner_frame, bg='#2c3e50')
            progress_container.grid(row=0, column=0, columnspan=ncols, sticky='nsew', pady=20)
            progress_label = tk.Label(progress_container,
                                     text=f"Generando {num_thumbnails} miniaturas...",
                                     bg='#2c3e50', fg='white', font=('Arial', 10))
            # Dentro del contenedor temporal usamos pack para centrar el texto fácilmente
            progress_label.pack(expand=True, pady=10)
            self.root.update()

            # Calcular frames a capturar
            if num_thumbnails <= 0:
                cap.release()
                messagebox.showwarning("Advertencia", "Número de miniaturas calculado es 0")
                return
            frame_interval = max(1, total_frames // (num_thumbnails + 1))

            thumbnails = []
            for i in range(1, num_thumbnails + 1):
                frame_pos = i * frame_interval
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)  # type: ignore
                ret, frame = cap.read()

                if ret and frame is not None:
                    try:
                        # Convertir a RGB
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # type: ignore
                        # Crear imagen PIL
                        img = Image.fromarray(frame_rgb)
                    except (cv2.error, ValueError, TypeError) as e:
                        # Omitir frame problemático (errores de OpenCV o creación de imagen)
                        print(f"Warning: fallo procesando frame {frame_pos}: {e}")
                        continue

                    # Crear imagen con relación 3:2 (centrado) y redimensionar a 150x100
                    try:
                        target_aspect = 3.0 / 2.0
                        width, height = img.size
                        current_aspect = width / height if height else 1

                        if current_aspect > target_aspect:
                            # demasiado ancha -> recortar ancho
                            new_width = int(target_aspect * height)
                            left = (width - new_width) // 2
                            img_cropped = img.crop((left, 0, left + new_width, height))
                        else:
                            # demasiado alta -> recortar alto
                            new_height = int(width / target_aspect)
                            top = (height - new_height) // 2
                            img_cropped = img.crop((0, top, width, top + new_height))

                        img_resized = img_cropped.resize((150, 100), Image.Resampling.LANCZOS)
                    except (ValueError, OSError, AttributeError) as e:
                        # Fallback a un resize directo si el crop/resize falla por errores esperados
                        print(f"Warning: fallback while creating timeline thumb: {e}")
                        img_resized = img.resize((150, 100), Image.Resampling.LANCZOS)

                    # Calcular tiempo de esta miniatura
                    time_seconds = frame_pos / fps
                    time_str = self.format_duration(int(time_seconds))

                    thumbnails.append((img_resized, time_str))

                    # Save the frame positions for potential 'add more' operations
                    try:
                        self.last_timeline_frame_positions = [i * frame_interval for i in range(1, num_thumbnails + 1)]
                    except Exception:
                        self.last_timeline_frame_positions = []

            cap.release()

            # Limpiar contenedor de progreso antes de insertar miniaturas
            try:
                progress_container.destroy()
            except (tk.TclError, AttributeError):
                # Si el widget ya fue destruido o no tiene el método, ignorar
                pass

            if not thumbnails:
                messagebox.showwarning("Advertencia", "No se pudieron generar miniaturas")
                self.clear_timeline_preview()
                return

            # Crear grid de miniaturas (hasta ncols por fila)
            for idx, (img, time_str) in enumerate(thumbnails):
                row = idx // ncols
                col = idx % ncols

                # Frame para cada miniatura
                thumb_frame = tk.Frame(self.preview_inner_frame, bg='#34495e',
                                      relief='raised', borderwidth=2)
                thumb_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')

                # Convertir a PhotoImage
                photo = ImageTk.PhotoImage(img)
                self.timeline_images.append(photo)  # Guardar referencia

                # Label con la imagen
                img_label = tk.Label(thumb_frame, image=photo, bg='#34495e')
                img_label.pack(padx=2, pady=2)

                # Label con el tiempo
                time_label = tk.Label(thumb_frame, text=time_str,
                                     bg='#34495e', fg='white', font=('Arial', 9, 'bold'))
                time_label.pack()

            # Enable the add-four button if the video is long enough
            try:
                if duration_seconds > 15 * 60:
                    self.add_four_btn.config(state='normal')
                else:
                    self.add_four_btn.config(state='disabled')
            except Exception:
                pass

            # Configurar grid para centrar: dar peso a cada columna
            for c in range(ncols):
                self.preview_inner_frame.grid_columnconfigure(c, weight=1)

            messagebox.askokcancel("Éxito",
                                   f"Se generaron {len(thumbnails)} miniaturas del timeline")

        except (OSError, ValueError, tk.TclError) as e:
            messagebox.showerror("Error", f"Error generando timeline: {e}")
            print(f"Error generando timeline: {e}")
            self.clear_timeline_preview()

    def _on_preview_mousewheel(self, event):
        """Handle mouse wheel events to scroll the preview canvas vertically."""
        # For Windows and macOS, event.delta will be a multiple of 120 (positive or negative)
        try:
            if hasattr(event, 'delta') and event.delta:
                # On Windows, event.delta is in units of 120 per notch; scale down
                delta = -1 * (event.delta // 120)
                self.preview_canvas.yview_scroll(delta, 'units')
            else:
                # Linux: Button-4 = scroll up, Button-5 = scroll down
                if event.num == 4:
                    self.preview_canvas.yview_scroll(-3, 'units')
                elif event.num == 5:
                    self.preview_canvas.yview_scroll(3, 'units')
        except (AttributeError, tk.TclError, ValueError) as e:
            # Catch only expected exceptions raised during event handling / canvas operations
            print(f"Error handling mouse wheel event: {e}")


    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        if VLC_AVAILABLE and self.player:
            self.player.stop()
        self.db.close()
        self.root.destroy()

    def add_four_more_thumbnails_if_long(self):
        """Añade 4 miniaturas adicionales si la duración del video es > 15 minutos.
        Las miniaturas se generan y se añaden a la vista previa existente.
        """
        if not self.current_video:
            return

        filepath = self.current_video[1]
        if not os.path.exists(filepath):
            messagebox.showerror("Error", "El archivo de video no existe")
            return

        try:
            cap = cv2.VideoCapture(filepath)  # type: ignore
            if not cap.isOpened():
                messagebox.showerror("Error", "No se pudo abrir el video")
                return

            fps = cap.get(cv2.CAP_PROP_FPS)  # type: ignore
            total_frames_f = cap.get(cv2.CAP_PROP_FRAME_COUNT)  # type: ignore
            try:
                total_frames = int(total_frames_f)
            except Exception:
                total_frames = 0

            if not (math.isfinite(fps) and fps > 0) or total_frames <= 0:
                cap.release()
                messagebox.showerror("Error", "No se pudo obtener información del video")
                return

            duration_seconds = total_frames / fps
            if duration_seconds <= 15 * 60:
                messagebox.askokcancel("Info",
                                       "La duración no supera los 15 minutos"
                                       " (no se añadirán miniaturas)")
                cap.release()
                return

            # Determine candidate frame positions for 4 new thumbs
            existing = getattr(self, 'last_timeline_frame_positions', []) or []

            new_positions = []
            if existing:
                # compute midpoints between existing frames where possible
                pairs = []
                for i in range(len(existing) - 1):
                    a = existing[i]
                    b = existing[i + 1]
                    pairs.append((a + b) // 2)
                # If not enough midpoints, supplement with evenly spaced frames
                for p in pairs:
                    if len(new_positions) >= 4:
                        break
                    if p not in existing and p not in new_positions:
                        new_positions.append(int(p))

            # Fill remaining positions evenly across the video (avoid duplicates)
            i = 1
            while len(new_positions) < 4 and i <= 20:
                candidate = (i * total_frames) // 20
                if candidate > 0 and candidate not in existing and candidate not in new_positions:
                    new_positions.append(int(candidate))
                i += 1

            # Limit to 4
            new_positions = new_positions[:4]

            if not new_positions:
                messagebox.askokcancel("Info",
                                       "No se encontraron posiciones nuevas"
                                       " para generar miniaturas")
                cap.release()
                return

            # Build a mapping of frame_pos -> PhotoImage/time for both existing and new thumbnails
            ncols = 4

            existing = getattr(self, 'last_timeline_frame_positions', []) or []
            existing_photos = list(self.timeline_images)

            # Try to map existing positions to existing PhotoImage objects only if lengths match
            pos_to_photo = {}
            try:
                if len(existing) == len(existing_photos) and len(existing) > 0:
                    for p, ph in zip(existing, existing_photos):
                        pos_to_photo[int(p)] = ph
                else:
                    # If mismatch, rebuild mapping conservatively by ignoring existing photos
                    pos_to_photo = {}
            except Exception:
                pos_to_photo = {}

            # Generate photos for the new positions and add to mapping
            generated_photos = {}
            for frame_pos in new_positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)  # type: ignore
                ret, frame = cap.read()
                if not (ret and frame is not None):
                    continue
                try:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # type: ignore
                    img = Image.fromarray(frame_rgb)
                except Exception:
                    continue

                # Crop to 3:2 and resize to 150x100
                try:
                    target_aspect = 3.0 / 2.0
                    width, height = img.size
                    current_aspect = width / height if height else 1
                    if current_aspect > target_aspect:
                        new_width = int(target_aspect * height)
                        left = (width - new_width) // 2
                        img_cropped = img.crop((left, 0, left + new_width, height))
                    else:
                        new_height = int(width / target_aspect)
                        top = (height - new_height) // 2
                        img_cropped = img.crop((0, top, width, top + new_height))
                    img_resized = img_cropped.resize((150, 100), Image.Resampling.LANCZOS)
                except Exception:
                    img_resized = img.resize((150, 100), Image.Resampling.LANCZOS)

                photo = ImageTk.PhotoImage(img_resized)
                generated_photos[int(frame_pos)] = photo

            cap.release()

            # Merge existing positions and new positions, deduplicate and sort chronologically
            try:
                merged_positions = sorted(set([
                    int(p) for p in existing] + [int(p) for p in new_positions]))
            except Exception:
                merged_positions = sorted(list(set(existing + new_positions)))

            if not merged_positions:
                messagebox.askokcancel("Info", "No se añadieron miniaturas nuevas")
                return

            # Clear the preview area and rebuild thumbnails in chronological order
            for widget in self.preview_inner_frame.winfo_children():
                widget.destroy()

            self.timeline_images = []

            for idx, frame_pos in enumerate(merged_positions):
                row = idx // ncols
                col = idx % ncols

                thumb_frame = tk.Frame(self.preview_inner_frame, bg='#34495e',
                                       relief='raised', borderwidth=2)
                thumb_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')

                # Prefer existing photo mapping; else use generated photo; else skip
                photo = pos_to_photo.get(int(frame_pos)) or generated_photos.get(int(frame_pos))
                if not photo:
                    # As fallback, attempt to re-extract the frame now (best-effort)
                    try:
                        cap2 = cv2.VideoCapture(filepath)  # type: ignore
                        cap2.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)  # type: ignore
                        ret2, frame2 = cap2.read()
                        cap2.release()
                        if ret2 and frame2 is not None:
                            frame_rgb2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)  # type: ignore
                            img2 = Image.fromarray(frame_rgb2)
                            # Crop/resize
                            t_aspect = 3.0 / 2.0
                            w2, h2 = img2.size
                            if (w2 / h2 if h2 else 1) > t_aspect:
                                new_w2 = int(t_aspect * h2)
                                left2 = (w2 - new_w2) // 2
                                img_cropped2 = img2.crop((left2, 0, left2 + new_w2, h2))
                            else:
                                new_h2 = int(w2 / t_aspect)
                                top2 = (h2 - new_h2) // 2
                                img_cropped2 = img2.crop((0, top2, w2, top2 + new_h2))
                            img_resized2 = img_cropped2.resize((150, 100), Image.Resampling.LANCZOS)
                            photo = ImageTk.PhotoImage(img_resized2)
                        else:
                            continue
                    except Exception:
                        continue

                self.timeline_images.append(photo)

                img_label = tk.Label(thumb_frame, image=photo, bg='#34495e')
                img_label.pack(padx=2, pady=2)

                # Compute and show time label
                try:
                    time_seconds = frame_pos / fps
                    time_str = self.format_duration(int(time_seconds))
                except Exception:
                    time_str = "00:00"

                time_label = tk.Label(thumb_frame, text=time_str, bg='#34495e', fg='white', font=('Arial', 9, 'bold'))
                time_label.pack()

            # Update stored frame positions
            try:
                self.last_timeline_frame_positions = merged_positions
            except Exception:
                self.last_timeline_frame_positions = merged_positions

            # Ensure grid columns have weight
            for c in range(ncols):
                try:
                    self.preview_inner_frame.grid_columnconfigure(c, weight=1)
                except Exception:
                    pass

            messagebox.askokcancel("Éxito", f"Se añadieron {len(new_positions)} miniaturas")

        except Exception as e:
            messagebox.showerror("Error", f"Error generando miniaturas adicionales: {e}")
            cap.release()

    def show_about(self):
        """Muestra un diálogo About con la versión de la aplicación."""
        try:
            version = get_version()
            messagebox.showinfo("About",
                                f"Gestor de Videos\nVersion: {version}\n\nDesarrollado con Python/Tkinter")
        except Exception:
            messagebox.showinfo("About", "Gestor de Videos\nVersion: unknown")


def main():
    """Función principal"""
    root = tk.Tk()
    app = VideoManagerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()
