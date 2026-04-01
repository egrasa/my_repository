""" Simple GUI to calculate outfit price based on CSV files. """

import random
import tkinter as tk
import tkinter.font as tkfont
from collections import Counter
from tkinter import messagebox, ttk
from typing import Optional

from app_constants import (
    COLOR_DUP_TEXT,
    COLOR_TOTAL_HIGH,
    COLOR_TOTAL_LOW,
    COLOR_TOTAL_MID,
    DEFAULT_BOTTOM_ITEMS,
    DEFAULT_TOP_ITEMS,
    FOOTER_PANEL_HEIGHT,
    FONT_DUP,
    FONT_INFO,
    FONT_LABEL,
    FONT_NAME,
    FONT_TOTAL,
    HERO_PANEL_HEIGHT,
    ITEM_NAMES_PANEL_HEIGHT,
    QUICK_NOTES_HEIGHT,
    RATING_LABELS,
    SELECTOR_PANEL_HEIGHT,
    THEMES,
    TOTAL_METRIC_CARD_HEIGHT,
    TOTAL_METRIC_CARD_WIDTH,
    TOTAL_PANEL_HEIGHT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from item_store import get_runtime_base_dir, load_items, make_csv_if_missing
from permissions import PERMISSIONS, filter_items_by_permissions
from pricing import (
    apply_price_multiplier_to_details,
    build_lookup,
    calculate_combination_details,
    color_for_total,
    get_bar_color,
    price_to_logarithmic_scale,
    round_price_to_step,
)
from ratings_store import get_combination_rating, load_ratings, set_combination_rating
from search_utils import fuzzy_search
from statistics_utils import calculate_statistics

from matplotlib.patches import Patch
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('TkAgg')
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class ToolTip:
    """Small tooltip helper for Tk widgets."""

    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind('<Enter>', self.show_tooltip, add='+')
        widget.bind('<Leave>', self.hide_tooltip, add='+')
        widget.bind('<ButtonPress>', self.hide_tooltip, add='+')

    def show_tooltip(self, _event=None):
        """ Show tooltip near the widget.
        If tooltip already exists or text is empty, do nothing."""
        if self.tooltip_window is not None or not self.text:
            return
        x_pos = self.widget.winfo_rootx() + 12
        y_pos = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f'+{x_pos}+{y_pos}')

        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify=tk.LEFT,
            bg='#FFF8D9',
            fg='#2A2A2A',
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=5,
            wraplength=240,
            font=('Segoe UI', 9),
        )
        label.pack()

    def hide_tooltip(self, _event=None):
        """ Destroy tooltip if it exists."""
        if self.tooltip_window is not None:
            self.tooltip_window.destroy()
            self.tooltip_window = None


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

def show_statistics_window(root, all_items: list, ratings: Optional[dict] = None):
    """Mostrar ventana con estadísticas."""
    stats = calculate_statistics(all_items, ratings)

    if not stats:
        messagebox.showinfo("Estadísticas", "No hay items para analizar.")
        return

    stat_window = tk.Toplevel(root)
    stat_window.title("Estadísticas")
    stat_window.geometry("450x500")

    text_widget = tk.Text(stat_window, wrap=tk.WORD, font=('Courier', 10))
    text_widget.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

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
    stats_text += f"  ⭐ Favorite:      {stats['rating_counts']['favorite']}\n"
    stats_text += f"  ✓ Normal:         {stats['rating_counts']['normal']}\n"
    stats_text += f"  ◆ Not common:     {stats['rating_counts']['rare']}\n"
    stats_text += f"  ✗ Incompatible:   {stats['rating_counts']['incompatible']}\n"

    text_widget.insert("1.0", stats_text)
    text_widget.config(state=tk.DISABLED)

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
    stat_window.geometry("1200x600")

    # Frame principal
    main_frame = tk.Frame(stat_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    rating_info = [
        ('favorite', '⭐\nFavorite', '#4A9EFF'),
        ('normal', '✓\nNormal', '#4CAF50'),
        ('rare', '◆\nNot common', '#FF9800'),
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

def show_graphics_window(_root, all_items: list, ratings: Optional[dict] = None):
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
                                  allowed_ratings: Optional[list] = None,
                                  price_multiplier_pct: float = 100.0):
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
                    combo_details = calculate_combination_details(
                        top_item,
                        bottom_item,
                        tops_dict,
                        bottoms_dict,
                    )
                    adjusted_details = apply_price_multiplier_to_details(
                        combo_details,
                        price_multiplier_pct,
                    )
                    prices.append(round_price_to_step(adjusted_details['total']))
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

    # Leyenda fuera del gráfico, a la derecha
    legend_elements = [
        Patch(facecolor='#4A9EFF', edgecolor='black', label='Favorito'),
        Patch(facecolor='#4CAF50', edgecolor='black', label='Normal'),
        Patch(facecolor='#FF9800', edgecolor='black', label='Raro'),
        Patch(facecolor='#f44336', edgecolor='black', label='Incompatible'),
    ]

    ax.legend(
        handles=legend_elements,
        loc='upper left',
        bbox_to_anchor=(1.02, 1.0),
        fontsize=10,
        framealpha=0.6,
        borderaxespad=0,
    )

    # Agregar anotación sobre los tamaños
    if prices:
        min_price = min(prices)
        max_price = max(prices)
        #ax.text(0.98, 0.02,
                #f'combinación\nRango: ${int(min_price)} - ${int(max_price)}',
               #transform=ax.transAxes, fontsize=9, verticalalignment='bottom',
               #horizontalalignment='right', bbox=dict(boxstyle='round',
                                                      #facecolor='wheat', alpha=0.8))

    plt.tight_layout(rect=(0, 0, 1, 1))
    plt.show()

def show_prices_by_combination_graph(_root, ratings: dict, tops: list, bottoms: list,
                                     allowed_ratings: Optional[list] = None,
                                     price_multiplier_pct: float = 100.0):
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
                combo_details = calculate_combination_details(
                    top_item,
                    bottom_item,
                    tops_dict,
                    bottoms_dict,
                )
                adjusted_details = apply_price_multiplier_to_details(
                    combo_details,
                    price_multiplier_pct,
                )
                total_price = round_price_to_step(adjusted_details['total'])
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
        Patch(facecolor='#4A9EFF', edgecolor='black', label='Favorite'),
        Patch(facecolor='#4CAF50', edgecolor='black', label='Normal'),
        Patch(facecolor='#FF9800', edgecolor='black', label='Rare'),
        Patch(facecolor='#f44336', edgecolor='black', label='Incompatible')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10, framealpha=0.95)

    plt.tight_layout()
    plt.show()

