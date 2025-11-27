"""Main UI window. Integrates file selection, processing and table display.


Features in this maximal version:
- Menu and toolbar: Open file, Open second file (compare), Export (CSV), Quit
- Central DataFrame viewer (table)
- Status bar with messages
- Progress indicator (simple) while processing
- Error dialogs


This file assumes existing modules:
- src.file_handler.load_file
- src.data_processing.normalize_dataframe
- src.data_processing.fix_columns


Adjust imports if your package layout differs.
"""

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import (
QMainWindow,
QToolBar,
QFileDialog,
QMessageBox,
QProgressDialog,
QVBoxLayout,
QWidget,
QPushButton,
QHBoxLayout,
QLabel,
)

from PySide6.QtGui import QAction
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QThread, Signal, QObject


import pandas as pd
import traceback
from src.workers.file_loader import LoadeWorker
from PySide6.QtCore import QRunnable


# Import local processing modules
from src.file_handler import load_file, compare_columns
from src.data_processing import normalize_dataframe, fix_columns, list_columns, select_columns
from src.gui.file_picker import choose_file
from src.gui.table_viewer import DataFrameView

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem

def dataframe_to_table(df):
    table = QTableWidget()
    table.setRowCount(df.shape[0])
    table.setColumnCount(df.shape[1])
    table.setHorizontalHeaderLabels(df.columns)

    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            item = QTableWidgetItem(str(df.iloc[i, j]))
            table.setItem(i, j, item)

    table.resizeColumnsToContents()
    return table



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.setCentralWidget(self.container)
        self.threadpool = QThreadPool()
        print("ThreadPool inicializado com", self.threadpool.maxThreadCount(), "threads")

        self.setWindowTitle("Data Treatment Application")
        self.resize(1100, 700)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)


        open_action = QAction("Abrir Arquivo", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        open_second_action = QAction("Abrir Segundo Arquivo", self)
        open_second_action.triggered.connect(self.open_second_file)
        toolbar.addAction(open_second_action)

        export_action = QAction("Expotar CSV", self)
        export_action.triggered.connect(self.export_csv)
        toolbar.addAction(export_action)

        quit_action = QAction("Sair", self)
        quit_action.triggered.connect(self.close)   
        toolbar.addAction(quit_action)

        controls = QHBoxLayout()
        self.Ibl_info = QLabel("Nenhum arquivo carregado.")
        controls.addWidget(self.Ibl_info)
        controls.addStretch()

        btn_show_columns = QPushButton("Selecione as Colunas")
        btn_show_columns.clicked.connect(self.show_column_selection)
        controls.addWidget(btn_show_columns)

        layout.addLayout(controls)

        self.table_view = DataFrameView()
        layout.addWidget(self.table_view)

        self.statusBar().showMessage("Pronto")

        self.current_df = None
        self.second_df = None

    def carregar_arquivo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo", "", "CSV (*.csv);;Excel (*.xlsx)")

        if not path:
            return

        import pandas as pd

        if path.endswith(".csv"):
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)

        tabela = dataframe_to_table(df)

        # Remove tabela antiga, se existir
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Adiciona a nova
        self.layout.addWidget(tabela)

    def file_result(self, df):
        """ Recebe o DataFrame carregado pelo Worker e exibe na tela"""
        try:
            self.table_view.set_dataframe(df)
            self.df = df

            self.statusBar().showMessage(f"{len(df)} linhas carregadas.")
            self.Ibl_info.setText("Arquivo carregado com sucesso!")
        
        except Exception as e:
            self.show_error_message(f"Erro ao exibir tabela:\n{e}")

        

    def file_loaded(self):
        """Chamado quando o Worker finaliza."""
        if hasattr(self, "progress") and self.progress:
            self.progress.close()


    def file_error(self, msg):
        self.progress.close()
        QMessageBox.critical(self, "Erro ao carregar arquivo", msg)


    def show_column_selection(self):
        """
        Abre a janela de seleção de colunas.
        """
        if self.current_df is None:
            QMessageBox.warning(self, "Atenção", "Nenhum arquivo carregado ainda.")
            return

        from PySide6.QtWidgets import QInputDialog

        cols = list(self.current_df.columns)
        selected, ok = QInputDialog.getItem(
            self,
            "Selecionar Coluna",
            "Escolha uma coluna:",
            cols,
            0,
            False
        )

        if ok:
            QMessageBox.information(self, "Selecionado", f"Você escolheu: {selected}")

    def open_file(self):
        path = choose_file(self, "Selecione o arquivo PDF")
        if not path:
            return

        self.Ibl_info.setText(f"Carregando arquivo: {path}")
        self.statusBar().showMessage(f"Carregando arquivo: {path}")

        # janela de progresso
        self.progress = QProgressDialog("Carregando arquivo...", "Cancelar", 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()

        # cria worker
        self.worker = LoadeWorker(path)

        # conecta sinais
        self.worker.signals.finished.connect(self.file_loaded)
        self.worker.signals.result.connect(self.file_result)
        self.worker.signals.error.connect(self.file_error)

        # roda em background
        self.threadpool.start(self.worker)

    def on_load_finished(self, df: pd.DataFrame):
        self.progress.cancel()
        self.current_df = df
        self.table_view.set_dataframe(df)
        self.Ibl_info.setText(f"Arquivo carregado com {len(df)} linhas e {len(df.columns)} colunas.")
        self.statusBar().showMessage("Arquivo carregado com sucesso.")
 
    def on_load_error(self, error_text: str):
        self._progress.cancel()
        QMessageBox.critical(self, "Erro ao carregar", f"Falha ao processar o arquivo:\n{error_text}")
        self.lbl_info.setText("Erro ao carregar arquivo.")
        self.statusBar().showMessage("Erro")
 
    def open_second_file(self):
        path = choose_file(self,   filetypes=[("Arquivos PDF", "*.pdf"),("Planilhas Excel", "*.xlsx"),("Arquivo CSV", "*.csv")])
        if not path:
            return
        try:
            df2 = load_file(path)
            df2 = fix_columns(df2)
            df2 = normalize_dataframe(df2)
            self.second_df = df2
            # compare columns
            eq, details = compare_columns(self.current_df, self.second_df)
            msg = "Arquivos compatíveis (mesmas colunas)." if eq else f"Diferenças encontradas:\nOnly in df1: {details['only_in_df1']}\nOnly in df2: {details['only_in_df2']}"
            QMessageBox.information(self, "Resultado da comparação", msg)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def handle_select_columns(self):
        if self.current_df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum arquivo carregado.")
            return
        cols = list_columns(self.current_df)
    # Simples seletor via input dialog (could be improved with a proper multi-select dialog)
        from PySide6.QtWidgets import QInputDialog
        choices_str = "\n".join(f"{i+1}. {c}" for i, c in enumerate(cols))
        text, ok = QInputDialog.getText(self, "Selecionar colunas", f"Escolha números separados por vírgula:\n{choices_str}")
        if not ok or not text:
            return
        
        try:
            idxs = [int(x.strip()) - 1 for x in text.split(",")]
            sel = [cols[i] for i in idxs]
            df_sel = select_columns(self.current_df, sel)
            self.current_df = df_sel
            self.table_view.set_dataframe(df_sel)
            self.statusBar().showMessage("Colunas selecionadas")
        except Exception as e:
            QMessageBox.critical(self, "Erro na seleção", str(e))


    def export_csv(self):
        if self.current_df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum arquivo carregado.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", str(), "CSV files (*.csv)")
        if not path:
            return
        try:
            self.current_df.to_csv(path, index=False)
            QMessageBox.information(self, "Exportado", "CSV exportado com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro exportando", str(e))            