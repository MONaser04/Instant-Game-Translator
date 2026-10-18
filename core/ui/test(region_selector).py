import sys
import ctypes
from ctypes import wintypes

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QAbstractNativeEventFilter, QTimer
from PySide6.QtGui import QPainter, QColor, QPen


user32 = ctypes.windll.user32

WM_HOTKEY = 0x0312
HOTKEY_ID = 1

VK_F12 = 0x7B
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000


class RegionSelector(QWidget):
    selected = Signal(dict)

    def __init__(self, min_size: int = 5):
        super().__init__()
        self.min_size = int(min_size)

        self.start = QPoint()
        self.selecting = False
        self.cut_rect = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.CrossCursor)

        self.hide()

    def show_selector(self):
        self.selecting = False
        self.cut_rect = None
        self.update()

        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        print("Selector shown")

    def cancel(self):
        self.selecting = False
        self.cut_rect = None
        self.update()
        self.hide()
        print("Selector hidden")

    def paintEvent(self, event):
        p = QPainter(self)

        p.fillRect(self.rect(), QColor(0, 0, 0, 80))

        if self.cut_rect:
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            p.fillRect(self.cut_rect, Qt.transparent)

            p.setCompositionMode(QPainter.CompositionMode_SourceOver)

            p.setPen(QPen(QColor(255, 255, 255, 220), 1))
            p.setBrush(Qt.NoBrush)
            p.drawRect(self.cut_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selecting = True
            self.start = event.position().toPoint()
            self.cut_rect = QRect(self.start, self.start)
            self.update()

    def mouseMoveEvent(self, event):
        if self.selecting:
            rect = QRect(self.start, event.position().toPoint()).normalized()
            self.cut_rect = rect
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False

            rect = self.cut_rect
            if rect and rect.width() >= self.min_size and rect.height() >= self.min_size:
                self.selected.emit({
                    "x": rect.x(),
                    "y": rect.y(),
                    "width": rect.width(),
                    "height": rect.height(),
                })

            self.cancel()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()


class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, on_hotkey):
        super().__init__()
        self.on_hotkey = on_hotkey

    def nativeEventFilter(self, eventType, message):
        if "windows" not in str(eventType):
            return False, 0

        try:
            msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
        except Exception:
            return False, 0

        if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
            QTimer.singleShot(0, self.on_hotkey)
            return True, 0

        return False, 0


def main():
    if sys.platform != "win32":
        raise SystemExit("Windows only")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = RegionSelector(min_size=5)

    state = {"region": None}

    def on_selected(r):
        state["region"] = r
        print(f"Region updated: {r}")

    window.selected.connect(on_selected)

    ok = user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_NOREPEAT, VK_F12)
    if not ok:
        err = ctypes.get_last_error()
        raise SystemExit(f"Failed to register Ctrl+F12. WinError={err}")

    print("Global hotkey registered: Ctrl+F12")
    print("App running in background. Press Ctrl+F12 ...")

    hotkey_filter = HotkeyFilter(window.show_selector)
    app.installNativeEventFilter(hotkey_filter)

    def cleanup():
        user32.UnregisterHotKey(None, HOTKEY_ID)

    app.aboutToQuit.connect(cleanup)

    QTimer.singleShot(0, window.show_selector)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()