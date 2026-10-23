
import os
import sys
import time
import winreg
import psutil

from pathlib import Path
from collections import deque

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame
)


class DiagnosticsPage(QWidget):
    def __init__(self):
        super().__init__()

        self.cpu_history = deque(maxlen=5)
        self.ram_history = deque(maxlen=5)

        self.setStyleSheet("""
            QWidget {
                background: #0b1120;
                color: #e5edf9;
                font-family: 'Segoe UI';
            }
            QLabel#Heading {
                font-size: 25px;
                font-weight: bold;
                color: #f1f5f9;
            }
            QLabel#Subtitle {
                color: #8291aa;
                font-size: 12px;
            }
            QFrame#Finding {
                background: #141e30;
                border: 1px solid #25334a;
                border-radius: 12px;
            }
            QLabel#FindingTitle {
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#FindingBody {
                color: #b7c4d8;
                font-size: 12px;
            }
            QPushButton {
                background: #164e63;
                color: #e0f2fe;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #155e75;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        heading = QLabel("Diagnostics Center")
        heading.setObjectName("Heading")

        subtitle = QLabel(
            "Check system health and understand potential issues."
        )
        subtitle.setObjectName("Subtitle")

        root.addWidget(heading)
        root.addWidget(subtitle)

        self.summary = QLabel("Preparing system checks...")
        self.summary.setStyleSheet(
            "font-size: 15px; font-weight: bold; padding: 8px 0;"
        )
        root.addWidget(self.summary)

        self.findings_layout = QVBoxLayout()
        self.findings_layout.setSpacing(10)
        root.addLayout(self.findings_layout)

        self.refresh_button = QPushButton("Run diagnostics again")
        self.refresh_button.clicked.connect(self.run_diagnostics)
        root.addWidget(self.refresh_button)

        root.addStretch()

        # Collect readings every two seconds.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.collect_readings)
        self.timer.start(2000)

        self.collect_readings()
        self.run_diagnostics()

    def collect_readings(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        self.cpu_history.append(cpu)
        self.ram_history.append(ram)

    def add_finding(self, title, message, level="info"):
        colors = {
            "good": "#34d399",
            "warning": "#fbbf24",
            "critical": "#fb7185",
            "info": "#38bdf8",
        }

        card = QFrame()
        card.setObjectName("Finding")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("FindingTitle")
        title_label.setStyleSheet(
            f"color: {colors.get(level, colors['info'])};"
        )

        body_label = QLabel(message)
        body_label.setObjectName("FindingBody")
        body_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(body_label)
        self.findings_layout.addWidget(card)

    def check_startup_entries(self):
        entries = []
        locations = [
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
            ),
        ]

        for hive, key_path in locations:
            try:
                with winreg.OpenKey(hive, key_path) as key:
                    index = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, index)
                            entries.append((name, str(value)))
                            index += 1
                        except OSError:
                            break
            except OSError:
                # Some registry locations may not exist or be accessible.
                continue

        folders = [
            Path(os.environ.get("APPDATA", ""))
            / "Microsoft/Windows/Start Menu/Programs/Startup",
            Path(os.environ.get("PROGRAMDATA", ""))
            / "Microsoft/Windows/Start Menu/Programs/Startup",
        ]

        for folder in folders:
            if not str(folder) or not folder.is_dir():
                continue

            try:
                for item in folder.iterdir():
                    entries.append((item.name, str(item)))
            except OSError:
                continue

        return entries

    def run_diagnostics(self):
        while self.findings_layout.count():
            item = self.findings_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        issues = 0

        # CPU: use recent samples to reduce alerts from brief spikes.
        if self.cpu_history:
            cpu_avg = sum(self.cpu_history) / len(self.cpu_history)

            if len(self.cpu_history) >= 3 and cpu_avg >= 90:
                self.add_finding(
                    "High CPU usage",
                    f"Recent average CPU usage is {cpu_avg:.1f}%. "
                    "A demanding app or background task may be responsible. "
                    "Check Task Manager's Processes tab to identify it.",
                    "critical",
                )
                issues += 1
            elif len(self.cpu_history) >= 3 and cpu_avg >= 80:
                self.add_finding(
                    "Elevated CPU usage",
                    f"Recent average CPU usage is {cpu_avg:.1f}%. "
                    "This can be normal during gaming or heavy work. "
                    "Check whether it remains high when your PC is idle.",
                    "warning",
                )
                issues += 1
            else:
                self.add_finding(
                    "CPU usage looks reasonable",
                    f"Recent average: {cpu_avg:.1f}%. "
                    "Short spikes are normal during demanding tasks.",
                    "good",
                )

        # RAM
        memory = psutil.virtual_memory()

        if memory.percent >= 95:
            self.add_finding(
                "Memory critically high",
                f"RAM usage is {memory.percent:.1f}%. "
                "Close unnecessary applications and check Task Manager "
                "for processes consuming the most memory.",
                "critical",
            )
            issues += 1
        elif memory.percent >= 85:
            self.add_finding(
                "High memory usage",
                f"RAM usage is {memory.percent:.1f}%. "
                "Some applications may slow down when memory is scarce. "
                "Check which apps are using the most RAM.",
                "warning",
            )
            issues += 1
        else:
            self.add_finding(
                "Memory usage looks reasonable",
                f"{memory.percent:.1f}% used; "
                f"{memory.available / (1024**3):.1f} GB available.",
                "good",
            )

        # Check all mounted disk partitions, avoiding duplicate drive letters.
        seen = set()

        for partition in psutil.disk_partitions(all=False):
            drive = partition.device

            if drive in seen:
                continue
            seen.add(drive)

            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except (OSError, PermissionError):
                continue

            free_gb = usage.free / (1024**3)

            if usage.percent >= 95 or free_gb < 5:
                level = "critical"
                title = f"Very low disk space: {drive}"
                issues += 1
            elif usage.percent >= 85 or free_gb < 10:
                level = "warning"
                title = f"Disk space getting low: {drive}"
                issues += 1
            else:
                level = "good"
                title = f"Disk space looks reasonable: {drive}"

            self.add_finding(
                title,
                f"{free_gb:.1f} GB free out of "
                f"{usage.total / (1024**3):.1f} GB. "
                + (
                    "Consider removing files you no longer need."
                    if level != "good"
                    else "No immediate space issue detected."
                ),
                level,
            )

        # Startup inventory: report what is configured, not what is bad.
        try:
            entries = self.check_startup_entries()
            count = len(entries)

            preview = ", ".join(name for name, _ in entries[:5])
            if count > 5:
                preview += ", and more"

            self.add_finding(
                f"Windows startup inventory: {count} entries",
                (
                    f"Found: {preview}. Review these entries in "
                    "Task Manager > Startup apps if booting is slow. "
                    "This inventory alone does not mean an app is harmful."
                    if count
                    else
                    "No entries were found in the checked Run keys or "
                    "Startup folders. Other startup mechanisms may exist."
                ),
                "info",
            )
        except Exception as error:
            self.add_finding(
                "Startup inventory unavailable",
                f"Windows startup entries could not be checked: {error}",
                "warning",
            )

        self.summary.setText(
            f"Diagnostics complete — {issues} potential issue(s) found."
        )
