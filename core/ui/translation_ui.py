import sys
import os
grandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(grandparent_dir)
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from config.settings import UIColors

class TranslationUI:
    def __init__(self, master):
        self.master = master
        self.label = QLabel(
            text="",
            parent=self.master
        )
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {UIColors.TEXT_MAIN};  # لون النص من الإعدادات
                background-color: {UIColors.BACKGROUND};  # لون الخلفية من الإعدادات
                font-family: Arial;
                font-size: 12px;
            }}
        """)
        self.label.setAlignment(Qt.AlignCenter)  # محاذاة النص إلى الوسط
        self.label.show()  # عرض الـ Label

    def update_text(self, text):
        print(f"Updating UI with translated text: {text}")
        self.label.setText(text)  # تحديث النص