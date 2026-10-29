
import time

import psutil

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
)

class NetworkGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.download_history = [0.0] * 60
        self.upload_history = [0.0] * 60

        self.setMinimumHeight(220)

    def add_reading(self, download, upload):
        self.download_history.append(download)
        self.upload_history.append(upload)

        self.download_history = self.download_history[-60:]
        self.upload_history = self.upload_history[-60:]

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        area = self.rect().adjusted(40, 20, -15, -30)

        painter.setPen(QPen(Qt.GlobalColor.darkGray, 1))

        for i in range(5):
            y = area.top() + i * area.height() / 4
            painter.drawLine(
                int(area.left()), int(y),
                int(area.right()), int(y)
            )

        max_speed = max(
            1.0,
            max(self.download_history),
            max(self.upload_history),
        ) * 1.2

        def draw_line(history, color):
            pen = QPen(color, 2)
            painter.setPen(pen)

            points = []
            for i, speed in enumerate(history):
                x = area.left() + i * area.width() / 59
                y = area.bottom() - (speed / max_speed) * area.height()
                points.append(QPointF(x, y))

            for i in range(1, len(points)):
                painter.drawLine(points[i - 1], points[i])

        draw_line(self.download_history, Qt.GlobalColor.cyan)
        draw_line(self.upload_history, Qt.GlobalColor.green)

        painter.end()
class NetworkMonitorPage(QWidget):
    def __init__(self):
        super().__init__()

        self.previous_time = time.monotonic()
        self.previous_stats = psutil.net_io_counters()

        self.setStyleSheet("""
            QWidget {
                background-color: #0b1120;
                color: #e5edf9;
                font-family: 'Segoe UI';
            }

            QFrame#metricCard {
                background-color: #141e30;
                border: 1px solid #25334a;
                border-radius: 12px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("Network Monitor")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #f1f5f9;"
        )

        subtitle = QLabel(
            "Monitor live network speeds and data usage."
        )
        subtitle.setStyleSheet("color: #8291aa; font-size: 12px;")

        root.addWidget(title)
        root.addWidget(subtitle)

        cards = QHBoxLayout()
        cards.setSpacing(16)

        self.download_label = self.create_metric_card(
            cards, "Download Speed", "0.00 Mbps"
        )
        self.upload_label = self.create_metric_card(
            cards, "Upload Speed", "0.00 Mbps"
        )

        root.addLayout(cards)
        graph_title = QLabel("Network Activity — Last 60 Seconds")
        graph_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #f1f5f9;"
        )
        root.addWidget(graph_title)

        self.network_graph = NetworkGraph()
        root.addWidget(self.network_graph)

        self.received_label = QLabel("Total downloaded: 0 MB")
        self.sent_label = QLabel("Total uploaded: 0 MB")
        self.connection_label = QLabel("Network: Checking...")

        for label in (
            self.received_label,
            self.sent_label,
            self.connection_label,
        ):
            label.setStyleSheet(
                "color: #a4b2c8; font-size: 13px; padding: 4px;"
            )
            root.addWidget(label)

        root.addStretch()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_network_stats)
        self.timer.start(1000)

        self.update_network_stats()

    def create_metric_card(self, layout, heading, initial_value):
        card = QFrame()
        card.setObjectName("metricCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(10)

        heading_label = QLabel(heading)
        heading_label.setStyleSheet(
            "color: #a4b2c8; font-size: 13px; border: none;"
        )

        value_label = QLabel(initial_value)
        value_label.setStyleSheet(
            "color: #38bdf8; font-size: 25px; "
            "font-weight: bold; border: none;"
        )

        card_layout.addWidget(heading_label)
        card_layout.addWidget(value_label)
        layout.addWidget(card)

        return value_label

    def update_network_stats(self):
        try:
            current_stats = psutil.net_io_counters()
            current_time = time.monotonic()

            elapsed = current_time - self.previous_time
            if elapsed <= 0:
                return

            download_mbps = (
                (current_stats.bytes_recv - self.previous_stats.bytes_recv)
                * 8 / elapsed / 1_000_000
            )

            upload_mbps = (
                (current_stats.bytes_sent - self.previous_stats.bytes_sent)
                * 8 / elapsed / 1_000_000
            )

            self.download_label.setText(
                f"{max(0, download_mbps):.2f} Mbps"
            )
            self.upload_label.setText(
                f"{max(0, upload_mbps):.2f} Mbps"
            )
            self.network_graph.add_reading(
                max(0, download_mbps),
                max(0, upload_mbps),
            )

            self.received_label.setText(
                f"Total downloaded: "
                f"{current_stats.bytes_recv / (1024 ** 2):.2f} MB"
            )
            self.sent_label.setText(
                f"Total uploaded: "
                f"{current_stats.bytes_sent / (1024 ** 2):.2f} MB"
            )

            if psutil.net_if_stats():
                active = any(
                    stats.isup for stats in psutil.net_if_stats().values()
                )
                self.connection_label.setText(
                    "Network: Connected" if active else "Network: Disconnected"
                )
            else:
                self.connection_label.setText(
                    "Network: Status unavailable"
                )

            self.previous_stats = current_stats
            self.previous_time = current_time

        except (psutil.Error, OSError) as error:
            self.connection_label.setText(
                f"Network reading error: {error}"
            )
