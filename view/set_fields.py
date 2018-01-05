# view.set_fields.py

from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import Qt, QModelIndex

from controller.table_model import TableModel
from view.ui_set_fields import Ui_SelectorFields
from controller.my_controller import Fields

FileFields = ['FileName', 'FileDate', 'Pages', 'Size', 'IssueDate',
              'Opened', 'Commented']
Heads = ['File', 'Date', 'Pages', 'Size', 'Issued', 'Opened', 'Commented']


class SetFields(QDialog):
    def __init__(self, current: Fields, parent=None):
        super().__init__(parent)
        self.ui = Ui_SelectorFields()
        self.ui.setupUi(self)

        self.aval_fields = [it for it in Heads if it not in current.headers]
        self.used_fields = current.headers

        self.left_m = TableModel()
        self.right_m = TableModel()
        self._setup_models(current)

        self.ui.btn_add.clicked.connect(self._add)
        self.ui.btn_remove.clicked.connect(self._remove)

    def _add(self):
        idx = self.ui.fieldsAval.currentIndex()
        item = self.left_m.get_row(idx.row())

        if item:
            self.right_m.insert_row(self.ui.fieldsUsed.currentIndex(), item[0], item[1])
            self.left_m.removeRows(idx.row())

    def _remove(self):
        idx = self.ui.fieldsUsed.currentIndex()
        item = self.right_m.get_row(idx.row())

        if item:
            if item[0][0] == 'File':
                QMessageBox.critical(self, 'File field', 'File field must be used!')
            else:
                self.left_m.insert_row(self.ui.fieldsAval.currentIndex(), item[0], item[1])
                self.right_m.removeRows(idx.row())

    def _setup_models(self, current):
        for it in self.aval_fields:
            id = Heads.index(it)
            self.left_m.append_row(it, (FileFields[id], id))

        self.left_m.setHeaderData(0, Qt.Horizontal, ("Available",))
        self.ui.fieldsAval.setModel(self.left_m)

        for it in self.used_fields:
            id = Heads.index(it)
            self.right_m.append_row(it, (FileFields[id], id))

        self.right_m.setHeaderData(0, Qt.Horizontal, ("Used",))
        self.ui.fieldsUsed.setModel(self.right_m)

    def get_result(self):
        co1 = self.right_m.rowCount(QModelIndex())
        heads = []
        fields = []
        idx = []
        for i in range(co1):
            it = self.right_m.get_row(i)
            heads.append(it[0][0])
            fields.append(it[1][0])
            idx.append(it[1][1])
        return Fields._make((fields, heads, idx))


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    sys._excepthook = sys.excepthook


    def my_exception_hook (exctype, value, traceback):
        # Print the error and traceback
        print(exctype, value, traceback)
        # Call the normal Exception hook after
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)


    sys.excepthook = my_exception_hook

    app = QApplication(sys.argv)

    curr = Fields._make((FileFields[:4], Heads[:4], range(4)))

    fields_set = SetFields(curr)
    if fields_set.exec_():
        print(fields_set.get_result())
        sys.exit(0)

    sys.exit(app.exec_())

