import sys
from pathlib import Path


if __name__ == "__main__":
# Ensure project root is on sys.path when running with `python -m src.app` (it already is)
    from src.gui.main_window import MainWindow
    from PySide6.QtWidgets import QApplication
    


app = QApplication(sys.argv)
win = MainWindow()
win.show()
sys.exit(app.exec())