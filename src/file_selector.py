import tkinter as tk
from tkinter import filedialog
from pathlib import Path


def choose_pdf_file() -> str:
    """
    Abre uma janela de seleção para o usuário escolher
    um arquivo PDF. Retorna o caminho completo.
    """

    # Evita que a janela principal do Tkinter apareça
    root = tk.Tk()
    root.withdraw()

    pdf_path = filedialog.askopenfilename(
        title="Selecione um arquivo PDF",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )

    if not pdf_path:
        raise ValueError("Nenhum arquivo foi selecionado.")

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError("Arquivo selecionado não existe.")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("O arquivo selecionado não é um PDF.")

    return str(pdf_path)
