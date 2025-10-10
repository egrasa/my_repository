"""Ventana con un slider para seleccionar un valor entre 0 y 5."""

import time
import re
import csv
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from collections import deque
import argparse
import matplotlib.pyplot as plt


# Color constants
REFILL_BG = '#cfefff'
MARKER_LINE_COLOR = 'black'

RECORDING_ROOT_BG = "#b28cb3"
RECORDING_FRAME_BG = "#8cb399"

RECORDING_MARKER_CANVAS_BG = "#8cb399"
RECORDING_EMERGENCY_BG = "#75a0ff"
RECORDING_REC_TIME_BG = "#8cb399"
RECORDING_TLABELFRAME_BG = "#8cb399"
RECORDING_TLABEL_BG = "#8cb399"
RECORDING_BUTTON_BG = "#44614E"
RECORDING_CHECKB_BG = "#8cb399"
RECORDING_SCALE_BG = "#0145BB"
RECORDING_TDP_BG = "#8cb399"

RECORDING_SCALE_FG = "#ca4545"
RECORDING_CHECKB_FG = "#e20000"
RECORDING_BUTTON_FG = "#d3e200"
RECORDING_TLABEL_FG = "#383838"
RECORDING_TLABELFRAME_FG = "#ffffff"
RECORDING_FG = "#d60000"

EMERGENCY_RED = 'red'
EMERGENCY_WHITE = 'white'
EMERGENCY_GREEN = 'green'
EMERGENCY_ORANGE = 'orange'

DEFAULT_BLACK = 'black'
PLOT_TDP_COLOR = 'tab:blue'
PLOT_LLENADO_COLOR = 'blue'
PLOT_EMERGENCIA_COLOR = 'red'
PLOT_FRENADO_COLOR = 'orange'
PLOT_BYPASS_COLOR = 'yellow'

EX_LIST = []

