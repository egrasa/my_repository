"""CSV-backed item loading and runtime path helpers."""

import csv
import os
import sys

from app_constants import CSV_COLUMNS


def get_runtime_base_dir() -> str:
    """Return the directory used to locate bundled application files."""
    if getattr(sys, 'frozen', False):
        bundled_dir = getattr(sys, '_MEIPASS', None)
        if bundled_dir:
            return bundled_dir
    return os.path.dirname(os.path.abspath(__file__))


def load_items(csv_path: str) -> list:
    """Load items from a CSV file and return normalized dictionaries."""
    items = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as file_handle:
            reader = csv.DictReader(file_handle)
            if reader.fieldnames:
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
            for row in reader:
                row = {(key or '').strip(): value for key, value in row.items()}
                try:
                    price = float(row.get('precio', 0))
                except ValueError:
                    price = 0.0

                tipo_raw = row.get('tipo', '').strip()
                try:
                    tipo_val = int(tipo_raw) if tipo_raw else 0
                except ValueError:
                    tipo_val = 0

                items.append({
                    'nombre': row.get('nombre', ''),
                    'precio': price,
                    'categoria': row.get('categoria', ''),
                    'tipo': tipo_val,
                })
    except FileNotFoundError:
        pass
    return items


def make_csv_if_missing(path: str, rows: list) -> None:
    """Create a CSV file with default rows if it does not exist yet."""
    if os.path.exists(path):
        return

    is_top = 'top' in os.path.basename(path).lower()
    default_tipo = 0 if is_top else 1

    with open(path, 'w', newline='', encoding='utf-8') as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            if len(row) == 3:
                writer.writerow([row[0], row[1], row[2], default_tipo])
            else:
                writer.writerow(row)
