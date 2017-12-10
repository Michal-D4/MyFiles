# controller/my_qt_model.py

from collections import Iterable
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, QAbstractTableModel


class TreeItem(object):
    def __init__(self, data_, user_data=None, parent=None):
        self.parentItem = parent
        self.userData = user_data
        self.itemData = data_
        self.childItems = []

    def appendChild(self, item):
        item.parentItem = self
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column, role):
        try:
            if role == Qt.DisplayRole:
                return self.itemData[column]

            if role == Qt.UserRole:
                return self.userData

        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

    def set_data(self, data_):
        self.itemData = data_


class TreeModel(QAbstractItemModel):
    def __init__(self, data_, parent=None):
        super(TreeModel, self).__init__(parent)

        self.rootItem = TreeItem(data_=("",))
        self._setup_model_data(data_)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if index.isValid() & role in (Qt.DisplayRole, Qt.UserRole):
            item = index.internalPointer()
            if item:
                return item.data(index.column(), role)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section, role)

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)

        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.rootItem:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:         # ??? why
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setHeaderData(self, p_int, orientation, value, role=None):
        if isinstance(value, str):
            value = value.split(' ')
        self.rootItem.set_data(value)

    def _setup_model_data(self, rows):
        """
        Fill tree structure
        :param rows: iterable, each item contains 3 elements
             item[0]  - data to be shown == Qt.DisplayRole,
             item[1:] - user_data:
                  item[1]  - Id of item, unique,
                  item[2]  - Id of parent item, 0 for root,
                        ...
             and sorted by item(2) - parent ID - in descendant order
        :return: None
        """
        id_list = []
        items_list = {0: self.rootItem}
        for row in rows:
            if not isinstance(row[0], tuple):
                row = ((row[0],),) + tuple(row[1:])
            items_list[row[1]] = TreeItem(data_=row[0], user_data=(row[1:]))
            id_list.append((row[1:3]))

        for id_ in id_list:
            if id_[1] in items_list:
                items_list[id_[1]].appendChild(items_list[id_[0]])


class TableModel(QAbstractTableModel):
    def __init__(self, parent=None, *args):
        super(TableModel, self).__init__(parent)
        self.__header = ()
        self.__data = []
        self.__user_data = []
        self.column_count = 0

    def rowCount(self, parent):
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

    def append_row(self, row, user_data=None):
        if isinstance(row, str) or not isinstance(row, Iterable):
            row = (str(row),)
        else:
            rr = []
            for r in row:
                rr.append(str(r))
            row = tuple(rr)

        self.__data.append(row)
        self.__user_data.append(user_data)

    def appendData(self, value, role=Qt.EditRole):
        in_row = self.rowCount(QModelIndex())
        self.__data.append(value)
        index = self.createIndex(in_row, 0, 0)
        self.dataChanged.emit(index, index)
        return True

    def removeRows(self, row, count=1, parent=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        del self.__data[row:row + count]
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


class TableModel2(TableModel):
    def __init__(self, parent=None, *args):
        super().__init__(parent, *args)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight
        return super().data(index, role)

    def append_row(self, row):
        data_ = []
        user_data = []
        for r in row:
            data_.append(r)
            # user_data.append(r[1])
        super().append_row(tuple(data_), user_data)
