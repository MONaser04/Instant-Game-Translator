import os
import sys
import ctypes
import numpy as np
from PIL import ImageGrab
import keyboard  # استيراد مكتبة keyboard

grandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(grandparent_dir)
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QTime, QPointF, QPoint
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from config.settings import Settings

if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes

    dwmapi = ctypes.WinDLL('dwmapi')
    user32 = ctypes.WinDLL('user32')

    DWMWA_SYSTEMBACKDROP_TYPE = 38
    DWM_SYSTEMBACKDROP_TYPE_ACRYLIC = 3

    # إضافة الثوابت الجديدة
    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    WDA_EXCLUDEFROMCAPTURE = 0x00000011

    class ACCENTPOLICY(ctypes.Structure):
        _fields_ = [
            ('AccentState', ctypes.c_uint),
            ('AccentFlags', ctypes.c_uint),
            ('GradientColor', ctypes.c_uint),
            ('AnimationId', ctypes.c_uint)
        ]

    class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
        _fields_ = [
            ('Attribute', ctypes.c_int),
            ('Data', ctypes.POINTER(ctypes.c_byte)),
            ('SizeOfData', ctypes.c_size_t)
        ]

    SetWindowCompositionAttribute = user32.SetWindowCompositionAttribute
    SetWindowCompositionAttribute.argtypes = [wintypes.HWND, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
    SetWindowCompositionAttribute.restype = wintypes.BOOL

    # إضافة دالة جديدة لجعل النافذة مستثناة من الالتقاط
    SetWindowDisplayAffinity = user32.SetWindowDisplayAffinity
    SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
    SetWindowDisplayAffinity.restype = wintypes.BOOL

class SubtitleOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_window()
        self._create_widgets()
        self._apply_glass_effect()
        
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_text_color)
        self._update_timer.start(50)  # تحديث لون النص كل 100 مللي ثانية
        
        self._hide_timer = QTimer(self)
        self._hide_timer.timeout.connect(self._hide_window)
        self._hide_timer.setSingleShot(True)  # تنفيذ مرة واحدة فقط
        
        self.last_update_time = 0
        self.current_text_color = "#FFD75A"
        self.color_change_delay = 500  # 0.5 ثانية
        self.luminance_threshold = 40
        # تحديد الموقع الثابت المطلق
        self.fixed_position = QPoint(960, 650)
        self.move(self.fixed_position)  # تعيين الموقع الثابت

        # متغيرات لتعقب حركة الماوس
        self.dragging = False
        self.offset = QPoint()
        self.draggable = True  # حالة النافذة (قابلة للتحريك أم لا)
        self.set_click_through(True)  # جعل النافذة شفافة للماوس دائمًا

        # حفظ الموضع الأصلي للنافذة
        self.original_position = self.pos()

        # متغير لتتبع حالة إخفاء النافذة
        self.is_hidden = False

        # استماع إلى حدث الضغط على زر "-"
        keyboard.on_press_key("-", lambda _: self.toggle_draggable())

    def toggle_draggable(self):
        """تبديل حالة التحريك"""
        self.draggable = not self.draggable
        self.set_click_through(not self.draggable)
        
        if self.draggable:
            print("وضع التحريك مفعل - يمكنك تحريك النافذة")
        else:
            print("وضع التمرير مفعل - يمكنك التفاعل مع الخلفية")

    def toggle_visibility(self):
        """تبديل حالة إخفاء/إظهار النافذة"""
        if self.is_hidden:
            self.show()
            self.is_hidden = False
            print("النافذة ظاهرة الآن")
        else:
            self.hide()
            self.is_hidden = True
            print("النافذة مخفية الآن")

    def _setup_window(self):
        """تهيئة النافذة"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMinimumSize(1, 1)

        # جعل النافذة مستثناة من الالتقاط (لن تظهر في لقطات الشاشة)
        if sys.platform == 'win32':
            hwnd = self.winId()
            SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

    def _apply_glass_effect(self):
        """تطبيق تأثير الزجاج"""
        if sys.platform == 'win32':
            hwnd = self.winId()
            
            if hasattr(dwmapi, 'DwmSetWindowAttribute'):
                dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_SYSTEMBACKDROP_TYPE,
                    ctypes.byref(ctypes.c_int(DWM_SYSTEMBACKDROP_TYPE_ACRYLIC)),
                    ctypes.sizeof(ctypes.c_int)
                )

            accent = ACCENTPOLICY()
            accent.AccentState = 3
            accent.GradientColor = 0x00FFFFFF

            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = 19
            data.SizeOfData = ctypes.sizeof(accent)
            data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(ctypes.c_byte))

            SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))

    def _create_widgets(self):
        """إنشاء العناصر داخل النافذة"""
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)  # تفعيل تقسيم النص إلى سطور جديدة
        self.label.setMargin(0)  # إزالة الهوامش الداخلية

        font = QFont()
        font.setFamily(Settings.UI_THEME['subtitle_font']['family'])
        font.setPointSize(Settings.UI_THEME['subtitle_font']['size'])
        self.label.setFont(font)

        # تصحيح الـ Stylesheet
        self.label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                font-weight: bold;
                padding: 0px;  /* إزالة الـ padding */
                margin: 0px;   /* إزالة الـ margin */
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # إزالة الهوامش الخارجية
        layout.setSpacing(0)  # إزالة المسافات بين العناصر
        layout.addWidget(self.label)
        self.setLayout(layout)

    def _get_background_color(self):
        """الحصول على لون الخلفية خلف النافذة"""
        try:
            # التقاط صورة للشاشة في منطقة النافذة
            rect = self.geometry()
            screenshot = ImageGrab.grab(bbox=(rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height()))
            
            # تحويل الصورة إلى مصفوفة numpy
            img = np.array(screenshot)
            
            # حساب متوسط لون الخلفية
            avg_color = np.mean(img, axis=(0, 1))
            return avg_color
        except Exception as e:
            print(f"Error getting background color: {str(e)}")
            return None

    def _update_text_color(self):
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        if current_time - self.last_update_time < self.color_change_delay:
            return

        bg_luminance = self._get_background_color()
        if bg_luminance is None:
            return

        # Calculate the luminance value from the array
        luminance_value = 0.2126 * bg_luminance[0] + 0.7152 * bg_luminance[1] + 0.0722 * bg_luminance[2]

        new_color = "#C49C30" if luminance_value > 127 else "#FFD75A"
        luminance_diff = abs(127 - luminance_value)

        # تغيير اللون فقط إذا كان التباين كافياً
        if luminance_diff > self.luminance_threshold:
            shadow_color = "#C49C30" if new_color == "#FFD75A" else "#FFD75A"
            effect = QGraphicsDropShadowEffect(
                blurRadius=2,
                color=QColor(shadow_color),
                offset=QPointF(1, 1)
            )
            
            self.label.setGraphicsEffect(effect)
            self.label.setStyleSheet(f"""
                QLabel {{
                    color: {new_color};
                    background-color: transparent;
                    font-weight: bold;
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            self.current_text_color = new_color
            self.last_update_time = current_time

    def _hide_window(self):
        """إخفاء النافذة إذا مرت 7 ثوانٍ دون تحديث النص"""
        if not self.is_hidden:  # لا تخفي النافذة إذا كانت مخفية بالفعل
            self.hide()
            # إعادة النافذة إلى الموضع الأصلي عند الإخفاء
            self.move(self.original_position)

    def reset(self):
        self.current_text = ""  # إعادة تعيين النص الحالي

    def update(self, text):
        """تحديث النص مع الحفاظ على التدفق السريع"""
        if self.is_hidden:  # لا تقم بتحديث النافذة إذا كانت مخفية
            return

        self.label.setText(text)  # تحديث النص مباشرةً

        line_count = text.count('\n') + 1
        font_metrics = self.label.fontMetrics()
        line_height = font_metrics.height()

        # حساب العرض بناءً على أطول سطر
        max_width = max(font_metrics.horizontalAdvance(line) for line in text.split('\n')) if text else 0

        # تحديد العرض الأقصى للنافذة بـ 1920 بكسل
        max_window_width = 1920
        new_width = min(max_width + 20, max_window_width)
        new_height = line_height * line_count

        # حساب الموضع الجديد للنافذة بحيث يتم توسيعها بشكل متساوٍ من اليمين واليسار
        old_width = self.width()
        delta_width = new_width - old_width
        # حساب الموضع الجديد مع التمديد المتساوي
        new_x = 960 - (new_width // 2)  # توسيع متساو حول المركز X=960
        new_y = 650  # ثابت للإحداثي Y
        
        # إجبار النافذة على البقاء في الموقع الثابت
        self.setGeometry(new_x, new_y, new_width, new_height)

        # إظهار النافذة إذا كانت مخفية
        if not self.isVisible():
            self.show()

        # إعادة تشغيل المؤقت لإخفاء النافذة بعد 7 ثوانٍ
        self._hide_timer.start(7000)  # 7000 مللي ثانية = 7 ثوانٍ

    def paintEvent(self, event):
        """رسم تأثير الزجاج"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 8, 8)  # زوايا مدورة بسلاسة
        
        painter.setClipPath(path)
        painter.fillRect(
            self.rect(), 
            QColor(30, 30, 30, int(200 * Settings.UI_THEME['opacity'])))
        overlay_color = QColor(255, 255, 255, int(25 * Settings.UI_THEME['opacity']))
        painter.fillRect(self.rect().adjusted(1, 1, -1, -1), overlay_color)

    def set_click_through(self, enable):
        """جعل النافذة شفافة لأحداث الماوس"""
        self.click_through = enable
        
        if sys.platform == 'win32':
            hwnd = self.winId()
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
            
            if enable:
                # WS_EX_TRANSPARENT يجعل النافذة شفافة للأحداث
                # WS_EX_LAYERED للحفاظ على الشفافية البصرية
                new_style = style | 0x00000020 | 0x00080000
            else:
                new_style = style & ~0x00000020 | 0x00080000
                
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, new_style)
        
        # ضبط خاصية Qt للشفافية
        self.setAttribute(Qt.WA_TransparentForMouseEvents, enable)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    if sys.platform == 'win32':
        ctypes.windll.user32.SetProcessDPIAware()
    
    window = SubtitleOverlay()
    window.update("نص تجريبي بدون هوامش!")
    window.show()
    
    sys.exit(app.exec())