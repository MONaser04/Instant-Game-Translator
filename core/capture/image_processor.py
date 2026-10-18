import cv2

class ImageProcessor:
    @staticmethod
    def preprocess(frame):
        # تحويل الصورة إلى تدرج الرمادي
        gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
        
        # تحسين التباين
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # تطبيق adaptive threshold
        threshold = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return threshold
    
    def process(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # إضافة تحويل الرمادي
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        _, thresholded = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresholded