from PyQt5.QtGui import QStandardItem

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, QAbstractListModel, QVariant

# import sys
# sys._excepthook = sys.excepthook
# def my_exception_hook(exctype, value, traceback):
#     # Print the error and traceback
#     print(exctype, value, traceback)
#     # Call the normal Exception hook after
#     sys._excepthook(exctype, value, traceback)
#     sys.exit(1)
#
# # Set the exception hook to our wrapping function
# sys.excepthook = my_exception_hook


class TreeItem(object):
    MyDataRole = Qt.UserRole + 1

    def __init__(self, data, user_data=None, parent=None):
        self.parentItem = parent
        self.userData = user_data
        self.itemData = data
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
        # return 1

    def data(self, column, role):
        try:
            if role == Qt.DisplayRole:
                return self.itemData[0]

            if role == self.MyDataRole:
                return self.userData

            return None

        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0
        

class TreeModel(QAbstractItemModel):
    def __init__(self, data, parent=None):
        super(TreeModel, self).__init__(parent)

        self.rootItem = TreeItem(data=("Directories",))
        self.setupModelData(data, self.rootItem)

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if not role in (Qt.DisplayRole, Qt.UserRole):
            return None

        item = index.internalPointer()

        return item.data(index.column(), role)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section, role)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self, dir_tree, parent):
        id_list = []
        items_list = {0: parent}  # as dir
        for row in dir_tree:
            items_list[row[0]] = TreeItem(data=(row[1],), user_data=(row[0], row[2]))
            id_list.append((row[0], row[2]))  # id and parent_id

        for id_ in reversed(id_list):
            if id_[1] in items_list:
                items_list[id_[1]].appendChild(items_list[id_[0]])


class MyListModel(QAbstractListModel):
    MyDataRole = Qt.UserRole + 1

    def __init__(self, parent=None, *args):
        """ datain: a list where each item is a row
        """
        QAbstractListModel.__init__(self, parent, *args)
        self.__data = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.__data)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return self.__data[index.row()][0]
            elif role == self.MyDataRole:
                return self.__data[index.row()][1]
        return None

    def append_row(self, row):
        self.__data.append(row)

    def appendData(self, value, role=Qt.EditRole):
        in_row = self.rowCount()
        self.__data.append(value)
        index = self.createIndex(in_row, 0, 0)
        self.dataChanged.emit(index, index)
        return True

    def removeRows(self, row, count=1, parent=QModelIndex()):
        print('|--> removeRows', row)
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        del self.__data[row:row + count]
        self.endRemoveRows()
        return True
