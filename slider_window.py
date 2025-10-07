"""Ventana con un slider para seleccionar un valor entre 0 y 5."""
import tkinter as tk
from tkinter import ttk
import time
from collections import deque
import argparse

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
            tdp_display.config(bg='#cfefff')
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
            marker_canvas.create_line(x, 8, x, 18, fill='black', width=2)

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
    # tiempo en el que se aplicó last_tfa (segundos epoch)
    last_tfa_time = time.time()

    def update_state():
        """Actualiza la etiqueta de estado según latest_mapped y latest_mando.
        Prioridad: Aflojado (mapped==0) > EMERGENCIA (mando<2) > Frenado (resto).
        """
        nonlocal latest_mando, latest_mapped, emergency_tdp_active
        if latest_mapped == 0.0:
            emergency_label.config(text='Aflojado', bg='green', fg='white')
            if not emergency_label.winfo_ismapped():
                emergency_label.pack(fill='x', pady=(8,0))
            try:
                mando_display.config(foreground='black')
            except tk.TclError:
                mando_display.config(fg='black')
                EX_LIST.append("Error setting mando_display fg to black in Aflojado state")
        elif latest_mando < 2.0 or emergency_tdp_active:
            emergency_label.config(text='EMERGENCIA', bg='red', fg='white')
            if not emergency_label.winfo_ismapped():
                emergency_label.pack(fill='x', pady=(8,0))
            try:
                mando_display.config(foreground='red')
            except tk.TclError:
                mando_display.config(fg='red')
                EX_LIST.append("Error setting mando_display fg to red in EMERGENCIA state")
        else:
            # Frenado (naranja)
            emergency_label.config(text='Frenado', bg='orange', fg='black')
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
        nonlocal latest_mapped, latest_tdp, last_tfa, last_tfa_time, emergency_tdp_active
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
            cil_value.config(text=f"{mapped:.1f}")
            # actualizar estado compartido y refrescar etiqueta
            latest_mapped = mapped
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