def build_window(auto_close=False, close_after_ms=1000):
    """Construye y devuelve la ventana principal con un slider."""
    root = tk.Tk()
    root.title('Brake simulator')
    # No fijar geometry; permitir que la ventana se ajuste al contenido

    # Aumentar padding general para ampliar un poco la ventana
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill='both', expand=True)

    #label = ttk.Label(frame, text='Ajusta el valor (0 - 5):')
    #label.pack(pady=(0,6))

    # Crear el slider (se hará responsivo). No asignamos command aún; lo configuramos
    # después de definir on_change para aceptar el value argument.
    slider = ttk.Scale(frame, from_=0.0, to=5.0, orient='horizontal')
    slider.set(2.5)

    # calcular valor inicial y mapeo según nueva regla con histeresis:
    # Regla base:
    #  - s >= 4.9 -> 0.0
    #  - 4.0 < s < 4.9 -> lineal de 3.8 (en 4.0) a 0.6 (en 4.9)
    #  - s <= 4.0 -> 3.8
    # Añadimos histeresis para evitar saltos en el umbral 4.9:
    #  - zero_enter (entrar a 0): 4.95
    #  - zero_exit  (salir de 0):  4.85
    initial_s = slider.get()
    zero_enter = 4.95
    # estado disponible en closure para histeresis
    is_zero = initial_s >= zero_enter

    if is_zero:
        initial_mapped = 0.0
    elif initial_s <= 4.0:
        initial_mapped = 3.8
    else:
        # mapear de 4.0..4.9 -> 3.8..0.6
        t0 = (initial_s - 4.0) / 0.9
        initial_mapped = 3.8 - 3.2 * t0

    # Crear cuadro TDP en la esquina superior derecha (mismo estilo que TFA/Cilindros)
    tdp_box = ttk.Labelframe(frame, text='TDP', width=180, padding=6)
    tdp_box.pack(side='top', anchor='ne')
    initial_tdp = 10.0 - 0.1 * initial_s
    # usamos tk.Label en lugar de ttk.Label para poder cambiar el background
    tdp_display = tk.Label(tdp_box, text=f"{initial_tdp:.2f}", font=('TkDefaultFont', 14),
                           width=6, anchor='center', justify='center', bg=root.cget('bg'))
    tdp_display.pack(fill='x', padx=6, pady=6)
    # Botón para iniciar recarga de TDP
    refill_job = None
    def start_refill():
        nonlocal refill_job, latest_tdp
        # evitar múltiples arranques
        if refill_job is not None:
            return
        refill_btn.config(state='disabled')

        # indicar visualmente que la recarga ha comenzado
        try:
            tdp_display.config(bg=REFILL_BG)
            tdp_display.config(text=f"🔄 {latest_tdp:.2f}")
        except tk.TclError as e:
            EX_LIST.append(f"Error setting tdp_display config: {e}")

        def refill_step():
            nonlocal refill_job, latest_tdp
            # aumentar TDP en 0.1, hasta un máximo de 10
            latest_tdp = min(10.0, latest_tdp + 0.05)
            # actualizar indicador (si está en modo recarga, mantener el icono)
            try:
                tdp_display.config(text=f"🔄 {latest_tdp:.2f}")
            except tk.TclError as e:
                EX_LIST.append(f"Error updating tdp_display text during refill_step: {e}")
            if latest_tdp < 10.0:
                refill_job = root.after(500, refill_step)
            else:
                # terminado
                refill_job = None
                # restaurar aspecto y reactivar el botón
                try:
                    tdp_display.config(bg=root.cget('bg'))
                    tdp_display.config(text=f"{latest_tdp:.2f}")
                except tk.TclError as e:
                    EX_LIST.append(f"Error restoring tdp_display config after refill: {e}")
                refill_btn.config(state='normal')

        # empezar el primer paso en 2s
        refill_job = root.after(500, refill_step)

    refill_btn = ttk.Button(frame, text='Recargar TDP', command=start_refill)
    refill_btn.pack(side='top', anchor='ne', pady=(4,6))

    # Checkbutton para bypass de la lógica TDP
    bypass_var = tk.BooleanVar(value=True)
    bypass_cb = ttk.Checkbutton(frame, text='Bypass TDP', variable=bypass_var)
    bypass_cb.pack(side='top', anchor='ne')

    # Mostrar Mando centrado encima del slider
    mando_label = ttk.Label(frame, text='Mando', font=('TkDefaultFont', 10, 'bold'))
    mando_label.pack(pady=(4,0))
    mando_display = ttk.Label(frame, text=f"{initial_s:.1f}",
                              font=('TkDefaultFont', 14), anchor='center')
    mando_display.pack(pady=(0,2))

    # Empaquetar el slider con más margen lateral para que los límites no queden pegados
    slider.pack(fill='x', padx=20, pady=8)

    # Añadir marcadores (ticks + etiquetas) bajo la barra del slider
    # Hacemos el canvas más alto para poder dibujar líneas guía que atraviesen
    # la zona del slider+marcadores y se vean como límites verticales
    marker_canvas = tk.Canvas(frame, height=80, highlightthickness=0)
    marker_canvas.pack(fill='x', padx=20, pady=(0,8))

    def draw_markers(_event=None):
        """Dibujar sólo las marcas (ticks) sin texto de etiqueta."""
        marker_canvas.delete('all')
        w = marker_canvas.winfo_width() or 400
        # h = marker_canvas.winfo_height() or 80
        # valores de marcador (en escala 0..5)
        markers = [5.0, 4.9, 4.0, 2.0, 0.0]
        for val in markers:
            # posición relativa en píxeles según el ancho actual
            x = int((val - 0.0) / 5.0 * w)
            # dibujar una línea de marcador (tick) corta
            marker_canvas.create_line(x, 8, x, 18, fill=MARKER_LINE_COLOR, width=2)

    # Redibujar al cambiar tamaño
    marker_canvas.bind('<Configure>', draw_markers)
    # Redibujar una vez al crear
    marker_canvas.after(50, draw_markers)

    # Contenedor inferior para el resto del contenido;
    #  a la derecha apilaremos TFA encima de Cilindros
    bottom_frame = ttk.Frame(frame)
    bottom_frame.pack(fill='both', expand=True)

    right_stack = ttk.Frame(bottom_frame)
    right_stack.pack(side='right', anchor='se', padx=(0,12), pady=(8,0))

    # Estándar para tamaño/estilo de los cuadros
    box_width = 180
    inner_font = ('TkDefaultFont', 14)
    label_width_chars = 6

    # Cuadro TFA (encima)
    box_tfa = ttk.Labelframe(right_stack, text='TFA', width=box_width, padding=6)
    box_tfa.pack(side='top', fill='x', pady=(0,6))
    tfa_delay_display = ttk.Label(box_tfa, text=f"{initial_s:.1f}", font=inner_font,
                                  width=label_width_chars, anchor='center', justify='center')
    tfa_delay_display.pack(fill='x', padx=6, pady=6)

    # Cuadro Cilindros (debajo)
    box_cil = ttk.Labelframe(right_stack, text='Cilindros', width=box_width, padding=6)
    box_cil.pack(side='top', fill='x')
    cil_value = ttk.Label(box_cil, text=f"{initial_mapped:.1f}", font=inner_font,
                         width=label_width_chars, anchor='center', justify='center')
    cil_value.pack(fill='x', padx=6, pady=6)

    # ----------------- Registrador simple in-app -----------------
    # Variables para checkbuttons de registro
    record_mando_var = tk.BooleanVar(value=True)
    record_tdp_var = tk.BooleanVar(value=True)
    record_tfa_var = tk.BooleanVar(value=True)
    record_cil_var = tk.BooleanVar(value=True)
    record_bypass_var = tk.BooleanVar(value=True)
    record_llenado_var = tk.BooleanVar(value=True)
    record_emergencia_var = tk.BooleanVar(value=True)
    record_frenado_var = tk.BooleanVar(value=True)
    records = []  # list of dicts with timestamp and selected data
    recorder_job = None
    record_interval_ms = 500
    # recording timer state
    record_start_time = None
    rec_time_job = None
    # store original colors to be able to restore after recording
    orig_colors = {}

    def _sample_once():
        # snapshot current values based on checkbuttons
        data = {'timestamp': time.time()}

        def _parse_label_float(label_widget, fallback, label_name):
            """Try to parse a float from a widget's text, extracting the first numeric token.
            Returns fallback on failure and logs the issue to EX_LIST."""
            try:
                txt = label_widget.cget('text')
            except tk.TclError as e:
                EX_LIST.append(f"Error reading {label_name} text in _sample_once: {e}")
                return fallback
            if txt is None:
                return fallback
            # extract first float-like substring
            m = re.search(r"-?\d+(?:\.\d+)?", str(txt))
            if not m:
                EX_LIST.append(f"Could not parse numeric from {label_name} text: '{txt}'")
                return fallback
            try:
                return float(m.group(0))
            except (ValueError, TypeError) as e:
                EX_LIST.append(f"Error converting parsed value for {label_name}: {e}")
                return fallback

        if record_mando_var.get():
            mando_v = _parse_label_float(mando_display, latest_mando, 'mando_display')
            data['mando'] = mando_v
        if record_tdp_var.get():
            tdp_v = _parse_label_float(tdp_display, latest_tdp, 'tdp_display')
            data['tdp'] = tdp_v
        if record_tfa_var.get():
            tfa_v = _parse_label_float(tfa_delay_display, last_tfa, 'tfa_delay_display')
            data['tfa'] = tfa_v
        if record_cil_var.get():
            cil_v = _parse_label_float(cil_value, latest_mapped, 'cil_value')
            data['cilindros'] = cil_v
        # Señales digitales
        if record_bypass_var.get():
            data['bypass_tdp'] = 1 if bypass_var.get() else 0
        if record_llenado_var.get():
            data['llenado_tdp'] = 1 if refill_job is not None else 0
        if record_emergencia_var.get():
            data['emergencia'] = 1 if (latest_mando < 2.0 or emergency_tdp_active) else 0
        if record_frenado_var.get():
            data['frenado'] = 1 if not (latest_mapped == 0.0) and not (
                latest_mando < 2.0 or emergency_tdp_active) else 0
        records.append(data)
        # enable clear/export/graph when we have at least one record
        try:
            if len(records) == 1:
                clear_btn.config(state='normal')
                export_btn.config(state='normal')
                view_plot_btn.config(state='normal')
        except NameError:
            # buttons may not exist in certain test contexts
            pass

    def _recorder_loop():
        nonlocal recorder_job
        _sample_once()
        recorder_job = root.after(record_interval_ms, _recorder_loop)

    def start_recording():
        nonlocal recorder_job, record_start_time, rec_time_job
        if recorder_job is None:
            # cambiar aspecto para indicar grabación: guardar colores originales
            try:
                orig_colors['root_bg'] = root.cget('bg')
                orig_colors['frame_style'] = (frame.cget('style') if 'style' in
                                              frame.keys() else '')
                orig_colors['tdp_box_style'] = (tdp_box.cget('style') if 'style' in
                                                tdp_box.keys() else '')
                orig_colors['refill_btn_style'] = (refill_btn.cget('style') if 'style' in
                                                   refill_btn.keys() else '')
                orig_colors['bypass_cb_style'] = (bypass_cb.cget('style') if 'style' in
                                                  bypass_cb.keys() else '')
                orig_colors['mando_label_style'] = (mando_label.cget('style') if 'style' in
                                                    mando_label.keys() else '')
                orig_colors['mando_display_style'] = (mando_display.cget('style') if 'style' in
                                                      mando_display.keys() else '')
                orig_colors['slider_style'] = (slider.cget('style') if 'style' in
                                               slider.keys() else '')
                orig_colors['marker_canvas_bg'] = (marker_canvas.cget('bg') if 'bg' in
                                                   marker_canvas.keys() else '')
                orig_colors['bottom_frame'] = (bottom_frame.cget('style') if 'style' in
                                                bottom_frame.keys() else '')
                orig_colors['right_stack_style'] = (right_stack.cget('style') if 'style' in
                                                    right_stack.keys() else '')
                orig_colors['box_tfa_style'] = (box_tfa.cget('style') if 'style' in
                                                box_tfa.keys() else '')
                orig_colors['tfa_delay_display_style'] = (tfa_delay_display.cget('style') if
                                                          'style' in
                                                          tfa_delay_display.keys() else '')
                orig_colors['box_cil_style'] = (box_cil.cget('style') if 'style' in
                                                box_cil.keys() else '')
                orig_colors['cil_value_style'] = (cil_value.cget('style') if 'style' in
                                                  cil_value.keys() else '')
                orig_colors['checkbuttons_frame_style'] = (checkbuttons_frame.cget('style') if
                                                           'style' in
                                                           checkbuttons_frame.keys() else '')
                orig_colors['analog_frame_style'] = (analog_frame.cget('style') if 'style' in
                                                     analog_frame.keys() else '')
                orig_colors['digital_frame_style'] = (digital_frame.cget('style') if 'style' in
                                                      digital_frame.keys() else '')
                orig_colors['bottom_buttons_frame_style'] = bottom_buttons_frame.cget('style')
                orig_colors['start_rec_btn_style'] = (start_rec_btn.cget('style') if 'style' in
                                                      start_rec_btn.keys() else '')
                orig_colors['stop_rec_btn_style'] = (stop_rec_btn.cget('style') if 'style' in
                                                     stop_rec_btn.keys() else '')
                orig_colors['view_plot_btn_style'] = (view_plot_btn.cget('style') if 'style' in
                                                      view_plot_btn.keys() else '')
                orig_colors['clear_btn_style'] = (clear_btn.cget('style') if 'style' in
                                                  clear_btn.keys() else '')
                orig_colors['export_btn_style'] = (export_btn.cget('style') if 'style' in
                                                   export_btn.keys() else '')
                orig_colors['emergency_label_bg'] = (emergency_label.cget('bg') if 'bg' in
                                                     emergency_label.keys() else '')
                orig_colors['emergency_label_fg'] = (emergency_label.cget('fg') if 'fg' in
                                                     emergency_label.keys() else '')
                orig_colors['rec_time_label_bg'] = (rec_time_label.cget('bg') if 'bg' in
                                                    rec_time_label.keys() else '')
                orig_colors['rec_time_label_fg'] = (rec_time_label.cget('fg') if 'fg' in
                                                    rec_time_label.keys() else '')
            except (tk.TclError, AttributeError) as e:
                EX_LIST.append(f"Warning: could not save original styles/colors for recording: {e}")
            try:
                # tratar de guardar textos/foregrounds de etiquetas principales
                orig_colors['mando_fg'] = (mando_display.cget('foreground') if 'foreground' in
                                           mando_display.keys() else None)
                orig_colors['tdp_bg'] = (tdp_display.cget('bg') if 'bg' in
                                         tdp_display.keys() else None)
            except (tk.TclError, AttributeError) as e:
                EX_LIST.append(f"Warning: could not save original fg/bg colors for recording: {e}")
            try:
                root.title('Brake simulator  [GRABANDO]')
                # aplicar paleta oscura a toda la aplicación
                root.configure(bg=RECORDING_ROOT_BG)
                frame.configure(style='Recording.TFrame')
                bottom_frame.configure(style='Recording.TFrame')
                tdp_box.configure(style='Recording.TLabelframe')
                refill_btn.configure(style='Recording.TButton')
                bypass_cb.configure(style='Recording.TCheckbutton')
                mando_label.configure(style='Recording.TLabel')
                mando_display.configure(style='Recording.TLabel')
                slider.configure(style='Recording.Horizontal.TScale')
                marker_canvas.configure(bg=RECORDING_MARKER_CANVAS_BG)
                right_stack.configure(style='Recording.TFrame')
                box_tfa.configure(style='Recording.TLabelframe')
                tfa_delay_display.configure(style='Recording.TLabel')
                box_cil.configure(style='Recording.TLabelframe')
                cil_value.configure(style='Recording.TLabel')
                checkbuttons_frame.configure(style='Recording.TFrame')
                analog_frame.configure(style='Recording.TLabelframe')
                digital_frame.configure(style='Recording.TLabelframe')
                bottom_buttons_frame.configure(style='Recording.TFrame')
                start_rec_btn.configure(style='Recording.TButton')
                stop_rec_btn.configure(style='Recording.TButton')
                view_plot_btn.configure(style='Recording.TButton')
                clear_btn.configure(style='Recording.TButton')
                export_btn.configure(style='Recording.TButton')
                emergency_label.configure(bg=RECORDING_EMERGENCY_BG, fg=RECORDING_FG)
                rec_time_label.configure(bg=RECORDING_REC_TIME_BG, fg=RECORDING_FG)
                # labels y displays a colores oscuros
                try:
                    mando_display.config(foreground=RECORDING_FG)
                except (tk.TclError, AttributeError):
                    EX_LIST.append("Warning: could not switch mando_display fg to recording color")
                try:
                    tdp_display.config(bg=RECORDING_TDP_BG, fg=RECORDING_TLABEL_FG)
                except (tk.TclError, AttributeError):
                    EX_LIST.append("Warning: could not switch tdp_display to recording colors")
            except (tk.TclError, AttributeError) as e:
                EX_LIST.append(f'Warning: could not switch UI to recording colors: {e}')

            record_start_time = time.time()

            def _update_rec_time():
                nonlocal rec_time_job
                if record_start_time is None:
                    return
                elapsed = int(time.time() - record_start_time)
                m, s = divmod(elapsed, 60)
                rec_time_label.config(text=f'Registro: {m:02d}:{s:02d}')
                rec_time_job = root.after(500, _update_rec_time)

            _update_rec_time()
            _recorder_loop()
            start_rec_btn.config(state='disabled')
            stop_rec_btn.config(state='normal')

    def stop_recording():
        nonlocal recorder_job, rec_time_job, record_start_time
        if recorder_job is not None:
            root.after_cancel(recorder_job)
            recorder_job = None
            start_rec_btn.config(state='normal')
        # restaurar apariencia desde colores guardados
        try:
            root.title('Brake simulator')
            root.configure(bg=orig_colors.get('root_bg', ''))
            frame.configure(style=orig_colors.get('frame_style', ''))
            tdp_box.configure(style=orig_colors.get('tdp_box_style', ''))
            refill_btn.configure(style=orig_colors.get('refill_btn_style', 'Rec.TButton'))
            bypass_cb.configure(style=orig_colors.get('bypass_cb_style', ''))
            mando_label.configure(style=orig_colors.get('mando_label_style', ''))
            mando_display.configure(style=orig_colors.get('mando_display_style', ''))
            slider.configure(style=orig_colors.get('slider_style', ''))
            marker_canvas.configure(bg=orig_colors.get('marker_canvas_bg', ''))
            bottom_frame.configure(style=orig_colors.get('bottom_frame', ''))
            right_stack.configure(style=orig_colors.get('right_stack_style', ''))
            box_tfa.configure(style=orig_colors.get('box_tfa_style', ''))
            tfa_delay_display.configure(style=orig_colors.get('tfa_delay_display_style', ''))
            box_cil.configure(style=orig_colors.get('box_cil_style', ''))
            cil_value.configure(style=orig_colors.get('cil_value_style', ''))
            checkbuttons_frame.configure(style=orig_colors.get('checkbuttons_frame_style', ''))
            analog_frame.configure(style=orig_colors.get('analog_frame_style', ''))
            digital_frame.configure(style=orig_colors.get('digital_frame_style', ''))
            bottom_buttons_frame.configure(style='')
            start_rec_btn.configure(style=orig_colors.get('start_rec_btn_style', 'Rec.TButton'))
            stop_rec_btn.configure(style=orig_colors.get('stop_rec_btn_style', 'Rec.TButton'))
            view_plot_btn.configure(style=orig_colors.get('view_plot_btn_style', 'Rec.TButton'))
            clear_btn.configure(style=orig_colors.get('clear_btn_style', 'Rec.TButton'))
            export_btn.configure(style=orig_colors.get('export_btn_style', 'Rec.TButton'))
            emergency_label.configure(bg=orig_colors.get('emergency_label_bg', EMERGENCY_RED),
                                      fg=orig_colors.get('emergency_label_fg', EMERGENCY_WHITE))
            rec_time_label.configure(bg=orig_colors.get('rec_time_label_bg', ''),
                                     fg=orig_colors.get('rec_time_label_fg', DEFAULT_BLACK))
            try:
                if orig_colors.get('mando_fg'):
                    mando_display.config(foreground=orig_colors.get('mando_fg'))
            except (tk.TclError, AttributeError) as e:
                EX_LIST.append(f"Warning: could not restore mando_display fg after recording: {e}")
            try:
                if orig_colors.get('tdp_bg'):
                    tdp_display.config(bg=orig_colors.get('tdp_bg'), fg=DEFAULT_BLACK)
            except (tk.TclError, AttributeError) as e:
                EX_LIST.append(f"Warning: could not restore tdp_display bg/fg after recording: {e}")
        except (tk.TclError, AttributeError) as e:
            EX_LIST.append(f'Warning: could not restore UI after recording: {e}')
        # detener actualizador de tiempo y resetear contador visual
        try:
            if rec_time_job is not None:
                root.after_cancel(rec_time_job)
                rec_time_job = None
        except tk.TclError as e:
            EX_LIST.append(f"Error cancelling rec_time_job: {e}")
        record_start_time = None
        rec_time_label.config(text='Registro: 00:00')

    def view_plot():
        if not records:
            return
        times = [r['timestamp'] - records[0]['timestamp'] for r in records]
        series = {}
        for r in records:
            for k, v in r.items():
                if k != 'timestamp':
                    if k not in series:
                        series[k] = []
                    series[k].append(v)
        #_, ax = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
        # Determine which subplots to show
        subplots_needed = []
        if any(k in series for k in ['mando', 'tfa', 'cilindros']):
            subplots_needed.append('analog')
        if 'tdp' in series:
            subplots_needed.append('tdp')
        if any(k in series for k in ['bypass_tdp', 'llenado_tdp', 'emergencia', 'frenado']):
            subplots_needed.append('digital')
        n = len(subplots_needed)
        if n == 0:
            return
        _, ax = plt.subplots(n, 1, figsize=(8, 3*n), sharex=True)
        if n == 1:
            ax = [ax]  # make it a list
        idx = 0
        # Plot analog
        if 'analog' in subplots_needed:
            plotted = False
            if 'mando' in series:
                ax[idx].plot(times, series['mando'], label='Mando')
                plotted = True
            if 'tfa' in series:
                ax[idx].plot(times, series['tfa'], label='TFA')
                plotted = True
            if 'cilindros' in series:
                ax[idx].plot(times, series['cilindros'], label='Cilindros')
                plotted = True
            if plotted:
                ax[idx].legend()
                ax[idx].set_ylabel('valores')
            idx += 1
        # Plot TDP
        if 'tdp' in subplots_needed:
            ax[idx].plot(times, series['tdp'], label='TDP', color=PLOT_TDP_COLOR)
            ax[idx].legend()
            ax[idx].set_ylabel('TDP')
            idx += 1
        # Plot digital
        if 'digital' in subplots_needed:
            if 'bypass_tdp' in series:
                ax[idx].step(times, series['bypass_tdp'], label='Bypass TDP', where='post',
                             color=PLOT_BYPASS_COLOR)
            if 'llenado_tdp' in series:
                ax[idx].step(times, series['llenado_tdp'], label='Llenado TDP', where='post',
                             color=PLOT_LLENADO_COLOR)
            if 'emergencia' in series:
                ax[idx].step(times, series['emergencia'], label='Emergencia', where='post',
                             color=PLOT_EMERGENCIA_COLOR)
            if 'frenado' in series:
                ax[idx].step(times, series['frenado'], label='Frenado', where='post',
                             color=PLOT_FRENADO_COLOR)
            ax[idx].legend()
            ax[idx].set_ylabel('señales digitales')
            ax[idx].set_yticks([0, 1])
        # Set xlabel on the last subplot
        ax[-1].set_xlabel('segundos')
        plt.show()

    def clear_records():
        records.clear()
        # disable graph/export/clear when there are no records left
        try:
            view_plot_btn.config(state='disabled')
            export_btn.config(state='disabled')
            clear_btn.config(state='disabled')
        except NameError:
            pass

    def export_csv():
        if not records:
            return
        # Ask for filename
        try:
            fpath = filedialog.asksaveasfilename(defaultextension='.csv',
                                                 filetypes=[('CSV files', '*.csv')],
                                                 title='Exportar registros a CSV')
        except tk.TclError as e:
            # Only catch Tcl/Tk related errors from the file dialog; let other errors propagate
            EX_LIST.append(f"File dialog failed: {e}")
            return
        if not fpath:
            return
        # Determine columns from first record keys (timestamp first)
        cols = []
        for k in records[0].keys():
            cols.append(k)
        try:
            with open(fpath, 'w', newline='', encoding='utf-8') as fh:
                writer = csv.writer(fh)
                writer.writerow(cols)
                for r in records:
                    row = [r.get(c, '') for c in cols]
                    writer.writerow(row)
        except (OSError, csv.Error, UnicodeEncodeError) as e:
            EX_LIST.append(f"Export CSV failed: {e}")

    # Label de estado (oculto por defecto). Usamos tk.Label para controlar bg/fg fácilmente
    emergency_label = tk.Label(frame, text='EMERGENCIA', fg='white',
                               bg='red', anchor='center',
                               font=('TkDefaultFont', 12, 'bold'))
    # no pack aún; se mostrará solo cuando haga falta

    # buffer de muestras (timestamp, value) para producir TFA retrasado en tiempo real
    sample_buffer = deque(maxlen=512)
    # intervalo de muestreo / actualización del TFA retrasado (ms)
    poll_ms = 50
    delay_seconds = 0.4
    # valores compartidos de estado
    latest_mando = initial_s
    latest_mapped = initial_mapped
    latest_tdp = 10.0
    # flag que indica emergencia forzada por TDP (cuando bypass desactivado y TDP<7)
    emergency_tdp_active = False
    last_tfa = initial_s
    # tiempo en el que se aplicó last_tfa (segundos epoch)
    last_tfa_time = time.time()
    last_cil = initial_mapped
    last_cil_time = time.time()

    # Checkbuttons para seleccionar qué datos registrar
    checkbuttons_frame = ttk.Frame(frame)
    checkbuttons_frame.pack(side='bottom', fill='x', pady=(5,0))
    analog_frame = ttk.Labelframe(checkbuttons_frame, text='Analógicas')
    analog_frame.pack(side='left', padx=(0,20))
    ttk.Checkbutton(analog_frame, text='Mando',
                    variable=record_mando_var).pack(side='left', padx=(0,10))
    ttk.Checkbutton(analog_frame, text='TDP',
                    variable=record_tdp_var).pack(side='left', padx=(0,10))
    ttk.Checkbutton(analog_frame, text='TFA',
                    variable=record_tfa_var).pack(side='left', padx=(0,10))
    ttk.Checkbutton(analog_frame, text='Cilindros',
                    variable=record_cil_var).pack(side='left')
    digital_frame = ttk.Labelframe(checkbuttons_frame, text='Digitales')
    digital_frame.pack(side='left')
    ttk.Checkbutton(digital_frame, text='Bypass TDP',
                    variable=record_bypass_var).pack(side='left', padx=(0,10))
    ttk.Checkbutton(digital_frame, text='Llenado TDP',
                    variable=record_llenado_var).pack(side='left', padx=(0,10))
    ttk.Checkbutton(digital_frame, text='Emergencia',
                    variable=record_emergencia_var).pack(side='left', padx=(0,10))
    ttk.Checkbutton(digital_frame, text='Frenado',
                    variable=record_frenado_var).pack(side='left')

    # Botones para registrar / parar y ver gráfica en la parte inferior
    bottom_buttons_frame = ttk.Frame(frame)
    bottom_buttons_frame.pack(side='bottom', fill='x', pady=(10,0))
    ttk.Separator(bottom_buttons_frame, orient='horizontal').pack(fill='x', pady=(5,5))
    # Use ttk buttons and a style for a more professional look
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except tk.TclError:
        # 'clam' theme may not be available on all platforms; ignore Tcl errors and continue.
        EX_LIST.append("Warning: 'clam' theme not available; using default theme.")
    style.configure('Rec.TButton', padding=6)
    # estilos para modo grabación oscura
    style.configure('Recording.TFrame', background=RECORDING_FRAME_BG)
    style.configure('Recording.TLabelframe', background=RECORDING_TLABELFRAME_BG,
                    foreground=RECORDING_TLABELFRAME_FG)
    style.configure('Recording.TLabel', foreground=RECORDING_TLABEL_FG,
                    background=RECORDING_TLABEL_BG)
    style.configure('Recording.TButton', background=RECORDING_BUTTON_BG,
                    foreground=RECORDING_BUTTON_FG)
    style.configure('Recording.TCheckbutton', foreground=RECORDING_CHECKB_FG,
                    background=RECORDING_CHECKB_BG)
    style.configure('Recording.Horizontal.TScale', background=RECORDING_SCALE_BG)

    start_rec_btn = ttk.Button(bottom_buttons_frame, text='Start', width=10,
                               style='Rec.TButton', command=start_recording)
    stop_rec_btn = ttk.Button(bottom_buttons_frame, text='Stop', width=10,
                              style='Rec.TButton', command=stop_recording, state='disabled')
    # start with graph/export/clear disabled until we have recorded data
    view_plot_btn = ttk.Button(bottom_buttons_frame, text='Gráfica', width=10,
                               style='Rec.TButton', command=view_plot, state='disabled')
    clear_btn = ttk.Button(bottom_buttons_frame, text='Limpiar', width=10,
                           style='Rec.TButton', command=clear_records, state='disabled')
    export_btn = ttk.Button(bottom_buttons_frame, text='Exportar CSV', width=12,
                            style='Rec.TButton', command=export_csv, state='disabled')
    # Label con tiempo de grabación (inicialmente 00:00)
    rec_time_label = tk.Label(bottom_buttons_frame, text='Registro: 00:00',
                              font=('TkDefaultFont', 10))
    rec_time_label.pack(side='left', padx=(0,12))
    start_rec_btn.pack(side='left', padx=(0,10))
    stop_rec_btn.pack(side='left', padx=(0,10))
    view_plot_btn.pack(side='left', padx=(0,10))
    clear_btn.pack(side='right', padx=(6,0))
    export_btn.pack(side='right')

    def update_state():
        """Actualiza la etiqueta de estado según latest_mapped y latest_mando.
        Prioridad: Aflojado (mapped==0) > EMERGENCIA (mando<2) > Frenado (resto).
        """
        nonlocal latest_mando, latest_mapped, emergency_tdp_active
        if latest_mapped == 0.0:
            emergency_label.config(text='Aflojado', bg=EMERGENCY_GREEN, fg=EMERGENCY_WHITE)
            if not emergency_label.winfo_ismapped():
                emergency_label.pack(fill='x', pady=(8,0))
            try:
                mando_display.config(foreground=DEFAULT_BLACK)
            except tk.TclError:
                mando_display.config(fg=DEFAULT_BLACK)
                EX_LIST.append("Error setting mando_display fg to black in Aflojado state")
        elif latest_mando < 2.0 or emergency_tdp_active:
            emergency_label.config(text='EMERGENCIA', bg=EMERGENCY_RED, fg=EMERGENCY_WHITE)
            if not emergency_label.winfo_ismapped():
                emergency_label.pack(fill='x', pady=(8,0))
            try:
                mando_display.config(foreground='red')
            except tk.TclError:
                mando_display.config(fg='red')
                EX_LIST.append("Error setting mando_display fg to red in EMERGENCIA state")
        else:
            # Frenado (naranja)
            emergency_label.config(text='Frenado', bg=EMERGENCY_ORANGE, fg=DEFAULT_BLACK)
            if not emergency_label.winfo_ismapped():
                emergency_label.pack(fill='x', pady=(8,0))
            try:
                mando_display.config(foreground='black')
            except tk.TclError:
                mando_display.config(fg='black')
                EX_LIST.append("Error setting mando_display fg to black in Frenado state")
    def on_change(value=None):
        """Handler llamado en tiempo real por el slider.
        Guarda una muestra timestamped en el buffer para producir TFA retrasado.
        Actualiza el display inmediato de Mando y actualiza el estado compartido.
        """
        nonlocal latest_mando
        try:
            s = float(value) if value is not None else float(slider.get())
        except ValueError:
            s = float(slider.get())
            EX_LIST.append("Error converting slider value to float in on_change")

        # Actualizar display inmediato de Mando
        mando_display.config(text=f"{s:.1f}")

        # actualizar estado compartido y refrescar etiqueta
        latest_mando = s
        update_state()

        # Añadir muestra con timestamp al buffer para que el poll procese el valor retrasado
        sample_buffer.append((time.time(), s))

    def process_delay():
        """Procesa el buffer y actualiza `tfa_delay_display` con el valor de Mando retrasado.
        Se ejecuta periódicamente cada poll_ms.
        """
        nonlocal latest_mapped, latest_tdp, last_tfa, last_tfa_time
        nonlocal emergency_tdp_active, last_cil, last_cil_time
        now = time.time()
        target_time = now - delay_seconds

        # buscar la muestra más cercana en el pasado (<= target_time)
        chosen = None
        for ts, val in reversed(sample_buffer):
            if ts <= target_time:
                chosen = val
                break

        if chosen is None and sample_buffer:
            # si no hay muestra suficientemente antigua, usar la más antigua disponible
            chosen = sample_buffer[0][1]

        if chosen is not None:

            # Si el bypass está desactivado, comprobar TDP para activar emergencia TDP
            try:
                bypass_on = bool(bypass_var.get())
            except tk.TclError as e:
                bypass_on = True
                EX_LIST.append(f"Error reading bypass_var in process_delay: {e}")

            if not bypass_on:
                # activar emergencia por TDP si baja de 7.0
                if not emergency_tdp_active and latest_tdp < 7.0:
                    emergency_tdp_active = True
                # desactivar emergencia por TDP solo cuando suba por encima de 7.5
                if emergency_tdp_active and latest_tdp > 7.5:
                    emergency_tdp_active = False

            # objetivo por defecto
            target_for_tfa = chosen

            # detectar emergencia por mando o por TDP y forzar descenso a 0.0
            emergency = (latest_mando < 2.0) or emergency_tdp_active
            if emergency:
                target_for_tfa = 0.0

            # si no hay emergencia, limitar por latest_tdp cuando corresponda
            if not emergency and latest_tdp <= 5.0 and target_for_tfa > latest_tdp:
                target_for_tfa = latest_tdp

            # Rate limiter normal: ±1 unidad cada 0.5s => 2.0 unidades/segundo
            max_rate = 2.0
            # emergency down-rate: 1 unidad cada 0.2s => 5.0 unidades/segundo
            emergency_rate = 5.0
            now_ts = time.time()
            elapsed = max(1e-6, now_ts - last_tfa_time)

            # calcular delta deseado desde last_tfa hacia target_for_tfa
            try:
                desired_delta = float(target_for_tfa) - float(last_tfa)
            except (TypeError, ValueError):
                desired_delta = 0.0
                EX_LIST.append("Error calculating desired_delta in process_delay")

            # límites permitidos según dirección y estado
            allowed_up = max_rate * elapsed
            allowed_down = (emergency_rate if emergency else max_rate) * elapsed

            # clamp desired_delta según sentido
            if desired_delta > 0:
                limited_delta = min(desired_delta, allowed_up)
            else:
                limited_delta = max(desired_delta, -allowed_down)

            # Si estamos en emergencia no permitimos incremento (solo descenso hasta 0)
            if emergency and limited_delta > 0:
                limited_delta = 0.0

            # aplicar delta limitado
            new_val = last_tfa + limited_delta

            # calcular consumo: diferencia positiva respecto al último TFA mostrado
            try:
                delta = float(new_val) - float(last_tfa)
            except (TypeError, ValueError):
                delta = 0.0
                EX_LIST.append("Error calculating delta in process_delay")
            if delta > 0:
                consume = 0.1 * delta
                # decrementar latest_tdp (solo disminuye)
                new_tdp = latest_tdp - consume
                if new_tdp < 0.0:
                    new_tdp = 0.0
                if new_tdp < latest_tdp:
                    latest_tdp = new_tdp

            # Si TDP baja de 8.0, iniciar recarga automática si no hay una en curso
            try:
                if latest_tdp < 8.0 and refill_job is None:
                    # iniciar recarga automática
                    start_refill()
            except tk.TclError as e:
                # en caso de cualquier problema con el botón/refill,
                # registrar y continuar para no romper el loop
                EX_LIST.append(f"Error checking/starting auto refill: {e}")

            # actualizar displays
            tfa_delay_display.config(text=f"{new_val:.1f}")
            try:
                tdp_display.config(text=f"{latest_tdp:.2f}")
            except tk.TclError as e:
                EX_LIST.append(f"Error updating tdp_display in process_delay: {e}")
            # actualizar last_tfa y su timestamp
            last_tfa = new_val
            try:
                last_tfa_time = now_ts
            except NameError:
                # fallback: usar tiempo actual
                last_tfa_time = time.time()

            # Además, recalcular el mapeo de Cilindros respecto al valor retrasado (TFA)
            tfa_val = new_val
            # aplicar las mismas reglas que antes pero usando tfa_val en lugar de s
            if tfa_val >= 4.95:
                mapped = 0.0
            elif tfa_val <= 4.0:
                mapped = 3.8
            else:
                tt = (tfa_val - 4.0) / 0.95
                # interpolación lineal desde 4.0..4.95 -> 3.8..0.6 (aprox)
                mapped = 3.8 - (3.2 * tt)
            # Rate limiter for Cilindros: 0.1 unidades cada 200ms => 0.5 unidades/segundo
            max_cil_rate = 0.5
            now_cil = time.time()
            elapsed_cil = max(1e-6, now_cil - last_cil_time)
            allowed_cil = max_cil_rate * elapsed_cil
            desired_cil_delta = mapped - last_cil
            limited_cil_delta = min(max(desired_cil_delta, -allowed_cil), allowed_cil)
            new_cil = last_cil + limited_cil_delta
            cil_value.config(text=f"{new_cil:.1f}")
            # actualizar estado compartido y refrescar etiqueta
            latest_mapped = new_cil
            last_cil = new_cil
            last_cil_time = now_cil
            update_state()

            # Mostrar el TDP actual (latest_tdp). Nota: latest_tdp sólo puede disminuir.
            try:
                tdp_display.config(text=f"{latest_tdp:.2f}")
            except tk.TclError as e:
                EX_LIST.append(f"Error updating tdp_display in process_delay: {e}")

        # reprogramar
        root.after(poll_ms, process_delay)

    # iniciar el bucle de polling
    root.after(poll_ms, process_delay)

    # Ejecutar una vez para fijar el estado inicial según el valor por defecto del slider
    on_change()

    # Usar el callback 'command' del Scale para recibir actualizaciones en tiempo real
    slider.configure(command=on_change)

    if auto_close:
        root.after(close_after_ms, root.destroy)

    return root


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto-close', action='store_true',
                        help='Cerrar la ventana automáticamente (para pruebas)')
    args = parser.parse_args()

    win = build_window(auto_close=args.auto_close)
    win.mainloop()

NUMBER_EX = len(EX_LIST)
print("Exceptions captured during execution: ", NUMBER_EX)
for ex in EX_LIST:
    print(f"- {ex}")
