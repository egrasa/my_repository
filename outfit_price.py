""" Simple GUI to calculate outfit price based on CSV files. """

import os
import csv
import random
import math
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
import difflib
from collections import Counter
from matplotlib.patches import Patch
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('TkAgg')
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Constants
DEFAULT_TOP_ITEMS = [
    ('bra', 50, 'basic', 0),
    ('bodysuit', 50, 'basic', 2),
    ('regular dress', 50, 'basic', 2),
    ('transparent dress', 100, 'normal', 2),
    ('belt bra', 150, 'special', 0),
    ('transparent top', 100, 'normal', 0),
    ('transparent robe', 100, 'normal', 2),
    ('paper bra', 150, 'special', 0),
    ('band aid bra', 150, 'special', 0),
    ('painting bra', 200, 'extreme', 0),
    ('foam bra', 200, 'extreme', 0),
    ('glitter bra', 300, 'extreme', 0),
    ('naked top', 500, 'naked', 0),
]
DEFAULT_BOTTOM_ITEMS = [
    ('panties', 50, 'basic', 1),
    ('bodysuit', 50, 'basic', 2),
    ('regular dress', 50, 'basic', 2),
    ('regular skirt/shorts', 50, 'basic', 1),
    ('transparent dress', 100, 'normal', 2),
    ('pantyhose', 200, 'normal', 1),
    ('transparent robe', 200, 'normal', 2),
    ('paper panties', 200, 'normal', 1),
    ('belt skirt', 300, 'special', 1),
    ('band aid panties', 400, 'extreme', 1),
    ('foam panties', 400, 'extreme', 1),
    ('painting panties', 400, 'extreme', 1),
    ('glitter panties', 600, 'extreme', 1),
    ('naked', 1000, 'naked', 1),
]
CSV_COLUMNS = ['nombre', 'precio', 'categoria', 'tipo']
WINDOW_WIDTH = 620
WINDOW_HEIGHT = 560
FONT_LABEL = ('Segoe UI', 10)
FONT_INFO = ('Segoe UI', 12, 'bold')
FONT_TOTAL = ('Segoe UI', 50, 'bold')
FONT_NAME = ('Segoe UI', 14, 'bold')
FONT_DUP = ('Segoe UI', 10)
COLOR_TOTAL_LOW = '#2E7D32'  # green
COLOR_TOTAL_MID = '#F57C00'  # orange
COLOR_TOTAL_HIGH = '#C62828'  # red
COLOR_DUP_TEXT = '#555555'
THRESH_MID = 200
THRESH_HIGH = 400

# Temas: claro (light) y oscuro (dark)
THEMES = {
    'light': {
        'bg': "#e0d8d6",
        'frame': '#f8f8f8',
        'frame_elevated': '#ffffff',
        'shadow': '#e8e8e8',
        'text': '#000000',
        'text_secondary': '#666666',
        'label': '#333333',
        'button': '#007acc',
        'button_text': '#ffffff',
        'button_hover': '#005a9e',
        'separator': '#e0e0e0',
        'accent': '#007acc',
        'border': '#d0d0d0',
    },
    'dark': {
        'bg': "#3D4246",
        'frame': '#252526',
        'frame_elevated': '#2d2d30',
        'shadow': '#1a1a1a',
        'text': "#c2d7f1",
        'text_secondary': "#b6d0d4",
        'label': "#919dc5",
        'button': '#0e639c',
        'button_text': "#531b9c",
        'button_hover': '#1177bb',
        'separator': '#3e3e42',
        'accent': '#007acc',
        'border': '#3e3e42',
    }
}


def load_items(csv_path):
    """ Load items from a CSV file and return a list of dictionaries. """
    items = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Clean column names (remove leading/trailing spaces)
            if reader.fieldnames:
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
            for row in reader:
                # Normalize row keys to handle spaces in column names
                row = {k.strip(): v for k, v in row.items()}
                # parse precio (price) and tipo fields
                try:
                    price = float(row.get('precio', 0))
                except ValueError:
                    price = 0.0
                # tipo column: 0=top only, 1=bottom only, 2=both
                tipo_raw = row.get('tipo', '').strip()
                try:
                    tipo_val = int(tipo_raw) if tipo_raw else 0
                except ValueError:
                    tipo_val = 0
                items.append({'nombre': row.get('nombre', ''),
                              'precio': price,
                              'categoria': row.get('categoria', ''),
                              'tipo': tipo_val})
    except FileNotFoundError:
        pass
    return items


def make_csv_if_missing(path, rows):
    """ Create a CSV file with the given rows if it doesn't already exist. """
    if os.path.exists(path):
        return

    is_top = 'top' in os.path.basename(path).lower()
    default_tipo = 0 if is_top else 1

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        for r in rows:
            if len(r) == 3:
                writer.writerow([r[0], r[1], r[2], default_tipo])
            else:
                writer.writerow(r)


def apply_theme_to_widgets(parent, theme_colors):
    """Aplica recursivamente los colores del tema a todos los widgets."""
    for widget in parent.winfo_children():
        if isinstance(widget, tk.Label):
            fg = theme_colors.get('text', theme_colors['label'])
            bg = theme_colors['bg']
            widget.config(bg=bg, fg=fg)
        elif isinstance(widget, (tk.Frame, tk.LabelFrame)):
            # Para LabelFrames, aplicar colores al marco y al texto
            if isinstance(widget, tk.LabelFrame):
                widget.config(bg=theme_colors['bg'], fg=theme_colors['label'],
                             borderwidth=2, relief=tk.FLAT)
            else:
                widget.config(bg=theme_colors['bg'])
            apply_theme_to_widgets(widget, theme_colors)
        elif isinstance(widget, ttk.Combobox):
            pass  # ttk widgets tienen su propio sistema de temas
        elif isinstance(widget, tk.Button):
            widget.config(bg=theme_colors['button'], fg=theme_colors['button_text'],
                         activebackground=theme_colors.get('button_hover', theme_colors['button']),
                         activeforeground=theme_colors['button_text'])
        elif isinstance(widget, tk.Checkbutton):
            widget.config(bg=theme_colors['bg'], fg=theme_colors['text'],
                         activebackground=theme_colors['bg'],
                         activeforeground=theme_colors['text'],
                         selectcolor=theme_colors['bg'])

def fuzzy_search(query: str, items: list, key: str = 'nombre') -> list:
    """Realizar búsqueda fuzzy sobre una lista de items."""
    if not query:
        return items

    names = [item[key] for item in items]
    matches = difflib.get_close_matches(query, names, n=len(names), cutoff=0.3)

    # Retornar items que coinciden, manteniendo el orden por relevancia
    result = []
    for match in matches:
        for item in items:
            if item[key] == match and item not in result:
                result.append(item)
    return result


def filter_items_by_permissions(items: list) -> list:
    """Filter out items based on current permissions."""
    if PERMISSIONS.get('naked_options', False) == False:
        # If naked_options is DISABLED, filter out items with 'naked' category
        return [item for item in items if item.get('categoria', '').lower() != 'naked']
    return items


