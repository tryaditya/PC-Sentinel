
import psutil

from PySide6.QtCore import Qt, QThread, Signal, QAbstractTableModel
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QHeaderView,
)


class ProcessScanWorker(QThread):
    processes_ready = Signal(list)
    scan_failed = Signal(str)

    def run(self):
        processes = []

        try:
            for process in psutil.process_iter(
                ["pid", "name", "memory_info"]
            ):
                try:
                    info = process.info
                    memory_info = info["memory_info"]

                    memory_mb = (
                        memory_info.rss / (1024 * 1024)
                        if memory_info else 0
                    )

                    processes.append({
                        "name": info["name"] or "Unknown",
                        "pid": info["pid"],
                        "cpu": process.cpu_percent(interval=None),
                        "memory_mb": memory_mb,
                    })

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

            processes.sort(
                key=lambda item: item["memory_mb"],
                reverse=True,
            )

            self.processes_ready.emit(processes)

        except Exception as error:
            self.scan_failed.emit(str(error))


class ProcessTableModel(QAbstractTableModel):
    HEADERS = ["Process", "PID", "CPU Usage", "Memory Usage"]

    def __init__(self):
        super().__init__()
        self.processes = []

    def rowCount(self, parent=None):
        return 0 if parent and parent.isValid() else len(self.processes)

    def columnCount(self, parent=None):
        return 0 if parent and parent.isValid() else 4

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() > 0:
                return int(
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                )
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        if role != Qt.ItemDataRole.DisplayRole:
            return None

        item = self.processes[index.row()]

        values = [
            item["name"],
            str(item["pid"]),
            f'{item["cpu"]:.1f}%',
            f'{item["memory_mb"]:.1f} MB',
        ]

        return values[index.column()]

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.HEADERS[section]

        return None

    def set_processes(self, processes):
        self.beginResetModel()
        self.processes = processes
        self.endResetModel()


class ProcessManagerPage(QWidget):
    def __init__(self):
        super().__init__()

        self.worker = None
        self.model = ProcessTableModel()

        self.setStyleSheet("""
            QWidget {
                background-color: #0b1120;
                color: #e5edf9;
                font-family: 'Segoe UI';
            }
            QPushButton {
                background-color: #141e30;
                color: #e5edf9;
                border: 1px solid #25334a;
                border-radius: 8px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: #25334a;
            }
            QPushButton:disabled {
                color: #64748b;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("Process Manager")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #f1f5f9;"
        )

        subtitle = QLabel(
            "View running processes and their resource usage."
        )
        subtitle.setStyleSheet("color: #8291aa; font-size: 12px;")

        root.addWidget(title)
        root.addWidget(subtitle)

        toolbar = QHBoxLayout()

        self.status = QLabel("Ready to scan processes.")
        self.status.setStyleSheet("color: #a4b2c8;")

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.refresh_button.setMinimumHeight(36)
        self.refresh_button.clicked.connect(self.refresh_processes)

        toolbar.addWidget(self.status)
        toolbar.addStretch()
        toolbar.addWidget(self.refresh_button)

        root.addLayout(toolbar)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableView.EditTrigger.NoEditTriggers
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

        for column in (1, 2, 3):
            header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )

        self.table.setStyleSheet("""
            QTableView {
                background: #141e30;
                alternate-background-color: #19253a;
                color: #e5edf9;
                gridline-color: #25334a;
                border: 1px solid #25334a;
                border-radius: 8px;
            }
            QHeaderView::section {
                background: #0f1728;
                color: #a4b2c8;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableView::item {
                padding: 5px;
            }
        """)

        root.addWidget(self.table, 1)

        self.refresh_processes()

    def refresh_processes(self):
        if self.worker is not None and self.worker.isRunning():
            return

        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Refreshing...")
        self.status.setText("Scanning running processes...")

        self.worker = ProcessScanWorker()
        self.worker.processes_ready.connect(self.show_processes)
        self.worker.scan_failed.connect(self.show_scan_error)
        self.worker.finished.connect(self.scan_finished)
        self.worker.start()

    def show_processes(self, processes):
        self.model.set_processes(processes)

        self.status.setText(
            f"{len(processes)} processes found · "
            "Sorted by memory usage"
        )

    def show_scan_error(self, message):
        self.status.setText(f"Scan failed: {message}")

    def scan_finished(self):
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("Refresh")
