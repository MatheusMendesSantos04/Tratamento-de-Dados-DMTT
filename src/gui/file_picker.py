from PySide6.QtWidgets import QFileDialog, QWidget
from typing import Optional



def choose_file(parent, title, filetypes=None):
    if filetypes is None:
        filetypes = [
            ("Arquivos PDF", "*.pdf"),
            ("Planilhas Excel", "*.xlsx"),
            ("Arquivo CSV", "*.csv")
        ]
    
    filter_parts = [f"{label} ({pattern})" for label, pattern in filetypes]
    filter_string = ";; ".join(filter_parts)

    dialog = QFileDialog(parent, title)
    path, _ = dialog.getOpenFileName(parent, title, "", filter_string)
    return path