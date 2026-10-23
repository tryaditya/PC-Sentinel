
import sys
import psutil

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QFrame, QProgressBar
)


class StatCard(QFrame):
    def __init__(self, title, accent):
        super().__init__()
        self.setObjectName("StatCard")
        self.setMinimumHeight(165)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        self.title = QLabel(title.upper())
        self.title.setObjectName("CardTitle")

        self.value = QLabel("--%")
        self.value.setObjectName("CardValue")
        self.value.setStyleSheet(f"color: {accent};")

        self.detail = QLabel("Waiting for data...")
        self.detail.setObjectName("CardDetail")

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(7)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background: #202b40;
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {accent};
                border-radius: 3px;
            }}
        """)

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.detail)
        layout.addStretch()
        layout.addWidget(self.bar)

    def update_card(self, value, detail):
        self.value.setText(f"{value:.1f}%")
        self.detail.setText(detail)
        self.bar.setValue(int(value))


class PCSentinel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC Sentinel")
        self.resize(1000, 650)
        self.setMinimumSize(750, 500)

        self.setStyleSheet("""
            QMainWindow, QWidget#Main {
                background: #0b1120;
                color: #e5edf9;
                font-family: 'Segoe UI';
            }
            QLabel#AppTitle {
                font-size: 29px;
                font-weight: 700;
                color: #f1f5f9;
            }
            QLabel#Subtitle {
                font-size: 13px;
                color: #8291aa;
            }
            QLabel#Section {
                font-size: 17px;
                font-weight: 600;
                color: #dce7f7;
            }
            QFrame#StatCard {
                background: #141e30;
                border: 1px solid #25334a;
                border-radius: 14px;
            }
            QLabel#CardTitle {
                color: #8291aa;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#CardValue {
                font-size: 34px;
                font-weight: 700;
            }
            QLabel#CardDetail {
                color: #a4b2c8;
                font-size: 12px;
            }
            QFrame#InfoPanel {
                background: #141e30;
                border: 1px solid #25334a;
                border-radius: 14px;
            }
        """)

        main = QWidget()
        main.setObjectName("Main")
        self.setCentralWidget(main)

        root = QVBoxLayout(main)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(22)

        header = QHBoxLayout()
        heading = QVBoxLayout()

        title = QLabel("PC SENTINEL")
        title.setObjectName("AppTitle")

        subtitle = QLabel("SYSTEM PERFORMANCE MONITOR")
        subtitle.setObjectName("Subtitle")

        heading.addWidget(title)
        heading.addWidget(subtitle)

        self.status = QLabel("● SYSTEM ONLINE")
        self.status.setStyleSheet(
            "color: #34d399; font-size: 12px; font-weight: bold;"
        )

        header.addLayout(heading)
        header.addStretch()
        header.addWidget(self.status, alignment=Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(header)

        section = QLabel("Performance Overview")
        section.setObjectName("Section")
        root.addWidget(section)

        cards = QHBoxLayout()
        cards.setSpacing(16)

        self.cpu = StatCard("Processor", "#38bdf8")
        self.ram = StatCard("Memory", "#a78bfa")
        self.disk = StatCard("System Drive (C:)", "#34d399")

        cards.addWidget(self.cpu)
        cards.addWidget(self.ram)
        cards.addWidget(self.disk)
        root.addLayout(cards)

        info = QFrame()
        info.setObjectName("InfoPanel")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(22, 18, 22, 18)
        info_layout.setSpacing(12)

        info_title = QLabel("SYSTEM INFORMATION")
        info_title.setStyleSheet(
            "color: #8291aa; font-size: 11px; font-weight: bold;"
        )
        info_layout.addWidget(info_title)

        self.cpu_info = QLabel()
        self.ram_info = QLabel()
        self.uptime_info = QLabel()

        for label in (self.cpu_info, self.ram_info, self.uptime_info):
            label.setStyleSheet("font-size: 13px; color: #c4d0e2;")
            info_layout.addWidget(label)

        root.addWidget(info)
        root.addStretch()

        footer = QLabel("PC SENTINEL  /  LOCAL MONITORING")
        footer.setStyleSheet("color: #52627b; font-size: 11px;")
        root.addWidget(footer)

        self.started_at = psutil.boot_time()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

        self.update_stats()

    def update_stats(self):
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        uptime = int(psutil.boot_time())
        elapsed = max(0, int(__import__("time").time()) - uptime)

        self.cpu.update_card(
            cpu, f"{psutil.cpu_count(logical=True)} logical processors"
        )
        self.ram.update_card(
            memory.percent,
            f"{memory.used / (1024 ** 3):.1f} / "
            f"{memory.total / (1024 ** 3):.1f} GB used"
        )
        self.disk.update_card(
            disk.percent,
            f"{disk.used / (1024 ** 3):.0f} / "
            f"{disk.total / (1024 ** 3):.0f} GB used"
        )

        self.cpu_info.setText(
            f"Processor threads: {psutil.cpu_count(logical=True)}"
        )
        self.ram_info.setText(
            f"Available memory: {memory.available / (1024 ** 3):.1f} GB"
        )
        self.uptime_info.setText(
            f"System uptime: {elapsed // 86400}d "
            f"{(elapsed % 86400) // 3600}h "
            f"{(elapsed % 3600) // 60}m"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PCSentinel()
    window.show()
    sys.exit(app.exec())
