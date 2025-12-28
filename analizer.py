""" Analizador de vídeos contenidos en una carpeta """

import errno
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import time
import os
import csv
import shutil
import threading
import json
from datetime import datetime
#from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, CancelledError
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.pyplot as plt
from moviepy import VideoFileClip


def _silenciar_tkerrar_mainloop():
    """Evita los errores "main thread is not in main loop" al cerrar Tkinter"""
    def _wrap(cls, attr):
        original = getattr(cls, attr, None)
        if not original:
            return

        def safe_del(self):
            try:
                return original(self)
            except RuntimeError as exc:
                if "main thread is not in main loop" in str(exc):
                    return
                raise

        setattr(cls, attr, safe_del)

    _wrap(tk.Variable, "__del__")
    _wrap(tk.Image, "__del__")


_silenciar_tkerrar_mainloop()

# --- Colores estilo oscuro ---
COLOR_BG = "#23272a"
COLOR_FRAME = "#2c2f33"
COLOR_LABEL = "#4A970A"
COLOR_TEXT = "#f3bc09"
COLOR_ENTRY = "#23272a"
COLOR_BUTTON = "#36393f"
COLOR_BUTTON_TEXT = "#e0e0e0"
COLOR_BUTTON_STOP = "#f04747"
COLOR_PROGRESS = "#7289da"
COLOR_TAB_DISABLED = "#7a848d"
COLOR_BUTTON_HIGHLIGHT = "#ff8c00"

lista_de_errores = list()  # Para almacenar errores únicos

def mostrar_grafico_visual(resultados, carpeta):
    """Muestra una gráfica de barras: eje X=nombre archivo, 
    eje Y=relación peso/duración, etiqueta=tiempo y línea 80MB/min.
    El video más largo en rojo, el más corto en verde."""
    lista_de_errores.append(carpeta)
    if not resultados:
        messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
        return
    nombres = [r[0] for r in resultados]
    duraciones = [r[1] for r in resultados]
    relaciones = [(r[2] / r[1]) if r[1] > 0 else 0 for r in resultados]

    # Identificar índices del video más largo y más corto
    idx_max = duraciones.index(max(duraciones))
    idx_min = duraciones.index(min(duraciones))

    # Colores: por defecto azul, el más largo rojo, el más corto verde
    colores = ["#7289da"] * len(nombres)
    colores[idx_max] = "red"
    colores[idx_min] = "green"

    plt.style.use('grayscale')
    _, ax = plt.subplots(figsize=(max(12, len(nombres) * 0.5), 6))
    bars = ax.bar(nombres, relaciones, color=colores, edgecolor='k', alpha=0.8)
    plt.xlabel("Archivo")
    plt.ylabel("Peso / Duración (MB/min)")
    plt.title("Relación Peso/Duración por archivo")
    plt.xticks(rotation=45, ha="right")

    # Añadir etiquetas con el tiempo encima de cada barra
    for bar1, dur in zip(bars, duraciones):
        ax.text(bar1.get_x() + bar1.get_width()/2, bar1.get_height(),
                f"{dur:.1f}", ha='center', va='bottom', fontsize=9, color='black', rotation=0)

    # Línea horizontal en 80 MB/min
    ax.axhline(80, color='red', linestyle='--', linewidth=1.5, label='80 MB/min')
    # Línea horizontal en 150 MB/min para resaltar el umbral de optimización
    ax.axhline(150, color='purple', linestyle='--', linewidth=1.5, label='150 MB/min')
    ax.legend()

    plt.tight_layout()
    plt.show()

def calcular_peso_medio(resultados):
    """ Calcula el peso medio por minuto de los vídeos analizados """
    if not resultados:
        return 0
    total_peso = sum(r[2] for r in resultados)
    total_duracion = sum(r[1] for r in resultados)
    if total_duracion == 0:
        return 0
    return total_peso / total_duracion

def calcular_duracion_media(resultados):
    """ Calcula la duración media de los vídeos analizados """
    if not resultados:
        return 0
    total_duracion = sum(r[1] for r in resultados)
    return total_duracion / len(resultados)

def calcular_rating_optimizacion(resultados):
    """
    Calcula el rating de optimización (1-5 estrellas) basado
    en el porcentaje de archivos bien optimizados.
    
    Criterios:
    - Archivos < 10 MB/min: Descartados (baja calidad)
    - Archivos 10-100 MB/min: Bien optimizados
    - Archivos > 100 MB/min: Mal optimizados
    
    Rating:
    - 5 estrellas: % bien optimizados >= 90%
    - 4 estrellas: % bien optimizados >= 70%
    - 3 estrellas: % bien optimizados >= 50%
    - 2 estrellas: % bien optimizados >= 20%
    - 1 estrella: % bien optimizados < 20%
    """
    if not resultados:
        return 0, 0, 0, 0, "Sin datos"

    bien_optimizados = 0
    mal_optimizados = 0

    for _nombre, duracion, peso, *_ in resultados:
        if duracion <= 0:
            continue
        ratio = peso / duracion

        # Descartar archivos < 10 MB/min (baja calidad)
        if ratio < 10:
            continue
        # Contar bien vs mal optimizados
        elif ratio <= 100:
            bien_optimizados += 1
        else:
            mal_optimizados += 1

    total_contable = bien_optimizados + mal_optimizados

    if total_contable == 0:
        return 0, 0, 0, 0, "Sin archivos contables"

    pct_bien = (bien_optimizados / total_contable) * 100
    _pct_mal = (mal_optimizados / total_contable) * 100

    # Asignar estrellas
    if pct_bien >= 90:
        estrellas = 5
        categoria = "Excelente"
    elif pct_bien >= 70:
        estrellas = 4
        categoria = "Muy bueno"
    elif pct_bien >= 50:
        estrellas = 3
        categoria = "Aceptable"
    elif pct_bien >= 20:
        estrellas = 2
        categoria = "Bajo"
    else:
        estrellas = 1
        categoria = "Crítico"

    return estrellas, pct_bien, bien_optimizados, mal_optimizados, categoria

def mostrar_grafico(resultados, carpeta):
    """ Muestra un gráfico de dispersión mejorado de duración vs tamaño
    de los vídeos con subplot de distribución """
    if not resultados:
        messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
        return
    duraciones = [r[1] for r in resultados]
    pesos = [r[2] for r in resultados]

    # Elegir estilo disponible
    preferred_styles = ['seaborn-v0_8-darkgrid', 'seaborn-darkgrid', 'seaborn', 'ggplot', 'default']
    for s in preferred_styles:
        if s in plt.style.available:
            try:
                plt.style.use(s)
            except (OSError, ValueError, ImportError):
                continue
            break

    # Crear figura con 2 subplots
    fig = plt.figure(figsize=(16, 8))
    fig.patch.set_facecolor('#f5f5f5')

    # Subplot principal (scatter)
    ax1 = plt.subplot(1, 2, 1)
    ax1.set_facecolor('#ffffff')

    # Calcular ratios para colorear puntos según categoría
    ratios = [(peso / dur if dur > 0 else 0) for dur, peso in zip(duraciones, pesos)]

    # Crear categorías: verde=ideal, azul=normal, naranja=alto, rojo=muy alto
    colores = []
    tamanios = []
    for dur, peso, ratio in zip(duraciones, pesos, ratios):
        if dur > 20 and ratio < 50:
            colores.append('#2ecc71')  # Verde: candidato a review
            tamanios.append(120)
        elif ratio > 100:
            colores.append('#e74c3c')  # Rojo: necesita optimizar
            tamanios.append(140)
        elif ratio > 50:
            colores.append('#f39c12')  # Naranja: moderado
            tamanios.append(110)
        else:
            colores.append('#3498db')  # Azul: normal
            tamanios.append(100)

    # Scatter plot mejorado
    ax1.scatter(duraciones, pesos, c=colores, s=tamanios,
                        edgecolor='#2c3e50', alpha=0.7, linewidth=1.5)

    # Anotaciones inteligentes: solo para valores destacados
    for i, r in enumerate(resultados):
        nombre, dur, peso = r[0], r[1], r[2]
        ratio = ratios[i]
        # Anotar solo si supera 200 MB/min y duración > 5 min
        if ratio > 200 and dur > 5:
            ax1.annotate(nombre, (dur, peso), fontsize=8,
                       xytext=(5, 5), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=colores[i], alpha=0.6),
                       fontweight='bold')

    # Línea de tendencia (sin extremos)
    if len(duraciones) > 2:
        ratios_con_idx = [(ratio, idx) for idx, ratio in enumerate(ratios)]
        ratios_ordenados = sorted(ratios_con_idx, key=lambda x: x[0])

        # Descartar extremos solo si hay suficientes datos
        if len(ratios) > 20:
            indices_a_descartar = {ratios_ordenados[0][1], ratios_ordenados[1][1],
                                   ratios_ordenados[-1][1], ratios_ordenados[-2][1]}
        else:
            indices_a_descartar = set()

        duraciones_filtradas = [dur for i,
                                dur in enumerate(duraciones) if i not in indices_a_descartar]
        pesos_filtrados = [peso for i,
                           peso in enumerate(pesos) if i not in indices_a_descartar]

        if len(duraciones_filtradas) > 1:
            z = np.polyfit(duraciones_filtradas, pesos_filtrados, 1)
            p = np.poly1d(z)
            x_linea = np.linspace(min(duraciones_filtradas), max(duraciones_filtradas), 100)
            ax1.plot(x_linea, p(x_linea), color='#95a5a6', linestyle='--',
                   linewidth=2.5, label='Tendencia', alpha=0.8)

    # Líneas de referencia mejoradas
    if duraciones:
        x_vals = [min(duraciones), max(duraciones)]

        # Línea de 50 MB/min (ideal)
        y_vals_50 = [x * 50 for x in x_vals]
        ax1.plot(x_vals, y_vals_50, color='#2ecc71', linestyle='-.',
               linewidth=2, label='50 MB/min (Ideal)', alpha=0.7)

        # Línea de 80 MB/min (bueno)
        y_vals_80 = [x * 80 for x in x_vals]
        ax1.plot(x_vals, y_vals_80, color='#3498db', linestyle='--',
               linewidth=2, label='80 MB/min (Bueno)', alpha=0.7)

        # Línea de 100 MB/min (umbral)
        y_vals_100 = [x * 100 for x in x_vals]
        ax1.plot(x_vals, y_vals_100, color='#f39c12', linestyle=':',
               linewidth=2, label='100 MB/min (Alto)', alpha=0.7)

        # Línea de 150 MB/min (crítico)
        y_vals_150 = [x * 150 for x in x_vals]
        ax1.plot(x_vals, y_vals_150, color='#e74c3c', linestyle='-',
               linewidth=2.5, label='150 MB/min (Crítico)', alpha=0.8)

    # Etiquetas y título mejorados
    ax1.set_xlabel('Duración (minutos)', fontsize=12, fontweight='bold', color='#2c3e50')
    ax1.set_ylabel('Tamaño (MB)', fontsize=12, fontweight='bold', color='#2c3e50')

    title_text = os.path.basename(carpeta) if carpeta else "Análisis: Duración vs Tamaño"
    ax1.set_title(title_text, fontsize=14, fontweight='bold',
                color='#2c3e50', pad=20)

    # Grid mejorado
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.7, color='#bdc3c7')

    # Leyenda mejorada
    legend = ax1.legend(loc='upper left', fontsize=10, framealpha=0.95,
                      edgecolor='#2c3e50', fancybox=True, shadow=True)
    legend.get_frame().set_facecolor('#ecf0f1')

    # Ajustar límites con margen
    if duraciones and pesos:
        margin_x = (max(duraciones) - min(duraciones)) * 0.1
        margin_y = (max(pesos) - min(pesos)) * 0.1
        ax1.set_xlim(max(0, min(duraciones) - margin_x), max(duraciones) + margin_x)
        ax1.set_ylim(max(0, min(pesos) - margin_y), max(pesos) + margin_y)

    # Mejorar apariencia general
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#2c3e50')
    ax1.spines['bottom'].set_color('#2c3e50')
    ax1.tick_params(colors='#2c3e50', labelsize=9)

    # ============ SUBPLOT 2: Distribución de rangos de ratio ============
    ax2 = plt.subplot(1, 2, 2)
    ax2.set_facecolor('#ffffff')

    # Definir rangos de ratio y contar archivos en cada rango
    rangos = [
        (0, 30, 'Excelente (0-30)', '#27ae60'),
        (30, 50, 'Ideal (30-50)', '#2ecc71'),
        (50, 80, 'Bueno (50-80)', '#3498db'),
        (80, 100, 'Moderado (80-100)', '#f39c12'),
        (100, 150, 'Alto (100-150)', '#e67e22'),
        (150, float('inf'), 'Crítico (>150)', '#e74c3c')
    ]

    datos_rangos = []
    etiquetas_rangos = []
    colores_rangos = []

    for min_ratio, max_ratio, etiqueta, color in rangos:
        cantidad = sum(1 for r in ratios if min_ratio <= r < max_ratio)
        if cantidad > 0:  # Solo mostrar rangos con datos
            datos_rangos.append(cantidad)
            etiquetas_rangos.append(f'{etiqueta}\n({cantidad})')
            colores_rangos.append(color)

    # Gráfico de barras horizontal
    if datos_rangos:
        y_pos = np.arange(len(datos_rangos))
        barras = ax2.barh(y_pos, datos_rangos, color=colores_rangos, edgecolor='#2c3e50',
                          linewidth=1.5)

        # Agregar valores en las barras
        for i, (barra, valor) in enumerate(zip(barras, datos_rangos)):
            porcentaje = (valor / len(ratios)) * 100
            ax2.text(barra.get_width() + 0.5, barra.get_y() + barra.get_height()/2,
                    f'{valor} ({porcentaje:.1f}%)',
                    va='center', fontsize=10, fontweight='bold', color='#2c3e50')

        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(etiquetas_rangos, fontsize=10)
        ax2.set_xlabel('Cantidad de archivos', fontsize=11, fontweight='bold', color='#2c3e50')
        ax2.set_title('Distribución por rango de ratio (MB/min)', fontsize=12, fontweight='bold',
                     color='#2c3e50', pad=15)
        ax2.grid(True, alpha=0.3, axis='x', linestyle='--', linewidth=0.7, color='#bdc3c7')
        ax2.set_axisbelow(True)

        # Mejorar apariencia
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_color('#2c3e50')
        ax2.spines['bottom'].set_color('#2c3e50')
        ax2.tick_params(colors='#2c3e50', labelsize=9)

        # Agregar información resumida
        info_text = (f'Total archivos: {len(ratios)}\n'
                    f'Ratio promedio: {np.mean(ratios):.2f} MB/min\n'
                    f'Ratio mediana: {np.median(ratios):.2f} MB/min\n'
                    f'Rango: {min(ratios):.2f} - {max(ratios):.2f}')
        ax2.text(0.98, 0.02, info_text, transform=ax2.transAxes,
                fontsize=9, verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.95,
                         edgecolor='#2c3e50', pad=0.6),
                family='monospace', fontweight='bold', color='#2c3e50')

    plt.tight_layout()
    plt.show()

