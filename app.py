
import sys
import time
import psutil

from collections import deque

from diagnostics import DiagnosticsPage
from process_manager import ProcessManagerPage
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QProgressBar,
    QPushButton,
    QStackedWidget,
)


class StatCard(QFrame):
    def __init__(self, title, accent):
        super().__init__()
        self.setObjectName("StatCard")
        self.accent = accent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        heading = QLabel(title.upper())
        heading.setObjectName("CardTitle")

        self.value = QLabel("--%")
        self.value.setStyleSheet(
            f"color: {accent}; font-size: 30px; font-weight: bold;"
        )

        self.detail = QLabel("Collecting data...")
        self.detail.setObjectName("CardDetail")

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background: #253047;
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {accent};
                border-radius: 3px;
            }}
        """)

        layout.addWidget(heading)
        layout.addWidget(self.value)
        layout.addWidget(self.detail)
        layout.addStretch()
        layout.addWidget(self.bar)

    def update_card(self, value, detail):
        self.value.setText(f"{value:.1f}%")
        self.detail.setText(detail)
        self.bar.setValue(max(0, min(100, int(value))))


class PerformanceGraph(QWidget):
    def __init__(self, title, accent):
        super().__init__()

        self.title = title
        self.accent = QColor(accent)
        self.values = deque([0.0] * 60, maxlen=60)

        self.setMinimumHeight(230)

    def add_value(self, value):
        self.values.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        panel = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor("#25334a"), 1))
        painter.setBrush(QColor("#141e30"))
        painter.drawRoundedRect(panel, 14, 14)

        painter.setPen(QColor("#a4b2c8"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(20, 28, self.title.upper())

        current = self.values[-1]
        painter.setPen(self.accent)
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(20, 59, f"{current:.1f}%")

        left = 42
        right = self.width() - 20
        top = 82
        bottom = self.height() - 30

        plot_width = right - left
        plot_height = bottom - top

        if plot_width <= 0 or plot_height <= 0:
            painter.end()
            return

        # Horizontal grid and percentage labels
        painter.setFont(QFont("Segoe UI", 8))
        for percentage in (100, 75, 50, 25, 0):
            y = top + (100 - percentage) / 100 * plot_height

            painter.setPen(QPen(QColor("#29364b"), 1))
            painter.drawLine(
                left, int(y), right, int(y)
            )

            painter.setPen(QColor("#8291aa"))
            painter.drawText(
                7, int(y) + 4, f"{percentage}"
            )

        # Plot the last 60 readings
        points = []
        count = len(self.values)

        for index, value in enumerate(self.values):
            x = left + index / (count - 1) * plot_width
            y = top + (100 - value) / 100 * plot_height
            points.append(QPointF(x, y))

        if len(points) >= 2:
            pen = QPen(self.accent, 2.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)

            for index in range(1, len(points)):
                painter.drawLine(points[index - 1], points[index])

        painter.setPen(QColor("#8291aa"))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(left, self.height() - 9, "60 seconds ago")
        painter.drawText(
            right - 24, self.height() - 9, "Now"
        )

        painter.end()


class PCSentinel(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PC Sentinel")
        self.resize(1050, 850)
        self.setMinimumSize(800, 700)

        self.setStyleSheet("""
            QMainWindow, QWidget#Main {
                background: #0b1120;
                color: #e5edf9;
                font-family: 'Segoe UI';
            }
            QLabel#AppTitle {
                font-size: 28px;
                font-weight: bold;
                color: #f1f5f9;
            }
            QLabel#Subtitle {
                font-size: 11px;
                color: #8291aa;
            }
            QLabel#Section {
                font-size: 17px;
                font-weight: bold;
                color: #dce7f7;
            }
            QFrame#StatCard {
                background: #141e30;
                border: 1px solid #25334a;
                border-radius: 14px;
            }
            QLabel#CardTitle {
                color: #8291aa;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QLabel#CardDetail {
                color: #a4b2c8;
                font-size: 11px;
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

        outer = QHBoxLayout(main)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(12)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(180)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 18, 12, 18)
        sidebar_layout.setSpacing(12)

        
        brand = QLabel("PC SENTINEL")
        brand.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
            color: #38bdf8;
            letter-spacing: 1px;
        """)
        sidebar_layout.addWidget(brand)

        brand_subtitle = QLabel("SYSTEM MONITOR")
        brand_subtitle.setStyleSheet("""
            font-size: 9px;
            font-weight: bold;
            color: #64748b;
            letter-spacing: 2px;
        """)
        sidebar_layout.addWidget(brand_subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #25334a; border: none;")
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(divider)
        sidebar_layout.addSpacing(8)


        self.overview_button = QPushButton("▦  Overview")
        self.diagnostics_button = QPushButton("⚙  Diagnostics")
        self.process_button = QPushButton("▤  Processes")

        for button in (
            self.overview_button,
            self.diagnostics_button,
            self.process_button,
        ):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(42)
            
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #94a3b8;
                    border: 1px solid transparent;
                    border-radius: 8px;
                    text-align: left;
                    padding: 10px 12px;
                    font-size: 12px;
                    font-weight: 500;
                }

                QPushButton:hover {
                    background-color: #19253a;
                    color: #f1f5f9;
                    border: 1px solid #25334a;
                }

                QPushButton[active="true"] {
                    background-color: #123047;
                    color: #38bdf8;
                    border: 1px solid #1e5675;
                    font-weight: bold;
                }
            """)

            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()
        outer.addWidget(sidebar)

        # Page container
        self.pages = QStackedWidget()
        outer.addWidget(self.pages, 1)

        # Existing dashboard goes inside its own page
        overview = QWidget()
        overview.setObjectName("Main")

        root = QVBoxLayout(overview)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(18)


        header = QHBoxLayout()
        heading = QVBoxLayout()

        title = QLabel("PC SENTINEL")
        title.setObjectName("AppTitle")

        subtitle = QLabel("Monitoring System's Performance")
        subtitle.setObjectName("Subtitle")

        heading.addWidget(title)
        heading.addWidget(subtitle)

        self.status = QLabel("● SYSTEM ONLINE")
        self.status.setStyleSheet(
            "color: #34d399; font-size: 11px; font-weight: bold;"
        )

        header.addLayout(heading)
        header.addStretch()
        header.addWidget(self.status)

        root.addLayout(header)

        section = QLabel("Performance Overview")
        section.setObjectName("Section")
        root.addWidget(section)

        cards = QHBoxLayout()
        cards.setSpacing(14)

        self.cpu = StatCard("Processor", "#38bdf8")
        self.ram = StatCard("Memory", "#a78bfa")
        self.disk = StatCard("System Drive (C:)", "#34d399")

        cards.addWidget(self.cpu)
        cards.addWidget(self.ram)
        cards.addWidget(self.disk)

        root.addLayout(cards)

        graph_heading = QLabel("Live Performance")
        graph_heading.setObjectName("Section")
        root.addWidget(graph_heading)

        graphs = QHBoxLayout()
        graphs.setSpacing(14)

        self.cpu_graph = PerformanceGraph("CPU Usage", "#38bdf8")
        self.ram_graph = PerformanceGraph("Memory Usage", "#a78bfa")

        graphs.addWidget(self.cpu_graph)
        graphs.addWidget(self.ram_graph)

        root.addLayout(graphs, 1)

        info = QFrame()
        info.setObjectName("InfoPanel")

        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(18, 14, 18, 14)
        info_layout.setSpacing(6)

        info_title = QLabel("SYSTEM INFORMATION")
        info_title.setStyleSheet(
            "color: #8291aa; font-size: 10px; font-weight: bold;"
        )

        self.cpu_info = QLabel()
        self.ram_info = QLabel()
        self.uptime_info = QLabel()

        info_layout.addWidget(info_title)

        for label in (self.cpu_info, self.ram_info, self.uptime_info):
            label.setStyleSheet("color: #c4d0e2; font-size: 11px;")
            info_layout.addWidget(label)

        root.addWidget(info)
        
               # Register pages
        self.pages.addWidget(overview)

        overview.setLayout(root)

        self.diagnostics_page = DiagnosticsPage()
        self.pages.addWidget(self.diagnostics_page)
        self.process_page = ProcessManagerPage()
        self.pages.addWidget(self.process_page)

        # Sidebar navigation
        
        # Sidebar navigation with active-page highlighting
        self.overview_button.clicked.connect(
            lambda: self.switch_page(overview, self.overview_button)
        )
        self.diagnostics_button.clicked.connect(
            lambda: self.switch_page(
                self.diagnostics_page, self.diagnostics_button
            )
        )
        self.process_button.clicked.connect(
            lambda: self.switch_page(
                self.process_page, self.process_button
            )
        )

        # Start on Overview
        self.switch_page(overview, self.overview_button)



        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

        self.update_stats()

    def update_stats(self):
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        try:
            disk = psutil.disk_usage("C:\\")
            disk_value = disk.percent
            disk_detail = (
                f"{disk.used / (1024**3):.0f} / "
                f"{disk.total / (1024**3):.0f} GB used"
            )
        except OSError:
            disk_value = 0
            disk_detail = "System drive unavailable"

        self.cpu.update_card(
            cpu, f"{psutil.cpu_count(logical=True)} logical processors"
        )

        self.ram.update_card(
            memory.percent,
            f"{memory.used / (1024**3):.1f} / "
            f"{memory.total / (1024**3):.1f} GB used"
        )

        self.disk.update_card(disk_value, disk_detail)

        self.cpu_graph.add_value(cpu)
        self.ram_graph.add_value(memory.percent)

        elapsed = max(0, int(time.time() - psutil.boot_time()))

        self.cpu_info.setText(
            f"Logical processors: {psutil.cpu_count(logical=True)}"
        )
        self.ram_info.setText(
            f"Available memory: {memory.available / (1024**3):.1f} GB"
        )
        self.uptime_info.setText(
            f"System uptime: {elapsed // 86400}d "
            f"{(elapsed % 86400) // 3600}h "
            f"{(elapsed % 3600) // 60}m"
        )


    
    def switch_page(self, page, active_button):
        self.pages.setCurrentWidget(page)

        buttons = (
            self.overview_button,
            self.diagnostics_button,
            self.process_button,
        )

        for button in buttons:
            button.setProperty("active", button is active_button)

            button.setStyleSheet(
                """
                QPushButton {
                    background-color: #111c2f;
                    color: #38bdf8;
                    border: 1px solid #245477;
                    border-left: 4px solid #38bdf8;
                    border-radius: 8px;
                    text-align: left;
                    padding: 10px 12px;
                    font-weight: bold;
                }
                """
                if button is active_button else
                """
                QPushButton {
                    background-color: transparent;
                    color: #94a3b8;
                    border: 1px solid transparent;
                    border-radius: 8px;
                    text-align: left;
                    padding: 10px 12px;
                }
                QPushButton:hover {
                    background-color: #19253a;
                    color: #f1f5f9;
                    border: 1px solid #25334a;
                }
                """
            )


            # Refresh the stylesheet so Qt applies the new state.
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = PCSentinel()
    window.show()

    sys.exit(app.exec())