def calculate_statistics(all_items: list, ratings: dict = None) -> dict:
    """Calcular estadísticas de los items y calificaciones."""
    if not all_items:
        return {}

    prices = [item['precio'] for item in all_items]
    categories = [item['categoria'] for item in all_items]
    tipos = [item['tipo'] for item in all_items]

    # Contar calificaciones
    rating_counts = {'favorite': 0, 'normal': 0, 'rare': 0, 'incompatible': 0}
    if ratings:
        for rating in ratings.values():
            if rating in rating_counts:
                rating_counts[rating] += 1

    stats = {
        'total_items': len(all_items),
        'avg_price': sum(prices) / len(prices),
        'min_price': min(prices),
        'max_price': max(prices),
        'median_price': sorted(prices)[len(prices)//2],
        'categories': dict(Counter(categories)),
        'tipos': dict(Counter(tipos)),
        'rating_counts': rating_counts,
        'total_rated': sum(rating_counts.values()),
    }

    return stats

def show_statistics_window(root, all_items: list, ratings: dict = None):
    """Mostrar ventana con estadísticas."""
    stats = calculate_statistics(all_items, ratings)

    if not stats:
        messagebox.showinfo("Estadísticas", "No hay items para analizar.")
        return

    stat_window = tk.Toplevel(root)
    stat_window.title("Estadísticas")
    stat_window.geometry("450x500")

    text_widget = tk.Text(stat_window, wrap=tk.WORD, font=('Courier', 10))
    text_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    stats_text = f"""
ESTADÍSTICAS GENERALES
═════════════════════════════════════

Total de Items: {stats['total_items']}

PRECIOS:
  Precio Promedio: ${stats['avg_price']:.2f}
  Precio Mínimo:   ${stats['min_price']:.2f}
  Precio Máximo:   ${stats['max_price']:.2f}
  Precio Mediano:  ${stats['median_price']:.2f}

DISTRIBUCIÓN POR CATEGORÍA:
"""

    for cat, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
        stats_text += f"  {cat.upper()}: {count} items\n"

    stats_text += "\nDISTRIBUCIÓN POR TIPO:\n"
    type_names = {0: "Solo Top", 1: "Solo Bottom", 2: "Ambos"}
    for tipo, count in sorted(stats['tipos'].items()):
        stats_text += f"  {type_names.get(tipo, 'Desconocido')}: {count} items\n"

    stats_text += "\nCALIFICACIONES DE COMBINACIONES\n═════════════════════════════════════\n"
    stats_text += f"Total Combinaciones Calificadas: {stats['total_rated']}\n\n"
    stats_text += f"  ⭐ Favoritos:      {stats['rating_counts']['favorite']}\n"
    stats_text += f"  ✓ Normal:         {stats['rating_counts']['normal']}\n"
    stats_text += f"  ◆ Raro:           {stats['rating_counts']['rare']}\n"
    stats_text += f"  ✗ Incompatible:   {stats['rating_counts']['incompatible']}\n"

    text_widget.insert("1.0", stats_text)
    text_widget.config(state=tk.DISABLED)

# Rating system for combinations
RATING_LABELS = {
    'favorite': ('⭐ Favorito', '#4A9EFF'),
    'normal': ('✓ Normal', '#4CAF50'),
    'rare': ('◆ Raro', '#FF9800'),
    'incompatible': ('✗ Incompatible', '#f44336'),
    'unrated': ('', '#cccccc')
}

# Variables globales para permisos (desactivados por defecto)
PERMISSIONS = {
    'naked_options': False,
    'statistics': False,
    'graphics': False,
    'califications': False
}

def get_ratings_file():
    """Obtener ruta del archivo de ratings."""
    # Cuando se ejecuta como .exe desde PyInstaller, usar sys._MEIPASS
    # En desarrollo, usar el directorio del script actual
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(__file__)
    return os.path.join(base, 'combination_ratings.json')

def load_ratings(_permitted: bool = True):
    """Cargar calificaciones de combinaciones desde archivo."""
    # Las calificaciones ya realizadas siempre se cargan, sin importar el permiso
    ratings_file = get_ratings_file()
    if os.path.exists(ratings_file):
        try:
            with open(ratings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_ratings(ratings: dict, permitted: bool = True):
    """Guardar calificaciones a archivo JSON."""
    # Usar permiso global si está permitido
    if permitted:
        permitted = PERMISSIONS.get('califications', False)

    if not permitted:
        return False

    ratings_file = get_ratings_file()
    try:
        with open(ratings_file, 'w', encoding='utf-8') as f:
            json.dump(ratings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error guardando ratings: {e}")
        return False

def get_combination_key(top_name: str, bottom_name: str) -> str:
    """Generar clave única para una combinación."""
    return f"{top_name}|{bottom_name}"

def get_combination_rating(ratings: dict, top_name: str, bottom_name: str) -> str:
    """Obtener la calificación de una combinación."""
    key = get_combination_key(top_name, bottom_name)
    return ratings.get(key, 'unrated')

def set_combination_rating(ratings: dict, top_name: str, bottom_name: str, rating: str):
    """Establecer la calificación de una combinación."""
    key = get_combination_key(top_name, bottom_name)
    if rating == 'unrated':
        if key in ratings:
            del ratings[key]
    else:
        ratings[key] = rating
    save_ratings(ratings)

def show_rating_statistics_window(root, ratings: dict, _tops: list, _bottoms: list):
    """Mostrar estadísticas específicas sobre items con más calificaciones en columnas."""
    if not ratings:
        messagebox.showinfo("Estadísticas de Calificaciones",
                            "No hay combinaciones calificadas aún.")
        return

    # Crear diccionarios de conteo por tipo de calificación
    rating_stats = {
        'favorite': {'tops': Counter(), 'bottoms': Counter()},
        'normal': {'tops': Counter(), 'bottoms': Counter()},
        'rare': {'tops': Counter(), 'bottoms': Counter()},
        'incompatible': {'tops': Counter(), 'bottoms': Counter()}
    }

    # Procesar todas las combinaciones calificadas
    for combo_key, rating in ratings.items():
        if '|' in combo_key and rating in rating_stats:
            top_name, bottom_name = combo_key.split('|', 1)
            rating_stats[rating]['tops'][top_name] += 1
            rating_stats[rating]['bottoms'][bottom_name] += 1

    # Crear ventana
    stat_window = tk.Toplevel(root)
    stat_window.title("Estadísticas de Calificaciones por Item")
    stat_window.geometry("1200x650")

    # Frame principal
    main_frame = tk.Frame(stat_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    rating_info = [
        ('favorite', '⭐\nFavoritos', '#4A9EFF'),
        ('normal', '✓\nNormal', '#4CAF50'),
        ('rare', '◆\nRaro', '#FF9800'),
        ('incompatible', '✗\nIncompatible', '#f44336')
    ]

    # Función para manejar scroll del ratón
    def _on_mousewheel(event, canvas):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # Crear 4 columnas
    for rating_key, rating_label, color in rating_info:
        # Frame columna (con scroll vertical individual)
        col_frame = tk.Frame(main_frame, bg='white')
        col_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Encabezado de columna
        header_frame = tk.Frame(col_frame, bg=color, height=60)
        header_frame.pack(fill=tk.X, padx=2, pady=(0, 5))
        header_frame.pack_propagate(False)

        header_label = tk.Label(header_frame, text=rating_label,
                               font=('Segoe UI', 10, 'bold'),
                               fg='white', bg=color, justify=tk.CENTER)
        header_label.pack(fill=tk.BOTH, expand=True)

        # Frame scrollable dentro de cada columna
        col_canvas = tk.Canvas(col_frame, bg='white', highlightthickness=0, width=200)
        col_scrollbar = ttk.Scrollbar(col_frame, orient="vertical", command=col_canvas.yview)
        col_content = tk.Frame(col_canvas, bg='white')

        col_content.bind(
            "<Configure>",
            lambda e, c=col_canvas: c.configure(scrollregion=c.bbox("all"))
        )

        col_canvas.create_window((0, 0), window=col_content, anchor="nw")
        col_canvas.configure(yscrollcommand=col_scrollbar.set)

        # Binding para scroll del ratón en la columna
        col_canvas.bind("<MouseWheel>", lambda e, c=col_canvas: _on_mousewheel(e, c))
        col_content.bind("<MouseWheel>", lambda e, c=col_canvas: _on_mousewheel(e, c))

        # Extraer datos
        tops_data = rating_stats[rating_key]['tops']
        bottoms_data = rating_stats[rating_key]['bottoms']

        # Título TOPS
        if tops_data:
            tops_title = tk.Label(col_content, text="📍 Tops",
                                 font=('Segoe UI', 9, 'bold'),
                                 bg='white', fg=color, justify=tk.LEFT)
            tops_title.pack(anchor=tk.W, padx=5, pady=(5, 3))

            tops_sorted = sorted(tops_data.items(), key=lambda x: x[1], reverse=True)
            for top_name, count in tops_sorted:
                top_text = f"{top_name}\n({count}x)"
                top_item = tk.Label(col_content, text=top_text,
                                   font=('Segoe UI', 8),
                                   bg='#f5f5f5', fg='#333333',
                                   justify=tk.CENTER, padx=4, pady=4)
                top_item.pack(fill=tk.X, padx=3, pady=2)
                # Binding mousewheel para labels dentro del canvas
                top_item.bind("<MouseWheel>", lambda e, c=col_canvas: _on_mousewheel(e, c))

        # Separador
        if tops_data and bottoms_data:
            sep = tk.Frame(col_content, bg='#cccccc', height=1)
            sep.pack(fill=tk.X, padx=3, pady=5)

        # Título BOTTOMS
        if bottoms_data:
            bottoms_title = tk.Label(col_content, text="📍 Bottoms",
                                    font=('Segoe UI', 9, 'bold'),
                                    bg='white', fg=color, justify=tk.LEFT)
            bottoms_title.pack(anchor=tk.W, padx=5, pady=(5, 3))
            bottoms_title.bind("<MouseWheel>", lambda e, c=col_canvas: _on_mousewheel(e, c))

            bottoms_sorted = sorted(bottoms_data.items(), key=lambda x: x[1], reverse=True)
            for bottom_name, count in bottoms_sorted:
                bottom_text = f"{bottom_name}\n({count}x)"
                bottom_item = tk.Label(col_content, text=bottom_text,
                                      font=('Segoe UI', 8),
                                      bg='#f5f5f5', fg='#333333',
                                      justify=tk.CENTER, padx=4, pady=4)
                bottom_item.pack(fill=tk.X, padx=3, pady=2)
                # Binding mousewheel para labels dentro del canvas
                bottom_item.bind("<MouseWheel>", lambda e, c=col_canvas: _on_mousewheel(e, c))

        # Si sin datos
        if not tops_data and not bottoms_data:
            no_data = tk.Label(col_content, text="Sin datos",
                              font=('Segoe UI', 9),
                              bg='white', fg='#999999')
            no_data.pack(pady=20)
            no_data.bind("<MouseWheel>", lambda e, c=col_canvas: _on_mousewheel(e, c))

        # Empacar canvas y scrollbar de columna
        col_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        col_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def show_graphics_window(_root, all_items: list, ratings: dict = None):
    """Mostrar gráficos incluyendo distribución de calificaciones."""
    if not HAS_MATPLOTLIB:
        messagebox.showerror("Error", "matplotlib no está instalado.")
        return

    if not all_items:
        messagebox.showinfo("Gráficos", "No hay items para graficar.")
        return

    prices = [item['precio'] for item in all_items]
    categories = [item['categoria'] for item in all_items]

    # Contar calificaciones
    rating_counts = {'favorite': 0, 'normal': 0, 'rare': 0, 'incompatible': 0}
    if ratings:
        for rating in ratings.values():
            if rating in rating_counts:
                rating_counts[rating] += 1

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle('Outfit Price - Análisis Visual', fontsize=16, fontweight='bold')

    # Histograma de precios
    ax1.hist(prices, bins=15, color='#2E7D32', edgecolor='black', alpha=0.7)
    ax1.set_xlabel('Precio ($)')
    ax1.set_ylabel('Cantidad de Items')
    ax1.set_title('Distribución de Precios')
    ax1.grid(axis='y', alpha=0.3)

    # Pie chart de categorías
    cat_counts = Counter(categories)
    cmap = plt.get_cmap("Set3")
    colors = [cmap(i) for i in range(len(cat_counts))]
    ax2.pie(cat_counts.values(), labels=cat_counts.keys(), autopct='%1.1f%%',
            colors=colors, startangle=90)
    ax2.set_title('Proporción por Categoría')

    # Box plot de precios por categoría
    items_by_cat = {}
    for item in all_items:
        cat = item['categoria']
        if cat not in items_by_cat:
            items_by_cat[cat] = []
        items_by_cat[cat].append(item['precio'])

    ax3.boxplot(items_by_cat.values(), tick_labels=items_by_cat.keys())
    ax3.set_ylabel('Precio ($)')
    ax3.set_title('Rango de Precios por Categoría')
    ax3.grid(axis='y', alpha=0.3)

    # Pie chart de calificaciones
    if ratings and any(rating_counts.values()):
        rating_labels = ['Favoritos', 'Normal', 'Raro', 'Incompatible']
        rating_values = [rating_counts['favorite'], rating_counts['normal'],
                        rating_counts['rare'], rating_counts['incompatible']]
        rating_colors = ['#4A9EFF', '#4CAF50', '#FF9800', '#f44336']

        # Filtrar etiquetas y valores vacíos
        non_zero = [(label, val, color) for label, val, color in zip(rating_labels,
                                                                     rating_values,
                                                                     rating_colors) if val > 0]
        if non_zero:
            labels, values, colors_list = zip(*non_zero)
            ax4.pie(values, labels=labels, autopct='%1.1f%%', colors=colors_list, startangle=90)
        else:
            ax4.text(0.5, 0.5, 'Sin calificaciones\naún', ha='center', va='center',
                    transform=ax4.transAxes, fontsize=12)
    else:
        ax4.text(0.5, 0.5, 'Sin calificaciones\naún', ha='center', va='center',
                transform=ax4.transAxes, fontsize=12)

    ax4.set_title('Distribución de Calificaciones')

    plt.tight_layout()
    plt.show()

def show_rated_combinations_graph(_root, ratings: dict, tops: list, bottoms: list,
                                  allowed_ratings: list = None):
    """Mostrar scatter plot de combinaciones calificadas con precios."""
    if not HAS_MATPLOTLIB:
        messagebox.showerror("Error", "matplotlib no está instalado.")
        return

    if allowed_ratings is None:
        allowed_ratings = ['favorite', 'normal', 'rare', 'incompatible']

    if not ratings:
        messagebox.showinfo("Gráfico de Combinaciones", "No hay combinaciones calificadas aún.")
        return

    # Crear diccionarios de lookup para tops y bottoms por nombre
    tops_dict = {item['nombre']: item for item in tops}
    bottoms_dict = {item['nombre']: item for item in bottoms}

    # Obtener listas únicas de tops y bottoms calificados
    tops_set = set()
    bottoms_set = set()
    _combo_data = {}  # {(top_idx, bottom_idx): (price, rating, top_name, bottom_name)}

    color_map = {
        'favorite': '#4A9EFF',
        'normal': '#4CAF50',
        'rare': '#FF9800',
        'incompatible': '#f44336'
    }

    # Procesar las combinaciones calificadas
    for combo_key, rating in ratings.items():
        if '|' in combo_key and rating in allowed_ratings:
            top_name, bottom_name = combo_key.split('|', 1)
            tops_set.add(top_name)
            bottoms_set.add(bottom_name)

    # Convertir sets a listas ordenadas
    tops_list = sorted(list(tops_set))
    bottoms_list = sorted(list(bottoms_set))

    if not tops_list or not bottoms_list:
        messagebox.showinfo("Gráfico de Combinaciones",
                            "No hay combinaciones válidas para graficar.")
        return

    # Crear índices
    top_to_idx = {name: i for i, name in enumerate(tops_list)}
    bottom_to_idx = {name: i for i, name in enumerate(bottoms_list)}

    # Extraer datos para scatter plot
    x_coords = []  # bottoms
    y_coords = []  # tops
    colors = []
    prices = []
    sizes = []
    rating_types = []

    for combo_key, rating in ratings.items():
        if '|' in combo_key:
            top_name, bottom_name = combo_key.split('|', 1)
            if top_name in top_to_idx and bottom_name in bottom_to_idx:
                x_coords.append(bottom_to_idx[bottom_name])
                y_coords.append(top_to_idx[top_name])
                colors.append(color_map.get(rating, '#cccccc'))
                rating_types.append(rating)

                # Calcular precio
                top_item = tops_dict.get(top_name)
                bottom_item = bottoms_dict.get(bottom_name)
                if top_item and bottom_item:
                    # Aplicar lógica de tipo 2 igual que en la app principal
                    top_price = top_item['precio']
                    bot_price = bottom_item['precio']

                    if top_item.get('tipo') == 2 and bottom_item.get('tipo') == 2:
                        if top_name != bottom_name:
                            bot_in_top = tops_dict.get(bottom_name)
                            top_in_bot = bottoms_dict.get(top_name)
                            top_price = min(top_price,
                                            bot_in_top['precio']) if bot_in_top else top_price
                            bot_price = min(bot_price,
                                            top_in_bot['precio']) if top_in_bot else bot_price
                    elif top_item.get('tipo') == 2:
                        bottom_version = bottoms_dict.get(top_name)
                        if bottom_version:
                            bot_price = min(bot_price, bottom_version['precio'])
                    elif bottom_item.get('tipo') == 2:
                        top_version = tops_dict.get(bottom_name)
                        if top_version:
                            top_price = min(top_price, top_version['precio'])

                    prices.append(top_price + bot_price)
                else:
                    prices.append(0)

    # Calcular tamaños de marcadores basados en precios
    if prices:
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price if max_price > min_price else 1

        # Normalizar precios a tamaño de marcador (100 - 1200)
        for price in prices:
            normalized = (price - min_price) / price_range if price_range > 0 else 0.5
            size = 100 + (normalized * 1200)  # Rango de 100 a 1200
            sizes.append(size)
    else:
        sizes = [800] * len(prices)

    # Crear figura
    _fig, ax = plt.subplots(figsize=(12, 8))

    # Configurar fuente para soporte Unicode
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']

    # Scatter plot con tamaños variables
    _scatter = ax.scatter(x_coords, y_coords, c=colors, s=sizes, alpha=0.8,
                        edgecolors='black', linewidth=1.5, zorder=3)

    # Configurar ejes
    ax.set_xticks(range(len(bottoms_list)))
    ax.set_xticklabels(bottoms_list, rotation=45, ha='right', fontsize=10)
    ax.set_yticks(range(len(tops_list)))
    ax.set_yticklabels(tops_list, fontsize=10)

    ax.set_xlabel('Bottom Items', fontsize=12, fontweight='bold')
    ax.set_ylabel('Top Items', fontsize=12, fontweight='bold')
    ax.set_title('Matriz de Combinaciones Calificadas', fontsize=14, fontweight='bold')

    # Establecer límites con padding
    ax.set_xlim(-0.5, len(bottoms_list) - 0.5)
    ax.set_ylim(-0.5, len(tops_list) - 0.5)

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', zorder=0)

    # Leyenda
    legend_elements = [
        Patch(facecolor='#4A9EFF', edgecolor='black', label='Favorito'),
        Patch(facecolor='#4CAF50', edgecolor='black', label='Normal'),
        Patch(facecolor='#FF9800', edgecolor='black', label='Raro'),
        Patch(facecolor='#f44336', edgecolor='black', label='Incompatible')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10, framealpha=0.95)

    # Agregar anotación sobre los tamaños
    if prices:
        min_price = min(prices)
        max_price = max(prices)
        ax.text(0.98, 0.02,
                f'combinación\nRango: ${int(min_price)} - ${int(max_price)}',
               transform=ax.transAxes, fontsize=9, verticalalignment='bottom',
               horizontalalignment='right', bbox=dict(boxstyle='round',
                                                      facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.show()

def show_prices_by_combination_graph(_root, ratings: dict, tops: list, bottoms: list,
                                     allowed_ratings: list = None):
    """Mostrar gráfico de barras de precios por combinación, ordenado de menor a mayor precio."""
    if not HAS_MATPLOTLIB:
        messagebox.showerror("Error", "matplotlib no está instalado.")
        return

    if allowed_ratings is None:
        allowed_ratings = ['favorite', 'normal', 'rare', 'incompatible']

    if not ratings:
        messagebox.showinfo("Gráfico de Precios", "No hay combinaciones calificadas aún.")
        return

    # Crear diccionarios de lookup para tops y bottoms por nombre
    tops_dict = {item['nombre']: item for item in tops}
    bottoms_dict = {item['nombre']: item for item in bottoms}

    color_map = {
        'favorite': '#4A9EFF',
        'normal': '#4CAF50',
        'rare': '#FF9800',
        'incompatible': '#f44336'
    }

    # Extraer combinaciones con precios y calificaciones
    combo_data = []  # Lista de (combo_label, price, color, rating)

    for combo_key, rating in ratings.items():
        if '|' in combo_key and rating in allowed_ratings:
            top_name, bottom_name = combo_key.split('|', 1)
            top_item = tops_dict.get(top_name)
            bottom_item = bottoms_dict.get(bottom_name)

            if top_item and bottom_item:
                # Calcular precio aplicando lógica de tipo 2
                top_price = top_item['precio']
                bot_price = bottom_item['precio']

                if top_item.get('tipo') == 2 and bottom_item.get('tipo') == 2:
                    if top_name != bottom_name:
                        bot_in_top = tops_dict.get(bottom_name)
                        top_in_bot = bottoms_dict.get(top_name)
                        top_price = min(top_price,
                                        bot_in_top['precio']) if bot_in_top else top_price
                        bot_price = min(bot_price,
                                        top_in_bot['precio']) if top_in_bot else bot_price
                elif top_item.get('tipo') == 2:
                    bottom_version = bottoms_dict.get(top_name)
                    if bottom_version:
                        bot_price = min(bot_price, bottom_version['precio'])
                elif bottom_item.get('tipo') == 2:
                    top_version = tops_dict.get(bottom_name)
                    if top_version:
                        top_price = min(top_price, top_version['precio'])

                total_price = top_price + bot_price
                color = color_map.get(rating, '#cccccc')
                combo_label = f"{top_name}\n+ {bottom_name}"
                combo_data.append((combo_label, total_price, color, rating))

    if not combo_data:
        messagebox.showinfo("Gráfico de Precios", "No hay combinaciones válidas para graficar.")
        return

    # Ordenar por precio de menor a mayor
    combo_data.sort(key=lambda x: x[1])

    # Extraer componentes para graficar
    labels = [item[0] for item in combo_data]
    prices = [item[1] for item in combo_data]
    colors = [item[2] for item in combo_data]

    # Crear figura
    _fig, ax = plt.subplots(figsize=(14, 7))

    # Configurar fuente para soporte Unicode
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']

    # Gráfico de barras
    bars = ax.bar(range(len(labels)), prices, color=colors, edgecolor='black',
                  linewidth=1.5, alpha=0.8)

    # Configurar ejes
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    ax.set_ylabel('Precio ($)', fontsize=12, fontweight='bold')
    ax.set_title('Precios de Combinaciones por Calificación', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')

    # Agregar valores de precio encima de cada barra
    for _i, (bar1e, price) in enumerate(zip(bars, prices)):
        height = bar1e.get_height()
        ax.text(bar1e.get_x() + bar1e.get_width()/2., height,
               f'${int(price)}',
               ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Leyenda
    legend_elements = [
        Patch(facecolor='#4A9EFF', edgecolor='black', label='Favorito'),
        Patch(facecolor='#4CAF50', edgecolor='black', label='Normal'),
        Patch(facecolor='#FF9800', edgecolor='black', label='Raro'),
        Patch(facecolor='#f44336', edgecolor='black', label='Incompatible')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10, framealpha=0.95)

    plt.tight_layout()
    plt.show()

class AdvancedOptionsWindow:
    """Ventana con opciones avanzadas: búsqueda, estadísticas, gráficos y ratings."""
    def __init__(self, parent, tops: list, bottoms: list, top_var=None, bottom_var=None,
                 top_combo=None, bottom_combo=None):
        self.tops = tops
        self.bottoms = bottoms
        self.all_items = tops + bottoms
        self.ratings = load_ratings()

        # Referencias a los comboboxes principales para verificar permisos
        self.top_var = top_var
        self.bottom_var = bottom_var
        self.top_combo = top_combo
        self.bottom_combo = bottom_combo

        # Variables para filtrar gráficos por categoría
        self.show_favorite_var = tk.BooleanVar(value=True)
        self.show_normal_var = tk.BooleanVar(value=True)
        self.show_rare_var = tk.BooleanVar(value=True)
        self.show_incompatible_var = tk.BooleanVar(value=True)

        # Variables de permisos (desactivados por defecto)
        self.naked_options_permitted = tk.BooleanVar(value=False)
        self.statistics_permitted = tk.BooleanVar(value=False)
        self.graphics_permitted = tk.BooleanVar(value=False)
        self.califications_permitted = tk.BooleanVar(value=False)

        self.window = tk.Toplevel(parent)
        self.window.title("Advanced Options")
        self.window.geometry("700x600")

        # Crear notebook con pestañas
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # PESTAÑA 1: Búsqueda
        search_frame_main = tk.Frame(self.notebook)
        self.notebook.add(search_frame_main, text="🔍 Búsqueda")

        search_frame = tk.LabelFrame(search_frame_main, text="Buscador Inteligente",
                                     font=('Segoe UI', 11, 'bold'), padx=10, pady=10)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(search_frame, text="Buscar item:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', self.on_search_change)

        search_btn = tk.Button(search_frame, text="Buscar", command=self.perform_search)
        search_btn.pack(side=tk.LEFT, padx=5)

        # Frame para resultados de búsqueda
        results_frame = tk.LabelFrame(search_frame_main, text="Resultados",
                                      font=('Segoe UI', 10), padx=10, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Listbox con scrollbar
        scrollbar = tk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_listbox = tk.Listbox(results_frame, yscrollcommand=scrollbar.set,
                                          font=('Courier', 9), height=12)
        self.results_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_listbox.yview)

        # PESTAÑA 2: Ratings
        ratings_frame_main = tk.Frame(self.notebook)
        self.notebook.add(ratings_frame_main, text="⭐ Calificaciones")
        self.create_ratings_tab(ratings_frame_main)

        # PESTAÑA 3: Estadísticas
        stats_frame_main = tk.Frame(self.notebook)
        self.notebook.add(stats_frame_main, text="📊 Estadísticas")

        # Frame para botones
        stats_buttons_frame = tk.Frame(stats_frame_main)
        stats_buttons_frame.pack(pady=20)

        stats_btn = tk.Button(stats_buttons_frame, text="Ver Estadísticas Generales",
                             command=self.show_stats,
                             bg="#4CAF50", fg="white", padx=10, pady=10, font=('Segoe UI', 11))
        stats_btn.pack(side=tk.LEFT, padx=10)

        rating_stats_btn = tk.Button(stats_buttons_frame, text="Ver Estadísticas de Calificaciones",
                                    command=self.show_rating_statistics,
                                    bg="#9C27B0", fg="white", padx=10, pady=10,
                                    font=('Segoe UI', 11))
        rating_stats_btn.pack(side=tk.LEFT, padx=10)

        # Guardar referencias a los botones de estadísticas
        self.stats_btn = stats_btn
        self.rating_stats_btn = rating_stats_btn

        # Inicializar estado de botones de estadísticas
        self.update_statistics_buttons_state()

        # PESTAÑA 4: Gráficos
        graphics_frame_main = tk.Frame(self.notebook)
        self.notebook.add(graphics_frame_main, text="📈 Gráficos")

        # Frame para botones
        buttons_frame = tk.Frame(graphics_frame_main)
        buttons_frame.pack(pady=20)

        graphics_btn = tk.Button(buttons_frame, text="Ver Gráficos Generales",
                                command=self.show_graphics,
                                bg="#2196F3", fg="white", padx=10, pady=10, font=('Segoe UI', 11))
        graphics_btn.pack(side=tk.LEFT, padx=10)

        rated_btn = tk.Button(buttons_frame, text="Ver Combinaciones Calificadas",
                             command=self.show_rated_combinations,
                             bg="#FF9800", fg="white", padx=10, pady=10, font=('Segoe UI', 11))
        rated_btn.pack(side=tk.LEFT, padx=10)

        prices_btn = tk.Button(buttons_frame, text="Ver Precios por Combinación",
                              command=self.show_prices_by_combination,
                              bg="#E91E63", fg="white", padx=10, pady=10, font=('Segoe UI', 11))
        prices_btn.pack(side=tk.LEFT, padx=10)

        # Guardar referencias a los botones para habilitar/deshabilitar
        self.graphics_btn = graphics_btn
        self.rated_btn = rated_btn
        self.prices_btn = prices_btn

        # Inicializar estado de botones de gráficos
        self.update_graph_buttons_state()

        # Frame para checkbuttons de categorías
        filter_frame = tk.LabelFrame(graphics_frame_main, text="Filtrar por Categoría",
                                     font=('Segoe UI', 10, 'bold'), padx=10, pady=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)

        # Crear checkbuttons para cada categoría
        self.favorite_check = tk.Checkbutton(filter_frame, text="Favorito",
                                            variable=self.show_favorite_var,
                                            command=self.update_graph_buttons_state)
        self.favorite_check.pack(side=tk.LEFT, padx=10)

        self.normal_check = tk.Checkbutton(filter_frame, text="Normal",
                                          variable=self.show_normal_var,
                                          command=self.update_graph_buttons_state)
        self.normal_check.pack(side=tk.LEFT, padx=10)

        self.rare_check = tk.Checkbutton(filter_frame, text="Raro",
                                        variable=self.show_rare_var,
                                        command=self.update_graph_buttons_state)
        self.rare_check.pack(side=tk.LEFT, padx=10)

        self.incompatible_check = tk.Checkbutton(filter_frame, text="Incompatible",
                                                 variable=self.show_incompatible_var,
                                                 command=self.update_graph_buttons_state)
        self.incompatible_check.pack(side=tk.LEFT, padx=10)

        # Inicializar estado de botones
        self.update_graph_buttons_state()

        # PESTAÑA 5: Permisos
        permissions_frame_main = tk.Frame(self.notebook)
        self.notebook.add(permissions_frame_main, text="🔐 Permisos")

        permissions_frame = tk.LabelFrame(permissions_frame_main,
                                          text="Controlar Acceso a Funciones",
                                          font=('Segoe UI', 11, 'bold'), padx=15, pady=15)
        permissions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # SECCIÓN 1: Autenticación por contraseña (siempre rechaza)
        auth_frame = tk.LabelFrame(permissions_frame, text="Autenticación de Permisos",
                                   font=('Segoe UI', 10, 'bold'), padx=10, pady=10,
                                   fg='#333333')
        auth_frame.pack(anchor=tk.W, fill=tk.X, padx=20, pady=(0, 20))

        tk.Label(auth_frame, text="Contraseña (10 dígitos):",
                 font=('Segoe UI', 9)).pack(anchor=tk.W, pady=(0, 5))

        password_input_frame = tk.Frame(auth_frame)
        password_input_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 10))

        self.password_var = tk.StringVar()
        password_entry = tk.Entry(password_input_frame, textvariable=self.password_var,
                                  show="•", width=20, font=('Segoe UI', 10))
        password_entry.pack(side=tk.LEFT, padx=(0, 10))

        verify_btn = tk.Button(password_input_frame, text="Ver Acceso",
                              command=self.verify_password,
                              bg="#FF6B6B", fg="white", padx=15, pady=5,
                              font=('Segoe UI', 9, 'bold'))
        verify_btn.pack(side=tk.LEFT)

        # Label de instrucción antigua (ahora es para el método glitter)
        instruction_label = tk.Label(permissions_frame,
                                     text="Selecciona 'X' para desbloquear los permisos",
                                     font=('Segoe UI', 9, 'italic'),
                                     fg='#2196F3', bg=permissions_frame.cget('bg'))
        instruction_label.pack(anchor=tk.W, padx=20, pady=(10, 15), fill=tk.X)

        # Checkbutton para Naked Options
        self.naked_check = tk.Checkbutton(permissions_frame, text="Permitir Opciones Naked",
                                         variable=self.naked_options_permitted,
                                         command=self.on_permissions_changed,
                                         font=('Segoe UI', 10),
                                         justify=tk.LEFT, state=tk.DISABLED)
        self.naked_check.pack(anchor=tk.W, padx=20, pady=10, fill=tk.X)

        # Checkbutton para Statistics
        self.stats_check = tk.Checkbutton(permissions_frame, text="Permitir Estadísticas",
                                         variable=self.statistics_permitted,
                                         command=self.on_permissions_changed,
                                         font=('Segoe UI', 10),
                                         justify=tk.LEFT, state=tk.DISABLED)
        self.stats_check.pack(anchor=tk.W, padx=20, pady=10, fill=tk.X)

        # Checkbutton para Graphics
        self.graphics_check = tk.Checkbutton(permissions_frame, text="Permitir Gráficos",
                                            variable=self.graphics_permitted,
                                            command=self.on_permissions_changed,
                                            font=('Segoe UI', 10),
                                            justify=tk.LEFT, state=tk.DISABLED)
        self.graphics_check.pack(anchor=tk.W, padx=20, pady=10, fill=tk.X)

        # Checkbutton para Califications
        self.calif_check = tk.Checkbutton(permissions_frame, text="Permitir Calificaciones",
                                         variable=self.califications_permitted,
                                         command=self.on_permissions_changed,
                                         font=('Segoe UI', 10),
                                         justify=tk.LEFT, state=tk.DISABLED)
        self.calif_check.pack(anchor=tk.W, padx=20, pady=10, fill=tk.X)

        # Vincular verificación de permisos a los comboboxes si están disponibles
        if self.top_var and self.bottom_var:
            self.top_var.trace('w', self.verify_permissions)
            self.bottom_var.trace('w', self.verify_permissions)

    def create_ratings_tab(self, parent):
        """Crear pestaña de calificaciones."""
        # Frame para selección de combinación
        combo_frame = tk.LabelFrame(parent, text="Seleccionar Combinación",
                                    font=('Segoe UI', 10, 'bold'), padx=10, pady=10)
        combo_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(combo_frame, text="Top:").grid(row=0, column=0, sticky=tk.W, padx=5)
        top_names = [t['nombre'] for t in filter_items_by_permissions(self.tops)]
        self.rating_top_var = tk.StringVar(value=top_names[0] if top_names else '')
        self.rating_top_combo = ttk.Combobox(combo_frame, textvariable=self.rating_top_var,
                                values=top_names, state='readonly', width=30)
        self.rating_top_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        tk.Label(combo_frame, text="Bottom:").grid(row=1, column=0, sticky=tk.W, padx=5)
        bottom_names = [b['nombre'] for b in filter_items_by_permissions(self.bottoms)]
        self.rating_bottom_var = tk.StringVar(value=bottom_names[0] if bottom_names else '')
        self.rating_bottom_combo = ttk.Combobox(combo_frame, textvariable=self.rating_bottom_var,
                                   values=bottom_names, state='readonly', width=30)
        self.rating_bottom_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Frame para calificaciones
        rating_frame = tk.LabelFrame(parent, text="Calificación",
                                    font=('Segoe UI', 10, 'bold'), padx=10, pady=10)
        rating_frame.pack(fill=tk.X, padx=10, pady=10)

        self.rating_var = tk.StringVar(value='unrated')

        ratings_options = [
            ('⭐ Favorito', 'favorite', '#4A9EFF'),
            ('✓ Normal', 'normal', '#4CAF50'),
            ('◆ Raro', 'rare', '#FF9800'),
            ('✗ Incompatible', 'incompatible', '#f44336'),
            ('Sin calificación', 'unrated', '#cccccc'),
        ]

        for label, value, color in ratings_options:
            rb = tk.Radiobutton(rating_frame, text=label, variable=self.rating_var,
                               value=value, bg=color if value != 'unrated' else '#f0f0f0',
                               fg='white' if value != 'unrated' else 'black',
                               font=('Segoe UI', 10), padx=20, pady=8)
            rb.pack(anchor=tk.W, pady=3)

        # Botones
        button_frame = tk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=15)

        save_btn = tk.Button(button_frame, text="💾 Guardar Calificación",
                           command=self.save_rating,
                           bg="#4CAF50", fg="white", padx=15, pady=5, font=('Segoe UI', 10))
        save_btn.pack(side=tk.LEFT, padx=5)

        load_btn = tk.Button(button_frame, text="🔄 Cargar",
                           command=self.load_rating,
                           bg="#2196F3", fg="white", padx=15, pady=5, font=('Segoe UI', 10))
        load_btn.pack(side=tk.LEFT, padx=5)

    def load_rating(self):
        """Cargar la calificación de la combinación seleccionada."""
        top = self.rating_top_var.get()
        bottom = self.rating_bottom_var.get()
        if not top or not bottom:
            messagebox.showwarning("Advertencia", "Selecciona top y bottom.")
            return

        rating = get_combination_rating(self.ratings, top, bottom)
        self.rating_var.set(rating)

    def save_rating(self):
        """Guardar la calificación de la combinación seleccionada."""
        # Verificar permiso de calificaciones
        if not PERMISSIONS.get('califications', False):
            messagebox.showwarning("Permiso requerido",
                                 "Activa el permiso 'Calificaciones' en la"
                                 " pestaña Permisos para guardar nuevas calificaciones.")
            return

        top = self.rating_top_var.get()
        bottom = self.rating_bottom_var.get()
        rating = self.rating_var.get()

        if not top or not bottom:
            messagebox.showwarning("Advertencia", "Selecciona top y bottom.")
            return

        set_combination_rating(self.ratings, top, bottom, rating)
        label_text, _ = RATING_LABELS[rating]
        messagebox.askokcancel("Guardado", f"Combinación guardada como: {label_text}")

    def verify_permissions(self, *args):
        """Verificar si glitter bra y glitter panties están seleccionados."""
        if not self.top_var or not self.bottom_var:
            return

        # Verificar si los checkbuttons aún existen (en caso de que la ventana se haya cerrado)
        if not self.naked_check.winfo_exists():
            return

        top_selected = self.top_var.get()
        bottom_selected = self.bottom_var.get()

        # Habilitar permisos solo si están seleccionados glitter bra y glitter panties
        if top_selected == 'glitter bra' and bottom_selected == 'glitter panties':
            # Desbloquear todos los checkbuttons
            self.naked_check.config(state=tk.NORMAL)
            self.stats_check.config(state=tk.NORMAL)
            self.graphics_check.config(state=tk.NORMAL)
            self.calif_check.config(state=tk.NORMAL)
        else:
            # Bloquear todos los checkbuttons
            self.naked_check.config(state=tk.DISABLED)
            self.stats_check.config(state=tk.DISABLED)
            self.graphics_check.config(state=tk.DISABLED)
            self.calif_check.config(state=tk.DISABLED)
            # Desmarca los permisos si están bloqueados
            self.naked_options_permitted.set(False)
            self.statistics_permitted.set(False)
            self.graphics_permitted.set(False)
            self.califications_permitted.set(False)
            PERMISSIONS['naked_options'] = False
            PERMISSIONS['statistics'] = False
            PERMISSIONS['graphics'] = False
            PERMISSIONS['califications'] = False

    def on_permissions_changed(self):
        """Actualizar PERMISSIONS cuando cambia el estado de cualquier checkbox de permisos."""
        PERMISSIONS['naked_options'] = self.naked_options_permitted.get()
        PERMISSIONS['statistics'] = self.statistics_permitted.get()
        PERMISSIONS['graphics'] = self.graphics_permitted.get()
        PERMISSIONS['califications'] = self.califications_permitted.get()

        # Actualizar estado de botones según permisos
        self.update_statistics_buttons_state()
        self.update_graph_buttons_state()

        # Actualizar los comboboxes de la ventana principal si están disponibles
        self.update_main_window_combos()

    def update_main_window_combos(self):
        """Actualizar los valores de los comboboxes de la ventana principal
        cuando cambian los permisos."""
        if not self.top_combo or not self.bottom_combo or not self.top_var or not self.bottom_var:
            return

        # Recalcular las listas de items según los permisos actuales
        new_top_names = [t['nombre'] for t in filter_items_by_permissions(self.tops)]
        new_bottom_names = [b['nombre'] for b in filter_items_by_permissions(self.bottoms)]

        # Obtener los valores actuales seleccionados
        current_top = self.top_var.get()
        current_bottom = self.bottom_var.get()

        # Actualizar los valores de los comboboxes
        self.top_combo['values'] = new_top_names
        self.bottom_combo['values'] = new_bottom_names

        # Si el valor actual ya no está en la lista, seleccionar el primero disponible
        if current_top not in new_top_names and new_top_names:
            self.top_var.set(new_top_names[0])
        elif not new_top_names:
            self.top_var.set('')

        if current_bottom not in new_bottom_names and new_bottom_names:
            self.bottom_var.set(new_bottom_names[0])
        elif not new_bottom_names:
            self.bottom_var.set('')

        # Actualizar también los comboboxes de la pestaña de calificaciones si existen
        if hasattr(self, 'rating_top_combo') and hasattr(self, 'rating_bottom_combo'):
            try:
                # Verificar si los widgets todavía existen (podrían haber sido destruidos)
                if not self.rating_top_combo.winfo_exists(
                    ) or not self.rating_bottom_combo.winfo_exists():
                    return

                current_rating_top = self.rating_top_var.get()
                current_rating_bottom = self.rating_bottom_var.get()

                self.rating_top_combo['values'] = new_top_names
                self.rating_bottom_combo['values'] = new_bottom_names

                if current_rating_top not in new_top_names and new_top_names:
                    self.rating_top_var.set(new_top_names[0])
                elif not new_top_names:
                    self.rating_top_var.set('')

                if current_rating_bottom not in new_bottom_names and new_bottom_names:
                    self.rating_bottom_var.set(new_bottom_names[0])
                elif not new_bottom_names:
                    self.rating_bottom_var.set('')
            except tk.TclError:
                # La ventana fue cerrada, salir silenciosamente
                return

    def verify_password(self):
        """Verificar contraseña (siempre rechaza por diversión)."""
        password_entered = self.password_var.get()

        # Mostrar mensaje de acceso denegado
        messagebox.showerror("Acceso Denegado",
                           f"La contraseña ingresada es inválida.\n\n"
                           f"Contraseña ingresada:"
                           f" {password_entered if password_entered else '(vacía)'}\n\n"
                           f"Acceso denegado. Intenta nuevamente.")

        # Limpiar el campo de entrada
        self.password_var.set("")

    def on_search_change(self, _event=None):
        """Actualizar resultados al escribir."""
        query = self.search_var.get().lower()
        if len(query) >= 2:
            self.perform_search()

    def perform_search(self):
        """Realizar búsqueda fuzzy y mostrar resultados."""
        query = self.search_var.get()
        self.results_listbox.delete(0, tk.END)

        if not query:
            self.results_listbox.insert(tk.END, "Ingresa un término de búsqueda...")
            return

        # Búsqueda en tops (filtrar por permisos)
        tops_results = fuzzy_search(query, filter_items_by_permissions(self.tops))
        # Búsqueda en bottoms (filtrar por permisos)
        bottoms_results = fuzzy_search(query, filter_items_by_permissions(self.bottoms))

        if tops_results or bottoms_results:
            if tops_results:
                self.results_listbox.insert(tk.END, "═══ TOP ITEMS ═══")
                for item in tops_results:
                    self.results_listbox.insert(tk.END,
                        f"  {item['nombre']:<25} ${item['precio']:>6.0f}  ({item['categoria']})")

            if bottoms_results:
                if tops_results:
                    self.results_listbox.insert(tk.END, "")
                self.results_listbox.insert(tk.END, "═══ BOTTOM ITEMS ═══")
                for item in bottoms_results:
                    self.results_listbox.insert(tk.END,
                        f"  {item['nombre']:<25} ${item['precio']:>6.0f}  ({item['categoria']})")
        else:
            self.results_listbox.insert(tk.END, f"No se encontraron coincidencias para '{query}'")

    def show_stats(self):
        """Mostrar estadísticas."""
        show_statistics_window(self.window, self.all_items, self.ratings)

    def show_rating_statistics(self):
        """Mostrar estadísticas específicas de calificaciones por item."""
        show_rating_statistics_window(self.window, self.ratings, self.tops, self.bottoms)

    def show_graphics(self):
        """Mostrar gráficos."""
        show_graphics_window(self.window, self.all_items, self.ratings)

    def show_rated_combinations(self):
        """Mostrar gráfico de combinaciones calificadas."""
        allowed_ratings = []
        if self.show_favorite_var.get():
            allowed_ratings.append('favorite')
        if self.show_normal_var.get():
            allowed_ratings.append('normal')
        if self.show_rare_var.get():
            allowed_ratings.append('rare')
        if self.show_incompatible_var.get():
            allowed_ratings.append('incompatible')

        show_rated_combinations_graph(self.window, self.ratings, self.tops,
                                      self.bottoms, allowed_ratings)

    def show_prices_by_combination(self):
        """Mostrar gráfico de barras de precios por combinación."""
        allowed_ratings = []
        if self.show_favorite_var.get():
            allowed_ratings.append('favorite')
        if self.show_normal_var.get():
            allowed_ratings.append('normal')
        if self.show_rare_var.get():
            allowed_ratings.append('rare')
        if self.show_incompatible_var.get():
            allowed_ratings.append('incompatible')

        show_prices_by_combination_graph(self.window, self.ratings, self.tops,
                                         self.bottoms, allowed_ratings)

    def update_graph_buttons_state(self):
        """Habilitar/deshabilitar botones de gráfico según permiso y categorías seleccionadas."""
        # Verificar permiso de graphics
        graphics_permitted = self.graphics_permitted.get()

        # Verificar si hay categorías seleccionadas
        has_selection = (self.show_favorite_var.get() or self.show_normal_var.get() or
                        self.show_rare_var.get() or self.show_incompatible_var.get())

        # Ambas condiciones deben cumplirse para habilitar
        can_enable = graphics_permitted and has_selection

        # Actualizar estado de rated_btn y prices_btn
        if can_enable:
            self.rated_btn.config(state=tk.NORMAL)
            self.prices_btn.config(state=tk.NORMAL)
        else:
            self.rated_btn.config(state=tk.DISABLED)
            self.prices_btn.config(state=tk.DISABLED)

        # Actualizar estado de graphics_btn según permiso
        if graphics_permitted:
            self.graphics_btn.config(state=tk.NORMAL)
        else:
            self.graphics_btn.config(state=tk.DISABLED)

    def update_statistics_buttons_state(self):
        """Habilitar/deshabilitar botones de estadísticas según permiso."""
        if self.statistics_permitted.get():
            self.stats_btn.config(state=tk.NORMAL)
            self.rating_stats_btn.config(state=tk.NORMAL)
        else:
            self.stats_btn.config(state=tk.DISABLED)
            self.rating_stats_btn.config(state=tk.DISABLED)

def main():
    """ Main function to run the outfit price calculator GUI. """
    # Determinar la ruta base: funciona tanto con .py como con .exe
    if getattr(sys, 'frozen', False):
        # Se ejecuta como .exe (compilado con PyInstaller)
        # sys._MEIPASS es el directorio temporal de PyInstaller con los archivos de datos
        base = sys._MEIPASS
    else:
        # Se ejecuta como script .py
        base = os.path.dirname(os.path.abspath(__file__))

    top_csv = os.path.join(base, 'top_items.csv')
    bottom_csv = os.path.join(base, 'bottom_items.csv')

    # Create CSV files with requested content if missing
    make_csv_if_missing(top_csv, DEFAULT_TOP_ITEMS)
    make_csv_if_missing(bottom_csv, DEFAULT_BOTTOM_ITEMS)

    tops = load_items(top_csv)
    bottoms = load_items(bottom_csv)

    root = tk.Tk()
    root.title('Outfit Price Calculator')
    root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')

    style = ttk.Style()
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass

    # Configurar estilos personalizados para Combobox (amarillo pastel con mejor contraste)
    style.configure('Light.TCombobox',
                    entrybackground="#E6DD8F",  # Amarillo pastel claro
                   fieldbackground="#E6DD8F",  # Amarillo pastel claro
                   background="#E0DEC7",
                   foreground='#333333',       # Texto oscuro para contraste
                   insertcolor='#333333')

    style.configure('Dark.TCombobox',
                     entrybackground='#E6D68F',  # Amarillo pastel más saturado/oscuro
                   fieldbackground='#E6D68F',  # Amarillo pastel más saturado/oscuro
                   background="#DBC870",
                   foreground='#1a1a1a',       # Texto muy oscuro para buen contraste
                   insertcolor='#1a1a1a')

    # Configurar estilos personalizados para Progressbar con gradiente de color
    style.configure('Green.Vertical.TProgressbar', background=COLOR_TOTAL_LOW)
    style.configure('Yellow.Vertical.TProgressbar', background='#FFD700')
    style.configure('Orange.Vertical.TProgressbar', background=COLOR_TOTAL_MID)
    style.configure('Red.Vertical.TProgressbar', background=COLOR_TOTAL_HIGH)

    # Variable para guardar el tema actual
    current_theme = {'theme': 'light'}

    def toggle_theme():
        """Cambia entre tema claro y oscuro."""
        new_theme = 'dark' if current_theme['theme'] == 'light' else 'light'
        current_theme['theme'] = new_theme
        theme_colors = THEMES[new_theme]

        # Actualizar ventana principal y frame principal
        root.config(bg=theme_colors['bg'])
        frm.config(bg=theme_colors['bg'])
        main_container.config(bg=theme_colors['bg'])
        bar_frame.config(bg=theme_colors['bg'])

        # Aplicar tema a todos los widgets recursivamente
        apply_theme_to_widgets(frm, theme_colors)

        # Actualizar específicamente los frames de nombres
        sel_frame.config(bg=theme_colors['bg'], fg=theme_colors['label'])
        names_topframe.config(bg=theme_colors['bg'], fg=theme_colors['label'])
        names_bottomframe.config(bg=theme_colors['bg'], fg=theme_colors['label'])
        total_frame.config(bg=theme_colors['bg'])
        price_rating_frame.config(bg=theme_colors['bg'])
        combination_rating_label.config(bg=theme_colors['bg'])

        # Actualizar botón Random con colores pastel según tema
        if new_theme == 'light':
            btn.config(bg='#E8B4D4', fg='#333333', activebackground='#D99DB8')
            # Cambiar estilo de combobox a Light (amarillo pastel claro)
            top_combo.configure(style='Light.TCombobox')
            bottom_combo.configure(style='Light.TCombobox')
        else:  # dark
            btn.config(bg='#C9A0B3', fg="#7034fc", activebackground='#B88AA7')
            # Cambiar estilo de combobox a Dark (amarillo pastel oscuro)
            top_combo.configure(style='Dark.TCombobox')
            bottom_combo.configure(style='Dark.TCombobox')

        # Actualizar botón de tema con nuevo color
        theme_btn.config(bg=theme_colors['bg'], fg=theme_colors['label'],
                        text='🌙' if new_theme == 'dark' else '☀️',
                        activebackground=theme_colors['frame'],
                        activeforeground=theme_colors['label'])

        # Actualizar botón de opciones avanzadas con nuevo color
        advanced_btn.config(bg=theme_colors['bg'], fg=theme_colors['text_secondary'],
                           activebackground=theme_colors['frame'],
                           activeforeground=theme_colors['label'])

        # Actualizar labels de la barra de precio
        bar_max_label.config(bg=theme_colors['bg'], fg=theme_colors['text_secondary'])
        bar_min_label.config(bg=theme_colors['bg'], fg=theme_colors['text_secondary'])

    root_bg = THEMES['light']['bg']
    root.config(bg=root_bg)

    # Use tk.Frame so we can control background color consistently
    # Main container with content on left and price bar on right
    main_container = tk.Frame(root, bg=root_bg)
    main_container.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)

    # Left frame for main content
    frm = tk.Frame(main_container, bg=root_bg)
    frm.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Botón para cambiar de tema (esquina superior derecha) con estilo mejorado
    theme_btn = tk.Button(root, text='☀️', font=('Segoe UI', 14),
                          command=toggle_theme, bg=root_bg, fg='#333333',
                          relief=tk.FLAT, bd=0, highlightthickness=0,
                          activebackground=THEMES['light']['bg'],
                          activeforeground='#333333')
    theme_btn.pack(side=tk.TOP, anchor=tk.NE, padx=10, pady=5)

    # Botón de opciones avanzadas (esquina inferior izquierda)
    def open_advanced_options():
        AdvancedOptionsWindow(root, tops, bottoms, top_var, bottom_var, top_combo, bottom_combo)

    advanced_btn = tk.Button(root, text='⚙️', font=('Segoe UI', 14),
                            command=open_advanced_options, bg=root_bg,
                            fg=THEMES['light']['text_secondary'],
                            relief=tk.FLAT, bd=0, highlightthickness=0,
                            activebackground=THEMES['light']['frame'],
                            activeforeground=THEMES['light']['label'],
                            cursor='hand2')
    advanced_btn.pack(side=tk.BOTTOM, anchor=tk.SW, padx=10, pady=5)

    # Right frame for price bar (vertical progress bar)
    bar_frame = tk.Frame(main_container, bg=root_bg, width=60)
    bar_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
    bar_frame.pack_propagate(False)

    # Label for max price
    bar_max_label = tk.Label(bar_frame, text='1500', font=('Segoe UI', 8),
                             bg=root_bg, fg='#888888')
    bar_max_label.pack(side=tk.TOP, pady=2)

    # Vertical progress bar for price visualization (100-1500 scale with logarithmic)
    price_bar = ttk.Progressbar(bar_frame, orient=tk.VERTICAL, length=300,
                                mode='determinate', maximum=100, value=0,
                                style='Green.Vertical.TProgressbar')
    price_bar.pack(fill=tk.BOTH, expand=True, pady=5)

    # Label for min price
    bar_min_label = tk.Label(bar_frame, text='50', font=('Segoe UI', 8),
                             bg=root_bg, fg='#888888')
    bar_min_label.pack(side=tk.BOTTOM, pady=2)

    sel_frame = tk.LabelFrame(frm, bg=THEMES['light']['bg'],
                              text='top / bottom selection',
                              font=FONT_LABEL, padx=8, pady=8, fg='#333333',
                              relief=tk.FLAT, borderwidth=2)
    sel_frame.grid(row=2, column=0, sticky=tk.W)

    tk.Label(sel_frame, text='Top item:', font=FONT_LABEL,
             bg=THEMES['light']['bg'], fg='#333333').grid(row=0,
                                                          column=0,
                                                          sticky=tk.W,
                                                          padx=(0,8))
    top_names = [t['nombre'] for t in filter_items_by_permissions(tops)]
    top_var = tk.StringVar(value=top_names[0] if top_names else '')
    top_combo = ttk.Combobox(sel_frame, textvariable=top_var,
                             values=top_names, state='readonly', width=22,
                             style='Light.TCombobox')
    top_combo.grid(row=0, column=1, sticky=tk.W, padx=4, pady=6)

    tk.Label(sel_frame, text='Bottom item:', font=FONT_LABEL,
             bg=THEMES['light']['bg'], fg='#333333').grid(row=1,
                                                          column=0, sticky=tk.W,
                                                          padx=(0,8))
    bottom_names = [b['nombre'] for b in filter_items_by_permissions(bottoms)]
    bottom_var = tk.StringVar(value=bottom_names[0] if bottom_names else '')
    bottom_combo = ttk.Combobox(sel_frame, textvariable=bottom_var,
                                values=bottom_names, state='readonly', width=22,
                                style='Light.TCombobox')
    bottom_combo.grid(row=1, column=1, sticky=tk.W, padx=4, pady=6)
    # fonts for info and duplicate labels
    info_font = tkfont.Font(family=FONT_INFO[0], size=FONT_INFO[1], weight=FONT_INFO[2])
    dup_font = tkfont.Font(family=FONT_DUP[0], size=FONT_DUP[1])

    # create a small frame to hold the top info label and its tipo-2 duplicate label
    top_info_frame = tk.Frame(sel_frame, bg=root_bg )
    top_info_frame.grid(row=0, column=2, sticky=tk.W, padx=(12,0))
    top_info_label = tk.Label(top_info_frame, text='', font=info_font, bg=root_bg, justify=tk.LEFT)
    top_info_label.pack(side=tk.LEFT)

    # labels to the right that display names of tipo-2 (both) items
    top_dup_label = tk.Label(top_info_frame, text='', font=dup_font,
                             fg=COLOR_DUP_TEXT, bg=root_bg, justify=tk.LEFT)
    top_dup_label.pack(side=tk.LEFT, padx=(8,0))

    bottom_info_frame = tk.Frame(sel_frame, bg=root_bg)
    bottom_info_frame.grid(row=1, column=2, sticky=tk.W, padx=(12,0))
    bottom_info_label = tk.Label(bottom_info_frame, text='',
                                 font=info_font, bg=root_bg, justify=tk.LEFT)
    bottom_info_label.pack(side=tk.LEFT)
    bottom_dup_label = tk.Label(bottom_info_frame, text='',
                                font=dup_font, fg=COLOR_DUP_TEXT, bg=root_bg, justify=tk.LEFT)
    bottom_dup_label.pack(side=tk.LEFT, padx=(8,0))

    # Horizontal separator line after selectors
    #separator2 = tk.Frame(frm, bg='#cccccc', height=1)
    #separator2.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(8, 8))
    #separator2.grid_propagate(False)

    # Button at right of selectors
    random_selected = False  # Flag para saber si se seleccionó random

    def show_selection():
        nonlocal random_selected
        # Select random items from both top and bottom (filtered by permissions)
        filtered_tops = filter_items_by_permissions(tops)
        filtered_bottoms = filter_items_by_permissions(bottoms)
        if filtered_tops and filtered_bottoms:
            random_top = random.choice(filtered_tops)
            random_bottom = random.choice(filtered_bottoms)
            top_var.set(random_top['nombre'])
            bottom_var.set(random_bottom['nombre'])
            update_display()
            # Deshabilitar botón de opciones avanzadas y marcar como seleccionado por random
            advanced_btn.config(state=tk.DISABLED)
            random_selected = True

    # Función para re-habilitar el botón de opciones avanzadas
    # cuando se cambia la selección manualmente
    def on_selection_changed(*args):
        # Solo re-habilitar si no fue seleccionado mediante random
        if not random_selected:
            advanced_btn.config(state=tk.NORMAL)

    btn = tk.Button(sel_frame, text='Random\nOutfit', command=show_selection,
                   bg='#E8B4D4', fg="#312929", font=('Segoe UI', 10, 'bold'),
                   relief=tk.SOLID, bd=2, activebackground='#D99DB8',
                   activeforeground='#333333', cursor='hand2', padx=12, pady=10,
                   highlightthickness=0, overrelief=tk.SOLID)
    btn.grid(row=0, column=3, rowspan=2, sticky=tk.NS, padx=(12, 0), pady=6)
    # Checkbox to show/hide prices will be created after update_display() is defined
    show_prices_var = tk.BooleanVar(value=False)

    # prominent total area at the top, centered
    total_frame = tk.Frame(frm, bg=root_bg)
    total_frame.grid(row=0, column=0, columnspan=2, pady=(4,12))

    big_font = tkfont.Font(family=FONT_TOTAL[0], size=FONT_TOTAL[1], weight=FONT_TOTAL[2])

    # Frame para el precio y la calificación lado a lado
    price_rating_frame = tk.Frame(total_frame, bg=root_bg)
    price_rating_frame.pack(pady=(4,0))

    price_display = tk.Label(price_rating_frame, text='0', font=big_font,
                             fg=COLOR_TOTAL_LOW, bg=root_bg, bd=0)
    price_display.pack(side=tk.LEFT, padx=(0, 20))

    # Rating label grande al lado del precio
    rating_font = tkfont.Font(family='Segoe UI', size=20, weight='bold')
    combination_rating_label = tk.Label(price_rating_frame, text='', font=rating_font,
                                        bg=root_bg, fg='#4A9EFF')
    combination_rating_label.pack(side=tk.LEFT, padx=(10, 0))

    # Frame to hold the item names with separator
    names_topframe = tk.LabelFrame(total_frame, bg=THEMES['light']['bg'], text='Top',
                                font=FONT_LABEL, padx=8, pady=8, fg='#333333',
                                relief=tk.FLAT, borderwidth=1, width=350, height=84)
    names_topframe.pack(pady=(6,0))
    names_topframe.pack_propagate(False)  # No cambiar tamaño según contenido

    names_bottomframe = tk.LabelFrame(total_frame, bg=THEMES['light']['bg'],
                                      text='Bottom',
                                font=FONT_LABEL, padx=8, pady=8, fg='#333333',
                                relief=tk.FLAT, borderwidth=1, width=350, height=84)
    names_bottomframe.pack(pady=(6,0))
    names_bottomframe.pack_propagate(False)  # No cambiar tamaño según contenido

    # labels under the total showing the selected top and bottom item names
    top_name_label = tk.Label(names_topframe, text='', font=FONT_NAME, bg=THEMES['light']['bg'],
                             wraplength=320, justify=tk.CENTER)
    top_name_label.pack(fill=tk.BOTH, expand=True)

    bottom_name_label = tk.Label(names_bottomframe, text='', font=FONT_NAME,
                                 bg=THEMES['light']['bg'], wraplength=320, justify=tk.CENTER)
    bottom_name_label.pack(fill=tk.BOTH, expand=True)

    # Horizontal separator line after total
    #separator1 = tk.Frame(frm, bg='#cccccc', height=1)
    #separator1.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(8, 8))
    #separator1.grid_propagate(False)

    details_label = tk.Label(frm, text='', wraplength=380, bg=THEMES['light']['bg'],
                             font=('Segoe UI', 9),
                             fg='#666666')
    details_label.grid(row=4, column=0, sticky=tk.W, pady=(6,0))

    # Label to show maximum possible price
    bold_font = tkfont.Font(family='Segoe UI', size=9, weight='bold')
    max_price_label = tk.Label(frm, text='', bg=THEMES['light']['bg'], font=bold_font, fg='#333333')
    max_price_label.grid(row=5, column=0, sticky=tk.W, pady=(4,0))


    def build_lookup(collection):
        """Build a dictionary for O(1) item lookup by nombre."""
        return {item['nombre']: item for item in collection}

    tops_dict = build_lookup(tops)
    bottoms_dict = build_lookup(bottoms)

    # Cargar calificaciones de combinaciones
    ratings_data = load_ratings()

    def price_to_logarithmic_scale(price, min_price=50, max_price=1500):
        """Convierte un precio a escala logarítmica (50-1500)."""
        if price < min_price:
            return 0
        if price >= max_price:
            return 100
        # Usar logaritmo natural para suavizar la escala en el rango 50-1500
        # Fórmula: log(precio - min + 1) / log(max - min + 1) * 100
        log_value = math.log(price - min_price + 1) / math.log(max_price - min_price + 1) * 100
        return min(log_value, 100)

    def color_for_total(total):
        if total <= THRESH_MID:
            return COLOR_TOTAL_LOW
        if total <= THRESH_HIGH:
            return COLOR_TOTAL_MID
        return COLOR_TOTAL_HIGH

    def hex_to_rgb(hex_color):
        """Convierte color hexadecimal a tuple RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(r, g, b):
        """Convierte RGB a hexadecimal."""
        return f'#{r:02x}{g:02x}{b:02x}'

    def interpolate_color(color1, color2, factor):
        """Interpola entre dos colores RGB."""
        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        return rgb_to_hex(r, g, b)

    def get_bar_color(price, min_price=50, mid_price=275, max_price=1500):
        """Retorna color de gradiente según el precio."""
        if price <= min_price:
            return COLOR_TOTAL_LOW  # Verde
        elif price <= mid_price:
            # Interpolación verde a naranja
            factor = (price - min_price) / (mid_price - min_price)
            return interpolate_color(COLOR_TOTAL_LOW, COLOR_TOTAL_MID, factor)
        elif price <= max_price:
            # Interpolación naranja a rojo
            factor = (price - mid_price) / (max_price - mid_price)
            return interpolate_color(COLOR_TOTAL_MID, COLOR_TOTAL_HIGH, factor)
        else:
            return COLOR_TOTAL_HIGH  # Rojo


    def update_display(_event=None):
        top_sel = top_var.get()
        bot_sel = bottom_var.get()
        top_item = tops_dict.get(top_sel)
        bot_item = bottoms_dict.get(bot_sel)

        total = 0
        parts = []

        # Update labels and calculate total with minimum pricing for tipo-2 items
        original_top_price = 0
        original_bot_price = 0
        top_price = 0
        if top_item:
            original_top_price = top_item['precio']
            top_price = original_top_price
            parts.append(
                f"Top: {top_item['nombre']} ({top_item['categoria']}) - {top_item['precio']}")
            top_info_label.config(text=f"{top_item['precio']}" if show_prices_var.get() else '')
        else:
            top_info_label.config(text='')

        bot_price = 0
        if bot_item:
            original_bot_price = bot_item['precio']
            bot_price = original_bot_price
            parts.append(
                f"Bottom: {bot_item['nombre']} ({bot_item['categoria']}) - {bot_item['precio']}")
            bottom_info_label.config(text=f"{bot_item['precio']}" if show_prices_var.get() else '')
        else:
            bottom_info_label.config(text='')

        # Apply minimum pricing for tipo-2 items
        if top_item and top_item.get('tipo') == 2:
            # TOP is tipo 2: consider its price in BOTTOM CSV
            bottom_version = bottoms_dict.get(top_item['nombre'])
            if bottom_version and bot_item:
                # Choose minimum between bottom_version and selected bottom item
                bot_price = min(bot_price, bottom_version['precio'])

        if bot_item and bot_item.get('tipo') == 2:
            # BOTTOM is tipo 2: consider its price in TOP CSV
            top_version = tops_dict.get(bot_item['nombre'])
            if top_version and top_item:
                # Choose minimum between top_version and selected top item
                top_price = min(top_price, top_version['precio'])

        total = top_price + bot_price
        # Display tipo-2 (duplicate) items: show their prices in the corresponding position
        if top_item and top_item.get('tipo') == 2 and bot_item and bot_item.get('tipo') == 2:
            # Both are tipo 2 and different: show each other's prices cross-referenced
            if top_item['nombre'] != bot_item['nombre']:
                # Show BOTTOM's tipo 2 price searched in TOP CSV
                bot_in_top = tops_dict.get(bot_item['nombre'])
                top_dup = f"{bot_in_top['precio']}" if bot_in_top else ''
                # Show TOP's tipo 2 price searched in BOTTOM CSV
                top_in_bot = bottoms_dict.get(top_item['nombre'])
                bottom_dup = f"{top_in_bot['precio']}" if top_in_bot else ''
            else:
                # Same item selected in both (shouldn't show duplicates)
                top_dup = ''
                bottom_dup = ''
        elif top_item and top_item.get('tipo') == 2:
            # Only TOP is tipo 2: show its price in both positions
            top_dup = f"{top_item['precio']}"
            bottom_version = bottoms_dict.get(top_item['nombre'])
            bottom_dup = f"{bottom_version['precio']}" if bottom_version else ''
        elif bot_item and bot_item.get('tipo') == 2:
            # Only BOTTOM is tipo 2: show its price in both positions
            top_version = tops_dict.get(bot_item['nombre'])
            top_dup = f"{top_version['precio']}" if top_version else ''
            bottom_dup = f"{bot_item['precio']}"
        else:
            # Neither is tipo 2
            top_dup = ''
            bottom_dup = ''

        top_dup_label.config(text=top_dup if show_prices_var.get() else '')
        bottom_dup_label.config(text=bottom_dup if show_prices_var.get() else '')

        # Update price display with appropriate color
        price_display.config(text=str(int(total)), fg=color_for_total(total))

        # Update price bar (0-1500 scale) with color gradient
        price_bar['value'] = price_to_logarithmic_scale(total)  # Escala logarítmica
        # Get the appropriate bar color based on price
        bar_color = get_bar_color(total)
        # Create or update style with the interpolated color
        style.configure('Dynamic.Vertical.TProgressbar', background=bar_color)
        price_bar.config(style='Dynamic.Vertical.TProgressbar')

        # Update item name labels below total
        # Tipo 2 items appear in both lines, but avoid duplicates if same item is selected
        top_str = top_sel
        bottom_str = bot_sel

        # Build display for each label
        # Top label: always shows TOP, plus BOTTOM if it's tipo 2 and different from TOP
        display_top = top_str
        if bot_item and bot_item.get(
            'tipo') == 2 and bot_item['nombre'] != (top_item['nombre'] if top_item else ''):
            display_top = f"{top_str}\n{bottom_str}"

        # Bottom label: always shows BOTTOM, plus TOP if it's tipo 2 and different from BOTTOM
        display_bottom = bottom_str
        if top_item and top_item.get(
            'tipo') == 2 and top_item['nombre'] != (bot_item['nombre'] if bot_item else ''):
            display_bottom = f"{bottom_str}\n{top_str}"

        top_name_label.config(text=display_top)
        bottom_name_label.config(text=display_bottom)

        # Mostrar calificación de la combinación al lado del precio
        combination_rating = get_combination_rating(ratings_data, top_str, bottom_str)
        rating_label_text, rating_color = RATING_LABELS[combination_rating]
        combination_rating_label.config(text=rating_label_text, fg=rating_color)

        # Update details with explanation of price alternatives
        # Calculate what the maximum could be considering tipo-2 alternatives
        max_possible_top = original_top_price if top_item else 0
        max_possible_bot = original_bot_price if bot_item else 0

        # If top is tipo 2, check if it could be used for bottom at different price
        if top_item and top_item.get('tipo') == 2:
            bot_ver = bottoms_dict.get(top_item['nombre'])
            if bot_ver:
                max_possible_bot = max(max_possible_bot, bot_ver['precio'])

        # If bottom is tipo 2, check if it could be used for top at different price
        if bot_item and bot_item.get('tipo') == 2:
            top_ver = tops_dict.get(bot_item['nombre'])
            if top_ver:
                max_possible_top = max(max_possible_top, top_ver['precio'])

        max_possible = max_possible_top + max_possible_bot
        explanation = ''

        if max_possible > total:
            # Check if top item could replace bottom (exists in bottom CSV)
            if top_item and top_item.get('tipo') == 2:
                bot_ver = bottoms_dict.get(top_item['nombre'])
                if bot_ver and bot_item:
                    explanation = (f"{top_item['nombre']} could replace {bot_item['nombre']} for"
                                   f" {bot_ver['precio']} instead of {original_bot_price}.")

            # Check if bottom item could replace top (exists in top CSV)
            if not explanation and bot_item and bot_item.get('tipo') == 2:
                top_ver = tops_dict.get(bot_item['nombre'])
                if top_ver and top_item:
                    explanation = (f"{bot_item['nombre']} could replace {top_item['nombre']} for"
                                   f" {top_ver['precio']} instead of {original_top_price}.")

        details_label.config(text=explanation if explanation else '')

        # Show maximum possible price if it's higher than current total
        if max_possible > total:
            max_price_label.config(text=f"Maximum possible price: {int(max_possible)}")
        else:
            max_price_label.config(text='')

    # Create the checkbox AFTER update_display is defined
    prices_checkbox = tk.Checkbutton(sel_frame, text='Prices', variable=show_prices_var,
                                     bg=root_bg, font=('Segoe UI', 8),
                                     command=update_display)
    prices_checkbox.grid(row=0, column=4, rowspan=2, sticky=tk.NS, padx=(8, 0), pady=6)

    top_combo.bind('<<ComboboxSelected>>', update_display)
    bottom_combo.bind('<<ComboboxSelected>>', update_display)

    # Vincular cambios en los comboboxes para re-habilitar el botón de opciones avanzadas
    top_var.trace('w', on_selection_changed)
    bottom_var.trace('w', on_selection_changed)

    # initial update
    update_display()

    root.mainloop()


if __name__ == '__main__':
    main()
