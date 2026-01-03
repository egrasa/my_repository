"""control_vias.py
Simulación de manejo de una subestación con 5 vías.

Interfaz:
- Pestaña "Controles": Checkbuttons para indicar si cada seccionador tiene la llave;
botones para accionar el seccionador (abrir/cerrar).
- Pestaña "Circuito": Canvas que muestra gráficamente las 5 vías y el estado de cada seccionador.

Uso: python control_vias.py
"""

import tkinter as tk
from tkinter import ttk, messagebox

NUM_VIAS = 5

class Via:
    """ classe que representa una vía en la subestación """
    def __init__(self, idx):
        self.idx = idx
        # Circuito 25 kV (principal)
        self.llave = tk.BooleanVar(value=False)  # Si la llave está presente
        self.cerrada = tk.BooleanVar(value=False) # Estado del seccionador: True=cerrada
        # Componentes entre transformador y seccionador (por defecto abiertos)
        self.interruptor = tk.BooleanVar(value=False)  # Interruptor en la línea (False = abierto)
        self.disyuntor = tk.BooleanVar(value=False)    # Disyuntor en la línea (False = abierto)

        # Circuito adicional 3 kV (solo disponible para vías 8 y 9)
        self.llave_3k = tk.BooleanVar(value=False)
        self.cerrada_3k = tk.BooleanVar(value=False)
        self.interruptor_3k = tk.BooleanVar(value=False)
        self.disyuntor_3k = tk.BooleanVar(value=False)

    def alimentada(self, transformer_on: bool):
        """True si la vía principal (25 kV) está energizada:
        transformador conectado y todos los dispositivos cerrados."""
        return bool(transformer_on) and self.interruptor.get(
            ) and self.disyuntor.get() and self.cerrada.get()

    def alimentada_3k(self, transformer3_on: bool):
        """True si la vía 3 kV está energizada:
        transformador 3kV conectado y todos los dispositivos cerrados."""
        return bool(transformer3_on) and self.interruptor_3k.get(
            ) and self.disyuntor_3k.get() and self.cerrada_3k.get()

