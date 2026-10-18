import sys
import os
grandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(grandparent_dir)
import mss
import numpy as np
import cv2
import time
import threading
from config.settings import Settings
from core.ocr.local import OCR  # استيراد الـ OCR من local.py

class ScreenCapturer:
    def __init__(self, capture_region=None):
        self.capture_region = None
        self.monitor = capture_region or self._get_default_region()
        self.running = False    
        self.last_frame = None
        self.ocr = OCR(language='eng')  # إنشاء كائن OCR

    def get_latest_frame(self):
        if self.camera.is_capturing:
            frame = self.camera.get_latest_frame()  # تأكد من أن هذه الدالة لا ترجع null
            if frame is not None:
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # تحويل الألوان بشكل صحيح
        return None

    def _get_default_region(self):
        """الحصول على منطقة الالتقاط الافتراضية من الإعدادات"""
        return {
            "top": Settings.CAPTURE_REGION['top'],
            "left": Settings.CAPTURE_REGION['left'],
            "width": Settings.CAPTURE_REGION['width'],
            "height": Settings.CAPTURE_REGION['height']
        }

    def start_continuous_capture(self, callback=None):
        """بدء التقاط مستمر مع الخيط"""
        self.running = True
        def capture_loop():
            with mss.mss() as sct:
                while self.running:
                    try:
                        screenshot = sct.grab(self.monitor)
                        frame = np.array(screenshot)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                        
                        # معالجة الإطار باستخدام الـ OCR
                        self.process_frame_with_ocr(frame)
                        
                        # إذا كان هناك callback، قم باستدعائه
                        if callback:
                            callback(frame)
                    except Exception as e:
                        print(f"[Capture Error] {e}")
                    time.sleep(0.01)  # تأخير ثابت قدره 0.5 ثانية
        threading.Thread(target=capture_loop, daemon=True).start()

    def process_frame_with_ocr(self, frame):
        """معالجة الإطار باستخدام الـ OCR."""
        try:
            text_results = self.ocr.extract_text(frame)
            
            # استخراج النصوص من القواميس
            if isinstance(text_results, list):
                extracted_texts = [item['text'] for item in text_results if isinstance(item, dict)]
                text_results = " ".join(extracted_texts)
            
            if text_results.strip():
                print("Extracted Text:", text_results)
            else:
                print("No text detected.")
        except Exception as e:
            print(f"Error processing frame with OCR: {e}")

    def _capture_loop(self, callback):
        """دالة الحلقة التي تعمل في الخيط الخلفي"""
        while self.running:
            if self.capture_region:
                screenshot = self.sct.grab(self.capture_region)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                callback(frame)
            time.sleep(0.01)  # تأخير ثابت قدره 0.5 ثانية

    def capture_frame(self):
        """التقاط إطار واحد مع معالجة الصورة الأساسية"""
        try:
            # التقاط الإطار الخام
            raw_frame = self.sct.grab(self.monitor)
            
            # تحويل إلى numpy array وتحويل الألوان
            frame = np.array(raw_frame)
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
        except Exception as e:
            self._handle_error(e)
            return None

    def update_capture_region(self, new_region):
        """تحديث منطقة الالتقاط ديناميكيًا"""
        self.monitor = {
            "top": new_region['top'],
            "left": new_region['left'],
            "width": new_region['width'],
            "height": new_region['height']
        }

    def _handle_error(self, error):
        """معالجة الأخطاء وتسجيلها"""
        error_msg = f"Capture Error: {str(error)}"
        print(error_msg)

    def stop_capture(self):
        """إيقاف عملية الالتقاط"""
        self.running = False
        
    def __del__(self):
        """تنظيف الموارد عند حذف الكائن"""
        self.stop_capture()