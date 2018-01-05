# controller/table_model.py

from collections import Iterable
from PyQt5.QtCore import QModelIndex, Qt, QAbstractTableModel, QSortFilterProxyModel


class ProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)

    def append_row(self, row, user_data=None):
        self.sourceModel().append_row(row, user_data)

    def update(self, index, data, role=Qt.DisplayRole):
        self.sourceModel().update(self.mapToSource(index), data, role)

    def delete_row(self, index):
        self.sourceModel().delete_row(self.mapToSource(index))

    def lessThan(self, left, right):
        s_model = self.sourceModel()
        leftData = s_model.data(left)
        rightData = s_model.data(right)

        if s_model.headerData(left.column(), Qt.Horizontal) in ('Pages', 'Size'):
            leftData = int(leftData) or 0
            rightData = int(rightData) or 0

        return leftData < rightData

    def setHeaderData(self, value):
        self.sourceModel().setHeaderData(0, Qt.Horizontal, value)

class TableModel(QAbstractTableModel):
    def __init__(self, parent=None, *args):
        super(TableModel, self).__init__(parent)
        self.__header = ()
        self.__data = []
        self.__user_data = []
        self.column_count = 0

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.__data)

    def setColumnCount(self, count):
        self.column_count = count

    def columnCount(self, parent=None):
        return self.column_count

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                if len(self.__data[index.row()]) > index.column():
                    return self.__data[index.row()][index.column()]
                return None
            elif role == Qt.UserRole:
                return self.__user_data[index.row()]
            elif role == Qt.TextAlignmentRole:
                if index.column() == 0:
                    return Qt.AlignLeft
                return Qt.AlignRight

    def update(self, index, data, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                if len(self.__data[index.row()]) > index.column():
                    i = index.column()
                    if i + 1 < len(self.__data[index.row()]):
                        self.__data[index.row()] = self.__data[index.row()][:i] + \
                                                   (data,) + self.__data[index.row()][(i+1):]
                    else:
                        self.__data[index.row()] = self.__data[index.row()][:i] + (data,)
            elif role == Qt.UserRole:
                self.__user_data[index.row()] = data

    def delete_row(self, index):
        if index.isValid():
            self.beginRemoveRows(QModelIndex(), index.row(), index.row())
            row = index.row()
            self.__data.remove(self.__data[row])
            self.__user_data.remove(self.__user_data[row])
            self.endRemoveRows()

    def append_row(self, row, user_data=None):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        if isinstance(row, str) or not isinstance(row, Iterable):
            row = (str(row),)
        else:
            rr = []
            for r in row:
                rr.append(str(r))
            row = tuple(rr)

        self.__data.append(row)
        self.__user_data.append(user_data)
        self.endInsertRows()

    def insert_row(self, index, row_data, user_data=None):
        if index.isValid():
            row = index.row()
            self.beginInsertRows(QModelIndex(), row, row)
            self.__data.insert(row, row_data)
            self.__user_data.insert(row, user_data)
        else:
            self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
            self.__data.append(row_data)
            self.__user_data.append(user_data)
        self.endInsertRows()

    def appendData(self, value, role=Qt.EditRole):
        in_row = self.rowCount(QModelIndex())
        self.__data.append(value)
        index = self.createIndex(in_row, 0, 0)
        self.dataChanged.emit(index, index)
        return True

    def removeRows(self, row, count=1, parent=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        del self.__data[row:row + count]
        del self.__user_data[row:row + count]
        self.endRemoveRows()
        return True

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if not self.__header:
            return None
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.__header[section]

    def setHeaderData(self, p_int, orientation, value, role=None):
        if isinstance(value, str):
            value = value.split(' ')
        self.__header = value
        self.column_count = len(value)

    def setData(self, index, value, role):
        if index.isValid():
            if role == Qt.DisplayRole:
                self.__data[index.row()][index.column()] = value
                return
            if role == Qt.UserRole:
                self.__user_data[index.row()][index.column()] = value

    def get_row(self, row):
        if row >= 0 & row < self.rowCount():
            return (self.__data[row], self.__user_data[row])
        return ()


class TableModel2(TableModel):
    def __init__(self, parent=None, *args):
        super().__init__(parent, *args)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight
        return super().data(index, role)