class GestorHistorialAnalisis:
    """Gestiona el historial de análisis realizados con estadísticas por formato"""
    def __init__(self, archivo_historial="analisis_historial.json", callback_actualizar=None):
        self.archivo_historial = archivo_historial
        self.historial = []
        self.callback_actualizar = callback_actualizar
        self.cargar_historial()

    def cargar_historial(self):
        """Carga el historial desde el archivo JSON"""
        if os.path.exists(self.archivo_historial):
            try:
                with open(self.archivo_historial, 'r', encoding='utf-8') as f:
                    self.historial = json.load(f)

                necesita_guardar = False

                # Migrar registros antiguos que no tengan 'veces'
                for entrada in self.historial:
                    if 'veces' not in entrada:
                        entrada['veces'] = 1
                        necesita_guardar = True

                    # Reparar total_archivos que esté en 0
                    if entrada.get('total_archivos', 0) == 0 and entrada.get(
                        'estadisticas_por_formato'):
                        total_calculado = sum(
                            stats.get('cantidad', 0)
                            for stats in entrada['estadisticas_por_formato'].values()
                        )
                        if total_calculado > 0:
                            entrada['total_archivos'] = total_calculado
                            necesita_guardar = True

                # Si hay cambios, guardar el historial actualizado
                if necesita_guardar:
                    self.guardar_historial()

            except (json.JSONDecodeError, IOError):
                self.historial = []

    def guardar_historial(self):
        """Guarda el historial en el archivo JSON"""
        try:
            with open(self.archivo_historial, 'w', encoding='utf-8') as f:
                json.dump(self.historial, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error guardando historial: {e}")

    def registrar_analisis(self, carpeta, counts_by_ext, avg_by_ext, total_archivos, *,
                           rating=None):
        """Registra un análisis con estadísticas por formato y opcionalmente rating."""
        nuevo_analisis = {
            'timestamp': datetime.now().isoformat(),
            'carpeta': carpeta,
            'total_archivos': total_archivos,
            'estadisticas_por_formato': {},
            'veces': 1  # Contador de repeticiones
        }

        # Agregar estadísticas por cada formato encontrado
        for ext in sorted(counts_by_ext.keys()):
            nuevo_analisis['estadisticas_por_formato'][ext] = {
                'cantidad': counts_by_ext[ext],
                'ratio_promedio_mb_min': round(avg_by_ext.get(ext, 0.0), 2)
            }

        if rating is not None:
            nuevo_analisis['rating'] = {
                'estrellas': rating.get('estrellas'),
                'pct_bien': rating.get('pct_bien'),
                'bien_optimizados': rating.get('bien_optimizados'),
                'mal_optimizados': rating.get('mal_optimizados'),
                'categoria': rating.get('categoria')
            }

        # Buscar el último análisis de la MISMA carpeta (no solo el último del historial)
        ultimo_misma_carpeta = None
        for entrada in reversed(self.historial):
            if entrada['carpeta'] == carpeta:
                ultimo_misma_carpeta = entrada
                break

        # Comparar con el último análisis de la misma carpeta
        if ultimo_misma_carpeta is not None:
            # Verificar si tiene los mismos datos
            datos_iguales = (ultimo_misma_carpeta['total_archivos'] == total_archivos and
                ultimo_misma_carpeta['estadisticas_por_formato'] == nuevo_analisis[
                    'estadisticas_por_formato'])
            if rating is not None:
                datos_iguales = datos_iguales and (
                    ultimo_misma_carpeta.get('rating') == nuevo_analisis.get('rating'))
            if datos_iguales:
                # Es idéntico: incrementar contador en lugar de crear nueva entrada
                ultimo_misma_carpeta['veces'] = ultimo_misma_carpeta.get('veces', 1) + 1
                ultimo_misma_carpeta['timestamp'] = datetime.now().isoformat()
                self.guardar_historial()
                # Ejecutar callback si existe para actualizar UI
                if self.callback_actualizar:
                    self.callback_actualizar()
                return

        # Es diferente o es primera vez de esta carpeta: agregar como nueva entrada
        self.historial.append(nuevo_analisis)
        self.guardar_historial()
        # Ejecutar callback si existe para actualizar UI
        if self.callback_actualizar:
            self.callback_actualizar()

    def deshacer_ultimo(self):
        """Deshace el último análisis registrado"""
        if not self.historial:
            return False, "No hay análisis para deshacer"

        ultimo = self.historial[-1]
        self.historial.pop()
        self.guardar_historial()
        return True, f"Análisis de {ultimo['carpeta']} eliminado del historial"

    def deshacer_multiples(self, cantidad):
        """Deshace múltiples análisis"""
        if cantidad > len(self.historial):
            cantidad = len(self.historial)

        deshechados = 0
        for _ in range(cantidad):
            exito, _ = self.deshacer_ultimo()
            if exito:
                deshechados += 1

        return deshechados, 0

    def exportar_csv(self, archivo_salida="analisis_historial.csv"):
        """Exporta el historial a CSV"""
        if not self.historial:
            return False, "No hay análisis para exportar"

        try:
            with open(archivo_salida, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Carpeta', 'Veces', 'Total Archivos', 'Formato',
                                 'Cantidad', 'Ratio Promedio (MB/min)'])

                for analisis in self.historial:
                    veces = analisis.get('veces', 1)
                    for ext, stats in analisis['estadisticas_por_formato'].items():
                        writer.writerow([
                            analisis['timestamp'],
                            analisis['carpeta'],
                            veces,
                            analisis['total_archivos'],
                            ext,
                            stats['cantidad'],
                            stats['ratio_promedio_mb_min']
                        ])
            return True, f"Historial exportado a {archivo_salida}"
        except IOError as e:
            return False, f"Error exportando CSV: {e}"

    def exportar_json(self, archivo_salida="analisis_historial_export.json"):
        """Exporta el historial a JSON"""
        if not self.historial:
            return False, "No hay análisis para exportar"

        try:
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                json.dump(self.historial, f, ensure_ascii=False, indent=2)
            return True, f"Historial exportado a {archivo_salida}"
        except IOError as e:
            return False, f"Error exportando JSON: {e}"

    def obtener_resumen(self):
        """Obtiene un resumen del historial"""
        if not self.historial:
            return "No hay análisis registrados"

        total = len(self.historial)
        total_repeticiones = sum(analisis.get('veces', 1) - 1 for analisis in self.historial)
        resumen = f"Total análisis únicos: {total}"
        if total_repeticiones > 0:
            total_ejecuciones = total + total_repeticiones
            resumen += (f" | Total ejecuciones (incluyendo repetidas): {total_ejecuciones}"
                        f" | Análisis duplicados: {total_repeticiones}")
        return resumen

    def limpiar_historial(self):
        """Limpia todo el historial"""
        self.historial = []
        self.guardar_historial()

