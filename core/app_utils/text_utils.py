import re

class TextUtils:
    
    non_translatable_words = {
        "Nauts": "ناتس",
        "example": "مثال"
    }

    @staticmethod
    def handle_non_translatable_words(text):
        pattern = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(k) for k in TextUtils.non_translatable_words.keys()) + r')(?!\w)')
        return pattern.sub(lambda match: TextUtils.non_translatable_words[match.group(0)], text)

    @staticmethod
    def apply_text_color(text, color_code="\033[97m"):
        """إضافة ألوان للنص في الواجهة الطرفية (ANSI colors)"""
        reset_color = "\033[0m"  # رمز إعادة تعيين اللون
        return f"{color_code}{text}{reset_color}"    
    
    @staticmethod
    def style_text(text, color='white', style='normal'):
        """تنسيق النص لأغراض العرض (يمكن تطويره لواجهة GUI)"""
        colors = {
            'white': '\033[97m',
            'red': '\033[91m',
            'green': '\033[92m'
        }
        styles = {
            'normal': '\033[0m',
            'bold': '\033[1m',
            'underline': '\033[4m'
        }
        return f"{colors.get(color, '')}{styles.get(style, '')}{text}\033[0m"

    @staticmethod
    def transliterate_english_to_arabic(text):
        transliteration_map = {
            'a': 'ا', 'b': 'ب', 'c': 'ك', 'd': 'د', 'e': 'ي', 'f': 'ف', 'g': 'ج',
            'h': 'ه', 'i': 'ي', 'j': 'ج', 'k': 'ك', 'l': 'ل', 'm': 'م', 'n': 'ن',
            'o': 'و', 'p': 'ب', 'q': 'ق', 'r': 'ر', 's': 'س', 't': 'ت', 'u': 'و',
            'v': 'ف', 'w': 'و', 'x': 'كس', 'y': 'ي', 'z': 'ز'
        }

        arabic_text = []
        for char in text:
            if char.lower() in transliteration_map:
                arabic_text.append(transliteration_map[char.lower()])
            else:
                arabic_text.append(char)
        return ''.join(arabic_text)

    @staticmethod
    def clean_text(text):
        return text
    
    