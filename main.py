import sys
import os

grandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(grandparent_dir)

from core.ui.region_selector import MainWindow
from core.capture.screen_capturer import ScreenCapturer
from core.ocr.local import OCR
from core.translator.translation_manager import TranslationManager
from core.ui.overlay_window import SubtitleOverlay
import threading
import cv2
from core.ui.translation_options import TranslationOptions  # استيراد الواجهة الجديدة
from config.settings import Settings
from core.app_utils.text_utils import TextUtils
from core.ui.translation_ui import TranslationUI
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Signal, QObject, QTimer
from text.translation_cache import TranslationCache
logging.getLogger('tensorflow').setLevel(logging.ERROR)  # تعطيل تحذيرات TensorFlow

class Application(QObject):
    update_overlay_signal = Signal(str)  # إشارة لتحديث الـ Overlay
    
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.translator = TranslationManager()
        self.capturer = None 
        self.ocr = OCR(language='eng')
        self.ui = TranslationUI(self.main_window)
        self.text_utils = TextUtils()
        
        # إنشاء Overlay قبل توصيل الإشارة
        self.overlay = SubtitleOverlay()
        
        # تهيئة الـ TranslationCache بمسار قابل للتخصيص
        cache_path = os.environ.get("TRANSLATION_CACHE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "json"))
        self.translation_cache = TranslationCache(cache_path)

        # توصيل الإشارة بعد إنشاء Overlay
        self.update_overlay_signal.connect(self.overlay.update)
        
        self.main_window.on_region_selected = self.handle_region_selected
        self._setup_ui()

        # إضافة واجهة الخيارات
        self.translation_options = TranslationOptions()
        self.translation_options.bind_apply_button(self.update_translation_options)
        self.translation_options.show()

    def update_translation_options(self):
        """تحديث خيارات الترجمة بناءً على الاختيار"""
        option = self.translation_options.get_selected_option()
        self.translator.set_translation_option(option)

    def handle_region_selected(self, region):
        """معالجة اختيار المنطقة"""
        self.capturer = ScreenCapturer(region)
        self.start_capture_loop()
        
    def start_capture_loop(self):
        """ابدأ التقاط الإطارات بشكل مستمر"""
        self.capture_thread = threading.Thread(
            target=self.capturer.start_continuous_capture,
            args=(self.process_frame,)
        )
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def _setup_ui(self):
        self.overlay.show()

    def _start_services(self):
        self.start_capture_loop()

    def process_text(self, raw_text):
        cleaned = self.text_utils.clean_text(raw_text)
        translated = self.translator.translate(cleaned)
        self.ui.update_text(translated)
        
    def process_frame(self, frame):
        cv2.imwrite('raw_frame.jpg', frame)
        ocr_results = self.ocr.extract_text(frame)
        
        if not ocr_results:
            return
        
        # تجميع النصوص حسب الأسطر بناءً على الإحداثيات Y
        lines = {}
        for item in ocr_results:
            y_center = (item['coordinates']['y1'] + item['coordinates']['y3']) // 2
            if y_center not in lines:
                lines[y_center] = []
            lines[y_center].append(item)
        
        # ترتيب الأسطر حسب الإحداثيات Y
        sorted_lines = sorted(lines.items(), key=lambda x: x[0])
        
        translated_lines = []
        for line in sorted_lines:
            # تجميع النص في السطر الواحد
            line_text = " ".join([item['text'] for item in line[1]])
            
            # البحث في التخزين المؤقت لكل سطر على حدة
            translated = self.translation_cache.find_match(line_text)
            
            # إذا لم يوجد في الكاش، ترجمة السطر
            if not translated:
                translated = self.translator.translate(
                    line_text,
                    callback=lambda text: None  # لا ترسل حتى اكتمال جميع الأسطر
                )
                self.translation_cache.add_translation(line_text, translated)
            
            translated_lines.append(translated)
        
        # دمج الترجمات مع الحفاظ على الأسطر
        final_translation = "\n".join(translated_lines)
        
        # عرض جميع الترجمات معًا
        if final_translation.strip():
            self.update_overlay_signal.emit(final_translation)

    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = Application()
    app.run()