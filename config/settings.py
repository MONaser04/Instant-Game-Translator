class Settings:
    TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    CAPTURE_REGION = {'top': 150, 'left': 200, 'width': 900, 'height': 300}
    CAPTURE_FPS = 20
    
    # config/settings.py - تعديل OCR_CONFIG
    OCR_CONFIG = (
        "--oem 3 "
        "--psm 11 "
        "-c preserve_interword_spaces=1 "
        "-c textord_min_linesize=3.5 "
        "-c textord_old_xheight=1 "
        "-c language_model_ngram_on=1 "
        "-c user_words_file=game_terms.txt"
    )
    OCR_LANGUAGE = "eng"
    
    UI_THEME = {
        'bg_color': 'black',
        'font': ('Dubai', 24),
        'opacity': 0.1,  # بين 0 و1
        'subtitle_font': {
            'family': 'Dubai',
            'size': 24,
            'color': '#f9e6be'
        }
    }
    
    HOTKEYS = {
        'toggle_window': 'Ctrl+Alt+T',
        'toggle_subtitle': 'Ctrl+Alt+S',
        'instant_translate': 'Ctrl+Alt+Q',
        'quit_app': 'Ctrl+Alt+E'
    }
    
    DEBUG_MODE = True
    AUTO_UPDATE = True
    FALLBACK_FONTS = ['Arial', 'Calibri', 'Times New Roman']

class UIColors:
    TEXT_MAIN = "#FFFFFF"
    BACKGROUND = "#0A0A0A"
    WARNING = "#FF6B6B"
    SUCCESS = "#76FF7A"
    INFO = "#69B4FF"
    ACCENT = "#FFD700"
    TRANSLATING = "#FFA500"
    ERROR = "#FF0000"
    SUBTITLE_BORDER = "#404040"