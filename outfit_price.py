""" Simple GUI to calculate outfit price based on CSV files. """

import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox
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
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 380
FONT_LABEL = ('Segoe UI', 10)
FONT_INFO = ('Segoe UI', 12, 'bold')
FONT_TOTAL = ('Segoe UI', 36, 'bold')
FONT_NAME = ('Segoe UI', 12, 'bold')
FONT_DUP = ('Segoe UI', 10)
COLOR_TOTAL_LOW = '#2E7D32'  # green
COLOR_TOTAL_MID = '#F57C00'  # orange
COLOR_TOTAL_HIGH = '#C62828'  # red
COLOR_DUP_TEXT = '#555555'
THRESH_MID = 200
THRESH_HIGH = 400


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

    root_bg = root.cget('bg')

    # Use tk.Frame so we can control background color consistently
    frm = tk.Frame(root, bg=root_bg, padx=14, pady=8)
    frm.pack(fill=tk.BOTH, expand=True)

    sel_frame = tk.Frame(frm, bg=root_bg)
    sel_frame.grid(row=2, column=0, sticky=tk.W)

    tk.Label(sel_frame, text='Top item:', font=FONT_LABEL,
             bg=root_bg).grid(row=0, column=0, sticky=tk.W, padx=(0,8))
    top_names = [t['nombre'] for t in tops]
    top_var = tk.StringVar(value=top_names[0] if top_names else '')
    top_combo = ttk.Combobox(sel_frame, textvariable=top_var,
                             values=top_names, state='readonly', width=22)
    top_combo.grid(row=0, column=1, sticky=tk.W, padx=4, pady=6)

    tk.Label(sel_frame, text='Bottom item:', font=FONT_LABEL,
             bg=root_bg).grid(row=1, column=0, sticky=tk.W, padx=(0,8))
    bottom_names = [b['nombre'] for b in bottoms]
    bottom_var = tk.StringVar(value=bottom_names[0] if bottom_names else '')
    bottom_combo = ttk.Combobox(sel_frame, textvariable=bottom_var,
                                values=bottom_names, state='readonly', width=22)
    bottom_combo.grid(row=1, column=1, sticky=tk.W, padx=4, pady=6)
    # fonts for info and duplicate labels
    info_font = tkfont.Font(family=FONT_INFO[0], size=FONT_INFO[1], weight=FONT_INFO[2])
    dup_font = tkfont.Font(family=FONT_DUP[0], size=FONT_DUP[1])

    # create a small frame to hold the top info label and its tipo-2 duplicate label
    top_info_frame = tk.Frame(sel_frame, bg=root_bg)
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
    separator2 = tk.Frame(frm, bg='#cccccc', height=1)
    separator2.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(8, 8))
    separator2.grid_propagate(False)

    # prominent total area at the top, centered
    total_frame = tk.Frame(frm, bg=root_bg)
    total_frame.grid(row=0, column=0, columnspan=2, pady=(4,12))

    big_font = tkfont.Font(family=FONT_TOTAL[0], size=FONT_TOTAL[1], weight=FONT_TOTAL[2])
    price_display = tk.Label(total_frame, text='0', font=big_font,
                             fg=COLOR_TOTAL_LOW, bg=root_bg, bd=0)
    price_display.pack(pady=(4,0))

    # Frame to hold the item names with separator
    names_frame = tk.Frame(total_frame, bg=root_bg)
    names_frame.pack(pady=(6,0))

    # labels under the total showing the selected top and bottom item names
    top_name_label = tk.Label(names_frame, text='', font=FONT_NAME, bg=root_bg)
    top_name_label.pack()

    # Dashed separator between top and bottom names
    dashed_sep = tk.Label(names_frame, text='─ ─ ─ ─ ─', font=('Segoe UI', 8),
                          bg=root_bg, fg='#aaaaaa')
    dashed_sep.pack(pady=(2,2))

    bottom_name_label = tk.Label(names_frame, text='', font=FONT_NAME, bg=root_bg)
    bottom_name_label.pack()

    # Horizontal separator line after total
    separator1 = tk.Frame(frm, bg='#cccccc', height=1)
    separator1.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(8, 8))
    separator1.grid_propagate(False)

    details_label = tk.Label(frm, text='', wraplength=380, bg=root_bg, font=('Segoe UI', 9),
                             fg='#666666')
    details_label.grid(row=4, column=0, sticky=tk.W, pady=(6,0))


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
        top_price = 0
        if top_item:
            top_price = top_item['precio']
            parts.append(
                f"Top: {top_item['nombre']} ({top_item['categoria']}) - {top_item['precio']}")
            top_info_label.config(text=f"{top_item['precio']}")
        else:
            top_info_label.config(text='')

        bot_price = 0
        if bot_item:
            bot_price = bot_item['precio']
            parts.append(
                f"Bottom: {bot_item['nombre']} ({bot_item['categoria']}) - {bot_item['precio']}")
            bottom_info_label.config(text=f"{bot_item['precio']}")
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

        top_dup_label.config(text=top_dup)
        bottom_dup_label.config(text=bottom_dup)

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

        # Update details with explanation of price reductions
        max_possible = (
            top_item['precio'] if top_item else 0) + (bot_item['precio'] if bot_item else 0)
        explanation = ''

        if max_possible > total:
            # There's a price reduction due to tipo-2 items
            if top_item and top_item.get('tipo') == 2:
                bottom_version = bottoms_dict.get(top_item['nombre'])
                if bottom_version and bot_item and bottom_version['precio'] < bot_item['precio']:
                    explanation = (f"{top_item['nombre']} covers {bot_item['nombre']},"
                                   " using lower price instead.")

            if not explanation and bot_item and bot_item.get('tipo') == 2:
                top_version = tops_dict.get(bot_item['nombre'])
                if top_version and top_item and top_version['precio'] < top_item['precio']:
                    explanation = (f"{bot_item['nombre']} covers {top_item['nombre']},"
                                   " using lower price instead.")

        details_label.config(text=explanation if explanation else '')

    top_combo.bind('<<ComboboxSelected>>', update_display)
    bottom_combo.bind('<<ComboboxSelected>>', update_display)

    # initial update
    update_display()

    def show_selection():
        top_sel = top_var.get()
        bot_sel = bottom_var.get()
        total_text = price_display.cget("text")
        messagebox.showinfo('Selection', f'Top: {top_sel}\nBottom: {bot_sel}\nTotal: {total_text}')

    _btn = ttk.Button(frm, text='Show selection', command=show_selection)
    #_btn.grid(row=5, column=0, columnspan=2, pady=12)

    root.mainloop()


if __name__ == '__main__':
    main()
