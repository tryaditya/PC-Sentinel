
import sys
from PySide6.QtWidgets import QApplication
from diagnostics import DiagnosticsPage

app = QApplication(sys.argv)

window = DiagnosticsPage()
window.setWindowTitle("PC Sentinel - Diagnostics Test")
window.resize(750, 800)
window.show()

sys.exit(app.exec())
