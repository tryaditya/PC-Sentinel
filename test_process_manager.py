import sys

from PySide6.QtWidgets import QApplication
from process_manager import ProcessManagerPage

app = QApplication(sys.argv)

window = ProcessManagerPage()
window.resize(900, 600)
window.show()

sys.exit(app.exec())