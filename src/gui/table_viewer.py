from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtWidgets import QTableView
import pandas as pd
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView
)



class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame = None, parent=None):
        super().__init__(parent)
        self._df = pd.DataFrame() if df is None else df.reset_index(drop=True)


    def load_dataframe(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df.reset_index(drop=True)
        self.endResetModel()


    def rowCount(self, parent=QModelIndex()):
        return len(self._df.index)


    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        if role == Qt.DisplayRole:
            value = self._df.iat[index.row(), index.column()]
            # display NaN as empty

            if pd.isna(value):
                return ""
            return str(value)
        return None


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            try:
                return str(self._df.columns[section])
            except Exception:
                return None
        else:
            return str(section + 1)




class DataFrameView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = PandasModel()
        self.setModel(self._model)
        
        # enable column resizing stretch
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)   # ← CORREÇÃO
    
    
    def set_dataframe(self, df: pd.DataFrame):
        self._model.load_dataframe(df)

