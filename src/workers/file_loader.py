from PySide6.QtCore import QObject, Signal, QRunnable
import traceback
from src.file_handler import load_file
from src.data_processing import fix_columns, normalize_dataframe

class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(str)
    result = Signal(object)


class LoadWorker(QRunnable):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.signals = WorkerSignals()
        self._canceled = False

    
    def stop(self):
        self._canceled = True

    def run(self):
        print(f"[Worker] Iniciando leitura: {self.path}")
        try:
            if self._canceled:
                print("[Worker] Cancelado antes de iniciar.")
                self.signals.finished.emit()
                return
            

            df = load_file(self.path)
            print("[Worker] load_file OK:", type(df))
            if self._canceled:
                print("[Worker] Cancelado antes de iniciar.")
                self.signals.finished.emit()
                return

            df = fix_columns(df)
            print("[Worker] fix_columns OK:", df.shape)

            df = normalize_dataframe(df)
            print("[Worker] normalize_dataframe OK:", df.shape)

            self.signals.result.emit(df)

        except Exception:
            print("[Worker] ERRO:")
            print(traceback.format_exc())
            self.signals.error.emit(traceback.format_exc())
            return

        self.signals.finished.emit()
        print("[Worker] Finalizado com sucesso.")