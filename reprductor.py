""" Gestor de videos - Organizar, clasificar y reproducir videos """

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk
import cv2
import io

try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False

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
        
        self.conn.commit()
    
    def add_video(self, filepath, category='Sin categoría', tags=''):
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
        """Obtiene todas las categorías"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM videos WHERE category IS NOT NULL')
        return [row[0] for row in cursor.fetchall()]
    
    def update_video(self, video_id, **kwargs):
        """Actualiza campos de un video"""
        cursor = self.conn.cursor()
        
        set_clause = ', '.join([f'{key} = ?' for key in kwargs.keys()])
        values = list(kwargs.values()) + [video_id]
        
        cursor.execute(f'UPDATE videos SET {set_clause} WHERE id = ?', values)
        self.conn.commit()
    
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
        self.root.title("Gestor de Videos")
        self.root.geometry("1200x700")
        
        # Base de datos
        self.db = VideoDatabase()
        
        # Directorio para miniaturas
        self.thumbnail_dir = Path('thumbnails')
        self.thumbnail_dir.mkdir(exist_ok=True)
        
        # Reproductor VLC
        if VLC_AVAILABLE:
            self.instance = vlc.Instance()
            self.player = self.instance.media_player_new()
        else:
            self.player = None
            messagebox.showwarning("VLC no disponible", 
                                 "python-vlc no está instalado. La reproducción no estará disponible.")
        
        self.current_video = None
        self.current_thumbnail = None
        
        # Construir UI
        self.build_ui()
        
        # Cargar videos
        self.refresh_video_list()
    
    def build_ui(self):
        """Construye la interfaz de usuario"""
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
        ttk.Button(toolbar, text="🖼️ Generar Miniaturas", 
                  command=self.regenerate_all_thumbnails).pack(side='left', padx=2)
        
        # Búsqueda
        search_frame = ttk.Frame(library_frame)
        search_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        ttk.Label(search_frame, text="Buscar:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.refresh_video_list())
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side='left', fill='x', expand=True, padx=5)
        
        # Filtro por categoría
        filter_frame = ttk.Frame(library_frame)
        filter_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Categoría:").pack(side='left')
        self.category_var = tk.StringVar(value='Todos')
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, state='readonly')
        self.category_combo.pack(side='left', fill='x', expand=True, padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_video_list())
        
        # Lista de videos (Treeview)
        list_frame = ttk.Frame(library_frame)
        list_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview
        self.video_tree = ttk.Treeview(list_frame, columns=('filename', 'category', 'rating'),
                                       show='tree headings', yscrollcommand=scrollbar.set)
        self.video_tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.video_tree.yview)

        # Columnas
        self.video_tree.heading('#0', text='ID')
        self.video_tree.heading('filename', text='Nombre')
        self.video_tree.heading('category', text='Categoría')
        self.video_tree.heading('rating', text='⭐')
        
        self.video_tree.column('#0', width=50)
        self.video_tree.column('filename', width=200)
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
        
        # Frame para preview/thumbnail (cuadrado, en la parte inferior del panel de biblioteca)
        preview_frame = ttk.LabelFrame(library_frame, text="Vista Previa")
        preview_frame.pack(side='bottom', fill='x', padx=5, pady=5)
        
        # Contenedor con tamaño fijo para mantener formato cuadrado
        preview_container = tk.Frame(preview_frame, width=300, height=300, bg='#2c3e50')
        preview_container.pack(padx=10, pady=10)
        preview_container.pack_propagate(False)  # Evitar que el contenedor cambie de tamaño
        
        self.preview_label = tk.Label(preview_container, text="Selecciona un video\npara ver la vista previa", 
                                     bg='#2c3e50', fg='white', font=('Arial', 10))
        self.preview_label.place(relx=0.5, rely=0.5, anchor='center', relwidth=1, relheight=1)
    
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
        
        ttk.Button(controls_frame, text="⏹ Stop", command=self.stop_video).pack(side='left', padx=2)
        
        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_scale = ttk.Scale(controls_frame, from_=0, to=100, 
                                       variable=self.progress_var, orient='horizontal')
        self.progress_scale.pack(side='left', fill='x', expand=True, padx=10)
        self.progress_scale.bind('<Button-1>', self.on_progress_click)
        
        # Volumen
        ttk.Label(controls_frame, text="🔊").pack(side='left')
        self.volume_var = tk.IntVar(value=50)
        volume_scale = ttk.Scale(controls_frame, from_=0, to=100, 
                                variable=self.volume_var, orient='horizontal', 
                                command=self.set_volume, length=100)
        volume_scale.pack(side='left', padx=2)
        
        # Panel de detalles
        details_frame = ttk.LabelFrame(player_frame, text="Detalles del Video")
        details_frame.pack(side='top', fill='both', padx=5, pady=5)
        
        # Grid para detalles
        ttk.Label(details_frame, text="Nombre:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.name_label = ttk.Label(details_frame, text="-")
        self.name_label.grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(details_frame, text="Categoría:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.detail_category_var = tk.StringVar()
        self.detail_category_combo = ttk.Combobox(details_frame, textvariable=self.detail_category_var)
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
                # Generar miniatura
                self.generate_thumbnail(filepath, video_id)
                messagebox.showinfo("Éxito", f"Video añadido: {os.path.basename(filepath)}")
                self.refresh_video_list()
            else:
                messagebox.showwarning("Advertencia", "Este video ya está en la biblioteca")
    
    def add_folder(self):
        """Añade todos los videos de una carpeta"""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de videos")
        
        if folder:
            video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
            added_count = 0
            
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if Path(file).suffix.lower() in video_extensions:
                        filepath = os.path.join(root, file)
                        video_id = self.db.add_video(filepath)
                        if video_id:
                            self.generate_thumbnail(filepath, video_id)
                            added_count += 1
            
            messagebox.showinfo("Éxito", f"Se añadieron {added_count} videos")
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
            video_id, filepath, filename, category, tags, rating, *_ = video
            self.video_tree.insert('', 'end', iid=str(video_id),
                                  text=str(video_id),
                                  values=(filename, category or 'Sin categoría', '⭐' * rating))
    
    def on_video_select(self, event):
        """Maneja la selección de un video"""
        selection = self.video_tree.selection()
        if not selection:
            return
        
        video_id = int(selection[0])
        videos = self.db.get_all_videos()
        
        for video in videos:
            if video[0] == video_id:
                self.current_video = video
                self.load_video_details(video)
                break
    
    def load_video_details(self, video):
        """Carga los detalles de un video en el panel de detalles"""
        # Manejar tanto videos con 11 campos (viejos) como 12 campos (nuevos)
        if len(video) == 11:
            video_id, filepath, filename, category, tags, rating, duration, added_date, last_played, play_count, notes = video
            thumbnail_path = None
        else:
            video_id, filepath, filename, category, tags, rating, duration, added_date, last_played, play_count, notes, thumbnail_path = video
        
        self.name_label.config(text=filename)
        self.detail_category_var.set(category or 'Sin categoría')
        self.tags_entry.delete(0, 'end')
        self.tags_entry.insert(0, tags or '')
        self.rating_var.set(rating or 0)
        self.notes_text.delete('1.0', 'end')
        self.notes_text.insert('1.0', notes or '')
        
        # Cargar y mostrar miniatura
        self.load_thumbnail(video_id, thumbnail_path, filepath)
    
    def on_video_double_click(self, event):
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
        
        # Actualizar progreso
        self.update_progress()
    
    def play_pause(self):
        """Alterna entre play y pause"""
        if not VLC_AVAILABLE or not self.player:
            return
        
        if self.player.is_playing():
            self.player.pause()
            self.play_btn.config(text="▶ Play")
        else:
            if self.current_video:
                self.play_selected_video()
    
    def stop_video(self):
        """Detiene la reproducción"""
        if VLC_AVAILABLE and self.player:
            self.player.stop()
            self.play_btn.config(text="▶ Play")
    
    def set_volume(self, value):
        """Establece el volumen"""
        if VLC_AVAILABLE and self.player:
            self.player.audio_set_volume(int(float(value)))
    
    def on_progress_click(self, event):
        """Maneja el clic en la barra de progreso"""
        if not VLC_AVAILABLE or not self.player or not self.player.is_playing():
            return
        
        # Calcular posición
        length = self.player.get_length()
        if length > 0:
            position = self.progress_var.get() / 100.0
            self.player.set_position(position)
    
    def update_progress(self):
        """Actualiza la barra de progreso"""
        if VLC_AVAILABLE and self.player and self.player.is_playing():
            position = self.player.get_position()
            self.progress_var.set(position * 100)
            self.root.after(500, self.update_progress)
    
    def update_current_video_category(self, event=None):
        """Actualiza la categoría del video actual"""
        if self.current_video:
            video_id = self.current_video[0]
            category = self.detail_category_var.get()
            self.db.update_video(video_id, category=category)
            self.refresh_video_list()
    
    def update_current_video_tags(self, event=None):
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
    
    def update_current_video_notes(self, event=None):
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
        
        video_id, filepath, filename, *_ = self.current_video
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{filename}' de la biblioteca?\n(El archivo no se borrará del disco)"):
            self.db.delete_video(video_id)
            self.current_video = None
            self.refresh_video_list()
            messagebox.showinfo("Éxito", "Video eliminado de la biblioteca")
    
    def show_context_menu(self, event):
        """Muestra el menú contextual"""
        item = self.video_tree.identify_row(event.y)
        if item:
            self.video_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def generate_thumbnail(self, video_path, video_id):
        """Genera una miniatura del video"""
        try:
            # Abrir video con OpenCV
            cap = cv2.VideoCapture(video_path)
            
            # Obtener el frame del medio del video
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames > 0:
                middle_frame = total_frames // 2
                cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Convertir BGR a RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Crear imagen PIL
                img = Image.fromarray(frame_rgb)
                
                # Redimensionar manteniendo aspecto
                img.thumbnail((320, 180), Image.Resampling.LANCZOS)
                
                # Guardar miniatura
                thumbnail_path = self.thumbnail_dir / f"thumb_{video_id}.jpg"
                img.save(thumbnail_path, "JPEG", quality=85)
                
                # Actualizar base de datos
                self.db.update_video(video_id, thumbnail_path=str(thumbnail_path))
                
                return str(thumbnail_path)
        except Exception as e:
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
                
                # Crear imagen cuadrada (300x300) con crop centrado
                width, height = img.size
                
                # Determinar el tamaño del cuadrado (el menor lado)
                square_size = min(width, height)
                
                # Calcular coordenadas para crop centrado
                left = (width - square_size) // 2
                top = (height - square_size) // 2
                right = left + square_size
                bottom = top + square_size
                
                # Hacer crop cuadrado
                img_square = img.crop((left, top, right, bottom))
                
                # Redimensionar a 300x300
                img_square = img_square.resize((300, 300), Image.Resampling.LANCZOS)
                
                # Convertir a PhotoImage
                photo = ImageTk.PhotoImage(img_square)
                
                # Mostrar en label
                self.preview_label.config(image=photo, text="")
                self.preview_label.image = photo  # Mantener referencia
                self.current_thumbnail = photo
            else:
                # Mostrar placeholder
                self.preview_label.config(image="", text="Vista previa\nno disponible", 
                                        bg='#2c3e50', fg='white')
                self.current_thumbnail = None
        except Exception as e:
            print(f"Error cargando miniatura: {e}")
            self.preview_label.config(image="", text="Error cargando\nvista previa", 
                                    bg='#2c3e50', fg='white')
            self.current_thumbnail = None
    
    def regenerate_all_thumbnails(self):
        """Regenera todas las miniaturas de los videos en la biblioteca"""
        if not messagebox.askyesno("Confirmar", 
                                   "¿Generar miniaturas para todos los videos?\nEsto puede tomar unos minutos."):
            return
        
        videos = self.db.get_all_videos()
        total = len(videos)
        generated = 0
        
        for video in videos:
            video_id = video[0]
            filepath = video[1]
            
            if os.path.exists(filepath):
                if self.generate_thumbnail(filepath, video_id):
                    generated += 1
        
        messagebox.showinfo("Completado", 
                           f"Se generaron {generated} miniaturas de {total} videos")
        self.refresh_video_list()
        
        # Recargar la miniatura del video actual si hay uno seleccionado
        if self.current_video:
            self.load_video_details(self.current_video)
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        if VLC_AVAILABLE and self.player:
            self.player.stop()
        self.db.close()
        self.root.destroy()


def main():
    """Función principal"""
    root = tk.Tk()
    app = VideoManagerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()

