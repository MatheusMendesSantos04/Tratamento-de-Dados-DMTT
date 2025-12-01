"""
main_window.py

Interface principal do aplicativo de tratamento de dados.

Funcionalidades:
- Upload de múltiplos arquivos (PDF, CSV, Excel)
- Validação de colunas entre arquivos
- Exibição de DataFrame em tabela
- Seleção de colunas para análise
- Exportação para CSV, PDF e DOCX

Autor: Matheus
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
    QDialog,
    QListWidget,
    QDialogButtonBox,
)
from PySide6.QtGui import QAction

import pandas as pd
from pathlib import Path

# Importações locais
from file_handler import load_file, compare_columns
from data_processing import normalize_dataframe, fix_columns, list_columns, select_columns
from gui.file_picker import choose_file
from gui.table_viewer import DataFrameView
from workers.file_loader import LoadWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configurações da janela
        self.setWindowTitle("Aplicativo de Tratamento de Dados")
        self.resize(1200, 800)
        
        # ThreadPool para processamento assíncrono
        self.threadpool = QThreadPool()
        print(f"ThreadPool inicializado com {self.threadpool.maxThreadCount()} threads")
        
        # Dados
        self.current_df = None
        self.loaded_files = []  # Lista de arquivos carregados
        self.all_dataframes = []  # Lista de DataFrames carregados
        
        # Setup UI
        self._setup_ui()
        
        # Status inicial
        self.statusBar().showMessage("Pronto para carregar arquivos")
    
    
    def _setup_ui(self):
        """Configura toda a interface do usuário"""
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        self._create_toolbar()
        
        # Área de controles
        controls_layout = QHBoxLayout()
        
        self.lbl_info = QLabel("Nenhum arquivo carregado")
        self.lbl_info.setStyleSheet("font-weight: bold; color: #555;")
        controls_layout.addWidget(self.lbl_info)
        
        controls_layout.addStretch()
        
        # Botões de ação
        btn_add_file = QPushButton("➕ Adicionar Arquivo")
        btn_add_file.clicked.connect(self.add_file)
        btn_add_file.setToolTip("Adicionar mais um arquivo ao conjunto")
        controls_layout.addWidget(btn_add_file)
        
        btn_clear = QPushButton("🗑️ Limpar Tudo")
        btn_clear.clicked.connect(self.clear_all)
        btn_clear.setToolTip("Remover todos os arquivos carregados")
        controls_layout.addWidget(btn_clear)
        
        btn_select_columns = QPushButton("📋 Selecionar Colunas")
        btn_select_columns.clicked.connect(self.show_column_selection)
        btn_select_columns.setToolTip("Escolher quais colunas exibir")
        controls_layout.addWidget(btn_select_columns)
        
        main_layout.addLayout(controls_layout)
        
        # Tabela de dados
        self.table_view = DataFrameView()
        main_layout.addWidget(self.table_view)
        
        # Status bar (já existe por padrão no QMainWindow)
    
    
    def _create_toolbar(self):
        """Cria a barra de ferramentas"""
        toolbar = QToolBar("Barra Principal")
        self.addToolBar(toolbar)
        
        # Ação: Abrir arquivo
        open_action = QAction("📂 Abrir Arquivo", self)
        open_action.triggered.connect(self.open_file)
        open_action.setToolTip("Carregar um arquivo (substitui os anteriores)")
        toolbar.addAction(open_action)
        
        # Ação: Abrir múltiplos arquivos
        open_multiple_action = QAction("📁 Abrir Múltiplos", self)
        open_multiple_action.triggered.connect(self.open_multiple_files)
        open_multiple_action.setToolTip("Carregar vários arquivos de uma vez")
        toolbar.addAction(open_multiple_action)
        
        toolbar.addSeparator()
        
        # Ação: Exportar CSV
        export_csv_action = QAction("💾 Exportar CSV", self)
        export_csv_action.triggered.connect(self.export_csv)
        export_csv_action.setToolTip("Salvar dados como CSV")
        toolbar.addAction(export_csv_action)
        
        # Ação: Exportar PDF
        export_pdf_action = QAction("📄 Exportar PDF", self)
        export_pdf_action.triggered.connect(self.export_pdf)
        export_pdf_action.setToolTip("Salvar dados como PDF")
        toolbar.addAction(export_pdf_action)
        
        # Ação: Exportar Word
        export_word_action = QAction("📝 Exportar Word", self)
        export_word_action.triggered.connect(self.export_word)
        export_word_action.setToolTip("Salvar dados como documento Word")
        toolbar.addAction(export_word_action)
        
        toolbar.addSeparator()
        
        # Ação: Sair
        quit_action = QAction("❌ Sair", self)
        quit_action.triggered.connect(self.close)
        toolbar.addAction(quit_action)
    
    
    # ============================================================
    # CARREGAMENTO DE ARQUIVOS
    # ============================================================
    
    def open_file(self):
        """Abre UM arquivo (substitui os anteriores)"""
        path = choose_file(self, "Selecione um arquivo")
        if not path:
            return
        
        # Limpa dados anteriores
        self.clear_all()
        
        # Carrega o arquivo
        self._load_file_async(path)
    
    
    def open_multiple_files(self):
        """Abre MÚLTIPLOS arquivos de uma vez"""
        dialog = QFileDialog(self, "Selecione múltiplos arquivos")
        paths, _ = dialog.getOpenFileNames(
            self,
            "Selecione múltiplos arquivos",
            "",
            "Todos os suportados (*.pdf *.csv *.xlsx);;PDF (*.pdf);;CSV (*.csv);;Excel (*.xlsx)"
        )
        
        if not paths:
            return
        
        # Limpa dados anteriores
        self.clear_all()
        
        # Carrega todos os arquivos
        for path in paths:
            self._load_file_async(path)
    
    
    def add_file(self):
        """Adiciona MAIS UM arquivo ao conjunto atual"""
        path = choose_file(self, "Adicionar arquivo")
        if not path:
            return
        
        self._load_file_async(path)
    
    
    def _load_file_async(self, path: str):
        """Carrega um arquivo em background usando Worker"""
        
        filename = Path(path).name
        self.lbl_info.setText(f"Carregando: {filename}")
        self.statusBar().showMessage(f"Processando {filename}...")
        
        # Cria janela de progresso
        progress = QProgressDialog(f"Carregando {filename}...", "Cancelar", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        self._current_progress = progress #
        
        # Cria Worker
        worker = LoadWorker(path)
        
        # Conecta sinais
        worker.signals.finished.connect(lambda: self._on_load_finished(progress, filename))
        worker.signals.result.connect(lambda df: self._on_load_result(df, path))
        worker.signals.error.connect(lambda msg: self._on_load_error(progress, msg, filename))

        #botão de cancelar
        progress.canceled.connect(worker.stop)
        
        # Inicia processamento
        self.threadpool.start(worker)
    
    
    def _on_load_result(self, df: pd.DataFrame, path: str):
        """Callback quando um arquivo é carregado com sucesso"""
        
        filename = Path(path).name
        
        # Adiciona à lista de arquivos
        self.loaded_files.append(filename)
        self.all_dataframes.append(df)
        # Se é o primeiro arquivo, apenas exibe
        if len(self.all_dataframes) == 1:
            self.current_df = df
            self.table_view.set_dataframe(df)
            self.lbl_info.setText(f"✅ {filename} | {len(df)} linhas, {len(df.columns)} colunas")
            return
        
        # Se há múltiplos arquivos, valida colunas
        self._validate_and_merge_dataframes()
    
    
    def _on_load_finished(self, progress: QProgressDialog, filename: str):
        """Callback quando o Worker finaliza"""
        progress.close()
        progress.deleteLater()
        self.statusBar().showMessage(f"✅ {filename} carregado com sucesso")
    
    
    def _on_load_error(self, progress: QProgressDialog, error_msg: str, filename: str):
        """Callback quando ocorre erro no carregamento"""
        progress.close()
        QMessageBox.critical(
            self,
            "Erro ao Carregar Arquivo",
            f"Falha ao processar '{filename}':\n\n{error_msg}"
        )
        self.statusBar().showMessage("❌ Erro ao carregar arquivo")
    
    
    def _validate_and_merge_dataframes(self):
        """Valida se todos os DataFrames têm as mesmas colunas e faz merge"""
        
        if len(self.all_dataframes) < 2:
            return
        
        # Pega o primeiro DataFrame como referência
        base_df = self.all_dataframes[0]
        base_cols = set(base_df.columns)
        
        # Valida todos os outros
        incompatible_files = []
        
        for i, df in enumerate(self.all_dataframes[1:], start=1):
            is_equal, details = compare_columns(base_df, df)
            
            if not is_equal:
                filename = self.loaded_files[i]
                incompatible_files.append({
                    'file': filename,
                    'only_in_base': details['only_in_df1'],
                    'only_in_file': details['only_in_df2']
                })
        
        # Se há arquivos incompatíveis, exibe erro
        if incompatible_files:
            error_msg = "⚠️ ARQUIVOS COM COLUNAS DIFERENTES:\n\n"
            
            for item in incompatible_files:
                error_msg += f"📄 {item['file']}:\n"
                if item['only_in_base']:
                    error_msg += f"  Faltam: {', '.join(item['only_in_base'])}\n"
                if item['only_in_file']:
                    error_msg += f"  Extras: {', '.join(item['only_in_file'])}\n"
                error_msg += "\n"
            
            error_msg += "⚠️ Não é possível mesclar arquivos com estruturas diferentes."
            
            QMessageBox.warning(self, "Validação de Colunas", error_msg)
            
            # Remove os arquivos incompatíveis
            for item in incompatible_files:
                idx = self.loaded_files.index(item['file'])
                self.loaded_files.pop(idx)
                self.all_dataframes.pop(idx)
            
            return
        
        # Se todos são compatíveis, faz o merge
        self._merge_all_dataframes()
    
    
    def _merge_all_dataframes(self):
        """Faz merge de todos os DataFrames validados"""
        
        if not self.all_dataframes:
            return
        
        # Concatena todos os DataFrames
        merged_df = pd.concat(self.all_dataframes, ignore_index=True)
        
        # Atualiza a interface
        self.current_df = merged_df
        self.table_view.set_dataframe(merged_df)
        
        total_files = len(self.loaded_files)
        total_rows = len(merged_df)
        total_cols = len(merged_df.columns)
        
        files_list = ", ".join(self.loaded_files)
        
        self.lbl_info.setText(
            f"✅ {total_files} arquivos mesclados | {total_rows} linhas, {total_cols} colunas"
        )
        
        QMessageBox.information(
            self,
            "Merge Concluído",
            f"✅ {total_files} arquivos foram mesclados com sucesso!\n\n"
            f"Arquivos: {files_list}\n"
            f"Total de linhas: {total_rows}\n"
            f"Total de colunas: {total_cols}"
        )
    
    
    # ============================================================
    # SELEÇÃO DE COLUNAS
    # ============================================================
    
    def show_column_selection(self):
        """Permite ao usuário selecionar colunas para exibir"""
        
        if self.current_df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum arquivo carregado.")
            return
        
        # Cria diálogo
        dialog = QDialog(self)
        dialog.setWindowTitle("Selecionar Colunas")
        dialog.resize(400, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Lista de colunas
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        
        for col in self.current_df.columns:
            list_widget.addItem(col)
        
        # Seleciona todas por padrão
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(True)
        
        layout.addWidget(QLabel("Selecione as colunas que deseja manter:"))
        layout.addWidget(list_widget)
        
        # Botões
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Executa diálogo
        if dialog.exec() == QDialog.Accepted:
            selected_items = list_widget.selectedItems()
            selected_cols = [item.text() for item in selected_items]
            
            if not selected_cols:
                QMessageBox.warning(self, "Aviso", "Nenhuma coluna selecionada.")
                return
            
            # Filtra DataFrame
            df_filtered = select_columns(self.current_df, selected_cols)
            self.current_df = df_filtered
            self.table_view.set_dataframe(df_filtered)
            
            self.lbl_info.setText(
                f"✅ {len(selected_cols)} colunas selecionadas | {len(df_filtered)} linhas"
            )
            self.statusBar().showMessage("Colunas filtradas com sucesso")
    
    
    # ============================================================
    # EXPORTAÇÃO
    # ============================================================
    
    def export_csv(self):
        """Exporta o DataFrame atual para CSV"""
        
        if self.current_df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum dado para exportar.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar CSV",
            "dados_exportados.csv",
            "CSV (*.csv)"
        )
        
        if not path:
            return
        
        try:
            self.current_df.to_csv(path, index=False, encoding='utf-8-sig')
            QMessageBox.information(
                self,
                "Sucesso",
                f"✅ Dados exportados com sucesso!\n\n{path}"
            )
            self.statusBar().showMessage(f"✅ CSV exportado: {Path(path).name}")
        
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar", f"Falha ao salvar CSV:\n{str(e)}")
    
    
    def export_pdf(self):
        """Exporta o DataFrame atual para PDF"""
        
        if self.current_df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum dado para exportar.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar PDF",
            "relatorio.pdf",
            "PDF (*.pdf)"
        )
        
        if not path:
            return
        
        try:
            from exporters.export_pdf import export_to_pdf
            export_to_pdf(self.current_df, path)
            
            QMessageBox.information(
                self,
                "Sucesso",
                f"✅ PDF gerado com sucesso!\n\n{path}"
            )
            self.statusBar().showMessage(f"✅ PDF exportado: {Path(path).name}")
        
        except ImportError:
            QMessageBox.warning(
                self,
                "Módulo Faltando",
                "O módulo de exportação PDF ainda não foi implementado.\n"
                "Crie o arquivo: src/exporters/pdf_exporter.py"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar", f"Falha ao gerar PDF:\n{str(e)}")
    
    
    def export_word(self):
        """Exporta o DataFrame atual para Word (DOCX)"""
        
        if self.current_df is None:
            QMessageBox.warning(self, "Aviso", "Nenhum dado para exportar.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Word",
            "relatorio.docx",
            "Word (*.docx)"
        )
        
        if not path:
            return
        
        try:
            from exporters.export_docx import export_to_word
            export_to_word(self.current_df, path)
            
            QMessageBox.information(
                self,
                "Sucesso",
                f"✅ Documento Word gerado com sucesso!\n\n{path}"
            )
            self.statusBar().showMessage(f"✅ Word exportado: {Path(path).name}")
        
        except ImportError:
            QMessageBox.warning(
                self,
                "Módulo Faltando",
                "O módulo de exportação Word ainda não foi implementado.\n"
                "Crie o arquivo: src/exporters/word_exporter.py"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar", f"Falha ao gerar Word:\n{str(e)}")
    
    
    # ============================================================
    # UTILITÁRIOS
    # ============================================================
    
    def clear_all(self):
        """Limpa todos os dados carregados"""
        self.current_df = None
        self.loaded_files.clear()
        self.all_dataframes.clear()
        self.table_view.set_dataframe(pd.DataFrame())
        self.lbl_info.setText("Nenhum arquivo carregado")
        self.statusBar().showMessage("Dados limpos")