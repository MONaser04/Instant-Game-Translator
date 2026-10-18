import json
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QPushButton, QMessageBox
from core.ui.region_selector import MainWindow  # استيراد MainWindow من main_window.py

class TranslationOptions(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Translation Options")
        self.setGeometry(100, 100, 300, 250)  # زيادة الارتفاع لإضافة زر جديد

        # Layout
        layout = QVBoxLayout()

        # Checkboxes for options
        self.ai_only_checkbox = QCheckBox("Use AI Only", self)
        self.json_only_checkbox = QCheckBox("Use JSON Only", self)
        self.both_checkbox = QCheckBox("Use Both (Priority to JSON)", self)

        # Set default state
        self.both_checkbox.setChecked(True)

        # Add checkboxes to layout
        layout.addWidget(self.ai_only_checkbox)
        layout.addWidget(self.json_only_checkbox)
        layout.addWidget(self.both_checkbox)

        # Apply button
        self.apply_button = QPushButton("Apply", self)
        layout.addWidget(self.apply_button)

        # Save Defaults button
        self.save_defaults_button = QPushButton("Save as Default", self)
        layout.addWidget(self.save_defaults_button)

        # Redefine Capture Area button
        self.redefine_area_button = QPushButton("Redefine Capture Area", self)
        layout.addWidget(self.redefine_area_button)

        self.setLayout(layout)

        # Connect buttons to their respective functions
        self.save_defaults_button.clicked.connect(self.save_defaults)
        self.redefine_area_button.clicked.connect(self.redefine_capture_area)  # ربط الزر الجديد بالدالة
        self.load_defaults()  # تحميل الإعدادات الافتراضية عند بدء التشغيل

    def get_selected_option(self):
        if self.ai_only_checkbox.isChecked():
            return "ai_only"
        elif self.json_only_checkbox.isChecked():
            return "json_only"
        elif self.both_checkbox.isChecked():
            return "both"
        return "both"  # Default option

    def bind_apply_button(self, callback):
        self.apply_button.clicked.connect(callback)

    def save_defaults(self):
        """حفظ الإعدادات الحالية كإعدادات افتراضية"""
        settings = {
            "ai_only": self.ai_only_checkbox.isChecked(),
            "json_only": self.json_only_checkbox.isChecked(),
            "both": self.both_checkbox.isChecked()
        }

        try:
            with open("settings.json", "w") as file:
                json.dump(settings, file)
            QMessageBox.information(self, "Success", "Settings saved as default!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def load_defaults(self):
        """تحميل الإعدادات الافتراضية من الملف"""
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as file:
                    settings = json.load(file)
                    self.ai_only_checkbox.setChecked(settings.get("ai_only", False))
                    self.json_only_checkbox.setChecked(settings.get("json_only", False))
                    self.both_checkbox.setChecked(settings.get("both", True))
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Failed to load settings: {str(e)}")

    def redefine_capture_area(self):
        """فتح نافذة MainWindow لإعادة تحديد مساحة التقاط الشاشة"""
        self.main_window = MainWindow()
        self.main_window.bind_region_selected(self.update_capture_region)  # ربط حدث اختيار المنطقة
        self.main_window.show()

    def update_capture_region(self, new_region):
        """تحديث منطقة التقاط الشاشة بناءً على المنطقة الجديدة المحددة"""
        # هنا يمكنك تحديث منطقة التقاط الشاشة في الكلاس الذي يستخدمها (مثل ScreenCapturer)
        print(f"New capture region: {new_region}")
        # يمكنك هنا تمرير المنطقة الجديدة إلى الكلاس الذي يقوم بالتقاط الشاشة
        # مثال: self.screen_capturer.update_capture_region(new_region)