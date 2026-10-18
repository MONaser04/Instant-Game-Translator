import os
import cv2
import difflib
import time
import re
from ctypes import (
    CDLL,
    c_char_p,
    c_size_t,
    c_void_p,
    c_int32,
    POINTER,
    Structure,
    pointer,
)

def get_dll_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(base_dir, "files", "plugins", "OCR64.dll")
    if os.path.exists(candidate):
        return candidate
    return "core\\ocr\\files\\plugins\\OCR64.dll"

class ocrpoints(Structure):
    _fields_ = [
        ("x1", c_int32),
        ("y1", c_int32),
        ("x2", c_int32),
        ("y2", c_int32),
        ("x3", c_int32),
        ("y3", c_int32),
        ("x4", c_int32),
        ("y4", c_int32),
    ]

class ocrwrapper:
    def __init__(self, det, rec, key) -> None:
        self.dll = CDLL(get_dll_path())
        self.pOcrObj = None
        self.__OcrInit(det, rec, key)

    def __OcrInit(self, szDetModel, szRecModel, szKeyPath):
        _OcrInit = self.dll.OcrInit
        _OcrInit.restype = c_void_p
        self.pOcrObj = _OcrInit(
            c_char_p(szDetModel.encode("utf8")),
            c_char_p("".encode("utf8")),
            c_char_p(szRecModel.encode("utf8")),
            c_char_p(szKeyPath.encode("utf8")),
            4,
        )

    def __OcrDetect(self, data: bytes, angle):
        _OcrDetect = self.dll.OcrDetect
        _OcrDetect.argtypes = (
            c_void_p,
            c_void_p,
            c_size_t,
            c_int32,
            POINTER(c_int32),
            POINTER(POINTER(ocrpoints)),
            POINTER(POINTER(c_char_p)),
        )

        num = c_int32()
        ps = POINTER(ocrpoints)()
        chars = POINTER(c_char_p)()
        res = _OcrDetect(
            self.pOcrObj,
            data,
            len(data),
            c_int32(angle),
            pointer(num),
            pointer(ps),
            pointer(chars),
        )

        if not res:
            return []

        results = []
        for i in range(num.value):
            text = chars[i].decode("utf8")
            text = self.clean_text(text)
            
            points = ps[i]
            coordinates = {
                "x1": points.x1, "y1": points.y1,
                "x2": points.x2, "y2": points.y2,
                "x3": points.x3, "y3": points.y3,
                "x4": points.x4, "y4": points.y4
            }
            
            results.append({"text": text, "coordinates": coordinates})

        return results

    def clean_text(self, text):
        text = re.sub(r'\d+', '', text)  # إزالة الأرقام
        return re.sub(r'\b\w\b', '', text).strip()

    def ocr(self, data, angle=0):
        try:
            return self.__OcrDetect(data, angle)
        except Exception as e:
            print(f"OCR Error: {e}")
            return []

    def __del__(self):
        if self.pOcrObj:
            _OcrDestroy = self.dll.OcrDestroy
            _OcrDestroy.argtypes = (c_void_p,)
            _OcrDestroy(self.pOcrObj)

class OCR:
    def __init__(self, language):
        self.language = language
        self.ocr_wrapper = None
        self.load_model()
        self.last_sent_text = None
        self.pending_start_time = None

    def calculate_similarity(self, text1, text2):
        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def load_model(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "files", "ocr", "en")
        if not (os.path.exists(os.path.join(path, "det.onnx")) and os.path.exists(os.path.join(path, "rec.onnx"))):
            path = "core/ocr/files/ocr/en"
        if not (os.path.exists(os.path.join(path, "det.onnx")) and os.path.exists(os.path.join(path, "rec.onnx"))):
            raise Exception("OCR model not found.")

        self.ocr_wrapper = ocrwrapper(
            os.path.join(path, "det.onnx"),
            os.path.join(path, "rec.onnx"),
            os.path.join(path, "dict.txt")
        )

    def perform_ocr(self, image_binary):
        raw_results = self.ocr_wrapper.ocr(image_binary)
        return raw_results

    def extract_text(self, image):
        """ يستخرج النص مع إحداثياته من الصورة """
        _, img_encoded = cv2.imencode('.jpg', image)
        image_bytes = img_encoded.tobytes()
        ocr_results = self.perform_ocr(image_bytes)
        
        if not ocr_results:
            self.last_sent_text = None
            self.pending_start_time = None
            return []
        
        # تجميع النصوص حسب الأسطر بناءً على الإحداثيات Y
        lines = {}
        for item in ocr_results:
            y_center = (item['coordinates']['y1'] + item['coordinates']['y3']) // 2
            if y_center not in lines:
                lines[y_center] = []
            lines[y_center].append(item)
        
        # ترتيب الأسطر حسب الإحداثيات Y
        sorted_lines = sorted(lines.items(), key=lambda x: x[0])
        
        # تجميع النصوص في كل سطر
        current_text = []
        for line in sorted_lines:
            line_text = " ".join([item.get('text', '') for item in line[1]])
            current_text.append(line_text)
        
        if self.last_sent_text is None:
            self.last_sent_text = current_text
            return ocr_results
        
        similarity = self.calculate_similarity(' '.join(current_text), ' '.join(self.last_sent_text))
        if similarity < 0.8:
            self.last_sent_text = current_text
            self.pending_start_time = None
            return ocr_results
        else:
            if self.pending_start_time is None:
                self.pending_start_time = time.time()
                return []
            else:
                elapsed = time.time() - self.pending_start_time
                if elapsed >= 1:
                    self.last_sent_text = current_text
                    self.pending_start_time = None
                    return ocr_results
                else:
                    return []

if __name__ == "__main__":
    ocr = OCR(language='ar')
    image = cv2.imread("test.jpg")
    results = ocr.extract_text(image)
    
    for idx, item in enumerate(results):
        print(f"Text {idx + 1}: {item['text']}")
        print(f"Coordinates: {item['coordinates']}\n")