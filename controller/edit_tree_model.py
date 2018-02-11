# controller/edit_tree_model.py

import copy

# from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtCore import (QAbstractItemModel, QModelIndex, Qt, QMimeData, QByteArray,
                          QDataStream, QIODevice)
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QPixmap
from model.helpers import MimeTypes, AppFont


class TreeItem(object):
    def __init__(self, data_, user_data=None, parent=None):
        self.parentItem = parent
        self.userData = user_data
        self.itemData = data_
        self.childItems = []

    def removeChildren(self, position, count):
        if position < 0 or position + count > len(self.childItems):
            return False

        for row in range(count):
            self.childItems.pop(position)

        return True

    def is_virtual(self):
        return self.userData[-2] > 0

    def is_favorites(self):
        return (self.userData[-2] > 0) & (self.userData[-1] == 'Favorites')

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column, role):
        if role == Qt.DisplayRole:
            return self.itemData[column]

        if role == Qt.UserRole:
            return self.userData

        if role == Qt.BackgroundRole:
            if self.is_virtual():
                return QApplication.palette().alternateBase()
            return QApplication.palette().base()

        if role == Qt.FontRole:
            if self.is_virtual():
                return EditTreeModel.alt_font
        return None

    def appendChild(self, item):
        item.parentItem = self
        self.childItems.append(item)

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

    def set_data(self, data_):
        self.itemData = data_


class EditTreeModel(QAbstractItemModel):

    alt_font = QFont("Times", 10)

    @staticmethod
    def set_alt_font(font: QFont):
        EditTreeModel.alt_font = QFont(font)
        EditTreeModel.alt_font.setItalic(True)

    def __init__(self, parent=None):
        super(EditTreeModel, self).__init__(parent)

        self.rootItem = TreeItem(data_=("", (0,0,0,"Root")))

    @staticmethod
    def is_virtual(index):
        if index.isValid():
            return index.internalPointer().is_virtual()
        return False

    @staticmethod
    def is_favorites(index):
        if index.isValid():
            return index.internalPointer().is_favorites()
        return False

    def columnCount(self, parent):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item.data(index.column(), role)
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        # return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | \
               Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section, role)
        return None

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

    def removeRows(self, row, count, parent=QModelIndex()):
        """
         removes count rows starting with the given row under parent parent
        :param row:
        :param count:
        :param parent:
        :return:
        """
        parentItem = self.getItem(parent)
        print('--> removeRows', parentItem.userData, row, count)

        self.beginRemoveRows(parent, row, row + count - 1)
        success = parentItem.removeChildren(row, count)
        self.endRemoveRows()

        return success

    def remove_row(self, index):
        print('--> remove_row', index.row())
        return self.removeRows(index.row(), 1, self.parent(index))

    def rowCount(self, parent=QModelIndex()):
        parentItem = self.getItem(parent)

        return parentItem.childCount()

    def setHeaderData(self, p_int, orientation, value, role=None):
        if isinstance(value, str):
            value = value.split(' ')
        self.rootItem.set_data(value)

    def append_child(self, item, parent):
        parentItem = self.getItem(parent)
        position = parentItem.childCount()
        self.beginInsertRows(parent, position, position)
        parentItem.appendChild(item)

        # self.dataChanged.emit(index, index)   # Is it necessary? then calculate also index for appended row
        self.endInsertRows()
        return True

    def set_model_data(self, rows):
        """
        Fill tree structure
        :param rows: iterable, each item contains at least 3 elements
             item[0]  - string/"tuple of strings" to be shown == Qt.DisplayRole,
             item[1:] - user_data:
                  item[1]  - Id of item, unique,
                  item[2]  - Id of parent item, 0 for root,
                        ...
             and sorted by item(2) - parent ID - in descendant order
        :return: None
        """
        id_list = []
        items_dict = {0: self.rootItem}
        for row in rows:
            if not isinstance(row[0], tuple):
                row = ((row[0],),) + tuple(row[1:])
            items_dict[row[1]] = TreeItem(data_=row[0], user_data=(row[1:]))
            id_list.append((row[1:]))

        for id_ in id_list:
            if id_[1] in items_dict:
                # use copy because the same item may used in different branches
                items_dict[id_[1]].appendChild(copy.deepcopy(items_dict[id_[0]]))

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def mimeTypes(self):
        return MimeTypes

    def mimeData(self, indexes):
        print('--> EditTreeModel.mimeData', len(indexes))
        item_data = QByteArray()
        data_stream = QDataStream(item_data, QIODevice.WriteOnly)
        data_stream.writeInt(len(indexes))

        for idx in indexes:
            pack = EditTreeModel.save_index(idx)
            data_stream.writeQString(','.join((str(x) for x in pack)))

        mime_data = QMimeData()

        mime_data.setData(MimeTypes[0], item_data)

        return mime_data

    def dropMimeData(self, data, action, row, column, parent):
        print('--> dropMimeData', row, column, parent.isValid())
        if parent.isValid():
            print(parent.internalPointer().data(0, Qt.DisplayRole))

        if action == Qt.IgnoreAction:
            return True

        if data.hasFormat(MimeTypes[0]):
            print('  Folder(s) dragged')
            drop_data = data.data(MimeTypes[0])
            print('  type of data', type(drop_data))
            stream = QDataStream(drop_data, QIODevice.ReadOnly)
            idx_count = stream.readInt()
            for i in range(idx_count):
                tmp_str = stream.readQString()
                id_list = (int(i) for i in tmp_str.split(','))
                index = self.restore_index(id_list)
                item = index.internalPointer()
                print(item.data(0, Qt.DisplayRole))
            return True

        if data.hasFormat(MimeTypes[1]):
            print('  File(s) dragged')
            # need fileIDs only in data ???
            return True

        return False

    def restore_index(self, path):
        parent = QModelIndex()
        for id_ in path:
            idx = self.index(int(id_), 0, parent)
            parent = idx
        return parent

    @staticmethod
    def save_index(index):
        idx = index
        path = []
        while idx.isValid():
            path.append(idx.row())
            idx = idx.parent()
        path.reverse()
        return path
