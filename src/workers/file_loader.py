from PySide6.QtCore import QObject, Signal, QRunnable
import traceback
from src.file_handler import load_file
from src.data_processing import fix_columns, normalize_dataframe

class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(str)
    result = Signal(object)

class LoadeWorker(QRunnable):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.signals = WorkerSignals()

    def run(self):
        try:
            df = load_file(self.path)
            df = fix_columns(df)
            df = normalize_dataframe(df)

            # ENVIA O DATAFRAME
            self.signals.result.emit(df)

        except Exception:
            self.signals.error.emit(traceback.format_exc())
            return

        # SINAL FINAL
        self.signals.finished.emit()