class ToolTip:
    """Tooltip para widgets de Tkinter"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, _event=None):
        """Muestra el tooltip"""
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert") if self.widget.winfo_ismapped() else (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 20
        y = y + cy + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#333", foreground="#fff",
                         relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "9", "normal"))
        label.pack(ipadx=6, ipady=2)

    def hide_tip(self, _event=None):
        """Oculta el tooltip"""
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class GestorAnalisisHistorico:
    """Gestiona análisis históricos por carpeta con comentarios y comparativas"""
    def __init__(self, archivo_datos="analisis_carpetas.json"):
        self.archivo_datos = archivo_datos
        self.datos = {}
        self.cargar_datos()

    def cargar_datos(self):
        """Carga los datos históricos de carpetas"""
        if os.path.exists(self.archivo_datos):
            try:
                with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                    self.datos = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.datos = {}
        else:
            self.datos = {}

    def guardar_datos(self):
        """Guarda los datos históricos"""
        try:
            with open(self.archivo_datos, 'w', encoding='utf-8') as f:
                json.dump(self.datos, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error guardando datos: {e}")

    def registrar_analisis(self, carpeta, resultados):
        """Registra un análisis de una carpeta"""
        clave = os.path.abspath(carpeta)

        # Calcular estadísticas
        peso_total = sum(r[2] for r in resultados)
        duracion_total = sum(r[1] for r in resultados)
        altos = [r[3] for r in resultados]

        analisis_actual = {
            'timestamp': datetime.now().isoformat(),
            'total_archivos': len(resultados),
            'peso_total_mb': round(peso_total, 2),
            'duracion_total_min': round(duracion_total, 2),
            'peso_promedio_mb': round(peso_total / len(resultados), 2) if resultados else 0,
            'duracion_promedio_min': round(duracion_total / len(resultados),
                                           2) if resultados else 0,
            'alto_promedio': round(sum(altos) / len(altos), 0) if altos else 0,
            'altos_unicos': sorted(list(set(altos))),
        }

        if clave not in self.datos:
            self.datos[clave] = {
                'carpeta': carpeta,
                'comentarios': [],
                'analisis': []
            }

        self.datos[clave]['analisis'].append(analisis_actual)
        self.guardar_datos()

    def obtener_analisis_anterior(self, carpeta):
        """Obtiene el análisis anterior de una carpeta"""
        clave = os.path.abspath(carpeta)
        if clave in self.datos and len(self.datos[clave]['analisis']) > 0:
            return self.datos[clave]['analisis'][-1]
        return None

    def obtener_todos_analisis(self, carpeta):
        """Obtiene todos los análisis de una carpeta"""
        clave = os.path.abspath(carpeta)
        if clave in self.datos:
            return self.datos[clave]['analisis']
        return []

    def carpeta_analizada_antes(self, carpeta):
        """Verifica si una carpeta ha sido analizada antes"""
        clave = os.path.abspath(carpeta)
        return clave in self.datos and len(self.datos[clave]['analisis']) > 0

    def anadir_comentario(self, carpeta, comentario):
        """Añade un comentario a una carpeta"""
        clave = os.path.abspath(carpeta)
        if clave not in self.datos:
            self.datos[clave] = {
                'carpeta': carpeta,
                'comentarios': [],
                'analisis': []
            }

        self.datos[clave]['comentarios'].append({
            'timestamp': datetime.now().isoformat(),
            'texto': comentario
        })
        self.guardar_datos()

    def obtener_comentarios(self, carpeta):
        """Obtiene los comentarios de una carpeta"""
        clave = os.path.abspath(carpeta)
        if clave in self.datos:
            return self.datos[clave]['comentarios']
        return []


class AnalizadorVideosApp:
    """ Aplicación para analizar vídeos en una carpeta """
    def __init__(self, master):
        self.root = master
        self.root.title("Analizador de vídeos")
        self.resultados = []
        self.preview_counts = {}
        self.videos_problema = []
        self._analysis_executor = None
        self._analisis_future = None
        self.carpeta = None  # Inicializar el atributo carpeta
        self._parar_analisis = False  # Control de parada
        self._previsualizacion_hecha = False  # Control para saber si ya se hizo previsualización
        self.gestor_historial = GestorHistorialAnalisis(
            callback_actualizar=self._habilitar_botones_historial)
        self.gestor_analisis_historico = GestorAnalisisHistorico()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.configure(bg=COLOR_BG)

        # Frame principal para selección de carpeta y análisis
        self.frame_principal = ttk.Frame(master, padding=5)
        self.frame_principal.pack(fill="x", pady=5)

        # --- Fila para selección de carpeta y mostrar ruta ---
        frame_dir = tk.Frame(self.frame_principal, bg=COLOR_FRAME)
        frame_dir.pack(fill="x", pady=2)

        self.boton = tk.Button(frame_dir, text="    📁    Carpeta ", width=15,
                       command=self.seleccionar_carpeta, height=2,
                       bg=COLOR_BUTTON_HIGHLIGHT, fg=COLOR_BUTTON_TEXT,
                       activebackground=COLOR_PROGRESS)
        self.boton.pack(side="left", padx=(0, 5))
        ToolTip(self.boton, "Selecciona la carpeta raíz para analizar")

        self.carpeta_var = tk.StringVar()
        self.label_carpeta = tk.Label(frame_dir, textvariable=self.carpeta_var,
                                      width=60, anchor="w", bg=COLOR_FRAME, fg=COLOR_LABEL)
        self.label_carpeta.pack(side="left", padx=(0, 5), fill="x", expand=True)
        self.label_carpeta.config(text="")  # Inicialmente vacío

        # Botón unificado para pre-análisis y análisis
        self.boton_analizar = tk.Button(frame_dir, text="  🔍 Pre-analizar  ",
                                        command=self.analizar_o_previsualizar,
                                        bg=COLOR_BUTTON, fg=COLOR_LABEL, width=16,
                                        activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_analizar["state"] = "disabled"
        ToolTip(self.boton_analizar, "Primero hace previsualización, luego análisis completo")

        # Sistema de pestañas
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Pestaña para archivos AVI
        self.frame_avi = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_avi, text="__AVI")

        # Pestaña para archivos MOV (misma funcionalidad que AVI)
        self.frame_mov = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_mov, text="__MOV")

        # Pestaña para archivos MKV (definida justo después de MOV)
        self.frame_mkv = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_mkv, text="__MKV")

        # Añadir pestaña separadora visual entre grupos de pestañas
        self.frame_separador = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_separador, text=" ")
        self.notebook.tab(self.frame_separador, state="disabled")

        # Pestaña para gráficos
        self.frame_graficos = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_graficos, text=" - Gráficos - ")

        # Pestaña principal con resultados
        self.frame_resultados = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(self.frame_resultados, text=" - Resultados - ")

        # Empezar con las pestañas de formato desactivadas hasta saber qué archivos hay
        self._actualizar_tabs_formatos({})
        # --- CONTENIDO PESTAÑA AVI ---
        avi_buttons_frame = tk.Frame(self.frame_avi, bg=COLOR_FRAME)
        avi_buttons_frame.pack(fill="x", pady=10)

        # Botón para contar archivos AVI en subcarpetas
        self.boton_contar_avis = tk.Button(avi_buttons_frame, text="Contar AVI", width=15,
                                           command=self.contar_avis_en_subcarpetas,
                                           bg=COLOR_BUTTON, fg=COLOR_PROGRESS, relief="flat",
                                           activebackground=COLOR_PROGRESS)
        self.boton_contar_avis.pack(side="left", padx=5)

        # Botón para mover archivos AVI a la carpeta 'avi'
        self.boton_avi = tk.Button(avi_buttons_frame, text="Mover AVI", width=15,
                                   command=self.mover_avis_a_carpeta, relief="flat",
                                   bg=COLOR_BUTTON, fg=COLOR_PROGRESS,
                                   activebackground=COLOR_PROGRESS)
        self.boton_avi.pack(side="left", padx=5)
        self.boton_avi["state"] = "disabled"

        # Etiqueta para mostrar resultados de conteo en la pestaña AVI
        self.label_conteo_avi = tk.Label(self.frame_avi, text="", bg=COLOR_FRAME,
                         fg=COLOR_LABEL, anchor="w")
        self.label_conteo_avi.pack(fill="x", padx=8)

        # (El botón global "Ver Vacías" se crea en la pestaña Resultados)

        # Botón para buscar archivos AVI repetidos
        self.boton_repetidos = tk.Button(avi_buttons_frame, text="Buscar Repetidos", width=15,
                                         command=self.buscar_avis_repetidos, relief="flat",
                                         bg=COLOR_BUTTON, fg=COLOR_TEXT,
                                         activebackground=COLOR_PROGRESS)
        self.boton_repetidos.pack(side="left", padx=5)

        # Área de texto específica para la pestaña AVI (resultados de esa pestaña)
        texto_avi_container = ttk.Frame(self.frame_avi)
        texto_avi_container.pack(fill="both", expand=True, pady=(10,0), padx=8)
        self.texto_avi = tk.Text(texto_avi_container, height=15, width=80, fg=COLOR_TEXT,
                                 bg=COLOR_BG, insertbackground=COLOR_LABEL,
                                 state="disabled", wrap="word", relief="flat")
        self.texto_avi.pack(side="left", fill="both", expand=True)
        scroll_avi = ttk.Scrollbar(texto_avi_container, orient="vertical",
                                   command=self.texto_avi.yview)
        scroll_avi.pack(side="right", fill="y")
        self.texto_avi.configure(yscrollcommand=scroll_avi.set)
        self.texto_avi.config(font=("Consolas", 10))

        # --- CONTENIDO PESTAÑA MOV (duplicado funcionalmente de AVI) ---
        mov_buttons_frame = tk.Frame(self.frame_mov, bg=COLOR_FRAME)
        mov_buttons_frame.pack(fill="x", pady=10)

        # Botón para contar archivos MOV en subcarpetas
        self.boton_contar_movs = tk.Button(mov_buttons_frame, text="Contar MOV", width=15,
                           command=self.contar_movs_en_subcarpetas,
                           bg=COLOR_BUTTON, fg=COLOR_PROGRESS, relief="flat",
                           activebackground=COLOR_PROGRESS)
        self.boton_contar_movs.pack(side="left", padx=5)

        # Botón para mover archivos MOV a la carpeta 'mov'
        self.boton_mov = tk.Button(mov_buttons_frame, text="Mover MOV", width=15,
                       command=self.mover_movs_a_carpeta, relief="flat",
                       bg=COLOR_BUTTON, fg=COLOR_PROGRESS,
                       activebackground=COLOR_PROGRESS)
        self.boton_mov.pack(side="left", padx=5)
        self.boton_mov["state"] = "disabled"

        # (El botón global "Ver Vacías" se crea en la pestaña Resultados)

        # Botón para buscar archivos MOV repetidos
        self.boton_repetidos_mov = tk.Button(mov_buttons_frame, text="Buscar Repetidos", width=15,
                            command=self.buscar_movs_repetidos, relief="flat",
                            bg=COLOR_BUTTON, fg=COLOR_TEXT,
                            activebackground=COLOR_PROGRESS)
        self.boton_repetidos_mov.pack(side="left", padx=5)

        self.label_conteo_mov = tk.Label(self.frame_mov, text="", bg=COLOR_FRAME,
                         fg=COLOR_LABEL, anchor="w")
        self.label_conteo_mov.pack(fill="x", padx=8)

        # Área de texto específica para la pestaña MOV
        texto_mov_container = ttk.Frame(self.frame_mov)
        texto_mov_container.pack(fill="both", expand=True, pady=(10,0), padx=8)
        self.texto_mov = tk.Text(texto_mov_container, height=15, width=80, fg=COLOR_TEXT,
                     bg=COLOR_BG, insertbackground=COLOR_LABEL,
                     state="disabled", wrap="word", relief="flat")
        self.texto_mov.pack(side="left", fill="both", expand=True)
        # configure scrollbar for MOV text area
        scroll_mov = ttk.Scrollbar(texto_mov_container, orient="vertical",
                                   command=self.texto_mov.yview)
        scroll_mov.pack(side="right", fill="y")
        self.texto_mov.configure(yscrollcommand=scroll_mov.set)
        self.texto_mov.config(font=("Consolas", 10))

        # --- CONTENIDO PESTAÑA MKV (duplicado funcionalmente de AVI/MOV) ---
        mkv_buttons_frame = tk.Frame(self.frame_mkv, bg=COLOR_FRAME)
        mkv_buttons_frame.pack(fill="x", pady=10)

        # Botón para contar archivos MKV en subcarpetas
        self.boton_contar_mkvs = tk.Button(mkv_buttons_frame, text="Contar MKV", width=15,
                           command=self.contar_mkvs_en_subcarpetas,
                           bg=COLOR_BUTTON, fg=COLOR_PROGRESS, relief="flat",
                           activebackground=COLOR_PROGRESS)
        self.boton_contar_mkvs.pack(side="left", padx=5)

        # Botón para mover archivos MKV a la carpeta 'mkv'
        self.boton_mkv = tk.Button(mkv_buttons_frame, text="Mover MKV", width=15,
                       command=self.mover_mkvs_a_carpeta, relief="flat",
                       bg=COLOR_BUTTON, fg=COLOR_PROGRESS,
                       activebackground=COLOR_PROGRESS)
        self.boton_mkv.pack(side="left", padx=5)
        self.boton_mkv["state"] = "disabled"

        # (El botón global "Ver Vacías" se crea en la pestaña Resultados)

        # Botón para buscar archivos MKV repetidos
        self.boton_repetidos_mkv = tk.Button(mkv_buttons_frame, text="Buscar Repetidos", width=15,
                            command=self.buscar_mkvs_repetidos, relief="flat",
                            bg=COLOR_BUTTON, fg=COLOR_TEXT,
                            activebackground=COLOR_PROGRESS)
        self.boton_repetidos_mkv.pack(side="left", padx=5)

        self.label_conteo_mkv = tk.Label(self.frame_mkv, text="", bg=COLOR_FRAME,
                         fg=COLOR_LABEL, anchor="w")
        self.label_conteo_mkv.pack(fill="x", padx=8)

        # Área de texto específica para la pestaña MKV
        texto_mkv_container = ttk.Frame(self.frame_mkv)
        texto_mkv_container.pack(fill="both", expand=True, pady=(10,0), padx=8)
        self.texto_mkv = tk.Text(texto_mkv_container, height=15, width=80, fg=COLOR_TEXT,
                     bg=COLOR_BG, insertbackground=COLOR_LABEL,
                     state="disabled", wrap="word", relief="flat")
        self.texto_mkv.pack(side="left", fill="both", expand=True)
        scroll_mkv = ttk.Scrollbar(texto_mkv_container, orient="vertical",
                                   command=self.texto_mkv.yview)
        scroll_mkv.pack(side="right", fill="y")
        self.texto_mkv.configure(yscrollcommand=scroll_mkv.set)
        self.texto_mkv.config(font=("Consolas", 10))

        # --- CONTENIDO PESTAÑA GRÁFICOS ---
        graficos_buttons_frame = tk.Frame(self.frame_graficos, bg=COLOR_FRAME)
        graficos_buttons_frame.pack(fill="both", expand=True, pady=10, padx=10)

        # Columna 1: Histogramas
        col_histogramas = tk.Frame(graficos_buttons_frame, bg=COLOR_FRAME)
        col_histogramas.pack(side="left", fill="both", expand=True, padx=10)

        tk.Label(col_histogramas, text="📊 HISTOGRAMAS", bg=COLOR_FRAME, fg=COLOR_LABEL,
                 font=("Arial", 10, "bold")).pack(pady=(0, 10))

        self.boton_histograma = tk.Button(col_histogramas, text="📊 Histograma duración",
                                          width=25, command=self.mostrar_histograma_duraciones,
                                          bg=COLOR_BUTTON, fg=COLOR_TEXT, relief="ridge",
                                          activebackground=COLOR_PROGRESS, state="disabled")
        self.boton_histograma.pack(pady=5)

        self.boton_boxplot = tk.Button(col_histogramas, text="📊 Histograma ratio", width=25,
                                       command=self.mostrar_boxplot_ratio,
                                       bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                       activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_boxplot.pack(pady=5)

        self.boton_histograma_altos = tk.Button(col_histogramas, text="📊 Histograma altos",
                                                width=25, command=self.mostrar_histograma_altos,
                                                bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                                activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_histograma_altos.pack(pady=5)

        # Columna 2: Otros Gráficos
        col_otros = tk.Frame(graficos_buttons_frame, bg=COLOR_FRAME)
        col_otros.pack(side="left", fill="both", expand=True, padx=10)

        tk.Label(col_otros, text="📈 OTROS GRÁFICOS", bg=COLOR_FRAME, fg=COLOR_LABEL,
                 font=("Arial", 10, "bold")).pack(pady=(0, 10))

        self.boton_grafico = tk.Button(col_otros, text="📈 Gráfico Duración/Peso", relief="ridge",
                                       command=self.mostrar_grafico, width=25,
                                       bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                       activebackground=COLOR_PROGRESS)
        self.boton_grafico.pack(pady=5)
        ToolTip(self.boton_grafico, "Muestra duración vs peso para los archivos analizados")

        self.boton_ratio_alto = tk.Button(col_otros, text="📈 Ratio vs Alto",
                                          width=25, command=self.mostrar_grafico_ratio_vs_alto,
                                          bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                          activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_ratio_alto.pack(pady=5)

        self.boton_visual = tk.Button(col_otros, text="📊 Visual (Barras)", width=25,
                                    command=lambda: mostrar_grafico_visual(self.resultados,
                                                                           self.carpeta),
                                    bg=COLOR_BUTTON, fg=COLOR_TEXT, state="disabled",
                                    activebackground=COLOR_PROGRESS, relief="ridge")
        self.boton_visual.pack(pady=5)

        self.boton_pie_previsualizar = tk.Button(col_otros,
                             text="🥧 Pie Previsualizar", width=25,
                             command=self.mostrar_pie_previsualizar,
                             bg=COLOR_BUTTON, fg=COLOR_TEXT,
                             activebackground=COLOR_PROGRESS,
                             relief="ridge", state="disabled")
        self.boton_pie_previsualizar.pack(pady=5)
        ToolTip(self.boton_pie_previsualizar,
                "Grafica el resumen de extensiones generado por Pre-visualizar")

        # --- CONTENIDO PESTAÑA RESULTADOS ---
        # Frame para control y progreso
        self.frame3 = tk.Frame(self.frame_resultados, bg=COLOR_FRAME)
        self.frame3.pack(fill="x", pady=5)

        # Añadir aquí el botón de Analizar dentro de la pestaña "Resultados"
        self.boton_parar = tk.Button(self.frame3, text="Parar", width=10,
                         command=self.parar_analisis,
                         bg=COLOR_BUTTON, fg=COLOR_BUTTON_STOP,
                         activebackground=COLOR_PROGRESS)
        # Empaquetar el botón "Analizar" junto al control de progreso
        # para que esté en la pestaña Resultados
        self.boton_analizar.pack(side="left", padx=5)

        # Botón global para ver carpetas vacías (habilitado cuando se selecciona carpeta)
        self.boton_ver_vacias_general = tk.Button(self.frame3, text="🧹 Ver Vacías", width=12,
                                  command=self.ver_carpetas_vacias,
                              bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                              activebackground=COLOR_PROGRESS, state="disabled")
        self.boton_ver_vacias_general.pack(side="left", padx=5)
        ToolTip(self.boton_ver_vacias_general,
                "Lista carpetas vacías dentro de la carpeta seleccionada")

        self.boton_parar.pack(side="left", padx=10)
        self.boton_parar["state"] = "disabled"

        # Barra de progreso y porcentaje
        self.progress = None
        self.label_porcentaje = tk.Label(self.frame3, text="", bg=COLOR_FRAME, fg=COLOR_LABEL)
        self.label_porcentaje.pack(side='left', padx=5)

        # Etiqueta de resultados
        self.label_resultado = tk.Label(self.frame_resultados, text="Resultados: ", width=130,
                                        bg=COLOR_FRAME, fg=COLOR_LABEL, anchor="w")
        self.label_resultado.pack(pady=2, fill="x")

        # Frame para botones de carpetas especiales
        carpetas_frame = tk.Frame(self.frame_resultados, bg=COLOR_FRAME)
        carpetas_frame.pack(fill="x", pady=5)

        # Frame para botones adicionales
        extras_frame = tk.Frame(self.frame_resultados, bg=COLOR_FRAME)
        extras_frame.pack(fill="x", pady=5)

        # Botón para búsqueda avanzada
        self.boton_mostrar_problemas = tk.Button(extras_frame, text="Mostrar problemáticos",
                             command=self.mostrar_videos_problema,
                             bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                             state="disabled")
        self.boton_mostrar_problemas.pack(side="right", padx=5)

        self.boton_mover_problemas = tk.Button(extras_frame, text="Mover problemáticos",
                               command=self.mover_videos_problema,
                               bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                               state="disabled")
        self.boton_mover_problemas.pack(side="right", padx=5)

        self.boton_busqueda_avanzada = tk.Button(extras_frame, text="Búsqueda avanzada",
                            command=self.abrir_busqueda_avanzada, state="disabled",
                            bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT)
        self.boton_busqueda_avanzada.pack(side="right", padx=5)

        # Botón para ver análisis anterior y comentarios
        self.boton_analisis_anterior = tk.Button(extras_frame, text="📊 Análisis anterior",
                            command=self.mostrar_analisis_anterior, state="disabled",
                            bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT)
        self.boton_analisis_anterior.pack(side="right", padx=5)
        ToolTip(self.boton_analisis_anterior, "Ver análisis anterior y comentarios de esta carpeta")

        # Boton para ver errores
        self.boton_print_errores = tk.Button(extras_frame, text="Ver Errores", borderwidth=0,
                             command=self.ver_lista_errores, state="disabled",
                             bg=COLOR_FRAME, fg=COLOR_BUTTON_TEXT,
                             activebackground=COLOR_PROGRESS)
        self.boton_print_errores.pack(side="right", padx=5)

        # Frame para botones de historial
        historial_frame = tk.Frame(self.frame_resultados, bg=COLOR_FRAME)
        historial_frame.pack(fill="x", pady=5)

        # Botón para mostrar historial
        self.boton_mostrar_historial = tk.Button(historial_frame, text="📋 Historial",
                                                 command=self.mostrar_historial_movimientos,
                                                 bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                                                 state="disabled")
        self.boton_mostrar_historial.pack(side="left", padx=5)
        ToolTip(self.boton_mostrar_historial, "Muestra el historial de movimientos realizados")

        # Botón para deshacer último movimiento
        self.boton_deshacer = tk.Button(historial_frame, text="↩️ Deshacer",
                                        command=self.deshacer_ultimo_movimiento,
                                        bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT, state="disabled")
        self.boton_deshacer.pack(side="left", padx=5)
        ToolTip(self.boton_deshacer, "Elimina el último análisis registrado del historial")

        # Botón para exportar historial a CSV
        self.boton_exportar_csv = tk.Button(historial_frame, text="📊 CSV",
                                            command=self.exportar_historial_csv,
                                            bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT, state="disabled")
        self.boton_exportar_csv.pack(side="left", padx=5)
        ToolTip(self.boton_exportar_csv, "Exporta el historial a formato CSV")

        # Botón para exportar historial a JSON
        self.boton_exportar_json = tk.Button(historial_frame, text="📄 JSON",
                                             command=self.exportar_historial_json,
                                             bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                                             state="disabled")
        self.boton_exportar_json.pack(side="left", padx=5)
        ToolTip(self.boton_exportar_json, "Exporta el historial a formato JSON")

        # Botón para limpiar historial
        self.boton_limpiar_historial = tk.Button(historial_frame, text="🗑️ Limpiar",
                                                 command=self.limpiar_historial,
                                                 bg=COLOR_BUTTON_STOP, fg=COLOR_BUTTON_TEXT,
                                                 state="disabled")
        self.boton_limpiar_historial.pack(side="left", padx=5)
        ToolTip(self.boton_limpiar_historial, "Limpia todo el historial de movimientos")

        # Recuadro tipo Text para mostrar archivos
        self.texto_archivos = tk.Text(self.frame_resultados, height=25, width=120, fg=COLOR_TEXT,
                                      bg=COLOR_BG, insertbackground=COLOR_LABEL,
                                      state="disabled", wrap="word", relief="flat")
        self.texto_archivos.pack(pady=2, padx=10, fill="both", expand=True)
        self.texto_archivos.config(font=("Consolas", 10))

        # Cambiar estilos ttk
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TFrame", background=COLOR_FRAME)
        style.configure("TNotebook", background=COLOR_FRAME)
        style.configure("TNotebook.Tab", background=COLOR_BUTTON, foreground=COLOR_BUTTON_TEXT)
        # Configurar pestaña seleccionada con mejor contraste
        style.map("TNotebook.Tab",
              background=[("selected", COLOR_PROGRESS)],
              foreground=[("selected", "#FFFFFF"),
                      ("disabled", COLOR_TAB_DISABLED)])
        style.configure("TProgressbar", troughcolor=COLOR_BG,
                        background=COLOR_PROGRESS, bordercolor=COLOR_FRAME,
                        lightcolor=COLOR_PROGRESS, darkcolor=COLOR_PROGRESS)
        style.configure("TLabel", background=COLOR_FRAME, foreground=COLOR_LABEL)
        style.configure("TButton", background=COLOR_BUTTON, foreground=COLOR_BUTTON_TEXT)

        # Habilitar botones de historial si hay datos previos
        self._habilitar_botones_historial()

    def mostrar_grafico(self):
        """ Llama a la función global mostrar_grafico con los resultados actuales """
        mostrar_grafico(self.resultados, self.carpeta)

    def mostrar_pie_previsualizar(self):
        """Muestra un gráfico de sectores basado en los recuentos de la previsualización"""
        if not self.preview_counts:
            messagebox.askokcancel("Sin datos", "Ejecuta 'Pre-visualizar' antes de graficar.")
            return
        etiquetas = []
        valores = []
        for ext, cantidad in sorted(self.preview_counts.items(), key=lambda item: item[0]):
            etiquetas.append(ext if ext else "sin_ext")
            valores.append(cantidad)
        plt.style.use('fivethirtyeight')
        _, ax = plt.subplots(figsize=(8, 6))
        ax.pie(valores, labels=etiquetas, autopct="%1.1f%%", startangle=140,
               colors=plt.get_cmap('tab20').colors, wedgeprops=dict(edgecolor='k'))
        ax.set_title("Distribución de archivos por extensión (Pre-visualizar)")
        ax.axis('equal')
        plt.tight_layout()
        plt.show()

    def ver_carpetas_vacias(self):
        """Muestra en el cuadro Text las carpetas y subcarpetas vacías 
        dentro de la carpeta seleccionada"""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return
        vacias = []
        for rooti, dirs, files in os.walk(self.carpeta):
            # Si no hay archivos y no hay subcarpetas con archivos
            if not files and not any(os.listdir(os.path.join(rooti, d)) for d in dirs) and not dirs:
                vacias.append(rooti)
        if vacias:
            texto = "Carpetas vacías:\n" + "\n".join(vacias) + "\n"
        else:
            texto = "No hay carpetas vacías.\n"
        self._set_texto_archivos(texto)

    def ver_lista_errores(self):
        """ Muestra los errores encontrados en un diálogo """
        #print(int(len(lista_de_errores)/2), '\n')
        print(lista_de_errores)
        print(" ")

    def seleccionar_carpeta(self):
        """ Abre un diálogo para seleccionar una carpeta """
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.carpeta = carpeta
            self.carpeta_var.set(carpeta)
            self._previsualizacion_hecha = False  # Reset al seleccionar nueva carpeta
            self.boton_analizar.config(text="  🔍 Pre-analizar  ")  # Restaurar texto inicial
            self.boton["state"] = "normal"
            self.boton_analizar["state"] = "normal"
            self.preview_counts = {}
            self.videos_problema = []
            self.boton_pie_previsualizar["state"] = "disabled"
            self.boton_grafico["state"] = "disabled"
            self.boton_avi["state"] = "normal"
            self.boton_mostrar_problemas["state"] = "disabled"
            self.boton_mover_problemas["state"] = "disabled"
            self.boton_busqueda_avanzada["state"] = "disabled"
            # enable MOV-specific buttons when a folder is selected
            try:
                self.boton_mov["state"] = "normal"
            except AttributeError:
                pass
            # enable MKV-specific buttons when a folder is selected
            try:
                self.boton_mkv["state"] = "normal"
            except AttributeError:
                pass

            # Habilitar el botón global "Ver Vacías"
            try:
                self.boton_ver_vacias_general["state"] = "normal"
            except AttributeError:
                pass

            # Habilitar botón de análisis anterior si la carpeta fue analizada
            self._actualizar_boton_analisis_anterior()

            self.boton.configure(bg=COLOR_BUTTON)
            self._actualizar_tabs_formatos({})
        else:
            self.boton_analizar["state"] = "disabled"
            self.boton_avi["state"] = "disabled"
            try:
                self.boton_ver_vacias_general["state"] = "disabled"
            except AttributeError:
                pass
            self.boton_pie_previsualizar["state"] = "disabled"
            self.boton.configure(bg=COLOR_BUTTON_HIGHLIGHT)
            self._actualizar_tabs_formatos({})
            self.boton_mostrar_problemas["state"] = "disabled"
            self.boton_mover_problemas["state"] = "disabled"
            self.boton_busqueda_avanzada["state"] = "disabled"
            self.boton_analisis_anterior["state"] = "disabled"

    def analizar_o_previsualizar(self):
        """Ejecuta previsualización primero, luego análisis completo"""
        if not self._previsualizacion_hecha:
            # Primera pulsación: hacer previsualización
            self.previsualizar_resumen()
            self._previsualizacion_hecha = True
            # Cambiar el nombre del botón
            self.boton_analizar.config(text="   ▶ Analizar   ")
            self.boton_analizar.config(relief="ridge")
        else:
            # Segunda pulsación: hacer análisis completo
            self._previsualizacion_hecha = False  # Reset para próxima carpeta
            self.analizar_carpeta_interno()

    def previsualizar_resumen(self):
        """Muestra un resumen rápido del número de archivos por extensión"""
        if not self.carpeta:
            messagebox.askokcancel("Aviso", "Primero selecciona una carpeta.")
            return

        # Llevar el foco a la pestaña Resultados antes de mostrar el resumen
        self.notebook.select(self.frame_resultados)
        self.texto_archivos.focus_set()
        counts = {}
        for _, _, files in os.walk(self.carpeta):
            for nombre in files:
                ext = os.path.splitext(nombre)[1].lower() or 'sin_ext'
                counts[ext] = counts.get(ext, 0) + 1
        if not counts:
            messagebox.askokcancel("Resultado", "No se encontraron archivos en la carpeta.")
            return
        self.preview_counts = counts
        self.boton_pie_previsualizar["state"] = "normal"
        resumen = ["Previsualización rápida:\n", "Número de archivos por extensión:\n"]
        for ext, cnt in sorted(counts.items(), key=lambda item: item[0]):
            resumen.append(f"- {cnt} archivos {ext}\n")
        texto = "".join(resumen)
        self._set_texto_archivos(texto)
        self._actualizar_tabs_formatos(counts)

    def analizar_carpeta_interno(self):
        """Inicia el análisis real de la carpeta seleccionada"""
        if not self.carpeta:
            messagebox.askokcancel("Aviso", "Primero selecciona una carpeta.")
            return

        # Mostrar aviso si la carpeta fue analizada antes
        self._mostrar_aviso_analisis_previo()

        # Buscar y mover archivos de la carpeta xcut a la raíz
        xcut_dir = os.path.join(self.carpeta, "xcut")
        if os.path.exists(xcut_dir) and os.path.isdir(xcut_dir):
            archivos_movidos = 0
            try:
                # Listar todos los archivos en la carpeta xcut
                for archivo in os.listdir(xcut_dir):
                    ruta_archivo = os.path.join(xcut_dir, archivo)
                    # Solo mover si es un archivo (no una carpeta)
                    if os.path.isfile(ruta_archivo):
                        destino = os.path.join(self.carpeta, archivo)
                        try:
                            shutil.move(ruta_archivo, destino)
                            archivos_movidos += 1
                        except (OSError, shutil.Error) as e:
                            print(f"No se pudo mover {archivo} desde xcut: {e}")

                # Intentar eliminar la carpeta xcut si está vacía
                try:
                    if os.path.exists(xcut_dir) and not os.listdir(xcut_dir):
                        os.rmdir(xcut_dir)
                except (OSError, shutil.Error) as e:
                    print(f"No se pudo eliminar la carpeta xcut: {e}")

                if archivos_movidos > 0:
                    print(f"Se movieron {archivos_movidos} archivos desde xcut a la raíz")
            except (OSError, shutil.Error) as e:
                print(f"Error procesando la carpeta xcut: {e}")

        # Proceder con análisis normal usando threading
        self._parar_analisis = False  # Reset al iniciar
        # -- seleccionar la pestaña "Resultados" automáticamente --
        def seleccionar_resultados():
            try:
                self.notebook.select(self.frame_resultados)
            except (tk.TclError, AttributeError):
                pass
        self.root.after(0, seleccionar_resultados)

        self.root.after(0, lambda: self.boton_parar.config(state="normal"))
        self.root.after(0, lambda: self.boton.config(state="disabled"))
        self.root.after(0, lambda: self.boton_grafico.config(state="disabled"))
        self.root.after(0, lambda: self.boton_histograma.config(state="disabled"))
        self.root.after(0, lambda: self.boton_histograma_altos.config(state="disabled"))
        self.root.after(0, lambda: self.boton_ratio_alto.config(state="disabled"))
        self.root.after(0, lambda: self.boton_avi.config(state="normal"))
        # enable MOV tab controls as well
        def habilitar_otros_botones():
            try:
                self.boton_mov.config(state="normal")
            except AttributeError:
                pass
            try:
                self.boton_mkv.config(state="normal")
            except AttributeError:
                pass
            self.boton_print_errores.config(state="normal")
        self.root.after(0, habilitar_otros_botones)

        threading.Thread(target=self._analizar_videos_thread, args=(self.carpeta,),
                         daemon=True).start()

    def _actualizar_tabs_formatos(self, counts):
        """Activa o desactiva las pestañas AVI/MOV/MKV según los recuentos"""
        formato_tabs = {
            '.avi': self.frame_avi,
            '.mov': self.frame_mov,
            '.mkv': self.frame_mkv,
        }
        for ext, frame in formato_tabs.items():
            has_files = counts.get(ext, 0) > 0
            self.notebook.tab(frame, state="normal" if has_files else "disabled")

    def contar_avis_en_subcarpetas(self):
        """Cuenta todos los archivos .avi en la carpeta seleccionada y sus subcarpetas"""
        if not self.carpeta:
            mensaje = "Primero selecciona una carpeta."
            self.label_resultado.config(text=mensaje)
            self.label_conteo_avi.config(text=mensaje)
            return
        total_avis = 0
        total_roots = 0
        root_list = []
        carpetas_con_avis = []
        for root_dir, _, files in os.walk(self.carpeta):
            avis_en_esta_carpeta = sum(1 for f in files if f.lower().endswith('.avi'))
            total_avis += avis_en_esta_carpeta
            if avis_en_esta_carpeta > 0:
                total_roots += 1
                carpetas_con_avis.append(root_dir)
            root_list.append(root_dir)
        mensaje = (f"Total - {total_avis} - archivos .avi  en "
               f"{total_roots} carpetas de ({len(root_list)})")
        self.label_resultado.config(text=mensaje)
        self.label_conteo_avi.config(text=mensaje)
        # Mostrar en el cuadro de texto
        # también escribir en la caja de la pestaña AVI si existe
        try:
            self.texto_avi.config(state="normal")
            self.texto_avi.delete(1.0, tk.END)
            if carpetas_con_avis:
                self.texto_avi.insert(tk.END, "Carpetas con archivos .avi:\n")
                for carpeta in carpetas_con_avis:
                    self.texto_avi.insert(tk.END, carpeta + "\n")
            else:
                self.texto_avi.insert(tk.END, "No se encontraron carpetas con archivos .avi.\n")
            self.texto_avi.config(state="disabled")
        except tk.TclError:
            # Ignorar errores específicos de tkinter al actualizar el widget Text
            pass
        # mantener comportamiento previo en el Text principal
        if carpetas_con_avis:
            texto = "Carpetas con archivos .avi:\n" + "\n".join(carpetas_con_avis) + "\n"
        else:
            texto = "No se encontraron carpetas con archivos .avi.\n"
        self._set_texto_archivos(texto)

    def mover_avis_a_carpeta(self):
        """Crea una carpeta 'avi' y mueve todos los archivos .avi a esa carpeta 
        dentro de la carpeta seleccionada."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return

        archivos_avi = [f for f in os.listdir(self.carpeta) if f.lower().endswith('.avi')]
        nombre_carpeta1 = os.path.basename(self.carpeta) or self.carpeta

        if not archivos_avi:
            # informar también en la pestaña AVI
            try:
                self.texto_avi.config(state="normal")
                self.texto_avi.insert(tk.END, f"-- {nombre_carpeta1} --   0 archivos .avi\n")
                self.texto_avi.config(state="disabled")
            except tk.TclError:
                # Ignorar errores específicos de tkinter al actualizar el widget Text
                pass
            print(f"-- {nombre_carpeta1} --", "   0 archivos .avi")
            return

        avi_dir = os.path.join(self.carpeta, "avi")
        if not os.path.exists(avi_dir):
            try:
                os.makedirs(avi_dir)
            except (OSError, shutil.Error) as e:
                print(f"No se pudo crear la carpeta 'avi': {e}")
                try:
                    self.texto_avi.config(state="normal")
                    self.texto_avi.insert(tk.END, f"Error creando carpeta 'avi': {e}\n")
                    self.texto_avi.config(state="disabled")
                except tk.TclError:
                    pass
                return

        movidos = 0
        for archivo in archivos_avi:
            origen = os.path.join(self.carpeta, archivo)
            destino = os.path.join(avi_dir, archivo)
            try:
                shutil.move(origen, destino)
                movidos += 1
                try:
                    self.texto_avi.config(state="normal")
                    self.texto_avi.insert(tk.END, f"Movido: {archivo} -> {avi_dir}\n")
                    self.texto_avi.config(state="disabled")
                except tk.TclError:
                    # Ignorar errores específicos de tkinter al actualizar el widget Text
                    pass
            except (OSError, shutil.Error) as e:
                print(f" //No se pudo mover {archivo}: {e}//")
                try:
                    self.texto_avi.config(state="normal")
                    self.texto_avi.insert(tk.END, f"Error moviendo {archivo}: {e}\n")
                    self.texto_avi.config(state="disabled")
                except tk.TclError:
                    # Ignorar errores específicos de tkinter al actualizar el widget Text
                    pass

        try:
            self.texto_avi.config(state="normal")
            self.texto_avi.insert(tk.END,
                                  f"-- {nombre_carpeta1} --  Se movieron [ {movidos} ]"
                                  " archivos .avi\n")
            self.texto_avi.config(state="disabled")
        except tk.TclError:
            # Ignorar errores específicos de tkinter al actualizar el widget Text
            pass

    def contar_movs_en_subcarpetas(self):
        """Cuenta todos los archivos .mov en la carpeta seleccionada y sus subcarpetas"""
        if not self.carpeta:
            mensaje = "Primero selecciona una carpeta."
            self.label_resultado.config(text=mensaje)
            self.label_conteo_mov.config(text=mensaje)
            return
        total_movs = 0
        total_roots = 0
        root_list = []
        carpetas_con_movs = []
        for root_dir, _, files in os.walk(self.carpeta):
            movs_en_esta_carpeta = sum(1 for f in files if f.lower().endswith('.mov'))
            total_movs += movs_en_esta_carpeta
            if movs_en_esta_carpeta > 0:
                total_roots += 1
                carpetas_con_movs.append(root_dir)
            root_list.append(root_dir)
        mensaje = (f"Total - {total_movs} - archivos .mov  en "
               f"{total_roots} carpetas de ({len(root_list)})")
        self.label_resultado.config(text=mensaje)
        self.label_conteo_mov.config(text=mensaje)
        try:
            self.texto_mov.config(state="normal")
            self.texto_mov.delete(1.0, tk.END)
            if carpetas_con_movs:
                self.texto_mov.insert(tk.END, "Carpetas con archivos .mov:\n")
                for carpeta in carpetas_con_movs:
                    self.texto_mov.insert(tk.END, carpeta + "\n")
            else:
                self.texto_mov.insert(tk.END, "No se encontraron carpetas con archivos .mov.\n")
            self.texto_mov.config(state="disabled")
        except tk.TclError:
            pass
        # also mirror to main text box
        if carpetas_con_movs:
            texto = "Carpetas con archivos .mov:\n" + "\n".join(carpetas_con_movs) + "\n"
        else:
            texto = "No se encontraron carpetas con archivos .mov.\n"
        self._set_texto_archivos(texto)

    def mover_movs_a_carpeta(self):
        """Crea una carpeta 'mov' y mueve todos los archivos .mov
        a esa carpeta dentro de la carpeta seleccionada."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return

        archivos_mov = [f for f in os.listdir(self.carpeta) if f.lower().endswith('.mov')]
        nombre_carpeta1 = os.path.basename(self.carpeta) or self.carpeta

        if not archivos_mov:
            try:
                self.texto_mov.config(state="normal")
                self.texto_mov.insert(tk.END, f"-- {nombre_carpeta1} --   0 archivos .mov\n")
                self.texto_mov.config(state="disabled")
            except tk.TclError:
                pass
            print(f"-- {nombre_carpeta1} --", "   0 archivos .mov")
            return

        mov_dir = os.path.join(self.carpeta, "mov")
        if not os.path.exists(mov_dir):
            try:
                os.makedirs(mov_dir)
            except (OSError, shutil.Error) as e:
                print(f"No se pudo crear la carpeta 'mov': {e}")
                try:
                    self.texto_mov.config(state="normal")
                    self.texto_mov.insert(tk.END, f"Error creando carpeta 'mov': {e}\n")
                    self.texto_mov.config(state="disabled")
                except tk.TclError:
                    pass
                return

        movidos = 0
        for archivo in archivos_mov:
            origen = os.path.join(self.carpeta, archivo)
            destino = os.path.join(mov_dir, archivo)
            try:
                shutil.move(origen, destino)
                movidos += 1
                try:
                    self.texto_mov.config(state="normal")
                    self.texto_mov.insert(tk.END, f"Movido: {archivo} -> {mov_dir}\n")
                    self.texto_mov.config(state="disabled")
                except tk.TclError:
                    pass
            except (OSError, shutil.Error) as e:
                print(f" //No se pudo mover {archivo}: {e}//")
                try:
                    self.texto_mov.config(state="normal")
                    self.texto_mov.insert(tk.END, f"Error moviendo {archivo}: {e}\n")
                    self.texto_mov.config(state="disabled")
                except tk.TclError:
                    pass

        try:
            self.texto_mov.config(state="normal")
            self.texto_mov.insert(tk.END,
                                  f"-- {nombre_carpeta1} --  Se movieron [ {movidos} ]"
                                  " archivos .mov\n")
            self.texto_mov.config(state="disabled")
        except tk.TclError:
            pass

    def buscar_movs_repetidos(self):
        """Busca archivos .mov que tengan el mismo nombre base pero con diferente extensión
        y los mueve a una carpeta 'repeat'."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return

        extensiones_video = ('.mp4', '.avi', '.mkv', '.wmv', '.flv', '.webm')
        archivos_repetidos = []

        for root_dir, _, files in os.walk(self.carpeta):
            archivos_mov = [f for f in files if f.lower().endswith('.mov')]

            for archivo_mov in archivos_mov:
                nombre_base = os.path.splitext(archivo_mov)[0]
                for archivo in files:
                    if archivo != archivo_mov and os.path.splitext(archivo)[0] == nombre_base:
                        if archivo.lower().endswith(extensiones_video):
                            archivos_repetidos.append((os.path.join(root_dir, archivo_mov),
                                                       root_dir))
                            break

        if not archivos_repetidos:
            print("No se encontraron archivos .mov repetidos.")
            try:
                self.texto_mov.config(state="normal")
                self.texto_mov.insert(tk.END, "No se encontraron archivos .mov repetidos.\n")
                self.texto_mov.config(state="disabled")
            except tk.TclError:
                pass
            return

        movidos = 0
        for ruta_mov, carpeta_origen in archivos_repetidos:
            repeat_dir = os.path.join(carpeta_origen, "repeat")
            if not os.path.exists(repeat_dir):
                os.makedirs(repeat_dir)

            nombre_archivo = os.path.basename(ruta_mov)
            destino = os.path.join(repeat_dir, nombre_archivo)

            try:
                shutil.move(ruta_mov, destino)
                movidos += 1
                print(f"Movido: {nombre_archivo} -> repeat/")
                try:
                    self.texto_mov.config(state="normal")
                    self.texto_mov.insert(tk.END, f"Movido: {nombre_archivo} -> {repeat_dir}\n")
                    self.texto_mov.config(state="disabled")
                except tk.TclError:
                    pass
            except (OSError, shutil.Error) as e:
                print(f"No se pudo mover {nombre_archivo}: {e}")
                try:
                    self.texto_mov.config(state="normal")
                    self.texto_mov.insert(tk.END, f"No se pudo mover {nombre_archivo}: {e}\n")
                    self.texto_mov.config(state="disabled")
                except tk.TclError:
                    pass

        try:
            self.texto_mov.config(state="normal")
            self.texto_mov.insert(tk.END,
                                  f"Se movieron {movidos} archivos .mov repetidos"
                                  " a carpetas 'repeat'.\n")
            self.texto_mov.config(state="disabled")
        except tk.TclError:
            pass

    def contar_mkvs_en_subcarpetas(self):
        """Cuenta todos los archivos .mkv en la carpeta seleccionada y sus subcarpetas"""
        if not self.carpeta:
            mensaje = "Primero selecciona una carpeta."
            self.label_resultado.config(text=mensaje)
            self.label_conteo_mkv.config(text=mensaje)
            return
        total = 0
        total_roots = 0
        root_list = []
        carpetas = []
        for root_dir, _, files in os.walk(self.carpeta):
            mkvs = sum(1 for f in files if f.lower().endswith('.mkv'))
            total += mkvs
            if mkvs > 0:
                total_roots += 1
                carpetas.append(root_dir)
            root_list.append(root_dir)
        mensaje = (f"Total - {total} - archivos .mkv"
               f"  en {total_roots} carpetas de ({len(root_list)})")
        self.label_resultado.config(text=mensaje)
        self.label_conteo_mkv.config(text=mensaje)
        try:
            self.texto_mkv.config(state="normal")
            self.texto_mkv.delete(1.0, tk.END)
            if carpetas:
                self.texto_mkv.insert(tk.END, "Carpetas con archivos .mkv:\n")
                for c in carpetas:
                    self.texto_mkv.insert(tk.END, c + "\n")
            else:
                self.texto_mkv.insert(tk.END, "No se encontraron carpetas con archivos .mkv.\n")
            self.texto_mkv.config(state="disabled")
        except tk.TclError:
            pass
        if carpetas:
            texto = "Carpetas con archivos .mkv:\n" + "\n".join(carpetas) + "\n"
        else:
            texto = "No se encontraron carpetas con archivos .mkv.\n"
        self._set_texto_archivos(texto)

    def mover_mkvs_a_carpeta(self):
        """Crea una carpeta 'mkv' y mueve todos los archivos .mkv a esa carpeta
        dentro de la carpeta seleccionada."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return
        archivos = [f for f in os.listdir(self.carpeta) if f.lower().endswith('.mkv')]
        nombre_carpeta1 = os.path.basename(self.carpeta) or self.carpeta
        if not archivos:
            try:
                self.texto_mkv.config(state="normal")
                self.texto_mkv.insert(tk.END, f"-- {nombre_carpeta1} --   0 archivos .mkv\n")
                self.texto_mkv.config(state="disabled")
            except tk.TclError:
                pass
            print(f"-- {nombre_carpeta1} --", "   0 archivos .mkv")
            return
        mkv_dir = os.path.join(self.carpeta, "mkv")
        if not os.path.exists(mkv_dir):
            try:
                os.makedirs(mkv_dir)
            except (OSError, shutil.Error) as e:
                try:
                    self.texto_mkv.config(state="normal")
                    self.texto_mkv.insert(tk.END, f"Error creando carpeta 'mkv': {e}\n")
                    self.texto_mkv.config(state="disabled")
                except tk.TclError:
                    pass
                return
        movidos = 0
        for archivo in archivos:
            origen = os.path.join(self.carpeta, archivo)
            destino = os.path.join(mkv_dir, archivo)
            try:
                shutil.move(origen, destino)
                movidos += 1
                try:
                    self.texto_mkv.config(state="normal")
                    self.texto_mkv.insert(tk.END, f"Movido: {archivo} -> {mkv_dir}\n")
                    self.texto_mkv.config(state="disabled")
                except tk.TclError:
                    pass
            except (OSError, shutil.Error) as e:
                try:
                    self.texto_mkv.config(state="normal")
                    self.texto_mkv.insert(tk.END, f"Error moviendo {archivo}: {e}\n")
                    self.texto_mkv.config(state="disabled")
                except tk.TclError:
                    pass
        try:
            self.texto_mkv.config(state="normal")
            self.texto_mkv.insert(tk.END, f"-- {nombre_carpeta1} --"
                                  f"  Se movieron [ {movidos} ] archivos .mkv\n")
            self.texto_mkv.config(state="disabled")
        except tk.TclError:
            pass

    def buscar_mkvs_repetidos(self):
        """Busca archivos .mkv que tengan el mismo nombre base
        pero con diferente extensión y los mueve a 'repeat'."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return
        extensiones_video = ('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm')
        repetidos = []
        for root_dir, _, files in os.walk(self.carpeta):
            mkvs = [f for f in files if f.lower().endswith('.mkv')]
            for archivo_mkv in mkvs:
                base = os.path.splitext(archivo_mkv)[0]
                for archivo in files:
                    if archivo != archivo_mkv and os.path.splitext(archivo)[0] == base:
                        if archivo.lower().endswith(extensiones_video):
                            repetidos.append((os.path.join(root_dir, archivo_mkv), root_dir))
                            break
        if not repetidos:
            try:
                self.texto_mkv.config(state="normal")
                self.texto_mkv.insert(tk.END, "No se encontraron archivos .mkv repetidos.\n")
                self.texto_mkv.config(state="disabled")
            except tk.TclError:
                pass
            return
        movidos = 0
        for ruta, carpeta_origen in repetidos:
            repeat_dir = os.path.join(carpeta_origen, "repeat")
            if not os.path.exists(repeat_dir):
                os.makedirs(repeat_dir)
            nombre = os.path.basename(ruta)
            destino = os.path.join(repeat_dir, nombre)
            try:
                shutil.move(ruta, destino)
                movidos += 1
                try:
                    self.texto_mkv.config(state="normal")
                    self.texto_mkv.insert(tk.END, f"Movido: {nombre} -> {repeat_dir}\n")
                    self.texto_mkv.config(state="disabled")
                except tk.TclError:
                    pass
            except (OSError, shutil.Error) as e:
                try:
                    self.texto_mkv.config(state="normal")
                    self.texto_mkv.insert(tk.END, f"No se pudo mover {nombre}: {e}\n")
                    self.texto_mkv.config(state="disabled")
                except tk.TclError:
                    pass
        try:
            self.texto_mkv.config(state="normal")
            self.texto_mkv.insert(tk.END, f"Se movieron {movidos} archivos .mkv"
                                  " repetidos a carpetas 'repeat'.\n")
            self.texto_mkv.config(state="disabled")
        except tk.TclError:
            pass


    def mostrar_histograma_duraciones(self):
        """Muestra un histograma mejorado de la distribución de duraciones de vídeos."""
        if not self.resultados:
            messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
            return

        duraciones = [r[1] for r in self.resultados]

        # Elegir estilo disponible
        preferred_styles = ['seaborn-v0_8-darkgrid', 'seaborn-darkgrid',
                            'seaborn', 'ggplot', 'default']
        for s in preferred_styles:
            if s in plt.style.available:
                try:
                    plt.style.use(s)
                except (OSError, ValueError, ImportError):
                    continue
                break

        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('#f5f5f5')
        ax.set_facecolor('#ffffff')

        # Calcular número de bins óptimo
        n_bins = max(15, int(np.ceil(np.log2(len(duraciones)) + 1)))

        # Crear histograma con colores degradados
        _, bins, patches = ax.hist(duraciones, bins=n_bins, edgecolor='#2c3e50',
                                   alpha=0.8, linewidth=1.2)

        # Colorear los bins con degradado según frecuencia
        cm = plt.colormaps.get_cmap('RdYlGn_r')
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        col = bin_centers - min(bin_centers)
        if max(col) > 0:
            col /= max(col)
        for c, p in zip(col, patches):
            p.set_facecolor(cm(c))

        # Calcular estadísticas
        media = np.mean(duraciones)
        mediana = np.median(duraciones)
        q1 = np.percentile(duraciones, 25)
        q3 = np.percentile(duraciones, 75)

        # Líneas de referencia con estadísticas
        ax.axvline(media, color='#e74c3c', linestyle='--', linewidth=2.5,
                  label=f'Media: {media:.1f} min', alpha=0.9)
        ax.axvline(mediana, color='#3498db', linestyle='-.', linewidth=2.5,
                  label=f'Mediana: {mediana:.1f} min', alpha=0.9)
        ax.axvline(q1, color='#95a5a6', linestyle=':', linewidth=1.5,
                  label=f'Q1: {q1:.1f} min', alpha=0.7)
        ax.axvline(q3, color='#95a5a6', linestyle=':', linewidth=1.5,
                  label=f'Q3: {q3:.1f} min', alpha=0.7)

        # Zona sombreada para rangos interpretativos
        ax.axvspan(0, 5, alpha=0.1, color='#e74c3c', label='Muy corto (< 5 min)')
        ax.axvspan(5, 20, alpha=0.1, color='#f39c12', label='Corto (5-20 min)')
        ax.axvspan(20, 60, alpha=0.1, color='#2ecc71', label='Normal (20-60 min)')
        if max(duraciones) > 60:
            ax.axvspan(60, max(duraciones) + 5, alpha=0.1, color='#3498db',
                      label='Largo (> 60 min)')

        # Etiquetas y título mejorados
        ax.set_xlabel('Duración (minutos)', fontsize=12, fontweight='bold', color='#2c3e50')
        ax.set_ylabel('Cantidad de vídeos', fontsize=12, fontweight='bold', color='#2c3e50')
        ax.set_title('Distribución de duraciones de vídeos', fontsize=14, fontweight='bold',
                    color='#2c3e50', pad=20)

        # Grid mejorado
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7, color='#bdc3c7')
        ax.set_axisbelow(True)

        # Leyenda mejorada
        legend = ax.legend(loc='upper right', fontsize=10, framealpha=0.95,
                          edgecolor='#2c3e50', fancybox=True, shadow=True, ncol=2)
        legend.get_frame().set_facecolor('#ecf0f1')

        # Estadísticas en texto
        muy_cortos = sum(1 for d in duraciones if d < 5)
        muy_largos = sum(1 for d in duraciones if d > 60)
        stats_text = (f'Total: {len(duraciones)} vídeos\nDesv. Est: {np.std(duraciones):.1f} min\n'
                      f'Rango: {min(duraciones):.1f} - {max(duraciones):.1f} min\n'
                      f'Muy cortos (<5 min): {muy_cortos}\nMuy largos (>60 min): {muy_largos}')
        ax.text(0.5, 0.98, stats_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top', horizontalalignment='center',
               bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.9,
                         edgecolor='#2c3e50', pad=0.8),
               family='monospace', fontweight='bold', color='#2c3e50')

        # Mejorar apariencia general
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#2c3e50')
        ax.spines['bottom'].set_color('#2c3e50')
        ax.tick_params(colors='#2c3e50', labelsize=10)

        plt.tight_layout()
        plt.show()

    def mostrar_histograma_altos(self):
        """Muestra un histograma de la distribución de altos de fotograma."""
        if not self.resultados:
            messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
            return

        altos = [r[3] for r in self.resultados]

        # Elegir estilo disponible
        preferred_styles = ['seaborn-v0_8-darkgrid', 'seaborn-darkgrid',
                            'seaborn', 'ggplot', 'default']
        for s in preferred_styles:
            if s in plt.style.available:
                try:
                    plt.style.use(s)
                except (OSError, ValueError, ImportError):
                    continue
                break

        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('#f5f5f5')
        ax.set_facecolor('#ffffff')

        # Crear el histograma
        n, bins, _patches = ax.hist(altos, bins='auto', color='#7289da',
                                   edgecolor='white', alpha=0.7, rwidth=0.85)

        # Personalización
        plt.title('Distribución de Altos de Fotograma', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Alto (píxeles)', fontsize=12)
        plt.ylabel('Frecuencia (Número de vídeos)', fontsize=12)

        # Añadir etiquetas sobre las barras
        for i, value in enumerate(n):
            if value > 0:
                ax.text(bins[i] + (bins[i+1]-bins[i])/2, value, int(value),
                        ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()

    def mostrar_grafico_ratio_vs_alto(self):
        """Muestra un gráfico de dispersión de Ratio (MB/min) vs Alto de fotograma
        dividido por formato."""
        if not self.resultados:
            messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
            return

        # Separar datos: MKV vs Otros
        mkv_altos, mkv_ratios = [], []
        otros_altos, otros_ratios = [], []

        for r in self.resultados:
            # r = (nombre, duracion, peso, alto)
            nombre, dur, peso, alto = r[0], r[1], r[2], r[3]
            if dur > 0:
                ratio = peso / dur
                ext = os.path.splitext(nombre)[1].lower()
                if ext == '.mkv':
                    mkv_altos.append(alto)
                    mkv_ratios.append(ratio)
                else:
                    otros_altos.append(alto)
                    otros_ratios.append(ratio)

        if not mkv_altos and not otros_altos:
            messagebox.askokcancel("Sin datos", "No hay vídeos con duración válida.")
            return

        # Estilo
        preferred_styles = ['seaborn-v0_8-darkgrid', 'seaborn-darkgrid',
                            'seaborn', 'ggplot', 'default']
        for s in preferred_styles:
            if s in plt.style.available:
                try:
                    plt.style.use(s)
                except (OSError, ValueError, ImportError):
                    continue
                break

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12), sharex=True)
        fig.patch.set_facecolor('#f5f5f5')

        def configurar_subplot(ax, altos, ratios, titulo, color_map):
            ax.set_facecolor('#ffffff')
            if altos:
                scatter = ax.scatter(altos, ratios, alpha=0.6, c=ratios, cmap=color_map,
                                    edgecolors='w', s=100)
                # Líneas de referencia
                ax.axhline(80, color='green', linestyle='--', alpha=0.5, label='Umbral 80 MB/min')
                ax.axhline(150, color='red', linestyle='--', alpha=0.5, label='Umbral 150 MB/min')

                # Caja de estadísticas
                media = np.mean(ratios)
                mediana = np.median(ratios)
                std = np.std(ratios)
                stats_text = (f'Muestras: {len(ratios)}\n'
                             f'Media: {media:.2f}\n'
                             f'Mediana: {mediana:.2f}\n'
                             f'Desv. Est: {std:.2f}\n'
                             f'Min: {min(ratios):.2f}\n'
                             f'Max: {max(ratios):.2f}')

                ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, fontsize=9,
                        verticalalignment='top', bbox=dict(boxstyle='round',
                        facecolor='#ecf0f1', alpha=0.8, edgecolor='#2c3e50'))

                ax.set_title(titulo, fontsize=14, fontweight='bold')
                ax.set_ylabel('Ratio (MB/min)', fontsize=10)
                ax.legend(loc='upper right', fontsize=8)
                return scatter
            else:
                ax.text(0.5, 0.5, "Sin datos para este grupo", ha='center',
                        va='center', transform=ax.transAxes)
                return None

        configurar_subplot(ax1, mkv_altos, mkv_ratios, "Archivos MKV", 'viridis')
        configurar_subplot(ax2, otros_altos, otros_ratios, "Otros Formatos", 'plasma')

        plt.xlabel('Alto de fotograma (píxeles)', fontsize=12)
        fig.suptitle('Relación Ratio (MB/min) vs Alto de Fotograma', fontsize=16, fontweight='bold')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()

    def mostrar_boxplot_ratio(self):
        """Genera dos histogramas de la relación Peso/Duración (MB/min)
        uno para archivos MKV y otro para todos los demás, con cajas de estadísticas."""
        if not self.resultados:
            messagebox.askokcancel("Sin datos", "No hay vídeos válidos para graficar.")
            return

        # Separar ratios por formato (MKV vs otros)
        ratios_mkv = []
        ratios_otros = []

        for r in self.resultados:
            nombre, dur, peso = r[0], r[1], r[2]
            if dur and dur > 0:
                ratio = peso / dur
                ext = os.path.splitext(nombre)[1].lower()
                if ext == '.mkv':
                    ratios_mkv.append(ratio)
                else:
                    ratios_otros.append(ratio)

        if not ratios_mkv and not ratios_otros:
            messagebox.askokcancel("Sin datos", "No hay ratios válidos (duración 0).")
            return

        # Elegir estilo disponible (fallback seguro)
        preferred_styles = ['seaborn-darkgrid', 'seaborn', 'ggplot', 'default']
        for s in preferred_styles:
            if s in plt.style.available:
                try:
                    plt.style.use(s)
                except (OSError, ValueError, ImportError):
                    continue
                break

        # Crear dos subplots (uno arriba, otro abajo)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 11))
        cm = plt.colormaps.get_cmap('viridis')

        # --- Subplot 1: Archivos MKV ---
        if ratios_mkv:
            n_bins = max(10, int(np.ceil(np.log2(len(ratios_mkv)) + 1)))
            _, bins, patches = ax1.hist(ratios_mkv, bins=n_bins, color='#9fb3c8',
                                         edgecolor='#2b5f78', alpha=0.75, linewidth=1.2)

            # Colorear los bins en degradado
            bin_centers = 0.5 * (bins[:-1] + bins[1:])
            col = bin_centers - min(bin_centers)
            if max(col) > 0:
                col /= max(col)
            for c, p in zip(col, patches):
                plt.setp(p, 'facecolor', cm(c))

            # Líneas de referencia
            media_mkv = np.mean(ratios_mkv)
            mediana_mkv = np.median(ratios_mkv)
            std_mkv = np.std(ratios_mkv)
            min_mkv = min(ratios_mkv)
            max_mkv = max(ratios_mkv)

            ax1.axvline(media_mkv, color='#e74c3c', linestyle='--', linewidth=2.5,
                       label=f'Media: {media_mkv:.2f}', alpha=0.9)
            ax1.axvline(mediana_mkv, color='#3498db', linestyle='-.', linewidth=2.5,
                       label=f'Mediana: {mediana_mkv:.2f}', alpha=0.9)

            # Caja de estadísticas
            stats_mkv = (f'n = {len(ratios_mkv)}\nMedia: {media_mkv:.2f} MB/min\n'
                         f'Mediana: {mediana_mkv:.2f} MB/min\nDesv. Est: {std_mkv:.2f}\n'
                         f'Rango: {min_mkv:.2f} - {max_mkv:.2f}')
            ax1.text(0.98, 0.97, stats_mkv, transform=ax1.transAxes,
                    fontsize=10, verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.95,
                             edgecolor='#2c3e50', pad=0.8, linewidth=1.5),
                    family='monospace', fontweight='bold', color='#2c3e50')

            ax1.set_xlabel('Ratio (MB/min)', fontsize=11, fontweight='bold')
            ax1.set_ylabel('Frecuencia', fontsize=11, fontweight='bold')
            ax1.set_title(f'Archivos MKV (n={len(ratios_mkv)})', fontsize=12, fontweight='bold',
                          color='#2c3e50')
            ax1.legend(loc='upper left', fontsize=10, framealpha=0.9, edgecolor='#2c3e50')
            ax1.grid(True, alpha=0.3, linestyle='--')
        else:
            ax1.text(0.5, 0.5, 'Sin datos MKV', ha='center', va='center',
                    transform=ax1.transAxes, fontsize=12, color='gray')
            ax1.set_title('Archivos MKV (n=0)', fontsize=12, fontweight='bold', color='#7f8c8d')

        # --- Subplot 2: Otros formatos ---
        if ratios_otros:
            n_bins = max(10, int(np.ceil(np.log2(len(ratios_otros)) + 1)))
            _, bins, patches = ax2.hist(ratios_otros, bins=n_bins, color='#9fb3c8',
                                         edgecolor='#2b5f78', alpha=0.75, linewidth=1.2)

            # Colorear los bins en degradado
            bin_centers = 0.5 * (bins[:-1] + bins[1:])
            col = bin_centers - min(bin_centers)
            if max(col) > 0:
                col /= max(col)
            for c, p in zip(col, patches):
                plt.setp(p, 'facecolor', cm(c))

            # Líneas de referencia
            media_otros = np.mean(ratios_otros)
            mediana_otros = np.median(ratios_otros)
            std_otros = np.std(ratios_otros)
            min_otros = min(ratios_otros)
            max_otros = max(ratios_otros)

            ax2.axvline(media_otros, color='#e74c3c', linestyle='--', linewidth=2.5,
                       label=f'Media: {media_otros:.2f}', alpha=0.9)
            ax2.axvline(mediana_otros, color='#3498db', linestyle='-.', linewidth=2.5,
                       label=f'Mediana: {mediana_otros:.2f}', alpha=0.9)

            # Caja de estadísticas
            stats_otros = (f'n = {len(ratios_otros)}\nMedia: {media_otros:.2f} MB/min\n'
                           f'Mediana: {mediana_otros:.2f} MB/min\nDesv. Est: {std_otros:.2f}\n'
                           f'Rango: {min_otros:.2f} - {max_otros:.2f}')
            ax2.text(0.98, 0.97, stats_otros, transform=ax2.transAxes,
                    fontsize=10, verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.95,
                             edgecolor='#2c3e50', pad=0.8, linewidth=1.5),
                    family='monospace', fontweight='bold', color='#2c3e50')

            ax2.set_xlabel('Ratio (MB/min)', fontsize=11, fontweight='bold')
            ax2.set_ylabel('Frecuencia', fontsize=11, fontweight='bold')
            ax2.set_title(f'Otros formatos (n={len(ratios_otros)})', fontsize=12, fontweight='bold',
                          color='#2c3e50')
            ax2.legend(loc='upper left', fontsize=10, framealpha=0.9, edgecolor='#2c3e50')
            ax2.grid(True, alpha=0.3, linestyle='--')
        else:
            ax2.text(0.5, 0.5, 'Sin datos', ha='center', va='center',
                    transform=ax2.transAxes, fontsize=12, color='gray')
            ax2.set_title('Otros formatos (n=0)', fontsize=12, fontweight='bold', color='#7f8c8d')

        fig.suptitle('Histograma: distribución de Peso/Duración (MB/min)',
                     fontsize=14, fontweight='bold', y=0.995, color='#2c3e50')
        plt.tight_layout()
        plt.show()

    def mostrar_analisis_anterior(self):
        """Muestra el análisis anterior, comentarios y gráfico comparativo"""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Selecciona una carpeta primero.")
            return

        analisis_anterior = self.gestor_analisis_historico.obtener_analisis_anterior(self.carpeta)
        if not analisis_anterior:
            messagebox.askokcancel("Sin datos", "No hay análisis anterior para esta carpeta.")
            return

        # Crear ventana de diálogo
        ventana = tk.Toplevel(self.root)
        ventana.title("📊 Análisis Anterior y Comparativa")
        ventana.geometry("800x700")
        ventana.resizable(True, True)
        ventana.configure(bg=COLOR_BG)

        # Frame principal con tabs
        notebook = ttk.Notebook(ventana, style='TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # TAB 1: Análisis Anterior
        frame_anterior = tk.Frame(notebook, bg=COLOR_FRAME)
        notebook.add(frame_anterior, text="📈 Análisis Anterior")

        texto_anterior = tk.Text(frame_anterior, height=25, width=95, fg=COLOR_TEXT,
                                bg=COLOR_BG, state="normal", wrap="word", relief="flat")
        texto_anterior.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        texto_anterior.config(font=("Consolas", 9))

        # Mostrar datos del análisis anterior
        fecha_anterior = analisis_anterior['timestamp']
        contenido_anterior = f"""
ANÁLISIS ANTERIOR: {fecha_anterior}
{'='*80}

Total de archivos:     {analisis_anterior['total_archivos']}
Peso total:            {analisis_anterior['peso_total_mb']:.2f} MB
Duración total:        {analisis_anterior['duracion_total_min']:.2f} minutos
Peso promedio:         {analisis_anterior['peso_promedio_mb']:.2f} MB
Duración promedio:     {analisis_anterior['duracion_promedio_min']:.2f} minutos
Alto promedio:         {int(analisis_anterior['alto_promedio'])}p
Altos únicos:          {', '.join(str(a) + 'p' for a in analisis_anterior['altos_unicos'])}
"""
        texto_anterior.insert('1.0', contenido_anterior)
        texto_anterior.config(state="disabled")

        # TAB 2: Comentarios
        frame_comentarios = tk.Frame(notebook, bg=COLOR_FRAME)
        notebook.add(frame_comentarios, text="💬 Comentarios")

        # Área de comentarios anteriores
        tk.Label(frame_comentarios, text="Comentarios previos:", bg=COLOR_FRAME,
                fg=COLOR_LABEL, font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))

        texto_comentarios = tk.Text(frame_comentarios, height=12, width=95, fg=COLOR_TEXT,
                                   bg=COLOR_BG, state="normal", wrap="word", relief="flat")
        texto_comentarios.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        texto_comentarios.config(font=("Consolas", 9))

        comentarios = self.gestor_analisis_historico.obtener_comentarios(self.carpeta)
        if comentarios:
            for com in comentarios:
                fecha_com = com['timestamp']
                texto_comentarios.insert(tk.END, f"[{fecha_com}]\n{com['texto']}\n\n")
        else:
            texto_comentarios.insert(tk.END, "No hay comentarios previos.")
        texto_comentarios.config(state="disabled")

        # Área para nuevo comentario
        tk.Label(frame_comentarios, text="Nuevo comentario:", bg=COLOR_FRAME,
                fg=COLOR_LABEL, font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))

        frame_nuevo_com = tk.Frame(frame_comentarios, bg=COLOR_FRAME)
        frame_nuevo_com.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        entry_comentario = tk.Text(frame_nuevo_com, height=4, width=95, fg=COLOR_TEXT,
                                   bg=COLOR_ENTRY, relief="flat", font=("Consolas", 9))
        entry_comentario.pack(fill=tk.BOTH, expand=True)

        def guardar_comentario():
            comentario = entry_comentario.get('1.0', tk.END).strip()
            if comentario:
                self.gestor_analisis_historico.anadir_comentario(self.carpeta, comentario)
                messagebox.showinfo("Éxito", "Comentario guardado correctamente.")
                entry_comentario.delete('1.0', tk.END)
            else:
                messagebox.showwarning("Advertencia", "El comentario no puede estar vacío.")

        boton_guardar = tk.Button(frame_nuevo_com, text="💾 Guardar comentario",
                                 command=guardar_comentario, bg=COLOR_BUTTON_HIGHLIGHT,
                                 fg=COLOR_BG, font=("Arial", 10, "bold"), padx=10, pady=5)
        boton_guardar.pack(pady=5)

        # TAB 3: Gráfico Comparativo
        frame_grafico = tk.Frame(notebook, bg=COLOR_FRAME)
        notebook.add(frame_grafico, text="📊 Comparativa")

        self._mostrar_grafico_comparativo_interno(frame_grafico, analisis_anterior)

    def _mostrar_grafico_comparativo_interno(self, parent_frame, analisis_anterior):
        """Muestra gráfico comparativo entre análisis anterior y actual"""
        if not self.resultados:
            label = tk.Label(parent_frame, text="No hay datos actuales para comparar.",
                           bg=COLOR_FRAME, fg=COLOR_TEXT)
            label.pack(pady=20)
            return

        # Calcular datos actuales
        peso_total_actual = sum(r[2] for r in self.resultados)
        duracion_total_actual = sum(r[1] for r in self.resultados)
        altos_actual = [r[3] for r in self.resultados]

        # Preparar datos para gráfico
        categorias = ['Total Archivos', 'Peso Total (MB)', 'Duración (min)', 'Alto Promedio']
        anterior = [
            analisis_anterior['total_archivos'],
            analisis_anterior['peso_total_mb'],
            analisis_anterior['duracion_total_min'],
            analisis_anterior['alto_promedio']
        ]
        actual = [
            len(self.resultados),
            peso_total_actual,
            duracion_total_actual,
            sum(altos_actual) / len(altos_actual) if altos_actual else 0
        ]

        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor(COLOR_BG)
        ax.set_facecolor(COLOR_FRAME)

        x = np.arange(len(categorias))
        ancho = 0.35

        barras1 = ax.bar(x - ancho/2, anterior, ancho, label='Anterior',
                        color='#3498db', alpha=0.8, edgecolor='white', linewidth=1.5)
        barras2 = ax.bar(x + ancho/2, actual, ancho, label='Actual',
                        color='#2ecc71', alpha=0.8, edgecolor='white', linewidth=1.5)

        # Añadir valores en las barras
        for barras in [barras1, barras2]:
            for barra in barras:
                altura = barra.get_height()
                ax.text(barra.get_x() + barra.get_width()/2., altura,
                       f'{altura:.1f}', ha='center', va='bottom',
                       fontsize=9, color=COLOR_TEXT, fontweight='bold')

        ax.set_ylabel('Valor', fontsize=11, color=COLOR_TEXT, fontweight='bold')
        ax.set_title('Comparativa: Análisis Anterior vs Actual', fontsize=13,
                    color=COLOR_TEXT, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(categorias, fontsize=10, color=COLOR_TEXT)
        ax.legend(fontsize=10, facecolor=COLOR_FRAME, edgecolor=COLOR_TEXT)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.tick_params(colors=COLOR_TEXT)

        # Colores de spines
        for spine in ax.spines.values():
            spine.set_color(COLOR_TEXT)
            spine.set_alpha(0.3)

        plt.tight_layout()

        # Insertar gráfico en tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def abrir_busqueda_avanzada(self):
        """Abre una ventana para búsqueda avanzada por peso, duración, formato, etc."""
        ventana = tk.Toplevel(self.root)
        ventana.title("🔍 Búsqueda Avanzada")
        ventana.geometry("500x680")
        ventana.resizable(False, False)
        ventana.configure(bg=COLOR_BG)

        # Centrar la ventana en la pantalla
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (ventana.winfo_width() // 2)
        y = (ventana.winfo_screenheight() // 2) - (ventana.winfo_height() // 2)
        ventana.geometry(f"+{x}+{y}")

        # Marco principal con padding
        main_frame = tk.Frame(ventana, bg=COLOR_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título descriptivo
        titulo = tk.Label(main_frame, text="Filtros de Búsqueda",
                         font=("Arial", 14, "bold"),
                         bg=COLOR_BG, fg=COLOR_LABEL)
        titulo.pack(pady=(0, 15))

        # Separador visual
        separador1 = ttk.Separator(main_frame, orient='horizontal')
        separador1.pack(fill=tk.X, pady=(0, 15))

        # ----- SECCIÓN DURACIÓN -----
        frame_duracion = tk.LabelFrame(main_frame, text="⏱️  Duración (minutos)",
                                       bg=COLOR_FRAME, fg=COLOR_LABEL,
                                       font=("Arial", 10, "bold"), padx=10, pady=10)
        frame_duracion.pack(fill=tk.X, pady=10)

        # Duración mínima
        frame_dur_min = tk.Frame(frame_duracion, bg=COLOR_FRAME)
        frame_dur_min.pack(fill=tk.X, pady=5)
        tk.Label(frame_dur_min, text="Mínima:", bg=COLOR_FRAME, fg=COLOR_TEXT,
                width=12).pack(side=tk.LEFT)
        entry_dur_min = tk.Entry(frame_dur_min, width=20, bg=COLOR_ENTRY,
                                fg=COLOR_TEXT, font=("Arial", 10))
        entry_dur_min.pack(side=tk.LEFT, padx=5)
        entry_dur_min.insert(0, "Opcional")
        entry_dur_min.bind("<FocusIn>", lambda e: entry_dur_min.delete(
            0, tk.END) if entry_dur_min.get() == "Opcional" else None)
        entry_dur_min.bind("<FocusOut>", lambda e: entry_dur_min.insert(
            0, "Opcional") if not entry_dur_min.get() else None)

        # Duración máxima
        frame_dur_max = tk.Frame(frame_duracion, bg=COLOR_FRAME)
        frame_dur_max.pack(fill=tk.X, pady=5)
        tk.Label(frame_dur_max, text="Máxima:", bg=COLOR_FRAME, fg=COLOR_TEXT,
                width=12).pack(side=tk.LEFT)
        entry_dur_max = tk.Entry(frame_dur_max, width=20, bg=COLOR_ENTRY,
                                fg=COLOR_TEXT, font=("Arial", 10))
        entry_dur_max.pack(side=tk.LEFT, padx=5)
        entry_dur_max.insert(0, "Opcional")
        entry_dur_max.bind("<FocusIn>", lambda e: entry_dur_max.delete(
            0, tk.END) if entry_dur_max.get() == "Opcional" else None)
        entry_dur_max.bind("<FocusOut>", lambda e: entry_dur_max.insert(
            0, "Opcional") if not entry_dur_max.get() else None)

        # ----- SECCIÓN PESO -----
        frame_peso = tk.LabelFrame(main_frame, text="💾  Peso (MB)",
                                  bg=COLOR_FRAME, fg=COLOR_LABEL,
                                  font=("Arial", 10, "bold"), padx=10, pady=10)
        frame_peso.pack(fill=tk.X, pady=10)

        # Peso mínimo
        frame_peso_min = tk.Frame(frame_peso, bg=COLOR_FRAME)
        frame_peso_min.pack(fill=tk.X, pady=5)
        tk.Label(frame_peso_min, text="Mínimo:", bg=COLOR_FRAME, fg=COLOR_TEXT,
                width=12).pack(side=tk.LEFT)
        entry_peso_min = tk.Entry(frame_peso_min, width=20, bg=COLOR_ENTRY,
                                 fg=COLOR_TEXT, font=("Arial", 10))
        entry_peso_min.pack(side=tk.LEFT, padx=5)
        entry_peso_min.insert(0, "Opcional")
        entry_peso_min.bind("<FocusIn>", lambda e: entry_peso_min.delete(
            0, tk.END) if entry_peso_min.get() == "Opcional" else None)
        entry_peso_min.bind("<FocusOut>", lambda e: entry_peso_min.insert(
            0, "Opcional") if not entry_peso_min.get() else None)

        # Peso máximo
        frame_peso_max = tk.Frame(frame_peso, bg=COLOR_FRAME)
        frame_peso_max.pack(fill=tk.X, pady=5)
        tk.Label(frame_peso_max, text="Máximo:", bg=COLOR_FRAME, fg=COLOR_TEXT,
                width=12).pack(side=tk.LEFT)
        entry_peso_max = tk.Entry(frame_peso_max, width=20, bg=COLOR_ENTRY,
                                 fg=COLOR_TEXT, font=("Arial", 10))
        entry_peso_max.pack(side=tk.LEFT, padx=5)
        entry_peso_max.insert(0, "Opcional")
        entry_peso_max.bind("<FocusIn>", lambda e: entry_peso_max.delete(
            0, tk.END) if entry_peso_max.get() == "Opcional" else None)
        entry_peso_max.bind("<FocusOut>", lambda e: entry_peso_max.insert(
            0, "Opcional") if not entry_peso_max.get() else None)

        # ----- SECCIÓN FORMATO -----
        frame_formato = tk.LabelFrame(main_frame, text="📁  Formato",
                                     bg=COLOR_FRAME, fg=COLOR_LABEL,
                                     font=("Arial", 10, "bold"), padx=10, pady=10)
        frame_formato.pack(fill=tk.X, pady=10)

        tk.Label(frame_formato, text="Extensión (ej: mp4, avi, mkv):",
                bg=COLOR_FRAME, fg=COLOR_TEXT).pack(anchor=tk.W, pady=(0, 5))
        entry_formato = tk.Entry(frame_formato, width=30, bg=COLOR_ENTRY,
                               fg=COLOR_TEXT, font=("Arial", 10))
        entry_formato.pack(fill=tk.X, pady=5)
        entry_formato.insert(0, "Opcional")
        entry_formato.bind("<FocusIn>", lambda e: entry_formato.delete(
            0, tk.END) if entry_formato.get() == "Opcional" else None)
        entry_formato.bind("<FocusOut>", lambda e: entry_formato.insert(
            0, "Opcional") if not entry_formato.get() else None)

        # ----- SECCIÓN ALTO DE FOTOGRAMA -----
        frame_alto = tk.LabelFrame(main_frame, text="📏  Alto de Fotograma (píxeles)",
                                   bg=COLOR_FRAME, fg=COLOR_LABEL,
                                   font=("Arial", 10, "bold"), padx=10, pady=10)
        frame_alto.pack(fill=tk.X, pady=10)

        # Alto mínimo
        frame_alto_min = tk.Frame(frame_alto, bg=COLOR_FRAME)
        frame_alto_min.pack(fill=tk.X, pady=5)
        tk.Label(frame_alto_min, text="Mínimo:", bg=COLOR_FRAME, fg=COLOR_TEXT,
                width=12).pack(side=tk.LEFT)
        entry_alto_min = tk.Entry(frame_alto_min, width=20, bg=COLOR_ENTRY,
                                 fg=COLOR_TEXT, font=("Arial", 10))
        entry_alto_min.pack(side=tk.LEFT, padx=5)
        entry_alto_min.insert(0, "Opcional")
        entry_alto_min.bind("<FocusIn>", lambda e: entry_alto_min.delete(
            0, tk.END) if entry_alto_min.get() == "Opcional" else None)
        entry_alto_min.bind("<FocusOut>", lambda e: entry_alto_min.insert(
            0, "Opcional") if not entry_alto_min.get() else None)

        # Alto máximo
        frame_alto_max = tk.Frame(frame_alto, bg=COLOR_FRAME)
        frame_alto_max.pack(fill=tk.X, pady=5)
        tk.Label(frame_alto_max, text="Máximo:", bg=COLOR_FRAME, fg=COLOR_TEXT,
                width=12).pack(side=tk.LEFT)
        entry_alto_max = tk.Entry(frame_alto_max, width=20, bg=COLOR_ENTRY,
                                 fg=COLOR_TEXT, font=("Arial", 10))
        entry_alto_max.pack(side=tk.LEFT, padx=5)
        entry_alto_max.insert(0, "Opcional")
        entry_alto_max.bind("<FocusIn>", lambda e: entry_alto_max.delete(
            0, tk.END) if entry_alto_max.get() == "Opcional" else None)
        entry_alto_max.bind("<FocusOut>", lambda e: entry_alto_max.insert(
            0, "Opcional") if not entry_alto_max.get() else None)

        # Separador visual
        separador2 = ttk.Separator(main_frame, orient='horizontal')
        separador2.pack(fill=tk.X, pady=15)

        # Marco de botones
        frame_botones = tk.Frame(main_frame, bg=COLOR_BG)
        frame_botones.pack(fill=tk.X, pady=(10, 0))

        def obtener_valor(entry, placeholder):
            """Obtiene el valor del Entry, ignorando placeholders y espacios en blanco"""
            valor = entry.get().strip()
            if valor == placeholder or not valor:
                return None
            return valor

        def buscar_avanzado():
            """ Realiza la búsqueda avanzada según los criterios introducidos """
            try:
                dur_min_val = obtener_valor(entry_dur_min, "Opcional")
                dur_max_val = obtener_valor(entry_dur_max, "Opcional")
                peso_min_val = obtener_valor(entry_peso_min, "Opcional")
                peso_max_val = obtener_valor(entry_peso_max, "Opcional")
                alto_min_val = obtener_valor(entry_alto_min, "Opcional")
                alto_max_val = obtener_valor(entry_alto_max, "Opcional")
                formato_val = obtener_valor(entry_formato, "Opcional")

                dur_min = float(dur_min_val) if dur_min_val else None
                dur_max = float(dur_max_val) if dur_max_val else None
                peso_min = float(peso_min_val) if peso_min_val else None
                peso_max = float(peso_max_val) if peso_max_val else None
                alto_min = int(alto_min_val) if alto_min_val else None
                alto_max = int(alto_max_val) if alto_max_val else None
                formato = formato_val.lower() if formato_val else None
            except ValueError:
                messagebox.showerror("Error", "Por favor,"
                                     " introduce valores numéricos válidos para duración,"
                                     " peso y alto.")
                return

            encontrados = []
            for r in self.resultados:
                nombre, duracion, peso, alto = r[0], r[1], r[2], r[3]
                cumple = True
                if dur_min is not None and duracion < dur_min:
                    cumple = False
                if dur_max is not None and duracion > dur_max:
                    cumple = False
                if peso_min is not None and peso < peso_min:
                    cumple = False
                if peso_max is not None and peso > peso_max:
                    cumple = False
                if alto_min is not None and alto < alto_min:
                    cumple = False
                if alto_max is not None and alto > alto_max:
                    cumple = False
                if formato and not nombre.lower().endswith(f".{formato}"):
                    cumple = False
                if cumple:
                    encontrados.append((nombre, duracion, peso, alto))

            if encontrados:
                lineas = [f"✓ Búsqueda avanzada: {len(encontrados)} resultado(s) encontrado(s)\n\n"]
                for nombre, dur, peso, alt in encontrados:
                    lineas.append(f"{nombre}\t{dur:.2f} min\t{peso:.2f} MB\t{alt}p\n")
                texto = "".join(lineas)
            else:
                texto = "❌ No se encontraron archivos con los criterios especificados.\n"
            self._set_texto_archivos(texto)
            ventana.destroy()

        # Botón Buscar
        boton_buscar = tk.Button(frame_botones, text="🔍 Buscar",
                                command=buscar_avanzado,
                                bg=COLOR_BUTTON_HIGHLIGHT, fg=COLOR_BG,
                                font=("Arial", 11, "bold"),
                                padx=20, pady=8, relief=tk.RAISED,
                                activebackground="#ff7600", activeforeground=COLOR_BG)
        boton_buscar.pack(side=tk.LEFT, padx=5)

        # Botón Cancelar
        boton_cancelar = tk.Button(frame_botones, text="✕ Cancelar",
                                  command=ventana.destroy,
                                  bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
                                  font=("Arial", 11),
                                  padx=20, pady=8, relief=tk.RAISED,
                                  activebackground=COLOR_TAB_DISABLED,
                                  activeforeground=COLOR_BUTTON_TEXT)
        boton_cancelar.pack(side=tk.LEFT, padx=5)

        # Información útil
        info_label = tk.Label(main_frame,
                             text="💡 Todos los campos son opcionales."
                             " Rellena solo los que necesites.",
                             bg=COLOR_BG, fg=COLOR_TEXT, font=("Arial", 9, "italic"))
        info_label.pack(pady=(10, 0))

    def _actualizar_boton_analisis_anterior(self):
        """Habilita el botón de análisis anterior si la carpeta ya fue analizada"""
        if self.carpeta and self.gestor_analisis_historico.carpeta_analizada_antes(self.carpeta):
            self.boton_analisis_anterior.config(state="normal")
        else:
            self.boton_analisis_anterior.config(state="disabled")

    def _mostrar_aviso_analisis_previo(self):
        """Muestra un aviso si la carpeta ya fue analizada antes"""
        if not self.carpeta:
            return

        if self.gestor_analisis_historico.carpeta_analizada_antes(self.carpeta):
            analisis_anterior = self.gestor_analisis_historico.obtener_analisis_anterior(
                self.carpeta)
            fecha_anterior = analisis_anterior['timestamp']
            comentarios = self.gestor_analisis_historico.obtener_comentarios(self.carpeta)

            mensaje = f"📊 Esta carpeta fue analizada anteriormente el {fecha_anterior}"
            if comentarios:
                mensaje += f"\n💬 Hay {len(comentarios)} comentario(s) guardado(s)"

            messagebox.showinfo("Carpeta analizada anteriormente", mensaje)

            # Habilitar el botón de análisis anterior
            self.boton_analisis_anterior.config(state="normal")

    def parar_analisis(self):
        """ Detiene el análisis de vídeos """
        self._parar_analisis = True
        # Calcula el porcentaje analizado hasta el momento
        try:
            if self.progress:
                porcentaje = int(self.progress['value'] / self.progress['maximum'] * 100)
            else:
                porcentaje = 0
        except tk.TclError:
            porcentaje = 0
        print(f"Análisis abortado mediante el botón PARAR. Porcentaje analizado: {porcentaje}%")
        self._detener_procesos_analisis(wait=False)

    def _procesar_video(self, ruta):
        """Carga el clip y devuelve duración/peso (MB/min) y alto"""
        with VideoFileClip(ruta) as clip:
            duracion = clip.duration / 60
            peso = os.path.getsize(ruta) / (1024 * 1024)
            alto = clip.size[1]
        return duracion, peso, alto

    def _mover_archivo_a_errores(self, ruta, archivo):
        """Mueve un archivo a su carpeta 'errores' y devuelve si tuvo éxito"""
        errores_dir = os.path.join(os.path.dirname(ruta), "errores")
        if not os.path.exists(errores_dir):
            try:
                os.makedirs(errores_dir)
            except (OSError, shutil.Error) as exc:
                print(f"No se pudo crear la carpeta 'errores': {exc}")
                return False
        destino = os.path.join(errores_dir, archivo)
        max_intentos = 5
        for intento in range(1, max_intentos + 1):
            try:
                shutil.move(ruta, destino)
                # Registrar el movimiento en el historial
                return True
            except (OSError, shutil.Error) as exc:
                err_num = getattr(exc, "errno", None)
                win_err = getattr(exc, "winerror", None)
                if intento < max_intentos and (win_err == 32 or err_num == errno.EACCES):
                    wait = 0.4 + intento * 0.1
                    print(f"Intento {intento} de mover {archivo} bloqueado; esperando {wait:.1f}s")
                    time.sleep(wait)
                    continue
                print(f"Error al mover {archivo} a 'errores': {exc}")
                return False

    def _detener_procesos_analisis(self, wait=False):
        """Cancela y cierra el executor que analiza vídeos"""
        if self._analisis_future and not self._analisis_future.done():
            try:
                self._analisis_future.cancel()
            except (RuntimeError, CancelledError):
                pass
        if self._analysis_executor:
            try:
                self._analysis_executor.shutdown(wait=wait)
            except (RuntimeError, OSError):
                pass
            finally:
                self._analysis_executor = None
        self._analisis_future = None

    def on_closing(self):
        """Maneja el cierre de la aplicación de forma limpia"""
        self._parar_analisis = True
        self._detener_procesos_analisis(wait=False)

        # Limpiar variables de Tkinter para evitar errores en __del__ (Python 3.13+)
        try:
            if hasattr(self, 'carpeta_var'):
                del self.carpeta_var
        except Exception:
            pass

        # Detener el mainloop y destruir la ventana
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

    def _actualizar_texto_archivos(self, callback):
        """Ejecuta operaciones sobre el Text central desde el hilo principal"""
        def _run():
            try:
                if not self.root.winfo_exists():
                    return
                self.texto_archivos.config(state="normal")
                callback()
            except (tk.TclError, AttributeError):
                pass
            finally:
                try:
                    self.texto_archivos.config(state="disabled")
                except (tk.TclError, AttributeError):
                    pass
        self.root.after(0, _run)

    def _log_to_text(self, mensaje, tag='1.0'):
        """Inserta líneas en la parte superior del Text de forma segura"""
        self._actualizar_texto_archivos(lambda: self.texto_archivos.insert(tag, mensaje))

    def _set_texto_archivos(self, texto):
        """Reemplaza todo el contenido del Text central"""
        def _update():
            self.texto_archivos.delete(1.0, tk.END)
            self.texto_archivos.insert('1.0', texto)
        self._actualizar_texto_archivos(_update)

    def _analizar_videos_thread(self, carpeta):
        """ Función que se ejecuta en un hilo para analizar los vídeos en carpeta y subcarpetas """
        tiempo_inicio = time.time()
        extensiones_video = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
        archivos = []
        rutas_archivos = []
        carpetas_archivos = []
        # Recorrer carpeta y subcarpetas
        for root_dir, _, files in os.walk(carpeta):
            if os.path.basename(root_dir).lower() == "errores":
                continue
            for f in files:
                if f.lower().endswith(extensiones_video):
                    archivos.append(f)
                    rutas_archivos.append(os.path.join(root_dir, f))
                    carpetas_archivos.append(root_dir)
        total = len(rutas_archivos)
        resultados = []
        # Contadores para movimientos realizados durante el análisis
        moved_counts = {'optimizar': 0, 'review': 0, 'errores': 0}

        self._set_texto_archivos("")

        self.videos_problema.clear()
        self._detener_procesos_analisis(wait=False)
        self.root.after(0, self._actualizar_botones_problemas)

        def crear_barra():
            """ Crea la barra de progreso """
            self.progress = ttk.Progressbar(self.frame3, length=800,
                                            mode="determinate", maximum=total)
            self.progress.pack(pady=2)
            self.label_porcentaje.config(text="0%")
            self.frame3.update_idletasks()
        self.root.after(0, crear_barra)
        self._analysis_executor = ThreadPoolExecutor(max_workers=1)

        for idx, (
            archivo, ruta, carpeta_actual
            ) in enumerate(zip(archivos, rutas_archivos, carpetas_archivos), 1):
            if self._parar_analisis:
                break  # Sale del bucle si se pulsó "Parar"
            carpetita = os.path.basename(os.path.dirname(ruta))
            self._log_to_text(f"Analizando archivo: {idx}\n{carpetita} - {archivo}\n")

            if not self._analysis_executor:
                self._analysis_executor = ThreadPoolExecutor(max_workers=1)
            future = self._analysis_executor.submit(self._procesar_video, ruta)
            self._analisis_future = future
            skip_video = False

            try:
                duracion, peso, alto = future.result(timeout=30)
                if duracion > 0:
                    resultados.append((archivo, duracion, peso, ruta, carpeta_actual, alto))
            except TimeoutError:
                self._registrar_video_problema(ruta, archivo, "Timeout >30s")
                self._log_to_text(f"Timeout >30s en {archivo}, registro problemático.\n")
                skip_video = True
            except CancelledError:
                # Cuando se cancela la tarea, continuar sin marcar como problema
                self._log_to_text(f"Análisis cancelado para {archivo}.\n")
                skip_video = True
            except (OSError, ValueError) as e:
                parent_basename = os.path.basename(os.path.dirname(ruta)).lower()
                err_msg = str(e)
                self._log_to_text(err_msg + "\n")
                self._registrar_video_problema(ruta, archivo, err_msg)
                if parent_basename == "errores":
                    print(f"Archivo ya en 'errores', no se mueve: {ruta}")
                skip_video = True

            porcentaje = int((idx / total) * 100)
            self.root.after(0, lambda val=idx,
                            pct=porcentaje: self._actualizar_progreso(val, pct))

            if skip_video:
                continue
            if idx % 5 == 0:
                self.root.after(0, self.frame3.update_idletasks)

        self.root.after(0, lambda: self.boton_parar.config(state="disabled"))
        self._detener_procesos_analisis(wait=True)
        self.root.after(0, self._actualizar_botones_problemas)

        # --- Mover archivos que cumplen la condición a la carpeta
        # "review", "xcut" o "optimizar" ---
        for nombre, duracion, peso, ruta, carpeta_actual, *_extra in resultados:
            # Evita crear subcarpetas dentro de sí mismas (review/xcut/optimizar)
            basename_actual = os.path.basename(carpeta_actual).lower()
            # calcular ratio MB/min de forma segura
            ratio = (peso / duracion) if duracion else 0

            # Prioridad: mover a 'optimizar' si la relación peso/duración es excesiva
            if ratio > 100:
                if basename_actual != "optimizar":
                    optim_dir = os.path.join(carpeta_actual, "optimizar")
                else:
                    optim_dir = carpeta_actual
                if not os.path.exists(optim_dir):
                    os.makedirs(optim_dir)
                destino = os.path.join(optim_dir, nombre)
                try:
                    shutil.move(ruta, destino)
                    moved_counts['optimizar'] += 1
                except (OSError, shutil.Error) as e:
                    print(f"No se pudo mover {nombre} a 'optimizar': {e}")

            elif duracion > 20 and ratio < 50:
                # Verificar que el archivo sea .mkv antes de mover a review
                ext_archivo = os.path.splitext(nombre)[1].lower()
                if ext_archivo == ".mkv":
                    if basename_actual != "review":
                        review_dir = os.path.join(carpeta_actual, "review")
                    else:
                        review_dir = carpeta_actual
                    if not os.path.exists(review_dir):
                        os.makedirs(review_dir)
                    destino = os.path.join(review_dir, nombre)
                    try:
                        shutil.move(ruta, destino)
                        moved_counts['review'] += 1
                    except (OSError, shutil.Error) as e:
                        print(f"No se pudo mover {nombre}: {e}")

        # Calcular estadísticas por extensión y preparar resumen
        # Conteo total de archivos por extensión (a partir de la lista inicial `archivos`)
        counts_by_ext = {}
        for f in archivos:
            ext = os.path.splitext(f)[1].lower() or 'sin_ext'
            counts_by_ext[ext] = counts_by_ext.get(ext, 0) + 1

        # Calcular peso medio por minuto por extensión usando los resultados válidos
        peso_sum_by_ext = {}
        dur_sum_by_ext = {}

        for nombre, dur, peso, ruta, carpeta, alto in resultados:
            ext = os.path.splitext(nombre)[1].lower() or 'sin_ext'
            peso_sum_by_ext[ext] = peso_sum_by_ext.get(ext, 0.0) + peso
            dur_sum_by_ext[ext] = dur_sum_by_ext.get(ext, 0.0) + dur

        avg_by_ext = {}
        for ext in counts_by_ext:
            total_peso = peso_sum_by_ext.get(ext, 0.0)
            total_dur = dur_sum_by_ext.get(ext, 0.0)
            avg = (total_peso / total_dur) if total_dur > 0 else 0.0
            avg_by_ext[ext] = avg

        resumen_por_alto = self.generar_resumen_por_alto(resultados)

        # Preparar texto del resumen
        resumen_lines = []
        resumen_lines.append("\nResumen del análisis:\n")
        resumen_lines.append("="*80 + "\n")

        # Calcular rating
        estrellas_rating, pct_bien, bien_opt, mal_opt, categoria_rating = (
            calcular_rating_optimizacion(resultados))
        rating_info = {
            'estrellas': estrellas_rating,
            'pct_bien': pct_bien,
            'bien_optimizados': bien_opt,
            'mal_optimizados': mal_opt,
            'categoria': categoria_rating
        }
        estrella_llena = "★"
        estrella_vacia = "☆"
        representacion_estrellas = (
            estrella_llena * estrellas_rating + estrella_vacia * (5 - estrellas_rating))

        resumen_lines.append(f"\nRATING DE OPTIMIZACIÓN: {representacion_estrellas} - "
                             f"{categoria_rating}\n")
        resumen_lines.append(f"Archivos bien optimizados (10-100 MB/min): {bien_opt} "
                             f"({pct_bien:.1f}%)\n")
        resumen_lines.append(f"Archivos mal optimizados (>100 MB/min): {mal_opt} "
                             f"({100-pct_bien:.1f}%)\n")
        resumen_lines.append("="*80 + "\n")

        resumen_lines.append("\nNúmero de archivos por extensión:\n")
        for ext, cnt in sorted(counts_by_ext.items(), key=lambda x: x[0]):
            resumen_lines.append(f"- {cnt} archivos {ext}\n")
        resumen_lines.append("\nPeso medio por minuto por extensión:\n")
        for ext, avg in sorted(avg_by_ext.items(), key=lambda x: x[0]):
            resumen_lines.append(f"- {ext}: {avg:.2f} MB/min\n")

        resumen_lines.append("\nPeso medio por minuto por alto de fotograma:\n")
        for alto in sorted(resumen_por_alto.keys()):
            datos = resumen_por_alto[alto]
            resumen_lines.append(
                f"- {alto}p: {datos['promedio']:.2f} MB/min ({datos['conteo']} archivos)\n"
            )

        resumen_lines.append("\nArchivos movidos durante el análisis:\n")
        for k, v in moved_counts.items():
            resumen_lines.append(f"- {v} archivos -> {k}\n")
        if self.videos_problema:
            resumen_lines.append(
                f"\nSe detectaron {len(self.videos_problema)} vídeos problemáticos."
                " Usa 'Mostrar problemáticos' para verlos y"
                " 'Mover problemáticos' para enviarlos a errores.\n")

        resumen_text = "".join(resumen_lines)

        # Preparado el resumen (se mostrará desde 'actualizar_interfaz')

        def destruir_barra():
            if self.progress is not None:
                self.progress.destroy()

        self.root.after(0, lambda: self._actualizar_progreso(total, 100))
        self.root.after(0, destruir_barra)
        self.root.after(0, lambda: self.boton_busqueda_avanzada.config(state="normal"))
        self.root.after(0, lambda: self._actualizar_boton_analisis_anterior())

        # Registrar el análisis en el historial con estadísticas por formato
        # Usar len(resultados) que es la cantidad de videos procesados correctamente
        self.gestor_historial.registrar_analisis(
            carpeta=self.carpeta,
            counts_by_ext=counts_by_ext,
            avg_by_ext=avg_by_ext,
            total_archivos=len(resultados),
            rating=rating_info
        )

        # Actualiza resultados para mostrar solo nombre, duracion, peso, alto
        self.resultados = [(nombre, duracion, peso, alto) for nombre, duracion,
                           peso, _, _, alto in resultados]

        # Registrar análisis en historial
        self.gestor_analisis_historico.registrar_analisis(self.carpeta, self.resultados)

        tiempo_fin = time.time()  # <-- Añade esto justo antes de actualizar_interfaz
        tiempo_total = tiempo_fin - tiempo_inicio

        def actualizar_interfaz():
            if not self.resultados:
                self.label_resultado.config(text="No se encontraron vídeos válidos.")
                self.boton_grafico["state"] = "disabled"
                self.boton_histograma["state"] = "disabled"
                self.boton_histograma_altos["state"] = "disabled"
                self.boton_ratio_alto["state"] = "disabled"
                self.boton_visual["state"] = "disabled"
                self.boton["state"] = "normal"
                return
            peso_medio = calcular_peso_medio(self.resultados)
            duracion_media = calcular_duracion_media(self.resultados)
            estrellas, _pct_bien, _bien_opt, _mal_opt, categoria = (
                calcular_rating_optimizacion(self.resultados))

            total_archivos = len(self.resultados)

            # Crear representación visual de estrellas
            estrella_llena = "★"
            estrella_vacia = "☆"
            representacion_estrellas = estrella_llena * estrellas + estrella_vacia * (5 - estrellas)

            resultados_text =(f"Peso medio por minuto: {peso_medio:.2f} MB/min"
                     f"   |   Duración media: {duracion_media:.1f} min"
                     f"   |   Total archivos: {total_archivos}"
                     f"   |   Tiempo analizando: {tiempo_total:.1f} s"
                     f"   |   Tiempo por video: {tiempo_total/total_archivos:.2f} s"
                     f"   |   Rating: {representacion_estrellas} ({categoria})"
                     f"   |   Errores: {int(len(lista_de_errores)/2)}")
            self.label_resultado.config(text=resultados_text)
            self.boton_grafico["state"] = "normal"
            self.boton_histograma["state"] = "normal"
            self.boton_histograma_altos["state"] = "normal"
            self.boton_ratio_alto["state"] = "normal"
            self.boton["state"] = "normal"
            try:
                self.boton_analizar["state"] = "normal"
            except AttributeError:
                pass

            # Habilitar/deshabilitar botón Boxplot según número de ratios válidos
            # Condición: necesitamos al menos 3 vídeos con duración > 0
            # para que el boxplot tenga sentido
            valid_ratios_count = sum(1 for r in self.resultados if r[1] and r[1] > 0)
            if valid_ratios_count >= 3:
                self.boton_boxplot["state"] = "normal"
            else:
                self.boton_boxplot["state"] = "disabled"
                # Add a lightweight tooltip explaining the requirement (appears on hover)
                ToolTip(self.boton_boxplot,
                        "Se necesitan al menos 3 vídeos con duración > 0 para mostrar el boxplot.")

            # --- Cambia el estado y tooltip del botón Visual según el número de archivos ---
            if total_archivos > 100:
                self.boton_visual["state"] = "disabled"
                ToolTip(self.boton_visual, "demasiados videos")
            else:
                self.boton_visual["state"] = "normal"
                # Elimina tooltip si existe (crea uno vacío)
                ToolTip(self.boton_visual, "")

            # Mostrar solo el resumen en la pestaña Resultados
            self._set_texto_archivos(resumen_text)

        self.root.after(0, actualizar_interfaz)

    def _actualizar_progreso(self, valor, porcentaje):
        try:
            if self.progress:
                self.progress.config(value=valor)
            self.label_porcentaje.config(text=f"{porcentaje}%")
        except (tk.TclError, AttributeError):
            pass  # La barra o el label ya no existen, ignora el error

    def generar_resumen_por_alto(self, resultados=None):
        """Devuelve estadísticas agregadas (conteo/promedio) por altura"""
        resultados = resultados if resultados is not None else self.resultados
        resumen = {}
        for registro in resultados:
            if len(registro) < 4:
                continue
            alto = registro[-1]
            duracion = registro[1]
            peso = registro[2]
            datos = resumen.setdefault(alto, {
                'peso_total': 0.0,
                'dur_total': 0.0,
                'conteo': 0
            })
            datos['peso_total'] += peso
            datos['dur_total'] += duracion
            datos['conteo'] += 1
        for datos in resumen.values():
            dur_total = datos['dur_total']
            datos['promedio'] = (datos['peso_total'] / dur_total) if dur_total > 0 else 0.0
        return resumen

    def _registrar_video_problema(self, ruta, archivo, motivo):
        """Registra un video como problemático para mostrar/mover luego"""
        carpeta_actual = os.path.basename(os.path.dirname(ruta))
        lista_de_errores.append(carpeta_actual)
        lista_de_errores.append(archivo)
        self.videos_problema.append({
            'ruta': ruta,
            'archivo': archivo,
            'motivo': motivo,
        })

    def _actualizar_botones_problemas(self):
        estado = "normal" if self.videos_problema else "disabled"
        try:
            self.boton_mostrar_problemas["state"] = estado
            self.boton_mover_problemas["state"] = estado
        except tk.TclError:
            pass

    def mostrar_videos_problema(self):
        """Muestra en una ventana los vídeos problemáticos registrados"""
        if not self.videos_problema:
            messagebox.askokcancel("Videos problemáticos",
                                   "No hay vídeos problemáticos registrados.")
            return
        ventana = tk.Toplevel(self.root)
        ventana.title("Vídeos problemáticos")
        ventana.configure(bg=COLOR_FRAME)
        contenedor = ttk.Frame(ventana)
        contenedor.pack(fill="both", expand=True)
        texto = tk.Text(contenedor, height=20, width=100, bg=COLOR_BG, fg=COLOR_TEXT)
        texto.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        texto.config(state="normal")
        for idx, entrada in enumerate(self.videos_problema, 1):
            texto.insert(tk.END, f"{idx}. {entrada['archivo']} - {entrada['motivo']}\n")
            texto.insert(tk.END, f"   {entrada['ruta']}\n\n")
        texto.config(state="disabled")
        scroll = ttk.Scrollbar(contenedor, orient="vertical", command=texto.yview)
        scroll.pack(side="right", fill="y")
        texto.configure(yscrollcommand=scroll.set)

    def mover_videos_problema(self):
        """Mueve manualmente los vídeos problemáticos registrados a la carpeta 'errores'"""
        if not self.videos_problema:
            messagebox.askokcancel("Videos problemáticos",
                                   "No hay vídeos problemáticos registrados.")
            return
        pendientes = list(self.videos_problema)
        movidos = 0
        ya_en_errores = 0
        for entrada in pendientes:
            ruta = entrada['ruta']
            archivo = entrada['archivo']
            parent_basename = os.path.basename(os.path.dirname(ruta)).lower()
            if parent_basename == "errores":
                ya_en_errores += 1
                continue
            if self._mover_archivo_a_errores(ruta, archivo):
                movidos += 1
        self.videos_problema.clear()
        self.root.after(0, self._actualizar_botones_problemas)
        mensaje = f"Movidos {movidos} vídeos a errores." if movidos else "No se movió ningún vídeo."
        if ya_en_errores:
            mensaje += f" {ya_en_errores} ya estaban en 'errores'."
        self._log_to_text(mensaje + "\n")
        messagebox.showinfo("Videos problemáticos", mensaje)

    def mostrar_historial_movimientos(self):
        """Muestra una ventana con el historial de análisis realizados"""
        # Recargar el historial desde el archivo para asegurar que está actualizado
        self.gestor_historial.cargar_historial()

        if not self.gestor_historial.historial:
            messagebox.showinfo("Historial", "No hay análisis registrados aún.")
            return

        ventana = tk.Toplevel(self.root)
        ventana.title("Historial de Análisis")
        ventana.geometry("1000x800")
        ventana.configure(bg=COLOR_BG)

        # Frame superior con información
        frame_info = tk.Frame(ventana, bg=COLOR_FRAME)
        frame_info.pack(fill="x", padx=5, pady=5)

        resumen = self.gestor_historial.obtener_resumen()
        label_info = tk.Label(frame_info, text=resumen, bg=COLOR_FRAME,
                              fg=COLOR_LABEL, font=("Arial", 10, "bold"))
        label_info.pack(pady=5)

        # Texto con scroll para mostrar el historial
        frame_texto = ttk.Frame(ventana)
        frame_texto.pack(fill="both", expand=True, padx=5, pady=5)

        texto = tk.Text(frame_texto, height=25, width=110, bg=COLOR_BG, fg=COLOR_TEXT,
                       insertbackground=COLOR_LABEL, state="normal", wrap="word")
        texto.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(frame_texto, orient="vertical", command=texto.yview)
        scroll.pack(side="right", fill="y")
        texto.configure(yscrollcommand=scroll.set)
        texto.config(font=("Consolas", 9))

        # Llenar el texto con el historial de análisis
        for analisis in reversed(self.gestor_historial.historial):
            timestamp = analisis.get('timestamp', 'N/A')
            carpeta = analisis.get('carpeta', 'N/A')
            total_archivos = analisis.get('total_archivos', 0)
            veces = analisis.get('veces', 1)

            # Encabezado del análisis
            linea_encabezado = f"\n\n\n{'='*120}\n"
            veces_str = f" (Repetido {veces} veces)" if veces > 1 else ""
            linea_encabezado += (f"Fecha: {timestamp} | Carpeta: {carpeta} | "
                                 f"Total: {total_archivos} "
            f"archivos{veces_str}\n")
            linea_encabezado += f"{'='*120}\n"
            texto.insert(tk.END, linea_encabezado)

            # Estadísticas por formato
            stats = analisis.get('estadisticas_por_formato', {})
            if stats:
                texto.insert(tk.END, "Estadísticas por formato:\n")
                for ext in sorted(stats.keys()):
                    cant = stats[ext]['cantidad']
                    ratio = stats[ext]['ratio_promedio_mb_min']
                    linea = (f"  {ext:10} | Cantidad: {cant:4} | "
                             f"Ratio promedio: {ratio:7.2f} MB/min\n")
                    texto.insert(tk.END, linea)
            else:
                texto.insert(tk.END, "Sin estadísticas disponibles.\n")

            rating = analisis.get('rating')
            if rating:
                linea_rating = (
                    f"Rating: {rating.get('estrellas', 0)}★ ({rating.get('categoria', 'N/A')}) | "
                    f"{rating.get('pct_bien', 0):.1f}% bien | "
                    f"{rating.get('bien_optimizados', 0)} bien / {rating.get('mal_optimizados',
                    0)} mal\n"
                )
            else:
                linea_rating = "Rating: no disponible\n"
            texto.insert(tk.END, linea_rating)

        texto.config(state="disabled")

    def deshacer_ultimo_movimiento(self):
        """Elimina el último análisis registrado del historial"""
        exito, mensaje = self.gestor_historial.deshacer_ultimo()

        if exito:
            messagebox.showinfo("Deshacer", f"✓ {mensaje}")
            print(f"Deshacer exitoso: {mensaje}")
            self._habilitar_botones_historial()
        else:
            messagebox.showerror("Error", f"✗ {mensaje}")
            print(f"Error al deshacer: {mensaje}")

    def exportar_historial_csv(self):
        """Exporta el historial a un archivo CSV"""
        if not self.gestor_historial.historial:
            messagebox.showwarning("Historial vacío", "No hay movimientos para exportar.")
            return

        archivo_salida = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"movimientos_historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if archivo_salida:
            exito, mensaje = self.gestor_historial.exportar_csv(archivo_salida)
            if exito:
                messagebox.showinfo("Exportación exitosa", mensaje)
                print(f"CSV exportado: {archivo_salida}")
            else:
                messagebox.showerror("Error en exportación", mensaje)

    def exportar_historial_json(self):
        """Exporta el historial a un archivo JSON"""
        if not self.gestor_historial.historial:
            messagebox.showwarning("Historial vacío", "No hay movimientos para exportar.")
            return

        archivo_salida = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"movimientos_historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if archivo_salida:
            exito, mensaje = self.gestor_historial.exportar_json(archivo_salida)
            if exito:
                messagebox.showinfo("Exportación exitosa", mensaje)
                print(f"JSON exportado: {archivo_salida}")
            else:
                messagebox.showerror("Error en exportación", mensaje)

    def limpiar_historial(self):
        """Limpia todo el historial con confirmación"""
        if not self.gestor_historial.historial:
            messagebox.showinfo("Historial vacío", "No hay movimientos para limpiar.")
            return

        confirmacion = messagebox.askyesno(
            "Confirmar limpieza",
            f"¿Deseas eliminar los {len(self.gestor_historial.historial)} movimientos"
            " registrados?\nEsta acción no se puede deshacer."
        )

        if confirmacion:
            self.gestor_historial.limpiar_historial()
            messagebox.showinfo("Historial", "Historial limpiado correctamente.")
            print("Historial limpiado")
            self._habilitar_botones_historial()

    def _habilitar_botones_historial(self):
        """Habilita los botones de historial si hay datos en el historial (seguro para hilos)"""
        def _update():
            try:
                if self.gestor_historial.historial:
                    self.boton_mostrar_historial["state"] = "normal"
                    self.boton_deshacer["state"] = "normal"
                    self.boton_exportar_csv["state"] = "normal"
                    self.boton_exportar_json["state"] = "normal"
                    self.boton_limpiar_historial["state"] = "normal"
                else:
                    self.boton_mostrar_historial["state"] = "disabled"
                    self.boton_deshacer["state"] = "disabled"
                    self.boton_exportar_csv["state"] = "disabled"
                    self.boton_exportar_json["state"] = "disabled"
                    self.boton_limpiar_historial["state"] = "disabled"
            except (tk.TclError, AttributeError):
                pass
        self.root.after(0, _update)

    def buscar_avis_repetidos(self):
        """Busca archivos .avi que tengan el mismo nombre base pero con diferente extensión
        y los mueve a una carpeta 'repeat'."""
        if not self.carpeta:
            messagebox.askokcancel("Advertencia", "Primero selecciona una carpeta.")
            return

        extensiones_video = ('.mp4', '.mov', '.mkv', '.wmv', '.flv', '.webm')
        archivos_repetidos = []

        # Recorrer carpeta y subcarpetas
        for root_dir, _, files in os.walk(self.carpeta):
            archivos_avi = [f for f in files if f.lower().endswith('.avi')]

            for archivo_avi in archivos_avi:
                nombre_base = os.path.splitext(archivo_avi)[0]

                # Buscar si existe el mismo nombre con otra extensión
                for archivo in files:
                    if archivo != archivo_avi and os.path.splitext(archivo)[0] == nombre_base:
                        if archivo.lower().endswith(extensiones_video):
                            archivos_repetidos.append((os.path.join(root_dir, archivo_avi),
                                                       root_dir))
                            break

        if not archivos_repetidos:
            print("No se encontraron archivos .avi repetidos.")
            try:
                self.texto_avi.config(state="normal")
                self.texto_avi.insert(tk.END, "No se encontraron archivos .avi repetidos.\n")
                self.texto_avi.config(state="disabled")
            except tk.TclError:
                pass
            #messagebox.askokcancel("Resultado", "No se encontraron archivos .avi repetidos.")
            return

        # Mover archivos repetidos a carpeta 'repeat'
        movidos = 0
        for ruta_avi, carpeta_origen in archivos_repetidos:
            repeat_dir = os.path.join(carpeta_origen, "repeat")
            if not os.path.exists(repeat_dir):
                os.makedirs(repeat_dir)

            nombre_archivo = os.path.basename(ruta_avi)
            destino = os.path.join(repeat_dir, nombre_archivo)

            try:
                shutil.move(ruta_avi, destino)
                movidos += 1
                print(f"Movido: {nombre_archivo} -> repeat/")
                try:
                    self.texto_avi.config(state="normal")
                    self.texto_avi.insert(tk.END, f"Movido: {nombre_archivo} -> {repeat_dir}\n")
                    self.texto_avi.config(state="disabled")
                except tk.TclError:
                    # Ignorar errores de actualización del widget Text
                    # (por ejemplo, si la interfaz se cerró)
                    pass
            except (OSError, shutil.Error) as e:
                print(f"No se pudo mover {nombre_archivo}: {e}")
                try:
                    self.texto_avi.config(state="normal")
                    self.texto_avi.insert(tk.END, f"No se pudo mover {nombre_archivo}: {e}\n")
                    self.texto_avi.config(state="disabled")
                except tk.TclError:
                    # Ignorar errores de actualización del widget Text relacionados con Tkinter
                    pass

        print(f"Se movieron {movidos} archivos .avi repetidos a carpetas 'repeat'.")
        try:
            self.texto_avi.config(state="normal")
            self.texto_avi.insert(tk.END,
                                  f"Se movieron {movidos} archivos .avi repetidos"
                                  " a carpetas 'repeat'.\n")
            self.texto_avi.config(state="disabled")
        except tk.TclError:
            # Ignorar errores específicos de tkinter al actualizar el widget Text
            pass
        #messagebox.askokcancel("Resultado", f"Se movieron {movidos} archivos .avi repetidos.")

if __name__ == "__main__":
    root = tk.Tk()
    # Establecer tamaño fijo de la ventana
    root.geometry("1080x680")
    root.resizable(False, False)  # Deshabilitar redimensionamiento
    app = AnalizadorVideosApp(root)
    root.mainloop()
