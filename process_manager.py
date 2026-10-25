
import psutil

from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    QAbstractTableModel,
    QSortFilterProxyModel,
    QTimer,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QHeaderView,
    QLineEdit,
    QMessageBox,
)


class ProcessScanWorker(QThread):
    processes_ready = Signal(list)
    scan_failed = Signal(str)

    def run(self):
        processes = []

        try:
            for process in psutil.process_iter(
                ["pid", "name", "memory_info", "create_time"]
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
                        "create_time": info["create_time"],
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
            return int(
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter
            )

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

    def headerData(
        self,
        section,
        orientation,
        role=Qt.ItemDataRole.DisplayRole,
    ):
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

        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(0)
        self.proxy_model.setFilterCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive
        )

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
                border-color: #38bdf8;
            }

            QPushButton:disabled {
                color: #64748b;
            }

            QLineEdit {
                background-color: #141e30;
                color: #e5edf9;
                border: 1px solid #25334a;
                border-radius: 8px;
                padding: 9px 12px;
                selection-background-color: #075985;
            }

            QLineEdit:focus {
                border: 1px solid #38bdf8;
            }

            QLineEdit::placeholder {
                color: #8291aa;
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
        self.end_task_button = QPushButton("End Task")
        self.end_task_button.setCursor(
        Qt.CursorShape.PointingHandCursor
)
        self.end_task_button.setMinimumHeight(36)
        self.end_task_button.setEnabled(False)
        self.end_task_button.clicked.connect(
        self.end_selected_process
)
        

        toolbar.addWidget(self.status)
        toolbar.addStretch()
        toolbar.addWidget(self.end_task_button)
        toolbar.addWidget(self.refresh_button)


        root.addLayout(toolbar)

        search_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search processes by name, e.g. chrome.exe..."
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(
            self.filter_processes
        )

        self.result_count = QLabel("0 matches")
        self.result_count.setStyleSheet(
            "color: #8291aa; font-size: 11px;"
        )

        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.result_count)

        root.addLayout(search_row)

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableView.SelectionMode.SingleSelection
        )

        self.table.clicked.connect(
        self.on_process_row_clicked
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
                selection-background-color: #164e63;
                selection-color: #f1f5f9;
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

            QTableView::item:hover {
                background: #203149;
            }
        """)

        root.addWidget(self.table, 1)

        self.refresh_processes()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_processes)
        self.refresh_timer.start(5000)

    def filter_processes(self, text):
        self.proxy_model.setFilterFixedString(text)

        visible_count = self.proxy_model.rowCount()
        total_count = len(self.model.processes)

        self.result_count.setText(
            f"{visible_count} of {total_count} processes"
        )

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

        self.filter_processes(self.search_input.text())

    def show_scan_error(self, message):
        self.status.setText(f"Scan failed: {message}")

    def scan_finished(self):
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("Refresh")




    def on_process_row_clicked(self, index):
        self.end_task_button.setEnabled(index.isValid())

    def end_selected_process(self):
        index = self.table.currentIndex()

        if not index.isValid():
            return

        source_index = self.proxy_model.mapToSource(index)
        process_data = self.model.processes[source_index.row()]

        pid = process_data["pid"]
        name = process_data["name"]

        # Avoid terminating important Windows system processes.
        protected_names = {
            "system",
            "registry",
            "smss.exe",
            "csrss.exe",
            "wininit.exe",
            "winlogon.exe",
            "services.exe",
            "lsass.exe",
            "svchost.exe",
            "explorer.exe",
        }

        if name.lower() in protected_names or pid in {0, 4}:
            QMessageBox.warning(
                self,
                "Protected Process",
                f"{name} (PID {pid}) is protected from termination."
            )
            return

        answer = QMessageBox.question(
            self,
            "Confirm End Task",
            f"Are you sure you want to terminate {name} (PID {pid})?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            process = psutil.Process(pid)

            # Verify the PID still belongs to the same process.
            current_name = process.name()
            current_create_time = process.create_time()
            original_create_time = process_data["create_time"]

            if (
                current_name.lower() != name.lower()
                or original_create_time is None
                or abs(current_create_time - original_create_time) > 0.01
            ):
                QMessageBox.warning(
                    self,
                    "Process Changed",
                    "This process may have changed since the list was loaded. "
                    "Refresh the list and try again."
                )
                self.refresh_processes()
                return

            process.terminate()

            # Verify the PID still belongs to the same process.
            if process.name().lower() != name.lower():
                QMessageBox.warning(
                    self,
                    "Process Changed",
                    "This process has changed since the list was loaded. "
                    "Refresh the list and try again."
                )
                self.refresh_processes()
                return

            process.terminate()

            QMessageBox.information(
                self,
                "End Task",
                f"Termination requested for {name} (PID {pid})."
            )

            self.refresh_processes()

        except psutil.NoSuchProcess:
            QMessageBox.information(
                self,
                "Process Already Closed",
                f"{name} is no longer running."
            )
            self.refresh_processes()

        except (psutil.AccessDenied, psutil.Error) as error:
            QMessageBox.warning(
                self,
                "Unable to End Task",
                f"Windows did not allow this process to be terminated.\n\n"
                f"{error}"
            )