class AdvancedOptionsWindow:
    """Ventana con opciones avanzadas: búsqueda, estadísticas, gráficos y ratings."""
    def __init__(self, parent, tops: list, bottoms: list, top_var=None, bottom_var=None,
                 top_combo=None, bottom_combo=None, show_prices_var=None,
                 on_display_change=None, price_multiplier_var=None,
                 price_multiplier_enabled_var=None, main_item_names_provider=None,
                 outfit_preset_var=None, on_preset_change=None):
        self.tops = tops
        self.bottoms = bottoms
        self.all_items = tops + bottoms
        self.ratings = load_ratings()
        self.show_prices_var = show_prices_var
        self.on_display_change = on_display_change
        self.price_multiplier_var = price_multiplier_var
        self.price_multiplier_enabled_var = price_multiplier_enabled_var
        self.main_item_names_provider = main_item_names_provider
        self.outfit_preset_var = outfit_preset_var
        self.on_preset_change = on_preset_change

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

        # Variables de permisos sincronizadas con el estado actual de la sesión.
        self.naked_options_permitted = tk.BooleanVar(value=PERMISSIONS.get('naked_options', False))
        self.statistics_permitted = tk.BooleanVar(value=PERMISSIONS.get('statistics', False))
        self.graphics_permitted = tk.BooleanVar(value=PERMISSIONS.get('graphics', False))
        self.califications_permitted = tk.BooleanVar(value=PERMISSIONS.get('califications', False))
        self.price_multiplier_permitted = tk.BooleanVar(
            value=PERMISSIONS.get('price_multiplier', False)
        )
        self.top_trace_id = None
        self.bottom_trace_id = None

        self.window = tk.Toplevel(parent)
        self.window.title("Advanced Options")
        self.window.geometry("700x600")
        self.window.protocol('WM_DELETE_WINDOW', self.on_close)

        # Crear notebook con pestañas
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # PESTAÑA 1: Búsqueda
        search_frame_main = tk.Frame(self.notebook)
        self.notebook.add(search_frame_main, text="🔍 Búsqueda")

        search_frame = ttk.LabelFrame(search_frame_main, text="Buscador Inteligente",
                          padding=10, style='Panel.TLabelframe')
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(search_frame, text="Buscar item:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', self.on_search_change)

        search_btn = ttk.Button(search_frame, text="Buscar", command=self.perform_search,
                    style='Primary.TButton')
        search_btn.pack(side=tk.LEFT, padx=5)

        # Frame para resultados de búsqueda
        results_frame = ttk.LabelFrame(search_frame_main, text="Resultados",
                           padding=10, style='Panel.TLabelframe')
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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

        stats_btn = ttk.Button(stats_buttons_frame, text="Ver Estadísticas Generales",
                       command=self.show_stats, style='Success.TButton')
        stats_btn.pack(side=tk.LEFT, padx=5)

        rating_stats_btn = ttk.Button(stats_buttons_frame,
                                      text="Ver Estadísticas de Calificaciones",
                                      command=self.show_rating_statistics,
                                      style='Info.TButton')
        rating_stats_btn.pack(side=tk.LEFT, padx=5)

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
        buttons_frame.pack(pady=5)

        graphics_btn = ttk.Button(buttons_frame, text="Ver Gráficos Generales",
                      command=self.show_graphics, style='Info.TButton')
        graphics_btn.pack(side=tk.LEFT, padx=5)

        rated_btn = ttk.Button(buttons_frame, text="Ver Combinaciones Calificadas",
                       command=self.show_rated_combinations,
                       style='Warning.TButton')
        rated_btn.pack(side=tk.LEFT, padx=5)

        prices_btn = ttk.Button(buttons_frame, text="Ver Precios por Combinación",
                    command=self.show_prices_by_combination,
                    style='Danger.TButton')
        prices_btn.pack(side=tk.LEFT, padx=5)

        # Guardar referencias a los botones para habilitar/deshabilitar
        self.graphics_btn = graphics_btn
        self.rated_btn = rated_btn
        self.prices_btn = prices_btn

        # Inicializar estado de botones de gráficos
        self.update_graph_buttons_state()

        # Frame para checkbuttons de categorías
        filter_frame = ttk.LabelFrame(graphics_frame_main, text="Filtrar por Categoría",
                          padding=10, style='Panel.TLabelframe')
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Crear checkbuttons para cada categoría
        self.favorite_check = ttk.Checkbutton(filter_frame, text="Favorito",
                              variable=self.show_favorite_var,
                              command=self.update_graph_buttons_state,
                              style='Subtle.TCheckbutton')
        self.favorite_check.pack(side=tk.LEFT, padx=5)

        self.normal_check = ttk.Checkbutton(filter_frame, text="Normal",
                            variable=self.show_normal_var,
                            command=self.update_graph_buttons_state,
                            style='Subtle.TCheckbutton')
        self.normal_check.pack(side=tk.LEFT, padx=5)

        self.rare_check = ttk.Checkbutton(filter_frame, text="Raro",
                          variable=self.show_rare_var,
                          command=self.update_graph_buttons_state,
                          style='Subtle.TCheckbutton')
        self.rare_check.pack(side=tk.LEFT, padx=5)

        self.incompatible_check = ttk.Checkbutton(filter_frame, text="Incompatible",
                              variable=self.show_incompatible_var,
                              command=self.update_graph_buttons_state,
                              style='Subtle.TCheckbutton')
        self.incompatible_check.pack(side=tk.LEFT, padx=5)

        # Inicializar estado de botones
        self.update_graph_buttons_state()

        self.panel_background = ttk.Style(self.window).lookup('Panel.TLabelframe', 'background')
        if not self.panel_background:
            self.panel_background = THEMES['light']['frame']

        if self.price_multiplier_enabled_var is None:
            self.price_multiplier_enabled_var = tk.BooleanVar(
                value=PERMISSIONS.get('price_multiplier', False)
            )
        if self.price_multiplier_var is None:
            self.price_multiplier_var = tk.StringVar(value='100')

        multiplier_var = self.price_multiplier_var

        # PESTAÑA 5: Multiplicador
        multiplier_tab = tk.Frame(self.notebook)
        self.notebook.add(multiplier_tab, text="📐 Multiplicador")

        multiplier_panel = ttk.LabelFrame(
            multiplier_tab,
            text="Ajuste del Factor Multiplicador",
            padding=15,
            style='Panel.TLabelframe',
        )
        multiplier_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        multiplier_intro = tk.Label(
            multiplier_panel,
            text=(
                "Modifica el porcentaje aplicado a los precios mostrados. "
                "La autorización para usarlo se mantiene en la pestaña Permisos."
            ),
            font=('Segoe UI', 10),
            bg=self.panel_background,
            justify=tk.LEFT,
            wraplength=540,
        )
        multiplier_intro.pack(anchor=tk.W, pady=(0, 12))

        multiplier_controls = tk.Frame(multiplier_panel, bg=self.panel_background)
        multiplier_controls.pack(anchor=tk.CENTER, pady=(6, 8))

        self.multiplier_up_btn = ttk.Button(
            multiplier_controls,
            text='▲ 5%',
            command=lambda: self.adjust_multiplier(5),
            style='Secondary.TButton',
            state=tk.DISABLED,
        )
        self.multiplier_up_btn.pack(pady=(0, 8))

        entry_row = tk.Frame(multiplier_controls, bg=self.panel_background)
        entry_row.pack()

        self.multiplier_entry = tk.Entry(entry_row, textvariable=multiplier_var,
                                         width=8, font=('Segoe UI', 10), justify=tk.CENTER,
                                         state=tk.DISABLED)
        self.multiplier_entry.pack(side=tk.LEFT)
        self.multiplier_entry.bind('<Return>', self.on_multiplier_entry_commit)
        self.multiplier_entry.bind('<FocusOut>', self.on_multiplier_entry_commit)

        tk.Label(entry_row, text="%", bg=self.panel_background,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(6, 0))

        self.multiplier_down_btn = ttk.Button(
            multiplier_controls,
            text='▼ 5%',
            command=lambda: self.adjust_multiplier(-5),
            style='Secondary.TButton',
            state=tk.DISABLED,
        )
        self.multiplier_down_btn.pack(pady=(8, 0))

        self.multiplier_help_label = tk.Label(
            multiplier_panel,
            text=(
                "Por defecto 100%. Activa el permiso del factor multiplicador en la pestaña "
                "Permisos para poder editar este valor."
            ),
            font=('Segoe UI', 9, 'italic'),
            fg='#7a7a7a',
            bg=self.panel_background,
            justify=tk.LEFT,
            wraplength=520,
        )
        self.multiplier_help_label.pack(anchor=tk.W, pady=(8, 0))

        preset_panel = ttk.LabelFrame(
            multiplier_panel,
            text="Ajustes predefinidos",
            padding=10,
            style='Panel.TLabelframe',
        )
        preset_panel.pack(fill=tk.X, pady=(14, 0))

        preset_intro = tk.Label(
            preset_panel,
            text=(
                "Selecciona un modo para aplicar automáticamente el factor y las reglas "
                "especiales del selector principal."
            ),
            font=('Segoe UI', 9),
            bg=self.panel_background,
            justify=tk.LEFT,
            wraplength=520,
        )
        preset_intro.pack(anchor=tk.W, pady=(0, 8))

        if self.outfit_preset_var is None:
            self.outfit_preset_var = tk.StringVar(value='yoga')

        preset_options = [
            ('Dance', 'dance'),
            ('Sexy Dance', 'sexy_dance'),
            ('Yoga', 'yoga'),
            ('Adv Yoga', 'adv_yoga'),
            ('Crazy', 'crazy'),
        ]
        preset_change_handler = self.on_preset_change or (lambda _preset: None)

        for label, value in preset_options:
            preset_radio = ttk.Radiobutton(
                preset_panel,
                text=label,
                value=value,
                variable=self.outfit_preset_var,
                command=lambda preset_value=value: preset_change_handler(preset_value),
                style='Subtle.TRadiobutton',
            )
            preset_radio.pack(anchor=tk.W, pady=2)

        # PESTAÑA 6: Permisos
        permissions_frame_main = tk.Frame(self.notebook)
        self.notebook.add(permissions_frame_main, text="🔐 Permisos")

        permissions_frame = ttk.LabelFrame(permissions_frame_main,
                           text="Controlar Acceso a Funciones",
                           padding=15, style='Panel.TLabelframe')
        permissions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        display_frame = ttk.LabelFrame(permissions_frame, text="Display",
                           padding=10, style='Panel.TLabelframe')
        display_frame.pack(anchor=tk.W, fill=tk.X, padx=20, pady=(0, 6))

        if self.show_prices_var is not None:
            self.show_prices_check = ttk.Checkbutton(
                display_frame,
                text="Show individual prices",
                variable=self.show_prices_var,
                command=self.on_display_change or (lambda: None),
                style='Subtle.TCheckbutton',
            )
            self.show_prices_check.pack(anchor=tk.W)

        self.price_multiplier_check = ttk.Checkbutton(
            display_frame,
            text="Permitir variar el factor multiplicador",
            variable=self.price_multiplier_enabled_var,
            command=self.on_multiplier_permission_changed,
            style='Subtle.TCheckbutton',
            state=tk.DISABLED,
        )
        self.price_multiplier_check.pack(anchor=tk.W, pady=(4, 0))

        self.naked_check = ttk.Checkbutton(
            display_frame,
            text="Permitir opciones plus",
            variable=self.naked_options_permitted,
            command=self.on_permissions_changed,
            style='Subtle.TCheckbutton',
        )
        self.naked_check.pack(anchor=tk.W, pady=(4, 0))

        # SECCIÓN 1: Autenticación por contraseña (siempre rechaza)
        auth_frame = ttk.LabelFrame(permissions_frame, text="Autenticación de Permisos",
                        padding=10, style='Panel.TLabelframe')
        auth_frame.pack(anchor=tk.W, fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(auth_frame, text="Contraseña (10 dígitos):",
             font=('Segoe UI', 9), bg=self.panel_background).pack(anchor=tk.W, pady=(0, 5))

        password_input_frame = tk.Frame(auth_frame, bg=self.panel_background)
        password_input_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))

        self.password_var = tk.StringVar()
        password_entry = tk.Entry(password_input_frame, textvariable=self.password_var,
                                  show="•", width=20, font=('Segoe UI', 10))
        password_entry.pack(side=tk.LEFT, padx=(0, 10))

        verify_btn = ttk.Button(password_input_frame, text="Ver Acceso",
                    command=self.verify_password, style='Danger.TButton')
        verify_btn.pack(side=tk.LEFT)

        # Label de instrucción antigua (ahora es para el método glitter)
        instruction_label = tk.Label(permissions_frame,
                                     text="Selecciona 'X' para desbloquear los permisos",
                                     font=('Segoe UI', 9, 'italic'),
                                     fg='#2196F3', bg=self.panel_background)
        instruction_label.pack(anchor=tk.W, padx=20, pady=(2, 5), fill=tk.X)

        # Checkbutton para Statistics
        self.stats_check = ttk.Checkbutton(permissions_frame, text="Permitir Estadísticas",
                           variable=self.statistics_permitted,
                           command=self.on_permissions_changed,
                           style='Subtle.TCheckbutton', state=tk.DISABLED)
        self.stats_check.pack(anchor=tk.W, padx=20, pady=5, fill=tk.X)

        # Checkbutton para Graphics
        self.graphics_check = ttk.Checkbutton(permissions_frame, text="Permitir Gráficos",
                              variable=self.graphics_permitted,
                              command=self.on_permissions_changed,
                              style='Subtle.TCheckbutton', state=tk.DISABLED)
        self.graphics_check.pack(anchor=tk.W, padx=20, pady=5, fill=tk.X)

        # Checkbutton para Califications
        self.calif_check = ttk.Checkbutton(permissions_frame, text="Permitir Calificaciones",
                           variable=self.califications_permitted,
                           command=self.on_permissions_changed,
                           style='Subtle.TCheckbutton', state=tk.DISABLED)
        self.calif_check.pack(anchor=tk.W, padx=20, pady=5, fill=tk.X)

        # Vincular verificación de permisos a los comboboxes si están disponibles
        if self.top_var and self.bottom_var:
            self.top_trace_id = self.top_var.trace_add('write', self.verify_permissions)
            self.bottom_trace_id = self.bottom_var.trace_add('write', self.verify_permissions)

        self.update_multiplier_controls_state()
        self.verify_permissions()

    def on_close(self):
        """Cerrar la ventana liberando los traces de las variables compartidas."""
        if self.top_var is not None and self.top_trace_id is not None:
            self.top_var.trace_remove('write', self.top_trace_id)
            self.top_trace_id = None
        if self.bottom_var is not None and self.bottom_trace_id is not None:
            self.bottom_var.trace_remove('write', self.bottom_trace_id)
            self.bottom_trace_id = None
        self.window.destroy()

    def create_ratings_tab(self, parent):
        """Crear pestaña de calificaciones."""
        # Frame para selección de combinación
        combo_frame = ttk.LabelFrame(parent, text="Seleccionar Combinación",
                         padding=10, style='Panel.TLabelframe')
        combo_frame.pack(fill=tk.X, padx=5, pady=5)

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

        current_rating_frame = ttk.LabelFrame(parent, text="Calificación actual",
                              padding=10, style='Panel.TLabelframe')
        current_rating_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.current_rating_status_var = tk.StringVar(value='Unrated')
        self.current_rating_status_label = tk.Label(
            current_rating_frame,
            textvariable=self.current_rating_status_var,
            font=('Segoe UI', 10, 'bold'),
            anchor='w',
            justify=tk.LEFT,
        )
        self.current_rating_status_label.pack(anchor=tk.W)

        self.rating_top_combo.bind('<<ComboboxSelected>>', self.on_rating_selection_changed)
        self.rating_bottom_combo.bind('<<ComboboxSelected>>', self.on_rating_selection_changed)

        # Frame para calificaciones
        rating_frame = ttk.LabelFrame(parent, text="Calificación",
                          padding=10, style='Panel.TLabelframe')
        rating_frame.pack(fill=tk.X, padx=5, pady=5)

        self.rating_var = tk.StringVar(value='unrated')

        ratings_options = [
            ('⭐ Favorite', 'favorite'),
            ('✓ Normal', 'normal'),
            ('◆ Not common', 'rare'),
            ('✗ Incompatible', 'incompatible'),
            ('Unrated', 'unrated'),
        ]

        for label, value in ratings_options:
            rb = ttk.Radiobutton(rating_frame, text=label, variable=self.rating_var,
                                 value=value, style='Subtle.TRadiobutton')
            rb.pack(anchor=tk.W, pady=3)

        # Botones
        button_frame = tk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        save_btn = ttk.Button(button_frame, text="💾 Guardar Calificación",
                      command=self.save_rating, style='Success.TButton')
        save_btn.pack(side=tk.LEFT, padx=5)

        load_btn = ttk.Button(button_frame, text="🔄 Cargar",
                      command=self.load_rating, style='Info.TButton')
        load_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_current_rating_status()

    def refresh_current_rating_status(self):
        """Actualizar el label con la calificación guardada de la combinación seleccionada."""
        if not hasattr(self, 'rating_top_var') or not hasattr(self, 'rating_bottom_var'):
            return

        top = self.rating_top_var.get()
        bottom = self.rating_bottom_var.get()

        if not top or not bottom:
            self.current_rating_status_var.set('Unrated')
            return

        rating = get_combination_rating(self.ratings, top, bottom)
        label_text, _ = RATING_LABELS.get(rating, ('Unrated', '#cccccc'))
        self.current_rating_status_var.set(label_text if label_text else 'Unrated')

    def on_rating_selection_changed(self, _event=None):
        """Refrescar la calificación visible al cambiar la combinación seleccionada."""
        self.refresh_current_rating_status()

    def load_rating(self):
        """Cargar la calificación de la combinación seleccionada."""
        top = self.rating_top_var.get()
        bottom = self.rating_bottom_var.get()
        if not top or not bottom:
            messagebox.showwarning("Advertencia", "Selecciona top y bottom.")
            return

        rating = get_combination_rating(self.ratings, top, bottom)
        self.rating_var.set(rating)
        self.refresh_current_rating_status()

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
        self.refresh_current_rating_status()
        label_text, _ = RATING_LABELS[rating]
        messagebox.askokcancel("Guardado", f"Combinación guardada como: {label_text}")

    def verify_permissions(self, *args):
        """Verificar si glitter bra y glitter panties están seleccionados."""
        _ = args
        if not self.top_var or not self.bottom_var:
            return

        # Verificar si los checkbuttons protegidos aún existen
        if not self.stats_check.winfo_exists():
            return

        top_selected = self.top_var.get()
        bottom_selected = self.bottom_var.get()
        protected_combo_unlocked = (
            top_selected == 'glitter bra' and bottom_selected == 'glitter panties'
        )

        self.stats_check.config(
            state=tk.NORMAL if protected_combo_unlocked or self.statistics_permitted.get()
            else tk.DISABLED
        )
        self.graphics_check.config(
            state=tk.NORMAL if protected_combo_unlocked or self.graphics_permitted.get()
            else tk.DISABLED
        )
        self.calif_check.config(
            state=tk.NORMAL if protected_combo_unlocked or self.califications_permitted.get()
            else tk.DISABLED
        )
        multiplier_active = (
            self.price_multiplier_enabled_var.get()
            if self.price_multiplier_enabled_var is not None
            else False
        )
        self.price_multiplier_check.config(
            state=tk.NORMAL if protected_combo_unlocked or multiplier_active else tk.DISABLED
        )
        self.update_multiplier_controls_state()

    def on_permissions_changed(self):
        """Actualizar PERMISSIONS cuando cambia el estado de cualquier checkbox de permisos."""
        PERMISSIONS['naked_options'] = self.naked_options_permitted.get()
        PERMISSIONS['statistics'] = self.statistics_permitted.get()
        PERMISSIONS['graphics'] = self.graphics_permitted.get()
        PERMISSIONS['califications'] = self.califications_permitted.get()
        PERMISSIONS['price_multiplier'] = (
            self.price_multiplier_enabled_var.get()
            if self.price_multiplier_enabled_var is not None
            else False
        )

        # Actualizar estado de botones según permisos
        self.update_statistics_buttons_state()
        self.update_graph_buttons_state()

        # Actualizar los comboboxes de la ventana principal si están disponibles
        self.update_main_window_combos()
        self.verify_permissions()

    def get_price_multiplier_percentage(self) -> float:
        """Return the currently active percentage multiplier."""
        if self.price_multiplier_var is None:
            return 100.0
        try:
            value = float(self.price_multiplier_var.get().replace(',', '.'))
        except (AttributeError, ValueError):
            return 100.0
        return max(0.0, value)

    def update_multiplier_controls_state(self):
        """Enable or disable multiplier editing controls based on permission state."""
        assert self.price_multiplier_enabled_var is not None
        can_edit = (
            self.price_multiplier_check.instate(('!disabled',))
            and self.price_multiplier_enabled_var.get()
        )
        entry_state = tk.NORMAL if can_edit else tk.DISABLED
        button_state = tk.NORMAL if can_edit else tk.DISABLED
        self.multiplier_entry.config(state=entry_state)
        self.multiplier_down_btn.config(state=button_state)
        self.multiplier_up_btn.config(state=button_state)
        if self.on_display_change:
            self.on_display_change()

    def on_multiplier_permission_changed(self):
        """Sync multiplier permission and refresh dependent UI."""
        assert self.price_multiplier_enabled_var is not None
        PERMISSIONS['price_multiplier'] = self.price_multiplier_enabled_var.get()
        self.verify_permissions()
        self.update_multiplier_controls_state()

    def on_multiplier_entry_commit(self, _event=None):
        """Validate and apply a manually entered multiplier percentage."""
        assert self.price_multiplier_var is not None
        try:
            value = float(self.price_multiplier_var.get().replace(',', '.'))
        except ValueError:
            self.price_multiplier_var.set('100')
            value = 100.0

        normalized = max(0.0, value)
        self.price_multiplier_var.set(f'{normalized:.0f}' if normalized.is_integer(
            ) else f'{normalized:.2f}')
        if self.on_display_change:
            self.on_display_change()

    def adjust_multiplier(self, delta: float):
        """Adjust the multiplier percentage in 5% steps."""
        assert self.price_multiplier_var is not None
        value = self.get_price_multiplier_percentage() + delta
        value = max(0.0, value)
        self.price_multiplier_var.set(f'{value:.0f}' if value.is_integer() else f'{value:.2f}')
        if self.on_display_change:
            self.on_display_change()

    def update_main_window_combos(self):
        """Actualizar los valores de los comboboxes de la ventana principal
        cuando cambian los permisos."""
        if not self.top_combo or not self.bottom_combo or not self.top_var or not self.bottom_var:
            return

        if self.main_item_names_provider is not None:
            new_top_names, new_bottom_names = self.main_item_names_provider()
        else:
            new_top_names = [t['nombre'] for t in filter_items_by_permissions(self.tops)]
            new_bottom_names = [b['nombre'] for b in filter_items_by_permissions(self.bottoms)]

        rating_top_names = [t['nombre'] for t in filter_items_by_permissions(self.tops)]
        rating_bottom_names = [b['nombre'] for b in filter_items_by_permissions(self.bottoms)]

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

                self.rating_top_combo['values'] = rating_top_names
                self.rating_bottom_combo['values'] = rating_bottom_names

                if current_rating_top not in rating_top_names and rating_top_names:
                    self.rating_top_var.set(rating_top_names[0])
                elif not rating_top_names:
                    self.rating_top_var.set('')

                if current_rating_bottom not in rating_bottom_names and rating_bottom_names:
                    self.rating_bottom_var.set(rating_bottom_names[0])
                elif not rating_bottom_names:
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
                                      self.bottoms, allowed_ratings,
                                      self.get_price_multiplier_percentage())

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
                                         self.bottoms, allowed_ratings,
                                         self.get_price_multiplier_percentage())

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
    base = get_runtime_base_dir()

    top_csv = f'{base}\\top_items.csv'
    bottom_csv = f'{base}\\bottom_items.csv'

    # Create CSV files with requested content if missing
    make_csv_if_missing(top_csv, DEFAULT_TOP_ITEMS)
    make_csv_if_missing(bottom_csv, DEFAULT_BOTTOM_ITEMS)

    tops = load_items(top_csv)
    bottoms = load_items(bottom_csv)

    root = tk.Tk()
    root.title('Outfit Price Calculator')
    root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
    #root.minsize(940, 820)

    style = ttk.Style()
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass

    light_theme = THEMES['light']
    dark_theme = THEMES['dark']

    # Configurar estilos personalizados para Combobox a partir de la paleta del tema
    style.configure(
        'Light.TCombobox',
        entrybackground=light_theme['combo_fill'],
        fieldbackground=light_theme['combo_fill'],
        background=light_theme['combo_shell'],
        foreground=light_theme['combo_text'],
        insertcolor=light_theme['combo_text'],
    )

    style.configure(
        'Dark.TCombobox',
        entrybackground=dark_theme['combo_fill'],
        fieldbackground=dark_theme['combo_fill'],
        background=dark_theme['combo_shell'],
        foreground=dark_theme['combo_text'],
        insertcolor=dark_theme['combo_text'],
    )

    style.configure(
        'Random.TButton',
        font=('Segoe UI', 10, 'bold'),
        padding=(22, 9),
        anchor='center',
        borderwidth=1,
        focusthickness=1,
        relief='flat',
    )

    # Configurar estilos personalizados para Progressbar con gradiente de color
    style.configure('Green.Vertical.TProgressbar', background=COLOR_TOTAL_LOW)
    style.configure('Yellow.Vertical.TProgressbar', background='#FFD700')
    style.configure('Orange.Vertical.TProgressbar', background=COLOR_TOTAL_MID)
    style.configure('Red.Vertical.TProgressbar', background=COLOR_TOTAL_HIGH)

    # Variable para guardar el tema actual
    current_theme = {'theme': 'light'}
    dashboard_total_var = tk.StringVar(value='0')
    dashboard_rating_var = tk.StringVar(value='Sin calificar')
    dashboard_max_var = tk.StringVar(value='0')
    dashboard_mode_var = tk.StringVar(value='Precios ocultos')
    dashboard_multiplier_var = tk.StringVar(value='')
    theme_state_var = tk.StringVar(value='Modo claro')

    def style_surface(widget, background, border):
        widget.config(
            bg=background,
            highlightbackground=border,
            highlightcolor=border,
            highlightthickness=1,
            bd=0,
        )

    def configure_ttk_styles(theme_colors):
        style.configure('TFrame', background=theme_colors['bg'])
        style.configure('TLabel', background=theme_colors['bg'], foreground=theme_colors['text'])

        style.configure(
            'Panel.TLabelframe',
            background=theme_colors['frame'],
            bordercolor=theme_colors['border'],
            lightcolor=theme_colors['border'],
            darkcolor=theme_colors['border'],
            relief='solid',
            borderwidth=1,
        )
        style.configure(
            'Panel.TLabelframe.Label',
            background=theme_colors['frame'],
            foreground=theme_colors['label'],
            font=('Segoe UI', 10),
        )

        style.configure(
            'Subtle.TCheckbutton',
            background=theme_colors['frame'],
            foreground=theme_colors['text'],
            indicatorcolor=theme_colors['frame_elevated'],
            padding=(4, 4),
        )
        style.map(
            'Subtle.TCheckbutton',
            background=[('active', theme_colors['frame'])],
            foreground=[('disabled', theme_colors['text_secondary'])],
            indicatorcolor=[('selected', theme_colors['accent'])],
        )

        style.configure(
            'Subtle.TRadiobutton',
            background=theme_colors['frame'],
            foreground=theme_colors['text'],
            indicatorcolor=theme_colors['frame_elevated'],
            padding=(6, 6),
        )
        style.map(
            'Subtle.TRadiobutton',
            background=[('active', theme_colors['frame'])],
            foreground=[('disabled', theme_colors['text_secondary'])],
            indicatorcolor=[('selected', theme_colors['accent'])],
        )

        button_styles = {
            'Primary.TButton': (theme_colors['button'], theme_colors['button_hover'],
                                theme_colors['button_text']),
            'Secondary.TButton': (theme_colors['bg'],
                                  theme_colors['muted_button_hover'],
                                  theme_colors['label']),
            'HeroIcon.TButton': (theme_colors['accent'], theme_colors['accent_hover'],
                                 theme_colors['hero_text']),
            'Random.TButton': (theme_colors['random_button'],
                               theme_colors['random_button_hover'],
                               theme_colors['random_button_text']),
            'Success.TButton': (theme_colors['success'], theme_colors['success_hover'], '#ffffff'),
            'Info.TButton': (theme_colors['info'], theme_colors['info_hover'],
                             '#ffffff'),
            'Warning.TButton': (theme_colors['warning'], theme_colors['warning_hover'], '#ffffff'),
            'Danger.TButton': (theme_colors['danger'], theme_colors['danger_hover'], '#ffffff'),
        }

        for style_name, (background, hover, foreground) in button_styles.items():
            style.configure(
                style_name,
                background=background,
                foreground=foreground,
                bordercolor=background,
                darkcolor=background,
                lightcolor=background,
                focuscolor=background,
                borderwidth=0,
                focusthickness=0,
                relief='flat',
                padding=(14, 8),
                font=('Segoe UI', 10, 'bold'),
            )
            style.map(
                style_name,
                background=[('active', hover), ('pressed', hover)],
                foreground=[('active', foreground), ('pressed', foreground)],
                bordercolor=[('active', hover), ('pressed', hover)],
                darkcolor=[('active', hover), ('pressed', hover)],
                lightcolor=[('active', hover), ('pressed', hover)],
            )

        style.configure('Random.TButton', padding=(22, 9), anchor='center')

    def apply_custom_theme():
        theme_colors = THEMES[current_theme['theme']]
        configure_ttk_styles(theme_colors)
        root.config(bg=theme_colors['bg'])
        frm.config(bg=theme_colors['bg'])
        main_container.config(bg=theme_colors['bg'])
        footer_frame.config(bg=theme_colors['bg'])
        bar_frame.config(bg=theme_colors['bg'])
        insights_frame.config(bg=theme_colors['bg'])

        style_surface(hero_frame, theme_colors['accent'], theme_colors['accent'])
        hero_content.config(bg=theme_colors['accent'])
        hero_actions.config(bg=theme_colors['accent'])
        actions_row.config(bg=theme_colors['accent'])
        hero_title.config(bg=theme_colors['accent'], fg=theme_colors['hero_text'])
        hero_subtitle.config(bg=theme_colors['accent'], fg=theme_colors['hero_subtext'])
        theme_chip.config(bg=theme_colors['accent'], fg=theme_colors['hero_subtext'])

        style_surface(total_frame, theme_colors['frame'], theme_colors['border'])
        total_caption_frame.config(bg=theme_colors['frame'])
        total_caption_label.config(bg=theme_colors['frame'], fg=theme_colors['text_secondary'])
        multiplier_hint_label.config(bg=theme_colors['frame'], fg=theme_colors['text_secondary'])
        total_header_frame.config(bg=theme_colors['frame'])
        metric_cards_frame.config(bg=theme_colors['frame'])
        price_rating_frame.config(bg=theme_colors['frame'])
        price_display.config(bg=theme_colors['frame'])
        combination_rating_label.config(bg=theme_colors['frame'])
        top_names_container.config(bg=theme_colors['frame'])
        bottom_names_container.config(bg=theme_colors['frame'])

        top_selector_label.config(bg=theme_colors['frame'], fg=theme_colors['label'])
        bottom_selector_label.config(bg=theme_colors['frame'], fg=theme_colors['label'])
        preset_button_frame.config(bg=theme_colors['frame'])
        refresh_preset_buttons(theme_colors)

        for info_frame in (top_info_frame, bottom_info_frame):
            info_frame.config(bg=theme_colors['frame'])
        for info_label in (top_info_label, bottom_info_label):
            info_label.config(bg=theme_colors['frame'], fg=theme_colors['text_secondary'])
        for badge in (top_price_badge, bottom_price_badge):
            badge.config(bg=theme_colors['frame'])
        for dup_label in (top_dup_label, bottom_dup_label):
            dup_label.config(bg=theme_colors['frame'], fg=theme_colors['text_secondary'])

        for label in (
            top_name_primary_label,
            top_name_secondary_label,
            bottom_name_primary_label,
            bottom_name_secondary_label,
        ):
            label.config(bg=theme_colors['frame'], fg=theme_colors['text'])

        style_surface(insights_panel, theme_colors['frame'], theme_colors['border'])
        insights_title.config(bg=theme_colors['frame'], fg=theme_colors['label'])
        details_label.config(bg=theme_colors['frame'], fg=theme_colors['text_secondary'])
        max_price_label.config(bg=theme_colors['frame'], fg=theme_colors['text'])
        quick_actions_frame.config(bg=theme_colors['frame'])

        for card in dashboard_cards:
            style_surface(card['frame'], theme_colors['frame'], theme_colors['border'])
            card['content'].config(bg=theme_colors['frame'])
            card['title'].config(bg=theme_colors['frame'], fg=theme_colors['text_secondary'])
            card['value'].config(bg=theme_colors['frame'], fg=theme_colors['text'])

        if current_theme['theme'] == 'light':
            top_combo.configure(style='Light.TCombobox')
            bottom_combo.configure(style='Light.TCombobox')
            theme_state_var.set('light theme')
        else:
            top_combo.configure(style='Dark.TCombobox')
            bottom_combo.configure(style='Dark.TCombobox')
            theme_state_var.set('dark theme')

        theme_btn.config(text='🌙' if current_theme['theme'] == 'dark' else '☀️')
        bar_max_label.config(bg=theme_colors['bg'], fg=theme_colors['text_secondary'])
        bar_min_label.config(bg=theme_colors['bg'], fg=theme_colors['text_secondary'])

    def toggle_theme():
        """Cambia entre tema claro y oscuro."""
        new_theme = 'dark' if current_theme['theme'] == 'light' else 'light'
        current_theme['theme'] = new_theme
        apply_custom_theme()
        update_display()

    configure_ttk_styles(light_theme)

    root_bg = THEMES['light']['bg']
    root.config(bg=root_bg)

    # Use tk.Frame so we can control background color consistently
    # Main container with content on left and price bar on right
    main_container = tk.Frame(root, bg=root_bg)
    main_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=5)

    footer_frame = tk.Frame(root, bg=root_bg, height=FOOTER_PANEL_HEIGHT)
    footer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=16, pady=(0, 5))
    footer_frame.pack_propagate(False)

    # Left frame for main content
    frm = tk.Frame(main_container, bg=root_bg)
    frm.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    frm.grid_columnconfigure(0, weight=1)

    # Botón de opciones avanzadas integrado en la cabecera
    price_multiplier_var = tk.StringVar(value='100')
    price_multiplier_enabled_var = tk.BooleanVar(value=False)
    outfit_preset_var = tk.StringVar(value='yoga')
    applied_preset_state = {'value': 'yoga'}
    preset_multiplier_map = {
        'dance': 50,
        'sexy_dance': 75,
        'yoga': 100,
        'adv_yoga': 125,
        'crazy': 100,
    }

    def is_crazy_mode() -> bool:
        return outfit_preset_var.get() == 'crazy'

    def is_adv_yoga_mode() -> bool:
        return outfit_preset_var.get() == 'adv_yoga'

    def get_selectable_items(items: list) -> list:
        allow_plus_items = PERMISSIONS.get('naked_options', False) or is_crazy_mode()
        filtered_items = items if allow_plus_items else [
            item for item in items if item.get('categoria', '').lower() != 'naked'
        ]
        if is_crazy_mode():
            filtered_items = [
                item for item in filtered_items if float(item.get('precio', 0)) >= 200
            ]
        elif is_adv_yoga_mode():
            filtered_items = [
                item for item in filtered_items if float(item.get('precio', 0)) >= 100
            ]
        return filtered_items

    def get_main_item_names() -> tuple[list[str], list[str]]:
        return (
            [item['nombre'] for item in get_selectable_items(tops)],
            [item['nombre'] for item in get_selectable_items(bottoms)],
        )

    def close_application_after_crazy_rejection():
        messagebox.showwarning(
            'Crazy Mode Warning',
            "That was a mistake. Pressing 'No' was the wrong choice.\n\n"
            'The application will now close completely.',
        )
        root.destroy()

    def get_active_price_multiplier_pct() -> float:
        try:
            raw_value = float(price_multiplier_var.get().replace(',', '.'))
        except ValueError:
            raw_value = 100.0
        if not price_multiplier_enabled_var.get():
            return 100.0
        return max(0.0, raw_value)

    def open_advanced_options():
        AdvancedOptionsWindow(
            root,
            tops,
            bottoms,
            top_var,
            bottom_var,
            top_combo,
            bottom_combo,
            show_prices_var,
            update_display,
            price_multiplier_var,
            price_multiplier_enabled_var,
            get_main_item_names,
            outfit_preset_var,
            request_outfit_preset_change,
        )

    # Right frame for price bar (vertical progress bar)
    bar_frame = tk.Frame(main_container, bg=root_bg, width=68)
    bar_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
    bar_frame.pack_propagate(False)

    # Label for max price
    bar_max_label = tk.Label(bar_frame, text='1500', font=('Segoe UI', 8),
                             bg=root_bg, fg='#888888')
    bar_max_label.pack(side=tk.TOP, pady=2)

    # Vertical progress bar for price visualization (100-1500 scale with logarithmic)
    price_bar = ttk.Progressbar(bar_frame, orient=tk.VERTICAL, length=360,
                                mode='determinate', maximum=100, value=0,
                                style='Green.Vertical.TProgressbar')
    price_bar.pack(fill=tk.BOTH, expand=True, pady=5)

    # Label for min price
    bar_min_label = tk.Label(bar_frame, text='50', font=('Segoe UI', 8),
                             bg=root_bg, fg='#888888')
    bar_min_label.pack(side=tk.BOTTOM, pady=2)

    hero_frame = tk.Frame(frm, padx=10, pady=10, height=HERO_PANEL_HEIGHT)
    hero_frame.grid(row=0, column=0, sticky=tk.EW, pady=(2, 3))
    hero_frame.grid_columnconfigure(0, weight=1)
    hero_frame.grid_propagate(False)

    hero_content = tk.Frame(hero_frame)
    hero_content.grid(row=0, column=0, sticky=tk.EW)

    hero_title = tk.Label(hero_content, text='Outfit Price Dashboard',
                          font=('Segoe UI Semibold', 16, 'bold'), anchor='w')
    hero_title.pack(anchor=tk.W)

    hero_subtitle = tk.Label(
        hero_content,
        text=('Select a combination and check the price,'
              ' the rating, and the maximum potential at a glance.'),
        font=('Segoe UI', 10),
        anchor='w',
        justify=tk.LEFT,
    )
    hero_subtitle.pack(anchor=tk.W, pady=(6, 0))

    hero_actions = tk.Frame(hero_frame, bg=light_theme['accent'])
    hero_actions.grid(row=0, column=1, sticky=tk.NE, padx=(16, 0))

    actions_row = tk.Frame(hero_actions, bg=light_theme['accent'])
    actions_row.pack(anchor=tk.E)

    theme_btn = ttk.Button(hero_actions, text='☀️', command=toggle_theme,
                           style='HeroIcon.TButton')
    theme_btn.pack(in_=actions_row, side=tk.LEFT, padx=(0, 8))

    theme_chip = tk.Label(
        hero_actions,
        textvariable=theme_state_var,
        font=('Segoe UI', 9, 'bold'),
        padx=12,
        pady=6,
    )
    theme_chip.pack(anchor=tk.E, pady=(10, 0))

    advanced_btn = ttk.Button(footer_frame, text='⚙️ Options',
                              command=open_advanced_options, style='Secondary.TButton')
    advanced_btn.pack(side=tk.RIGHT)

    dashboard_cards = []

    def create_dashboard_card(parent, title, value_var, accent_color, width=None, height=None):
        if width is not None and height is not None:
            card_frame = tk.Frame(parent, padx=12, pady=5, width=width, height=height)
        elif width is not None:
            card_frame = tk.Frame(parent, padx=12, pady=5, width=width)
        elif height is not None:
            card_frame = tk.Frame(parent, padx=12, pady=5, height=height)
        else:
            card_frame = tk.Frame(parent, padx=12, pady=5)
        card_frame.pack_propagate(False)
        accent = tk.Frame(card_frame, bg=accent_color, width=8)
        accent.pack(side=tk.LEFT, fill=tk.Y)

        content = tk.Frame(card_frame)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))

        title_label = tk.Label(content, text=title, font=('Segoe UI', 9, 'bold'), anchor='w')
        title_label.pack(anchor=tk.W)

        value_label = tk.Label(content, textvariable=value_var,
                               font=('Segoe UI', 12, 'bold'), anchor='w')
        value_label.pack(anchor=tk.W, pady=(4, 0))

        dashboard_cards.append({
            'frame': card_frame,
            'content': content,
            'title': title_label,
            'value': value_label,
        })
        return card_frame, value_label

    sel_frame = ttk.LabelFrame(
        frm,
        text='Build your outfit',
        padding=12,
        style='Panel.TLabelframe',
        height=SELECTOR_PANEL_HEIGHT,
    )
    sel_frame.grid(row=1, column=0, sticky=tk.EW)
    sel_frame.grid_columnconfigure(1, weight=1)
    sel_frame.grid_columnconfigure(2, weight=1)
    sel_frame.grid_columnconfigure(1, weight=1)
    sel_frame.grid_propagate(False)

    preset_button_frame = tk.Frame(sel_frame, bg=THEMES['light']['frame'])
    preset_button_frame.grid(row=0, column=0, columnspan=4, sticky=tk.EW, padx=4, pady=(0, 6))

    top_selector_label = tk.Label(sel_frame, text='Top item:', font=FONT_LABEL,
                                  bg=THEMES['light']['frame'], fg='#333333')
    top_selector_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 8))
    top_names, bottom_names = get_main_item_names()
    top_var = tk.StringVar(value=top_names[0] if top_names else '')
    top_combo = ttk.Combobox(sel_frame, textvariable=top_var,
                             values=top_names, state='readonly', width=22,
                             style='Light.TCombobox')
    top_combo.grid(row=1, column=1, sticky=tk.EW, padx=4, pady=6)

    bottom_selector_label = tk.Label(sel_frame, text='Bottom item:', font=FONT_LABEL,
                                     bg=THEMES['light']['frame'], fg='#333333')
    bottom_selector_label.grid(row=2, column=0, sticky=tk.W, padx=(0, 8))
    bottom_var = tk.StringVar(value=bottom_names[0] if bottom_names else '')
    bottom_combo = ttk.Combobox(sel_frame, textvariable=bottom_var,
                                values=bottom_names, state='readonly', width=22,
                                style='Light.TCombobox')
    bottom_combo.grid(row=2, column=1, sticky=tk.EW, padx=4, pady=6)
    for column_index in range(5):
        preset_button_frame.grid_columnconfigure(column_index, weight=1)

    def refresh_main_selector_options():
        available_top_names, available_bottom_names = get_main_item_names()
        current_top = top_var.get()
        current_bottom = bottom_var.get()

        top_combo['values'] = available_top_names
        bottom_combo['values'] = available_bottom_names

        if current_top not in available_top_names:
            top_var.set(available_top_names[0] if available_top_names else '')
        if current_bottom not in available_bottom_names:
            bottom_var.set(available_bottom_names[0] if available_bottom_names else '')

        random_state = tk.NORMAL if available_top_names and available_bottom_names else tk.DISABLED
        btn.config(state=random_state)

    preset_style_map = {
        'dance': {'bg': '#C7DDE8', 'fg': '#244051'},
        'sexy_dance': {'bg': '#E8C7D7', 'fg': '#51243C'},
        'yoga': {'bg': '#CFE8C7', 'fg': '#2D4F2B'},
        'adv_yoga': {'bg': '#D8CCE8', 'fg': '#3C2952'},
        'crazy': {'bg': '#F0C98D', 'fg': '#5A3210'},
    }
    preset_buttons = {}

    def refresh_preset_buttons(theme_colors=None):
        colors = theme_colors or THEMES[current_theme['theme']]
        selected_preset = outfit_preset_var.get()
        for preset_key, button in preset_buttons.items():
            preset_colors = preset_style_map[preset_key]
            is_selected = preset_key == selected_preset
            button.config(
                bg=preset_colors['bg'] if is_selected else colors['frame_elevated'],
                fg=preset_colors['fg'] if is_selected else colors['text'],
                activebackground=preset_colors['bg'],
                activeforeground=preset_colors['fg'],
                highlightbackground=colors['border'],
                highlightcolor=preset_colors['bg'],
                highlightthickness=2 if is_selected else 1,
                relief=tk.SUNKEN if is_selected else tk.FLAT,
            )

    def apply_outfit_preset(preset_key=None):
        if preset_key is None:
            preset_key = outfit_preset_var.get()
        else:
            outfit_preset_var.set(preset_key)
        preset_multiplier = preset_multiplier_map.get(preset_key, 100)
        price_multiplier_var.set(str(preset_multiplier))
        price_multiplier_enabled_var.set(True)
        applied_preset_state['value'] = preset_key
        refresh_main_selector_options()
        refresh_preset_buttons()
        update_display()

    def request_outfit_preset_change(requested_preset: str):
        current_preset = applied_preset_state['value']
        if requested_preset == current_preset:
            refresh_preset_buttons()
            return

        if requested_preset == 'crazy':
            confirmed = messagebox.askyesno(
                'Enable Crazy Mode',
                'Are you sure you want to activate Crazy Mode?\n\n'
                'This mode is only intended for open-minded people.',
            )
            if confirmed:
                apply_outfit_preset('crazy')
                return
            close_application_after_crazy_rejection()
            return

        apply_outfit_preset(requested_preset)

    preset_options = [
        ('Dance', 'dance'),
        ('Sexy Dance', 'sexy_dance'),
        ('Yoga', 'yoga'),
        ('Adv Yoga', 'adv_yoga'),
        ('Crazy', 'crazy'),
    ]
    preset_tooltip_map = {
        'dance': 'Prices for regular dance.',
        'sexy_dance': 'Prices for explicit dances where body is more exposed like anime dance.',
        'yoga': 'Prices for easy yoga poses.',
        'adv_yoga': 'Prices for advances poses where body can be exposed.',
        'crazy': 'Prices for special actions for open minded.',
    }

    for index, (label, value) in enumerate(preset_options):
        preset_button = tk.Button(
            preset_button_frame,
            text=label,
            font=('Segoe UI', 8, 'bold'),
            padx=10,
            pady=6,
            bd=0,
            cursor='hand2',
            command=lambda preset_value=value: request_outfit_preset_change(preset_value),
        )
        preset_button.grid(row=0, column=index, sticky=tk.EW, padx=4, pady=2)
        preset_buttons[value] = preset_button
        ToolTip(preset_button, preset_tooltip_map[value])
    # fonts for info and duplicate labels
    info_font = tkfont.Font(family=FONT_INFO[0], size=FONT_INFO[1], weight=FONT_INFO[2])
    dup_font = tkfont.Font(family=FONT_DUP[0], size=FONT_DUP[1])

    # create a small frame to hold the top info label and its tipo-2 duplicate label
    top_info_frame = tk.Frame(sel_frame, bg=THEMES['light']['frame'])
    top_info_frame.grid(row=1, column=2, sticky=tk.EW, padx=(12,0))
    top_price_badge = tk.Label(top_info_frame, text='●', font=('Segoe UI', 10),
                               fg=COLOR_TOTAL_LOW, bg=THEMES['light']['frame'])
    top_price_badge.pack(side=tk.LEFT, padx=(0, 4))
    top_info_label = tk.Label(top_info_frame, text='', font=info_font,
                              bg=THEMES['light']['frame'], justify=tk.LEFT)
    top_info_label.pack(side=tk.LEFT)

    # labels to the right that display names of tipo-2 (both) items
    top_dup_label = tk.Label(top_info_frame, text='', font=dup_font,
                             fg=COLOR_DUP_TEXT, bg=THEMES['light']['frame'],
                             justify=tk.LEFT)
    top_dup_label.pack(side=tk.LEFT, padx=(8,0))

    bottom_info_frame = tk.Frame(sel_frame, bg=THEMES['light']['frame'])
    bottom_info_frame.grid(row=2, column=2, sticky=tk.EW, padx=(12,0))
    bottom_price_badge = tk.Label(bottom_info_frame, text='●', font=('Segoe UI', 10),
                                  fg=COLOR_TOTAL_LOW, bg=THEMES['light']['frame'])
    bottom_price_badge.pack(side=tk.LEFT, padx=(0, 4))
    bottom_info_label = tk.Label(bottom_info_frame, text='',
                                 font=info_font, bg=THEMES['light']['frame'],
                                 justify=tk.LEFT)
    bottom_info_label.pack(side=tk.LEFT)
    bottom_dup_label = tk.Label(bottom_info_frame, text='',
                                font=dup_font, fg=COLOR_DUP_TEXT,
                                bg=THEMES['light']['frame'], justify=tk.LEFT)
    bottom_dup_label.pack(side=tk.LEFT, padx=(8,0))

    # Horizontal separator line after selectors
    #separator2 = tk.Frame(frm, bg='#cccccc', height=1)
    #separator2.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(8, 8))
    #separator2.grid_propagate(False)

    def show_selection():
        # Build weighted top-bottom pairs so incompatible combinations stay possible
        # but appear half as often as the rest.
        filtered_tops = get_selectable_items(tops)
        filtered_bottoms = get_selectable_items(bottoms)
        if filtered_tops and filtered_bottoms:
            current_ratings = load_ratings()
            combinations = []
            weights = []

            for top_item in filtered_tops:
                for bottom_item in filtered_bottoms:
                    combinations.append((top_item, bottom_item))
                    rating = get_combination_rating(
                        current_ratings,
                        top_item['nombre'],
                        bottom_item['nombre'],
                    )
                    weights.append(0.5 if rating == 'incompatible' else 1.0)

            random_top, random_bottom = random.choices(combinations, weights=weights, k=1)[0]
            top_var.set(random_top['nombre'])
            bottom_var.set(random_bottom['nombre'])
            update_display()

    btn = ttk.Button(sel_frame, text='Random \nOutfit', command=show_selection,
                     style='Random.TButton')
    btn.grid(row=1, column=4, rowspan=2, sticky=tk.EW, padx=(12, 0), pady=5)
    # Checkbox to show/hide prices will be created after update_display() is defined
    show_prices_var = tk.BooleanVar(value=False)

    # prominent total area at the top, centered
    total_frame = tk.Frame(
        frm,
        bg=THEMES['light']['frame'],
        padx=18,
        pady=18,
        height=TOTAL_PANEL_HEIGHT,
    )
    total_frame.grid(row=2, column=0, sticky=tk.EW, pady=(6, 6))
    total_frame.grid_propagate(False)

    big_font = tkfont.Font(family=FONT_TOTAL[0], size=FONT_TOTAL[1], weight=FONT_TOTAL[2])

    total_caption_frame = tk.Frame(total_frame, bg=THEMES['light']['frame'])
    total_caption_frame.pack(fill=tk.X)

    total_caption_label = tk.Label(total_caption_frame, text='Current combination',
                                   font=('Segoe UI', 10, 'bold'),
                                   bg=THEMES['light']['frame'], fg='#666666')
    total_caption_label.pack(side=tk.LEFT, anchor=tk.W)

    multiplier_hint_label = tk.Label(
        total_caption_frame,
        textvariable=dashboard_multiplier_var,
        font=('Segoe UI', 9),
        bg=THEMES['light']['frame'],
        fg='#666666',
    )
    multiplier_hint_label.pack(side=tk.RIGHT, anchor=tk.E)

    total_header_frame = tk.Frame(total_frame, bg=THEMES['light']['frame'])
    total_header_frame.pack(fill=tk.X, pady=(2, 0))

    # Frame for the price and rating side by side
    price_rating_frame = tk.Frame(total_header_frame, bg=THEMES['light']['frame'])
    price_rating_frame.pack(side=tk.LEFT, anchor=tk.W)

    price_display = tk.Label(price_rating_frame, text='0', font=big_font,
                         fg=COLOR_TOTAL_LOW, bg=THEMES['light']['frame'], bd=0)
    price_display.pack(side=tk.LEFT, padx=(0, 20))

    # Rating label grande al lado del precio
    rating_font = tkfont.Font(family='Segoe UI', size=16, weight='bold')
    combination_rating_label = tk.Label(price_rating_frame, text='', font=rating_font,
                                bg=THEMES['light']['frame'], fg='#4A9EFF')
    combination_rating_label.pack(side=tk.LEFT, padx=(10, 0))

    metric_cards_frame = tk.Frame(total_header_frame, bg=THEMES['light']['frame'])
    metric_cards_frame.pack(side=tk.RIGHT, anchor=tk.NE, padx=(8, 0))

    total_card, dashboard_total_label = create_dashboard_card(
        metric_cards_frame,
        'current',
        dashboard_total_var,
        '#F59E0B',
        width=TOTAL_METRIC_CARD_WIDTH,
        height=TOTAL_METRIC_CARD_HEIGHT,
    )
    total_card.pack(side=tk.LEFT)

    max_card, _dashboard_max_label = create_dashboard_card(
        metric_cards_frame,
        'Maximum',
        dashboard_max_var,
        '#8B5CF6',
        width=TOTAL_METRIC_CARD_WIDTH,
        height=TOTAL_METRIC_CARD_HEIGHT,
    )
    max_card.pack(side=tk.LEFT, padx=(5, 0))

    # Frame to hold the item names with separator
    names_topframe = ttk.LabelFrame(total_frame, text='Top', padding=10,
                                                style='Panel.TLabelframe',
                                                width=340,
                                                height=ITEM_NAMES_PANEL_HEIGHT)
    names_topframe.pack(fill=tk.X, pady=(6, 0))
    names_topframe.pack_propagate(False)  # No cambiar tamaño según contenido

    names_bottomframe = ttk.LabelFrame(total_frame, text='Bottom', padding=10,
                                                    style='Panel.TLabelframe',
                                                    width=340,
                                                    height=ITEM_NAMES_PANEL_HEIGHT)
    names_bottomframe.pack(fill=tk.X, pady=(6, 0))
    names_bottomframe.pack_propagate(False)  # No cambiar tamaño según contenido

    # labels under the total showing the selected top and bottom item names
    top_names_container = tk.Frame(names_topframe, bg=THEMES['light']['frame'])
    top_names_container.pack(fill=tk.BOTH, expand=True)
    top_names_container.grid_columnconfigure(0, weight=1)
    top_names_container.grid_columnconfigure(1, weight=1)
    top_name_primary_label = tk.Label(top_names_container, text='', font=FONT_NAME,
                                      bg=THEMES['light']['frame'], wraplength=200,
                                      justify=tk.CENTER, anchor='center')
    top_name_primary_label.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 6))
    top_name_secondary_label = tk.Label(top_names_container, text='', font=FONT_NAME,
                                        bg=THEMES['light']['frame'], wraplength=200,
                                        justify=tk.CENTER, anchor='center')
    top_name_secondary_label.grid(row=0, column=1, sticky=tk.NSEW, padx=(6, 0))

    bottom_names_container = tk.Frame(names_bottomframe, bg=THEMES['light']['frame'])
    bottom_names_container.pack(fill=tk.BOTH, expand=True)
    bottom_names_container.grid_columnconfigure(0, weight=1)
    bottom_names_container.grid_columnconfigure(1, weight=1)
    bottom_name_primary_label = tk.Label(bottom_names_container, text='', font=FONT_NAME,
                                         bg=THEMES['light']['frame'], wraplength=200,
                                         justify=tk.CENTER, anchor='center')
    bottom_name_primary_label.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 6))
    bottom_name_secondary_label = tk.Label(bottom_names_container, text='', font=FONT_NAME,
                                           bg=THEMES['light']['frame'], wraplength=200,
                                           justify=tk.CENTER, anchor='center')
    bottom_name_secondary_label.grid(row=0, column=1, sticky=tk.NSEW, padx=(6, 0))

    # Horizontal separator line after total
    #separator1 = tk.Frame(frm, bg='#cccccc', height=1)
    #separator1.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(8, 8))
    #separator1.grid_propagate(False)

    insights_frame = tk.Frame(frm, bg=root_bg)
    insights_frame.grid(row=3, column=0, sticky=tk.EW)

    insights_panel = tk.Frame(
        insights_frame,
        bg=THEMES['light']['frame'],
        padx=10,
        pady=6,
        height=QUICK_NOTES_HEIGHT,
    )
    insights_panel.pack(fill=tk.X)
    insights_panel.pack_propagate(False)

    insights_title = tk.Label(insights_panel, text=' ', font=('Segoe UI', 2, 'bold'),
                              bg=THEMES['light']['frame'], fg='#333333')
    insights_title.pack(anchor=tk.W)

    details_label = tk.Label(insights_panel, text='', wraplength=680,
                             bg=THEMES['light']['frame'], font=('Segoe UI', 8),
                             fg='#666666', justify=tk.LEFT, anchor='w')
    details_label.pack(fill=tk.X, pady=(2, 0))

    quick_actions_frame = tk.Frame(insights_panel, bg=THEMES['light']['frame'])
    quick_actions_frame.pack(fill=tk.X, pady=(2, 0))

    # Label to show maximum possible price
    bold_font = tkfont.Font(family='Segoe UI', size=8, weight='bold')
    max_price_label = tk.Label(insights_panel, text='', bg=THEMES['light']['frame'],
                               font=bold_font, fg='#333333', justify=tk.LEFT, anchor='w')
    max_price_label.pack(fill=tk.X, pady=(2, 0))


    tops_dict = build_lookup(tops)
    bottoms_dict = build_lookup(bottoms)

    # Cargar calificaciones de combinaciones
    ratings_data = load_ratings()
    quick_top_discard_primary_var = tk.BooleanVar(value=False)
    quick_top_discard_secondary_var = tk.BooleanVar(value=False)
    quick_bottom_discard_primary_var = tk.BooleanVar(value=False)
    quick_bottom_discard_secondary_var = tk.BooleanVar(value=False)
    quick_option_state = {
        'top': {'key': ('', ''), 'primary': '', 'secondary': ''},
        'bottom': {'key': ('', ''), 'primary': '', 'secondary': ''},
    }

    def reset_quick_panel(panel_name):
        if panel_name == 'top':
            quick_top_discard_primary_var.set(False)
            quick_top_discard_secondary_var.set(False)
        else:
            quick_bottom_discard_primary_var.set(False)
            quick_bottom_discard_secondary_var.set(False)

    def handle_quick_discard(panel_name, discard_target):
        panel_state = quick_option_state[panel_name]
        if panel_name == 'top':
            primary_var = quick_top_discard_primary_var
            secondary_var = quick_top_discard_secondary_var
            selector_var = top_var
        else:
            primary_var = quick_bottom_discard_primary_var
            secondary_var = quick_bottom_discard_secondary_var
            selector_var = bottom_var

        if discard_target == 'primary':
            if primary_var.get():
                secondary_var.set(False)
                primary_var.set(False)
                if panel_state['secondary']:
                    selector_var.set(panel_state['secondary'])
                update_display()
            return

        if secondary_var.get():
            primary_var.set(False)
        update_display()


    def update_display(_event=None):
        def update_name_labels(primary_label, secondary_label, entries):
            default_color = THEMES[current_theme['theme']]['text']
            highlight_colors = [default_color] * len(entries)
            single_wraplength = 420
            dual_wraplength = 250

            if len(entries) == 2:
                first_price = entries[0][1]
                second_price = entries[1][1]
                if (first_price is not None and second_price is not None and
                    first_price != second_price):
                    if first_price > second_price:
                        highlight_colors = [COLOR_TOTAL_LOW, COLOR_TOTAL_HIGH]
                    else:
                        highlight_colors = [COLOR_TOTAL_HIGH, COLOR_TOTAL_LOW]

            primary_label.config(text=entries[0][0] if entries else '',
                                 wraplength=dual_wraplength if len(
                                     entries) > 1 else single_wraplength,
                                 fg=highlight_colors[0] if entries else default_color)

            if len(entries) > 1:
                primary_label.grid_configure(column=0, columnspan=1)
                secondary_label.grid()
                secondary_label.config(
                    text=entries[1][0],
                    wraplength=dual_wraplength,
                    fg=highlight_colors[1],
                )
            else:
                primary_label.grid_configure(column=0, columnspan=2)
                secondary_label.grid_remove()
                secondary_label.config(text='', wraplength=dual_wraplength, fg=default_color)

        top_sel = top_var.get()
        bot_sel = bottom_var.get()
        top_item = tops_dict.get(top_sel)
        bot_item = bottoms_dict.get(bot_sel)
        multiplier_factor = get_active_price_multiplier_pct() / 100.0

        if top_item:
            top_info_label.config(
                text=f"{top_item['precio'] * multiplier_factor:.0f}" if show_prices_var.get(
                    ) else ''
            )
            top_price_badge.config(fg=color_for_total(top_item['precio'] * multiplier_factor))
        else:
            top_info_label.config(text='')
            top_price_badge.config(fg=THEMES[current_theme['theme']]['text_secondary'])

        if bot_item:
            bottom_info_label.config(
                text=f"{bot_item['precio'] * multiplier_factor:.0f}" if show_prices_var.get(
                    ) else ''
            )
            bottom_price_badge.config(fg=color_for_total(bot_item['precio'] * multiplier_factor))
        else:
            bottom_info_label.config(text='')
            bottom_price_badge.config(fg=THEMES[current_theme['theme']]['text_secondary'])

        top_extra_name = ''
        top_extra_price = None
        if bot_item and bot_item.get('tipo') == 2 and bot_item['nombre'] != (
            top_item['nombre'] if top_item else ''):
            top_version = tops_dict.get(bot_item['nombre'])
            top_extra_name = bot_item['nombre']
            top_extra_price = top_version['precio'] if top_version else None

        bottom_extra_name = ''
        bottom_extra_price = None
        if top_item and top_item.get('tipo') == 2 and top_item['nombre'] != (
            bot_item['nombre'] if bot_item else ''):
            bottom_version = bottoms_dict.get(top_item['nombre'])
            bottom_extra_name = top_item['nombre']
            bottom_extra_price = bottom_version['precio'] if bottom_version else None

        top_context_key = (top_sel, top_extra_name)
        if quick_option_state['top']['key'] != top_context_key:
            quick_option_state['top'] = {
                'key': top_context_key,
                'primary': top_sel,
                'secondary': top_extra_name,
            }
            reset_quick_panel('top')
        else:
            quick_option_state['top']['primary'] = top_sel
            quick_option_state['top']['secondary'] = top_extra_name

        bottom_context_key = (bot_sel, bottom_extra_name)
        if quick_option_state['bottom']['key'] != bottom_context_key:
            quick_option_state['bottom'] = {
                'key': bottom_context_key,
                'primary': bot_sel,
                'secondary': bottom_extra_name,
            }
            reset_quick_panel('bottom')
        else:
            quick_option_state['bottom']['primary'] = bot_sel
            quick_option_state['bottom']['secondary'] = bottom_extra_name

        combo_details = calculate_combination_details(top_item, bot_item, tops_dict, bottoms_dict)
        adjusted_details = dict(combo_details)

        top_extra_active = bool(top_extra_name) and not quick_top_discard_secondary_var.get()
        bottom_extra_active = bool(
            bottom_extra_name) and not quick_bottom_discard_secondary_var.get()

        adjusted_details['top_price'] = combo_details['original_top_price']
        adjusted_details['bottom_price'] = combo_details['original_bottom_price']

        if top_extra_active and top_extra_price is not None:
            adjusted_details['top_price'] = min(adjusted_details['top_price'], top_extra_price)
            adjusted_details['top_duplicate_price'] = top_extra_price
        else:
            adjusted_details['top_duplicate_price'] = ''

        if bottom_extra_active and bottom_extra_price is not None:
            adjusted_details['bottom_price'] = min(adjusted_details['bottom_price'],
                                                   bottom_extra_price)
            adjusted_details['bottom_duplicate_price'] = bottom_extra_price
        else:
            adjusted_details['bottom_duplicate_price'] = ''

        max_possible_top = combo_details['original_top_price']
        max_possible_bottom = combo_details['original_bottom_price']
        if top_extra_active and top_extra_price is not None:
            max_possible_top = max(max_possible_top, top_extra_price)
        if bottom_extra_active and bottom_extra_price is not None:
            max_possible_bottom = max(max_possible_bottom, bottom_extra_price)

        adjusted_details['total'] = adjusted_details['top_price'] + adjusted_details['bottom_price']
        adjusted_details['max_possible'] = max_possible_top + max_possible_bottom
        adjusted_details['explanation'] = ''

        if adjusted_details['max_possible'] > adjusted_details['total']:
            if bottom_extra_active and top_item and bot_item and bottom_extra_price is not None:
                adjusted_details['explanation'] = (
                    f"{top_item['nombre']} could replace {bot_item['nombre']} for "
                    f"{bottom_extra_price} instead of {combo_details['original_bottom_price']}."
                )
            elif top_extra_active and bot_item and top_item and top_extra_price is not None:
                adjusted_details['explanation'] = (
                    f"{bot_item['nombre']} could replace {top_item['nombre']} for "
                    f"{top_extra_price} instead of {combo_details['original_top_price']}."
                )

        adjusted_details = apply_price_multiplier_to_details(
            adjusted_details,
            get_active_price_multiplier_pct(),
        )

        total = adjusted_details['total']
        rounded_total = round_price_to_step(total)
        rounded_max_possible = round_price_to_step(adjusted_details['max_possible'])
        active_multiplier_pct = get_active_price_multiplier_pct()

        top_dup_label.config(
            text=str(adjusted_details['top_duplicate_price']) if show_prices_var.get() else ''
        )
        bottom_dup_label.config(
            text=str(adjusted_details['bottom_duplicate_price']) if show_prices_var.get() else ''
        )

        dashboard_multiplier_var.set(
            f"Factor {active_multiplier_pct:.0f}%"
            if price_multiplier_enabled_var.get()
            else ''
        )

        # Update price display with appropriate color
        price_display.config(text=str(int(rounded_total)), fg=color_for_total(rounded_total))
        dashboard_total_var.set(str(int(rounded_total)))
        dashboard_total_label.config(fg=color_for_total(rounded_total))

        # Update price bar (0-1500 scale) with color gradient
        price_bar['value'] = price_to_logarithmic_scale(rounded_total)  # Escala logarítmica
        # Get the appropriate bar color based on price
        bar_color = get_bar_color(rounded_total)
        # Create or update style with the interpolated color
        style.configure('Dynamic.Vertical.TProgressbar', background=bar_color)
        price_bar.config(style='Dynamic.Vertical.TProgressbar')

        # Update item name labels below total
        # Tipo 2 items appear in both lines, but avoid duplicates if same item is selected
        # Build display for each panel.
        top_primary_label_text = top_sel
        if quick_bottom_discard_secondary_var.get():
            top_primary_label_text = f'{top_sel} *top only'

        bottom_primary_label_text = bot_sel
        if quick_top_discard_secondary_var.get():
            bottom_primary_label_text = f'{bot_sel} *bottom only'

        display_top_entries = [
            (top_primary_label_text,
             top_item['precio'] * multiplier_factor if top_item else None)
        ]
        if top_extra_active:
            scaled_top_extra_price = top_extra_price * multiplier_factor if (
                top_extra_price is not None) else None
            display_top_entries.append((bot_sel, scaled_top_extra_price))

        display_bottom_entries = [
            (bottom_primary_label_text,
             bot_item['precio'] * multiplier_factor if bot_item else None)
        ]
        if bottom_extra_active:
            scaled_bottom_extra_price = (
                bottom_extra_price * multiplier_factor if bottom_extra_price is not None else None
            )
            display_bottom_entries.append((top_sel, scaled_bottom_extra_price))

        update_name_labels(top_name_primary_label, top_name_secondary_label, display_top_entries)
        update_name_labels(bottom_name_primary_label, bottom_name_secondary_label,
                           display_bottom_entries)

        # Mostrar calificación de la combinación al lado del precio
        combination_rating = get_combination_rating(ratings_data, top_sel, bot_sel)
        rating_label_text, rating_color = RATING_LABELS[combination_rating]
        combination_rating_label.config(text=rating_label_text, fg=rating_color)
        dashboard_rating_var.set(rating_label_text if rating_label_text else 'Sin calificar')

        if top_extra_name:
            discard_top_primary_check.config(
                text=f'Discard {top_sel}',
                command=lambda: handle_quick_discard('top', 'primary'),
            )
            discard_top_primary_check.pack(anchor=tk.W, fill=tk.X)
            discard_top_secondary_check.config(
                text=(f'Discard {top_extra_name} from top, use only as'
                      ' a bottom item like panties or skirt'),
                command=lambda: handle_quick_discard('top', 'secondary'),
            )
            discard_top_secondary_check.pack(anchor=tk.W, fill=tk.X, pady=(4, 0))
        else:
            discard_top_primary_check.pack_forget()
            discard_top_secondary_check.pack_forget()

        if bottom_extra_name:
            discard_bottom_primary_check.config(
                text=f'Discard {bot_sel}',
                command=lambda: handle_quick_discard('bottom', 'primary'),
            )
            discard_bottom_primary_check.pack(anchor=tk.W, fill=tk.X, pady=(8, 0))
            discard_bottom_secondary_check.config(
                text=(f'Discard {bottom_extra_name} from bottom,'
                      ' use only as a top item like bra or top'),
                command=lambda: handle_quick_discard('bottom', 'secondary'),
            )
            discard_bottom_secondary_check.pack(anchor=tk.W, fill=tk.X, pady=(4, 0))
        else:
            discard_bottom_primary_check.pack_forget()
            discard_bottom_secondary_check.pack_forget()

        if top_extra_name or bottom_extra_name:
            details_label.config(
                text=('By default both options stay active. Discard one of them'
                      ' to keep the exact item assignment for better price optimization.'))
        else:
            details_label.config(text='No mirrored items available for this combination.')

        dashboard_mode_var.set('Precios visibles' if show_prices_var.get() else 'Precios ocultos')

        # Show maximum possible price if it's higher than current total
        if adjusted_details['max_possible'] > total:
            max_price_label.config(
                text=f"Maximum possible price: {int(rounded_max_possible)}")
            dashboard_max_var.set(str(int(rounded_max_possible)))
        else:
            max_price_label.config(text='')
            dashboard_max_var.set(str(int(rounded_total)))

    discard_top_primary_check = ttk.Checkbutton(
        quick_actions_frame,
        text='',
        variable=quick_top_discard_primary_var,
        style='Subtle.TCheckbutton',
    )

    discard_top_secondary_check = ttk.Checkbutton(
        quick_actions_frame,
        text='',
        variable=quick_top_discard_secondary_var,
        style='Subtle.TCheckbutton',
    )

    discard_bottom_primary_check = ttk.Checkbutton(
        quick_actions_frame,
        text='',
        variable=quick_bottom_discard_primary_var,
        style='Subtle.TCheckbutton',
    )

    discard_bottom_secondary_check = ttk.Checkbutton(
        quick_actions_frame,
        text='',
        variable=quick_bottom_discard_secondary_var,
        style='Subtle.TCheckbutton',
    )

    top_combo.bind('<<ComboboxSelected>>', update_display)
    bottom_combo.bind('<<ComboboxSelected>>', update_display)

    # initial update
    apply_outfit_preset()
    apply_custom_theme()
    update_display()

    root.mainloop()


if __name__ == '__main__':
    main()
