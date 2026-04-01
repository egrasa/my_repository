"""Shared constants for Outfit Price Calculator."""

DEFAULT_TOP_ITEMS = [
    ('bra', 50, 'basic', 0),
    ('transparent bra', 80, 'normal', 0),
    ('bodysuit', 50, 'basic', 2),
    ('transparent bodysuit', 100, 'normal', 2),
    ('regular dress', 50, 'basic', 2),
    ('transparent dress', 100, 'normal', 2),
    ('towel', 100, 'normal', 2),
    ('small towel', 150, 'normal', 2),
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
    ('transparent panties', 80, 'normal', 1),
    ('bodysuit', 50, 'basic', 2),
    ('transparent bodysuit', 100, 'normal', 2),
    ('regular dress', 50, 'basic', 2),
    ('regular skirt/shorts', 50, 'basic', 1),
    ('transparent dress', 100, 'normal', 2),
    ('towel', 100, 'normal', 2),
    ('small towel', 150, 'normal', 2),
    ('transparent skirt', 200, 'normal', 1),
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

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 780
HERO_PANEL_HEIGHT = 90
SELECTOR_PANEL_HEIGHT = 165
TOTAL_PANEL_HEIGHT = 320
ITEM_NAMES_PANEL_HEIGHT = 80
QUICK_NOTES_HEIGHT = 180
FOOTER_PANEL_HEIGHT = 40
TOTAL_METRIC_CARD_WIDTH = 120
TOTAL_METRIC_CARD_HEIGHT = 60

FONT_LABEL = ('Segoe UI', 8)
FONT_INFO = ('Segoe UI', 8, 'bold')
FONT_TOTAL = ('Segoe UI', 40, 'bold')
FONT_NAME = ('Segoe UI', 14, 'bold')
FONT_DUP = ('Segoe UI', 8)

COLOR_TOTAL_LOW = '#2E7D32'
COLOR_TOTAL_MID = '#F57C00'
COLOR_TOTAL_HIGH = '#C62828'
COLOR_DUP_TEXT = '#555555'

THRESH_MID = 180
THRESH_HIGH = 360

THEMES = {
    'light': {
        'bg': '#F7F2EC',
        'frame': '#FDF9F5',
        'frame_elevated': '#ffffff',
        'shadow': '#EBE2D8',
        'text': '#2A3741',
        'text_secondary': '#73808A',
        'label': '#3B4A54',
        'button': '#5E8CA3',
        'button_text': '#ffffff',
        'button_hover': '#4E7D93',
        'separator': '#E8DDD2',
        'accent': '#6B9DA4',
        'accent_hover': '#5E8F96',
        'border': '#DED2C5',
        'hero_text': '#FFFFFF',
        'hero_subtext': '#EDF8F7',
        'chip_bg': '#FFFFFF',
        'chip_text': '#5D8F96',
        'combo_fill': '#F3E5BF',
        'combo_shell': '#E9DBB0',
        'combo_text': '#2A2F35',
        'icon_button_bg': '#FFFDFC',
        'random_button': '#EBCDD8',
        'random_button_hover': '#E1BEC9',
        'random_button_text': '#3A2B34',
        'success': '#8EB59A',
        'success_hover': '#7EA58B',
        'info': '#8AAFC4',
        'info_hover': '#7AA0B6',
        'warning': '#D8B07B',
        'warning_hover': '#C89F6A',
        'danger': '#D99890',
        'danger_hover': '#CB877F',
        'muted_button': '#E9DFD5',
        'muted_button_hover': '#DED2C5',
    },
    'dark': {
        'bg': '#232A31',
        'frame': '#2D363E',
        'frame_elevated': '#37414A',
        'shadow': '#1A2026',
        'text': '#E8F0F6',
        'text_secondary': '#C2CDD7',
        'label': '#DEE7EE',
        'button': '#6E9FB8',
        'button_text': '#F7FBFF',
        'button_hover': '#7DAFC8',
        'separator': '#44525C',
        'accent': '#5F96A1',
        'accent_hover': '#6CA4AE',
        'border': '#475661',
        'hero_text': '#F8FCFF',
        'hero_subtext': '#DDECF5',
        'chip_bg': '#22303A',
        'chip_text': '#AEE0F6',
        'combo_fill': '#BFA872',
        'combo_shell': '#A38D5B',
        'combo_text': '#1D2126',
        'icon_button_bg': '#313B44',
        'random_button': '#A98598',
        'random_button_hover': '#B792A5',
        'random_button_text': '#1A1318',
        'success': '#6C9880',
        'success_hover': '#7AAA90',
        'info': '#6C92A8',
        'info_hover': '#7BA1B8',
        'warning': '#B79263',
        'warning_hover': '#C5A272',
        'danger': '#B97974',
        'danger_hover': '#C78883',
        'muted_button': '#414C56',
        'muted_button_hover': '#4B5762',
    },
}

RATING_LABELS = {
    'favorite': ('⭐ Favorite', '#4A9EFF'),
    'normal': ('✓ Normal', '#4CAF50'),
    'rare': ('◆ Not common', '#FF9800'),
    'incompatible': ('✗ Unusual', "#e27637"),
    'unrated': ('Unrated', '#cccccc'),
}
