import os
import sys
import time
import threading

# ---------- Optional metrics ----------
try:
    import psutil
except ImportError:
    psutil = None

# ---------- Make project imports work ----------
grandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(grandparent_dir)

from PySide6.QtWidgets import QApplication
from core.ui.region_selector import MainWindow


class MetricsSampler:
    """
    Samples process CPU% and RSS memory in background.
    Requires psutil. If psutil isn't installed, it will do nothing.
    """
    def __init__(self, interval_s: float = 0.2):
        self.interval_s = interval_s
        self._stop = threading.Event()
        self.samples = []

        self.proc = None
        if psutil:
            self.proc = psutil.Process(os.getpid())

    def start(self):
        if not self.proc:
            return
        # Prime cpu_percent measurement
        self.proc.cpu_percent(interval=None)
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.is_set():
            cpu = self.proc.cpu_percent(interval=None)  # %
            mem = self.proc.memory_info().rss / (1024 * 1024)  # MB
            self.samples.append((time.perf_counter(), cpu, mem))
            time.sleep(self.interval_s)

    def summary(self):
        if not self.samples:
            return None
        cpus = [s[1] for s in self.samples]
        mems = [s[2] for s in self.samples]
        return {
            "cpu_avg": sum(cpus) / len(cpus),
            "cpu_max": max(cpus),
            "mem_avg_mb": sum(mems) / len(mems),
            "mem_max_mb": max(mems),
            "n_samples": len(self.samples),
        }


def main():
    app = QApplication(sys.argv)

    # ---- Create window ----
    window = MainWindow(screen_capturer=None)

    # ---- Timers ----
    t_app_start = time.perf_counter()
    t_first_press = {"v": None}
    t_released = {"v": None}
    selected_region = {"v": None}

    # ---- Metrics ----
    sampler = MetricsSampler(interval_s=0.2)
    sampler.start()

    # ---- Hook events by monkey-patching (test only) ----
    orig_mousePressEvent = window.mousePressEvent
    orig_mouseReleaseEvent = window.mouseReleaseEvent

    def patched_mousePressEvent(event):
        if t_first_press["v"] is None:
            t_first_press["v"] = time.perf_counter()
        return orig_mousePressEvent(event)

    def patched_mouseReleaseEvent(event):
        # call original first (so it computes capture_region)
        ret = orig_mouseReleaseEvent(event)
        if t_released["v"] is None:
            t_released["v"] = time.perf_counter()
            selected_region["v"] = window.capture_region
            # stop after selection
            sampler.stop()
            # quit after a tiny delay to flush logs nicely
            QTimer_single_shot_quit(app, 100)
        return ret

    window.mousePressEvent = patched_mousePressEvent
    window.mouseReleaseEvent = patched_mouseReleaseEvent

    # ---- Start ----
    print("=== Region Selector Test ===")
    print("1) نافذة الاختيار هتظهر دلوقتي (شفافة/Fullscreen).")
    print("2) اسحب مستطيل بالماوس وحدد المنطقة، وبمجرد ما تسيب الزر الاختبار هيقفل.")
    print("Tip: اضغط \\ لإعادة التحديد داخل نفس النافذة (زي ما كودك عامل).")
    print()

    window.show()

    # Run UI loop
    app.exec()

    # ---- Results ----
    t_end = time.perf_counter()
    print("\n=== Results ===")
    print(f"Selected region (left, top, width, height): {selected_region['v']}")
    print(f"Total runtime: {(t_end - t_app_start):.3f} s")

    if t_first_press["v"] and t_released["v"]:
        print(f"Selection duration (press→release): {(t_released['v'] - t_first_press['v']):.3f} s")

    if psutil:
        summ = sampler.summary()
        if summ:
            print("\n=== Resource usage (process) ===")
            print(f"CPU avg: {summ['cpu_avg']:.1f}% | CPU max: {summ['cpu_max']:.1f}%")
            print(f"RAM avg: {summ['mem_avg_mb']:.1f} MB | RAM max: {summ['mem_max_mb']:.1f} MB")
            print(f"Samples: {summ['n_samples']}")
        else:
            print("\n(psutil موجود لكن مفيش samples كفاية)")
    else:
        print("\n(psutil مش متسطب — لو عايز CPU/RAM metrics: pip install psutil)")


def QTimer_single_shot_quit(app, delay_ms: int):
    # Local import to avoid extra top-level deps
    from PySide6.QtCore import QTimer
    QTimer.singleShot(delay_ms, app.quit)


if __name__ == "__main__":
    main()
