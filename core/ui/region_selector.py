import os
import sys
import ctypes
from ctypes import wintypes

from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import Qt, QRect, QPoint, QAbstractNativeEventFilter, QTimer
from PySide6.QtGui import QPainter, QColor, QPen

from core.capture.screen_capturer import ScreenCapturer

grandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(grandparent_dir)

user32 = ctypes.windll.user32
WM_HOTKEY = 0x0312
HOTKEY_ID = 1
VK_F12 = 0x7B
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000


class _HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, get_callback):
        super().__init__()
        self._get_callback = get_callback

    def nativeEventFilter(self, eventType, message):
        if "windows" not in str(eventType):
            return False, 0
        try:
            msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
        except Exception:
            return False, 0
        if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
            cb = self._get_callback()
            if cb:
                QTimer.singleShot(0, cb)
                return True, 0
        return False, 0


class MainWindow(QMainWindow):
    _hotkey_installed = False
    _hotkey_filter = None
    _hotkey_owner = None
    _cleanup_connected = False

    def __init__(self, screen_capturer=None, min_size=5, overlay_alpha=80):
        super().__init__()
        self.min_size = int(min_size)
        self.overlay_alpha = int(overlay_alpha)

        self.start_point = QPoint()
        self.is_selecting = False
        self.cut_rect = None

        self.capture_region = None
        self.on_region_selected = None
        self.screen_capturer = screen_capturer

        if sys.platform == "win32":
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        self.setWindowTitle("Region Selector")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.CrossCursor)
        self.hide()

        self._ensure_hotkey()

    def bind_region_selected(self, callback):
        self.on_region_selected = callback

    def show(self):
        self.show_selector()

    def show_selector(self):
        self.is_selecting = False
        self.cut_rect = None
        self.update()
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def cancel(self):
        self.is_selecting = False
        self.cut_rect = None
        self.update()
        self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, self.overlay_alpha))
        if self.cut_rect:
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            p.fillRect(self.cut_rect, Qt.transparent)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            p.setPen(QPen(QColor(255, 255, 255, 220), 1))
            p.setBrush(Qt.NoBrush)
            p.drawRect(self.cut_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selecting = True
            self.start_point = event.position().toPoint()
            self.cut_rect = QRect(self.start_point, self.start_point)
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            end = event.position().toPoint()
            self.cut_rect = QRect(self.start_point, end).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            rect = self.cut_rect
            self.cut_rect = None
            self.update()

            if rect and rect.width() >= self.min_size and rect.height() >= self.min_size:
                left, top, width, height = rect.x(), rect.y(), rect.width(), rect.height()
                self.capture_region = (left, top, width, height)
                region_dict = {"top": top, "left": left, "width": width, "height": height}

                if self.on_region_selected:
                    self.on_region_selected(region_dict)

                if self.screen_capturer:
                    self.screen_capturer.update_capture_region(region_dict)

            self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()

    def _ensure_hotkey(self):
        if sys.platform != "win32":
            return
        app = QApplication.instance()
        if not app:
            return

        MainWindow._hotkey_owner = self

        if not MainWindow._hotkey_installed:
            ok = user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_NOREPEAT, VK_F12)
            if ok:
                MainWindow._hotkey_installed = True

        if MainWindow._hotkey_filter is None:
            MainWindow._hotkey_filter = _HotkeyFilter(lambda: getattr(MainWindow._hotkey_owner, "show_selector", None))
            app.installNativeEventFilter(MainWindow._hotkey_filter)

        if not MainWindow._cleanup_connected:
            def cleanup():
                try:
                    if MainWindow._hotkey_installed:
                        user32.UnregisterHotKey(None, HOTKEY_ID)
                except Exception:
                    pass
            app.aboutToQuit.connect(cleanup)
            MainWindow._cleanup_connected = True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen_capturer = ScreenCapturer()
    window = MainWindow(screen_capturer)
    window.bind_region_selected(lambda region: print(f"Region selected: {region}"))
    QTimer.singleShot(0, window.show_selector)
    sys.exit(app.exec())