class ControlViasApp(tk.Tk):
    """ Aplicación principal de control de vías de subestación """
    def __init__(self):
        super().__init__()
        self.title("Simulador Subestación - Control de Vías")
        # Ventana más grande y redimensionable
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.resizable(True, True)

        self.vias = [Via(i+1) for i in range(NUM_VIAS)]
        # Transformadores de la subestación (por defecto desconectados)
        self.transformer = tk.BooleanVar(value=True)   # 25 kV
        self.transformer_3k = tk.BooleanVar(value=False) # 3 kV
        # Contadores para intentos de acciones prohibidas: key -> count
        # key format: "<acción>:<vía>" (ej. "llave25_conflict:4")
        self.prohibit_counters = {}
        self._build_ui()
        self._draw_circuit()

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Pestaña Controles
        frame_ctrl = ttk.Frame(nb, padding=(12,12))
        nb.add(frame_ctrl, text="Controles")

        lbl = ttk.Label(frame_ctrl, text="Controles de llaves y seccionadores",
                        font=(None, 12, 'bold'))
        lbl.grid(row=0, column=0, columnspan=5, pady=10)

        # Hacer que las columnas se adapten al tamaño de la ventana
        for c in range(5):
            frame_ctrl.columnconfigure(c, weight=1, minsize=90)

        # Transformador global 25 kV
        cb_trans = ttk.Checkbutton(frame_ctrl, text="Transformador 25 kV",
                                   variable=self.transformer, command=self._on_transformer_toggle)
        cb_trans.grid(row=1, column=0, columnspan=3, sticky='w', padx=10, pady=6)

        # Transformador global 3 kV (aplica solo a vías 4 y 5)
        cb_trans3 = ttk.Checkbutton(frame_ctrl, text="Transformador 3 kV",
                                    variable=self.transformer_3k, command=self._on_transformer_3k_toggle)
        cb_trans3.grid(row=2, column=0, columnspan=2, sticky='w', padx=10, pady=6)
        # Botón para activar/desactivar el transformador 3 kV
        btn_trans3 = ttk.Button(frame_ctrl, text="Activar 3 kV", command=self._toggle_transformer_3k)
        btn_trans3.grid(row=15, column=0, padx=6, sticky='w')

        # Separator under transformer controls to visually separate globals from per-vía controls
        #sep_trans = ttk.Separator(frame_ctrl, orient='horizontal')
        #sep_trans.grid(row=2, column=0, columnspan=5, sticky='ew', pady=6)

        for i, via in enumerate(self.vias):
            # Usamos dos filas por vía: una para 25 kV y otra (vacía o con controles) para 3 kV
            r = i*2 + 4
            r2 = r + 1
            real_via_idx = via.idx
            if via.idx == 4:
                real_via_idx = 8
            elif via.idx == 5:
                real_via_idx = 9

            # Si empezamos las vías especiales (3 kV), insertar una etiqueta separadora
            if via.idx == 1:
                lbl_group = ttk.Label(frame_ctrl, text="Vías culaton",
                                      foreground='blue', font=(None, 10, 'bold'))
                lbl_group.grid(row=r-1, column=0, columnspan=5, pady=(12,6))
                # asegurar algo de espacio extra
                frame_ctrl.rowconfigure(r-1, minsize=12)

            if via.idx == 4:
                lbl_group = ttk.Label(frame_ctrl, text="Vías 8 y 9",
                                      foreground='blue', font=(None, 10, 'bold'))
                lbl_group.grid(row=r-1, column=0, columnspan=5, pady=(12,6))
                # asegurar algo de espacio extra
                frame_ctrl.rowconfigure(r-1, minsize=12)

            # Fila principal (25 kV)
            ttk.Label(frame_ctrl, text=f"Vía {real_via_idx}:").grid(row=r, column=0, sticky='w',
                                                               padx=10, pady=4)
            cb_llave = ttk.Checkbutton(frame_ctrl, text=f"Llave {real_via_idx}", variable=via.llave,
                                       command=lambda v=via: self._on_llave_toggle(v))
            cb_llave.grid(row=r, column=1, sticky='w')

            cb_secc = ttk.Checkbutton(frame_ctrl, text="Seccionador 25kv", variable=via.cerrada,
                                      command=lambda v=via: self._toggle_seccionador(v))
            cb_secc.grid(row=r, column=2, sticky='w', padx=6)

            cb_int = ttk.Checkbutton(frame_ctrl, text="Interruptor 25kv", variable=via.interruptor,
                                     command=lambda v=via: self._on_interruptor_toggle(v))
            cb_int.grid(row=r, column=3, sticky='w', padx=6)

            cb_dis = ttk.Checkbutton(frame_ctrl, text="Disyuntor 25kv", variable=via.disyuntor,
                                     command=lambda v=via: self._on_disyuntor_toggle(v))
            cb_dis.grid(row=r, column=4, sticky='w', padx=6)

            # Guardar referencias de widgets para poder habilitarlos/deshabilitarlos
            via.cb_llave = cb_llave
            via.cb_secc = cb_secc
            via.cb_int = cb_int
            via.cb_dis = cb_dis

            # Segunda fila: solamente para vías 8 y 9 mostramos el circuito 3 kV
            if via.idx in (4, 5):
                ttk.Label(frame_ctrl, text="   ").grid(row=r2, column=0, sticky='w',
                                                       padx=10, pady=4)

                cb_llave_3 = ttk.Checkbutton(frame_ctrl, text=f"Llave {real_via_idx} i",
                                             variable=via.llave_3k,
                                             command=lambda v=via: self._on_llave_3k_toggle(v))
                cb_llave_3.grid(row=r2, column=1, sticky='w', pady=4)

                cb_secc_3 = ttk.Checkbutton(frame_ctrl, text="Seccionador 3kv",
                                            variable=via.cerrada_3k,
                                           command=lambda v=via: self._toggle_seccionador_3k(v))
                cb_secc_3.grid(row=r2, column=2, sticky='w', padx=6, pady=4)

                cb_int_3 = ttk.Checkbutton(frame_ctrl, text="Interruptor 3kv",
                                           variable=via.interruptor_3k,
                                          command=lambda v=via: self._on_interruptor_3k_toggle(v))
                cb_int_3.grid(row=r2, column=3, sticky='w', padx=6, pady=4)

                cb_dis_3 = ttk.Checkbutton(frame_ctrl, text="Disyuntor 3kv",
                                          variable=via.disyuntor_3k,
                                          command=lambda v=via: self._on_disyuntor_3k_toggle(v))
                cb_dis_3.grid(row=r2, column=4, sticky='w', padx=6, pady=4)

                via.cb_llave_3k = cb_llave_3
                via.cb_secc_3k = cb_secc_3
                via.cb_int_3k = cb_int_3
                via.cb_dis_3k = cb_dis_3
            else:
                # Fila vacía para mantener alineación
                ttk.Label(frame_ctrl, text="").grid(row=r2, column=0)

        # Actualizar el estado inicial de los controles según el estado de los disyuntores
        self._update_controls_states()

        # Separator and global controls (placed below all control rows to avoid overlap)
        sep = ttk.Separator(frame_ctrl, orient='horizontal')
        sep.grid(row=2*NUM_VIAS+7, column=0, columnspan=5, sticky='ew', pady=8)

        btn_reset = ttk.Button(frame_ctrl, text="Restablecer todo", command=self._reset)
        btn_reset.grid(row=2*NUM_VIAS+8, column=4, pady=6, padx=10, sticky='e')

        # Pestaña Circuito
        frame_circ = ttk.Frame(nb)
        nb.add(frame_circ, text="Circuito")

        self.canvas = tk.Canvas(frame_circ, width=960, height=560, bg="#f7f7f7")
        # Permitir que el canvas se expanda con la ventana
        self.canvas.pack(fill='both', expand=True, padx=10, pady=10)

        # La leyenda se dibuja dinámicamente en _draw_circuit() para ajustarse al tamaño del canvas

    def _on_llave_toggle(self, via):
        # Si el disyuntor está cerrado, no permitir cambiar la llave (25 kV)
        if via.disyuntor.get():
            via.llave.set(False)
            # Intento prohibido: registrar y mostrar advertencia solo a la 3ª vez seguida
            self._register_action('llave25_disy_closed', via.idx, success=False,
                                  warning=f"No se puede cambiar la llave de la Vía {via.idx} mientras el disyuntor esté cerrado.")
            self._draw_circuit()
            return
        # Exclusividad: no permitir la llave 25kV si existe la llave 3kV
        if hasattr(via, 'llave_3k') and via.llave_3k.get():
            via.llave.set(False)
            self._register_action('llave25_conflict', via.idx, success=False,
                                  warning=f"La llave 25 kV no puede colocarse cuando existe la llave 3 kV en la misma vía.")
            self._draw_circuit()
            return
        # Acción permitida: resetear contadores
        self._register_action(None, success=True)
        self._draw_circuit()

    def _on_llave_3k_toggle(self, via):
        # Si el disyuntor 3kV está cerrado, no permitir cambiar la llave 3kV
        if via.disyuntor_3k.get():
            via.llave_3k.set(False)
            self._register_action('llave3_disy_closed', via.idx, success=False,
                                  warning=f"No se puede cambiar la llave 3 kV de la Vía {via.idx} mientras su disyuntor esté cerrado.")
            self._draw_circuit()
            return
        # Exclusividad: no permitir la llave 3kV si existe la llave 25kV
        if via.llave.get():
            via.llave_3k.set(False)
            self._register_action('llave3_conflict', via.idx, success=False,
                                  warning=f"La llave 3 kV no puede colocarse cuando existe la llave 25 kV en la misma vía.")
            self._draw_circuit()
            return
        # Acción permitida: resetear contadores
        self._register_action(None, success=True)
        self._draw_circuit()

    def _toggle_seccionador(self, via):
        # No permitir accionar seccionador si el disyuntor está cerrado
        if via.disyuntor.get():
            # Revertir cualquier cambio accidental
            via.cerrada.set(False)
            self._register_action('secc25_disy_closed', via.idx, success=False,
                                  warning=f"No se puede accionar el seccionador de la Vía {via.idx} mientras el disyuntor esté cerrado.")
            self._draw_circuit()
            return
        # Controla la acción de cerrar/abrir el seccionador verificando la llave
        if via.cerrada.get() and not via.llave.get():
            # Si intentan dejarlo cerrado sin llave, impedir y avisar (contador)
            via.cerrada.set(False)
            self._register_action('secc25_no_key', via.idx, success=False,
                                  warning=f"No se puede cerrar el seccionador de la Vía {via.idx} porque no tiene la llave.")
            self._draw_circuit()
            return
        # Estado permitido
        #estado = 'cerrada' if via.cerrada.get() else 'abierta'
        #messagebox.showinfo("Seccionador", f"Vía {via.idx} ahora está {estado}.")
        self._draw_circuit()

    def _toggle_seccionador_3k(self, via):
        # No permitir accionar seccionador 3kV si el disyuntor 3kV está cerrado
        if via.disyuntor_3k.get():
            via.cerrada_3k.set(False)
            self._register_action('secc3_disy_closed', via.idx, success=False,
                                  warning=f"No se puede accionar el seccionador 3 kV de la Vía {via.idx} mientras su disyuntor esté cerrado.")
            self._draw_circuit()
            return
        # Control de llave 3kV
        if via.cerrada_3k.get() and not via.llave_3k.get():
            via.cerrada_3k.set(False)
            self._register_action('secc3_no_key', via.idx, success=False,
                                  warning=f"No se puede cerrar el seccionador 3 kV de la Vía {via.idx} porque no tiene la llave 3 kV.")
            self._draw_circuit()
            return
        #estado = 'cerrado' if via.cerrada_3k.get() else 'abierto'
        #messagebox.showinfo("Seccionador 3kV", f"Vía {via.idx} ahora está {estado} (3 kV).")
        self._draw_circuit()

    def _on_interruptor_toggle(self, via):
        # No permitir accionar el interruptor si el disyuntor está cerrado
        if via.disyuntor.get():
            via.interruptor.set(False)
            self._register_action('interruptor25_disy_closed', via.idx, success=False,
                                  warning=f"No se puede cambiar el interruptor de la Vía {via.idx} mientras el disyuntor esté cerrado.")
            self._draw_circuit()
            return
        # Acción permitida: resetear contadores
        self._register_action(None, success=True)
        self._draw_circuit()

    def _on_interruptor_3k_toggle(self, via):
        # No permitir accionar el interruptor 3kV si el disyuntor 3kV está cerrado
        if via.disyuntor_3k.get():
            via.interruptor_3k.set(False)
            self._register_action('interruptor3_disy_closed', via.idx, success=False,
                                  warning=f"No se puede cambiar el interruptor 3 kV de la Vía {via.idx} mientras su disyuntor esté cerrado.")
            self._draw_circuit()
            return
        # Acción permitida: resetear contadores
        self._register_action(None, success=True)
        self._draw_circuit()

    def _reset(self):
        # Restablecer a estado inicial: transformador desconectado,
        # interruptores y disyuntores abiertos, seccionadores y llaves abiertos
        self.transformer.set(False)
        self.transformer_3k.set(False)
        for via in self.vias:
            via.llave.set(False)
            via.cerrada.set(False)
            via.interruptor.set(False)
            via.disyuntor.set(False)
            via.llave_3k.set(False)
            via.cerrada_3k.set(False)
            via.interruptor_3k.set(False)
            via.disyuntor_3k.set(False)
        # Actualizar los estados de los controles de UI
        self._update_controls_states()
        self._draw_circuit()

    def _on_disyuntor_toggle(self, via):
        # Cuando el disyuntor principal se cierra,
        # bloquear todos los controles de la vía principal; al abrirlos, permitirlos
        if hasattr(via, 'cb_llave'):
            if via.disyuntor.get():
                via.cb_llave.config(state='disabled')
                via.cb_secc.config(state='disabled')
                via.cb_int.config(state='disabled')
            else:
                via.cb_llave.config(state='normal')
                via.cb_secc.config(state='normal')
                via.cb_int.config(state='normal')
        # acción (permitida): resetear contadores
        self._register_action(None, success=True)
        self._draw_circuit()

    def _on_disyuntor_3k_toggle(self, via):
        # Cuando el disyuntor 3kV se cierra,
        # bloquear todos los controles 3kV de esa vía; al abrirlos, permitirlos
        if hasattr(via, 'cb_llave_3k'):
            if via.disyuntor_3k.get():
                via.cb_llave_3k.config(state='disabled')
                via.cb_secc_3k.config(state='disabled')
                via.cb_int_3k.config(state='disabled')
            else:
                via.cb_llave_3k.config(state='normal')
                via.cb_secc_3k.config(state='normal')
                via.cb_int_3k.config(state='normal')
        # acción (permitida): resetear contadores
        self._register_action(None, success=True)
        self._draw_circuit()

    def _toggle_transformer_3k(self):
        # Alterna el estado del transformador 3 kV
        new_state = not self.transformer_3k.get()
        self.transformer_3k.set(new_state)
        estado = 'conectado' if new_state else 'desconectado'
        messagebox.showinfo("Transformador 3 kV", f"Transformador 3 kV {estado}.")
        # acción permitida: resetear contadores
        self._register_action(None, success=True)
        self._draw_circuit()

    def _on_transformer_3k_toggle(self):
        # Handler cuando se cambia el estado del checkbox del transformador 3kV
        self._register_action(None, success=True)
        self._draw_circuit()

    def _on_transformer_toggle(self):
        # Handler cuando se cambia el estado del checkbox del transformador 25kV
        self._register_action(None, success=True)
        self._draw_circuit()

    def _update_controls_states(self):
        for via in self.vias:
            if hasattr(via, 'cb_llave'):
                if via.disyuntor.get():
                    via.cb_llave.config(state='disabled')
                    via.cb_secc.config(state='disabled')
                    via.cb_int.config(state='disabled')
                else:
                    via.cb_llave.config(state='normal')
                    via.cb_secc.config(state='normal')
                    via.cb_int.config(state='normal')
            if hasattr(via, 'cb_llave_3k'):
                if via.disyuntor_3k.get():
                    via.cb_llave_3k.config(state='disabled')
                    via.cb_secc_3k.config(state='disabled')
                    via.cb_int_3k.config(state='disabled')
                else:
                    via.cb_llave_3k.config(state='normal')
                    via.cb_secc_3k.config(state='normal')
                    via.cb_int_3k.config(state='normal')

    def _register_action(self, action_key: str, via_idx: int = None, success: bool = False, warning: str = None):
        """Registrar una acción del usuario. Si success=True (acción permitida) se resetean todos los contadores.
        Si action_key es una acción prohibida (success=False), se cuenta y solo a la 3ª repetición seguida se muestra la advertencia.
        """
        if action_key is None or success:
            # Cualquier acción distinta o una acción permitida resetea los contadores
            self.prohibit_counters.clear()
            return
        key = f"{action_key}:{via_idx}"
        # Resetear otros contadores para que sólo las repeticiones consecutivas de la MISMA acción cuenten
        for k in list(self.prohibit_counters.keys()):
            if k != key:
                del self.prohibit_counters[k]
        self.prohibit_counters[key] = self.prohibit_counters.get(key, 0) + 1
        if self.prohibit_counters[key] >= 3:
            # Mostrar advertencia y resetear
            messagebox.showwarning("Acción bloqueada", warning or "Acción no permitida.")
            self.prohibit_counters.clear()

    def _draw_circuit(self):
        # Borrar trazados previos
        self.canvas.delete('via')
        self.canvas.delete('special_area')
        self.canvas.delete('special_label')
        #margin_x = 60
        gap_y = 70
        special_offset = 14  # desplazamiento vertical para vías especiales (4 y 5)

        for i, via in enumerate(self.vias):
            y_base = 40 + i*gap_y + (special_offset if via.idx in (4,5) else 0)
            x0 = 50
            # usar el ancho actual del canvas para colocar elementos de forma responsiva
            canvas_w = self.canvas.winfo_width() if self.canvas.winfo_width() > 200 else 960
            x1 = canvas_w - 20

            # Si la vía tiene doble circuito (4 y 5)
            # dibujamos dos líneas: alta (arriba) y baja (abajo)
            if via.idx in (4, 5):
                y_top = y_base - 8
                y_bot = y_base + 8
            else:
                y_top = y_base
                y_bot = None

            # Coordenadas de los elementos en la cadena:
            # Subestación -> Transformador -> Disyuntor -> Interruptor -> Seccionador (25 kV)
            tx = x0 + int((x1 - x0) * 0.20)
            dx = x0 + int((x1 - x0) * 0.40)
            ix = x0 + int((x1 - x0) * 0.60)
            sx = x0 + int((x1 - x0) * 0.75)

            # Determinar si la vía está realmente alimentada 25 kV y 3 kV
            alimentada = via.alimentada(self.transformer.get())
            alimentada3 = via.alimentada_3k(self.transformer_3k.get())
            # Primer tramo (Subestación -> Transformador) está siempre en rojo
            feed_color = 'red'
            # Colores: gris = sin alimentación, naranja = alimentada 25 kV, azul = alimentada 3 kV
            if alimentada3:
                line_color = 'blue'
            elif alimentada:
                line_color = 'orange'
            else:
                line_color = 'grey'

            # Líneas segmentadas (25 kV)
            # Primer tramo (Subestación -> Transformador) siempre rojo
            self.canvas.create_line(x0, y_top, tx-20, y_top, width=4, fill=feed_color, tags='via')
            # Tramo Transformador -> Disyuntor:
            # si el transformador está conectado se pinta en su color (naranja),
            # si no usa color de la cadena
            self.canvas.create_line(tx+20, y_top, dx-20, y_top, width=4,
                                    fill=('orange' if self.transformer.get() else line_color),
                                    tags='via')
            self.canvas.create_line(dx+20, y_top, ix-20, y_top, width=4, fill=line_color,
                                    tags='via')
            self.canvas.create_line(ix+20, y_top, sx-20, y_top, width=4, fill=line_color,
                                    tags='via')

            # Subestación (izquierda)
            self.canvas.create_oval(x0-20, y_top-12, x0+10, y_top+12, fill='#555', tags='via')
            self.canvas.create_text(x0+40, y_top-20, text=f"Subestación → Vía {via.idx}",
                                    anchor='w', tags='via')

            # Transformador 25 kV
            t_w, t_h = 36, 24
            self.canvas.create_rectangle(tx - t_w//2, y_top - t_h//2, tx + t_w//2, y_top + t_h//2,
                                         fill='orange' if self.transformer.get() else 'grey',
                                         tags='via')
            self.canvas.create_text(tx, y_top-2, text='T', fill='white', tags='via')
            self.canvas.create_text(tx, y_top+10, text='20 kV', fill='white', tags='via')

            # Disyuntor (25 kV)
            d_w, d_h = 30, 20
            self.canvas.create_rectangle(dx - d_w//2, y_top - d_h//2, dx + d_w//2, y_top + d_h//2,
                                         fill='orange' if (via.disyuntor.get() and alimentada
                                                           ) else 'grey',
                                         tags='via')
            self.canvas.create_text(dx, y_top, text='D', fill='white', tags='via')

            # Interruptor (25 kV)
            i_w, i_h = 24, 18
            self.canvas.create_rectangle(ix - i_w//2, y_top - i_h//2, ix + i_w//2, y_top + i_h//2,
                                         fill='orange' if (via.interruptor.get() and alimentada
                                                           ) else 'grey',
                                         tags='via')
            self.canvas.create_text(ix, y_top, text='I', fill='white', tags='via')

            # Seccionador 25 kV (color según alimentación)
            sy = y_top - 12
            secc25_color = 'orange' if alimentada else 'grey'
            self.canvas.create_rectangle(sx, sy, sx+60, sy+24, fill=secc25_color, tags='via')
            self.canvas.create_text(sx+30, y_top, text=f"S{via.idx}", fill='white', tags='via')

            # Indicador de llave 25 kV
            lock_text = '🔑' if via.llave.get() else '—'
            self.canvas.create_text(x1-30, y_top, text=lock_text, font=(None, 16), tags='via')

            # Estado textual de alimentación: para vías 4 y 5 consolidamos en una sola etiqueta
            if via.idx in (4, 5):
                # Prioridad: 3 kV (si está alimentada) -> 25 kV -> SIN ALIMENTACIÓN
                if alimentada3:
                    estado_total = 'ALIMENTADA 3kV'
                elif alimentada:
                    estado_total = 'ALIMENTADA 25kV'
                else:
                    estado_total = 'SIN ALIMENTACIÓN'
                # Dibujar la etiqueta consolidada en el centro vertical del bloque de la vía
                self.canvas.create_text(x1-100, y_base, text=estado_total, tags='via')
            else:
                estado = 'ALIMENTADA' if alimentada else 'SIN ALIMENTACIÓN'
                self.canvas.create_text(x1-100, y_top-20, text=f"{estado}", tags='via')

            # Si existe circuito 3 kV, dibujarlo en la línea inferior
            # (elementos gráficos; el texto ya fue consolidado si aplica)
            if y_bot is not None:
                # Reutilizar coordenadas anteriores para alinear 3 kV
                tx3 = tx
                dx3 = dx
                ix3 = ix
                sx3 = sx

                # Primer tramo 3kV (Subestación -> Transformador 3kV) siempre rojo
                #feed3_color = 'red'
                line_color3 = 'blue' if alimentada3 else 'grey'

                #self.canvas.create_line(x0, y_bot, tx3-20, y_bot, width=3, fill=feed3_color,
                # tags='via')
                # Tramo Transformador3kV -> Disyuntor3kV en azul si transformador 3kV conectado,
                # si no usa el color del circuito
                self.canvas.create_line(tx3+20, y_bot, dx3-20, y_bot, width=3,
                                        fill=('blue' if self.transformer_3k.get() else line_color3),
                                        tags='via')
                self.canvas.create_line(dx3+20, y_bot, ix3-20, y_bot, width=3, fill=line_color3,
                                        tags='via')
                self.canvas.create_line(ix3+20, y_bot, sx3-20, y_bot, width=3, fill=line_color3,
                                        tags='via')

                # Transformador 3 kV
                t_w, t_h = 28, 18
                self.canvas.create_rectangle(tx3 - t_w//2, y_bot - t_h//2,
                                             tx3 + t_w//2, y_bot + t_h//2,
                                             fill='blue' if self.transformer_3k.get() else 'grey',
                                             tags='via')
                self.canvas.create_text(tx3, y_bot-2, text='T3',
                                        fill='white', tags='via')
                self.canvas.create_text(tx3, y_bot+10, text='3 kV',
                                        fill='white', tags='via')

                # Disyuntor 3 kV
                d_w, d_h = 26, 16
                self.canvas.create_rectangle(dx3 - d_w//2, y_bot - d_h//2,
                                             dx3 + d_w//2, y_bot + d_h//2,
                                             fill='blue' if (via.disyuntor_3k.get() and alimentada3
                                                             ) else 'grey',
                                             tags='via')
                self.canvas.create_text(dx3, y_bot, text='D3', fill='white', tags='via')

                # Interruptor 3 kV
                i_w, i_h = 20, 14
                self.canvas.create_rectangle(ix3 - i_w//2, y_bot - i_h//2,
                                             ix3 + i_w//2, y_bot + i_h//2,
                                             fill='blue' if (via.interruptor_3k.get(
                                                 ) and alimentada3) else 'grey',
                                             tags='via')
                self.canvas.create_text(ix3, y_bot, text='I3', fill='white', tags='via')

                # Seccionador 3 kV
                sy3 = y_bot - 10
                color3 = 'blue' if alimentada3 else 'grey'
                self.canvas.create_rectangle(sx3, sy3, sx3+50, sy3+20, fill=color3, tags='via')
                self.canvas.create_text(sx3+25, y_bot, text=f"s{via.idx}", fill='white', tags='via')

                # Indicador de llave 3 kV
                lock_text3 = '🔑' if via.llave_3k.get() else '—'
                self.canvas.create_text(x1-30, y_bot, text=lock_text3, font=(None, 14), tags='via')

                # Indicador de llave 3 kV
                lock_text3 = '🔑' if via.llave_3k.get() else '—'
                self.canvas.create_text(x1-30, y_bot, text=lock_text3, font=(None, 14), tags='via')

        # Dibujar área especial para vías 4 y 5 (si existen) detrás de las trazas
        canvas_w = self.canvas.winfo_width() if self.canvas.winfo_width() > 200 else 960
        if NUM_VIAS >= 5:
            top = 40 + (4-1)*gap_y - 20 + special_offset
            bottom = 40 + (5-1)*gap_y + 20 + special_offset
            left = 20
            right = canvas_w - 40
            self.canvas.create_rectangle(left, top, right, bottom, fill='#eef7ff', outline='',
                                         tags='special_area')
            # Enviar el rectángulo al fondo (por debajo de los elementos 'via')
            try:
                self.canvas.tag_lower('special_area', 'via')
            except tk.TclError:
                pass


        # Dibujar leyenda dinámica en la parte inferior del canvas
        self.canvas.delete('legend')
        #w = self.canvas.winfo_width() if self.canvas.winfo_width() > 200 else 960
        h = self.canvas.winfo_height() if self.canvas.winfo_height() > 200 else 560
        x = 12
        y = h - 44
        legend_items = [
            ('grey', 'Sin alimentación'),
            ('red', 'Alimentado 20 kV'),
            ('orange', 'Alimentado 25 kV'),
            ('blue', 'Alimentado 3 kV'),
        ]
        for color, text in legend_items:
            self.canvas.create_rectangle(x, y, x+18, y+18, fill=color, outline='', tags='legend')
            self.canvas.create_text(x+24, y+9, anchor='w', text=text, tags='legend')
            x += 220

        # Forzar redibujado
        self.canvas.update_idletasks()

if __name__ == '__main__':
    app = ControlViasApp()
    app.mainloop()
