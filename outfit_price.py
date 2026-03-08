""" Simple GUI to calculate outfit price based on CSV files. """

import os
import csv
import random
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

# Constants
DEFAULT_TOP_ITEMS = [
    ('bra', 50, 'basic'),
    ('bodysuit', 50, 'basic'),
    ('dress', 50, 'basic'),
]
DEFAULT_BOTTOM_ITEMS = [
    ('panties', 50, 'basic'),
    ('skirt', 200, 'normal'),
    ('belt', 300, 'special'),
]
CSV_COLUMNS = ['nombre', 'precio', 'categoria', 'tipo']
WINDOW_WIDTH = 560
WINDOW_HEIGHT = 520
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

def main():
    """ Main function to run the outfit price calculator GUI. """
    base = os.path.dirname(__file__)
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

        # Aplicar tema a todos los widgets recursivamente
        apply_theme_to_widgets(frm, theme_colors)

        # Actualizar específicamente los frames de nombres
        sel_frame.config(bg=theme_colors['bg'], fg=theme_colors['label'])
        names_topframe.config(bg=theme_colors['bg'], fg=theme_colors['label'])
        names_bottomframe.config(bg=theme_colors['bg'], fg=theme_colors['label'])
        total_frame.config(bg=theme_colors['bg'])

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

    root_bg = THEMES['light']['bg']
    root.config(bg=root_bg)

    # Use tk.Frame so we can control background color consistently
    frm = tk.Frame(root, bg=root_bg, padx=14, pady=8)
    frm.pack(fill=tk.BOTH, expand=True)

    # Botón para cambiar de tema (esquina superior derecha) con estilo mejorado
    theme_btn = tk.Button(root, text='☀️', font=('Segoe UI', 14),
                          command=toggle_theme, bg=root_bg, fg='#333333',
                          relief=tk.FLAT, bd=0, highlightthickness=0,
                          activebackground=THEMES['light']['bg'],
                          activeforeground='#333333')
    theme_btn.pack(side=tk.TOP, anchor=tk.NE, padx=10, pady=5)

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
    top_names = [t['nombre'] for t in tops]
    top_var = tk.StringVar(value=top_names[0] if top_names else '')
    top_combo = ttk.Combobox(sel_frame, textvariable=top_var,
                             values=top_names, state='readonly', width=22,
                             style='Light.TCombobox')
    top_combo.grid(row=0, column=1, sticky=tk.W, padx=4, pady=6)

    tk.Label(sel_frame, text='Bottom item:', font=FONT_LABEL,
             bg=THEMES['light']['bg'], fg='#333333').grid(row=1,
                                                          column=0, sticky=tk.W,
                                                          padx=(0,8))
    bottom_names = [b['nombre'] for b in bottoms]
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
    def show_selection():
        # Select random items from both top and bottom
        if tops and bottoms:
            random_top = random.choice(tops)
            random_bottom = random.choice(bottoms)
            top_var.set(random_top['nombre'])
            bottom_var.set(random_bottom['nombre'])
            update_display()

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
    price_display = tk.Label(total_frame, text='0', font=big_font,
                             fg=COLOR_TOTAL_LOW, bg=root_bg, bd=0)
    price_display.pack(pady=(4,0))

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

    # Dashed separator between top and bottom names
    #dashed_sep = tk.Label(names_topframe, text='─ ─ ─ ─ ─', font=('Segoe UI', 8),
     #                     bg=THEMES['light']['bg'], fg='#aaaaaa')
    #dashed_sep.pack(pady=(2,2))

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

    def color_for_total(total):
        if total <= THRESH_MID:
            return COLOR_TOTAL_LOW
        if total <= THRESH_HIGH:
            return COLOR_TOTAL_MID
        return COLOR_TOTAL_HIGH


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

    # initial update
    update_display()

    root.mainloop()


if __name__ == '__main__':
    main()
