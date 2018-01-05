# view.set_fields.py

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, QModelIndex

from controller.table_model import TableModel
from view.ui_set_fields import Ui_SelectorFields

FileFields = ['FileName', 'FileDate', 'Pages', 'Size', 'IssueDate',
              'Opened', 'Commented']
Heads = ['File', 'Date', 'Pages', 'Size', 'Issued', 'Opened', 'Commented']
Noms = list(range(6))


class SetFields(QDialog):
    def __init__(self, left, right, parent=None):     # , flags, Qt_WindowFlags=None, Qt_WindowType=None, *args, **kwargs):
        super().__init__(parent)
        self.ui = Ui_SelectorFields()
        self.ui.setupUi(self)

        self.aval_fields = left
        self.used_fields = right

        self.left_m = TableModel()
        self.right_m = TableModel()
        self._setup_models()

        self.ui.btn_add.clicked.connect(self._add)
        self.ui.btn_remove.clicked.connect(self._remove)

    def _add(self):
        idx = self.ui.fieldsAval.currentIndex()
        item = self.left_m.get_row(idx)

        if item:
            self.right_m.append_row(item[0], item[1])
            self.left_m.removeRows(idx.row())

    def _remove(self):
        idx = self.ui.fieldsUsed.currentIndex()
        item = self.right_m.get_row(idx)

        if item:
            self.left_m.append_row(item[0], item[1])
            self.right_m.removeRows(idx.row())

    def _setup_models(self):
        for it in self.aval_fields:
            self.left_m.append_row(it)

        self.left_m.setHeaderData(0, Qt.Horizontal, ("Available",))
        self.ui.fieldsAval.setModel(self.left_m)

        for it in self.used_fields:
            self.right_m.append_row(it)

        self.right_m.setHeaderData(0, Qt.Horizontal, ("Used",))
        self.ui.fieldsUsed.setModel(self.right_m)

    def get_result(self):
        co1 = self.ui.fieldsUsed.model().rowCount(QModelIndex())
        print('--> Result', co1)


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

    left = FileFields[4:]
    right = FileFields[:4]

    fields_set = SetFields(left, right)
    if fields_set.exec_():
        fields_set.get_result()

    sys.exit(app.exec_())

