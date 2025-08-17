""" History Tracker Module
This module provides functionality to log file creation events,
retrieve the history of these events,
and clear the history. It stores the history in a JSON file.
"""

import json
import os
from datetime import datetime

HISTORY_DIR = os.path.dirname(os.path.abspath(__file__))

HISTORY_FILE = os.path.join(
    HISTORY_DIR,
    "carpetizador_history.json"
)

def log_file_creation(
    filename,
    file_count,
    total_size_gb,
    carpeta_origen,
    ruta_completa=None,
    carpetas_procesadas=None,
    archivos_procesados=None
):
    """
    Registra la creación de un archivo en el historial.

    Args:
        filename (str): Nombre del archivo creado
        file_count (int): Cantidad de carpetas procesadas (puede ser redundante)
        total_size_gb (float): Tamaño total en GB
        carpeta_origen (str): Ruta de la carpeta origen
        ruta_completa (str, optional): Ruta completa de la carpeta procesada
        carpetas_procesadas (int, optional): Total de carpetas procesadas
        archivos_procesados (int, optional): Total de archivos procesados
    """
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    new_entry = {
        'timestamp': datetime.now().isoformat(),
        'filename': filename,
        'file_count': file_count,
        'total_size_gb': round(total_size_gb, 2),
        'carpeta_origen': carpeta_origen,
        'ruta_completa': ruta_completa if ruta_completa else carpeta_origen,
        'fecha_legible': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'carpetas_procesadas': carpetas_procesadas,
        'archivos_procesados': archivos_procesados
    }

    history.append(new_entry)

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def get_history():
    """
    Obtiene todo el historial registrado.
    
    Returns:
        list: Lista de entradas del historial
    """
    if not os.path.exists(HISTORY_FILE):
        return []

    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def clear_history():
    """
    Limpia todo el historial.
    """
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
