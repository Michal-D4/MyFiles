# controller/editable_model.py

import copy

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex


class TreeItem(object):
    def __init__(self, data, user_data=None, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.userData = user_data
        self.childItems = []

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childNumber(self):
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0

    def columnCount(self):
        return len(self.itemData)

    def data(self, column, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.itemData[column]
        if role == Qt.UserRole:
            return self.userData
        return None

    def appendChild(self, item):
        item.parentItem = self
        self.childItems.append(item)

    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            data = [None for v in range(columns)]
            item = TreeItem(data, self)
            self.childItems.insert(position, item)

        return True

    def parent(self):
        return self.parentItem

    def removeChildren(self, position, count):
        if position < 0 or position + count > len(self.childItems):
            return False

        for row in range(count):
            self.childItems.pop(position)

        return True

    def setData(self, column, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            if column < 0 or column >= len(self.itemData):
                return False

            self.itemData[column] = value

            return True

        if role == Qt.UserRole:
            self.userData = value
            return False

    def set_data(self, data_):
        self.itemData = data_


class EditableTreeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(EditableTreeModel, self).__init__(parent)

        self.rootItem = TreeItem(())

    def columnCount(self, parent=QModelIndex()):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role in (Qt.DisplayRole, Qt.UserRole, Qt.EditRole):
            item = self.getItem(index)
            return item.data(index.column(), role)
        return None

    def flags(self, index):
        if not index.isValid():
            return 0

        return Qt.ItemIsEditable | super(EditableTreeModel, self).flags(index)

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()

        parentItem = self.getItem(parent)
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def insertRows(self, position, count, parent=QModelIndex()):
        parentItem = self.getItem(parent)
        self.beginInsertRows(parent, position, position + count - 1)
        success = parentItem.insertChildren(position, count,
                                            self.rootItem.columnCount())
        self.endInsertRows()

        return success

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = self.getItem(index)
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.childNumber(), 0, parentItem)

    def removeRows(self, row, count, parent=QModelIndex()):
        """
         removes count rows starting with the given row under parent parent
        :param row:
        :param count:
        :param parent:
        :return:
        """
        parentItem = self.getItem(parent)

        self.beginRemoveRows(parent, row, row + count - 1)
        success = parentItem.removeChildren(row, count)
        self.endRemoveRows()

        return success

    def rowCount(self, parent=QModelIndex()):
        parentItem = self.getItem(parent)

        return parentItem.childCount()

    def setData(self, index, value, role=Qt.EditRole):
        if not role in (Qt.EditRole, Qt.UserRole):
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value, role)

        if result:
            self.dataChanged.emit(index, index)

        return result

    def setHeaderData(self, p_int, orientation, value, role=None):
        if isinstance(value, str):
            value = value.split(' ')
        self.rootItem.set_data(value)

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
            items_dict[row[1]] = TreeItem(data=row[0], user_data=(row[1:]))
            id_list.append((row[1:]))

        for id_ in id_list:
            if id_[1] in items_dict:
                # use copy because the same item may used in different branches
                items_dict[id_[1]].appendChild(copy.deepcopy(items_dict[id_[0]]))
