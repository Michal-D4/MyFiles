# view/item_edit.py

import re
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from view.ui_items_edit import Ui_ItemChoice
from controller.my_qt_model import TableModel


class ItemEdit(QDialog):
    def __init__(self, titles, nodes, parent=None):
        super(ItemEdit, self).__init__(parent)
        self.view = Ui_ItemChoice()
        self.view.setupUi(self)

        self.view.label_1.setText(titles[0])
        self.view.label_2.setText(titles[1])
        self.setWindowTitle(titles[2])

        self.list_items = []
        for node in nodes:
            self.list_items.append(node)

        model = TableModel2(parent=self.view.items)
        self.view.items.setModel(model)

        if self.list_items:
            aa = max(nodes, key=lambda t: len(t[0]))[0]
            self.max_width = self.view.items.fontMetrics().boundingRect(aa).width() + 20
        else:
            self.max_width = 20

        self.view.items.resizeEvent = self.resize_event

    def get_rezult(self):
        return self.view.in_field.toPlainText()

    def setup_view(self):
        w = self.view.items.size().width()
        col_no = w // self.max_width
        self._setup_model(col_no)

    def resize_event(self, event):
        w = event.size().width()
        col_no = w // self.max_width
        if col_no != self.view.items.model().columnCount():
            self._setup_model(col_no)

    def selection_changed(self, selected, deselected):
        """
        Changed selection in self.view.items
        :param selected:   QList<QModelIndex>
        :param deselected: QList<QModelIndex>
        :return: None
        """
        txt = self.view.in_field.toPlainText()
        idx = selected.indexes()
        if idx:
            for jj in idx:
                tt = self.view.items.model().data(jj)
                txt = ', '.join((txt, tt)) if txt else tt

        id2 = deselected.indexes()
        if id2:
            for jj in id2:
                txt = re.sub(' '.join((',', self.view.items.model().data(jj))), '', txt)

        self.view.in_field.setText(txt)

    def _setup_model(self, col_no):
        row_no = len(self.list_items) // col_no + 1
        aa = []
        for i in range(row_no):
            aa.append(tuple(self.list_items[i*col_no: (i + 1)*col_no]))

        model = TableModel2(parent=self.view.items)
        model.setColumnCount(col_no)

        for a in aa:
            model.append_row(a)

        self.view.items.setModel(model)

        for i in range(0, col_no):
            self.view.items.horizontalHeader().resizeSection(i, self.max_width)

        self.view.items.selectionModel().selectionChanged.connect(self.selection_changed)


class TableModel2(TableModel):
    def __init__(self, parent=None, *args):
        super().__init__(parent, *args)

    def data(self, index, role=Qt.DisplayRole):
        return super().data(index, role)
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight

    def append_row(self, row):
        data_ = []
        user_data = []
        for r in row:
            data_.append(r[0])
            user_data.append(r[1])
        super().append_row(tuple(data_), user_data)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    sys._excepthook = sys.excepthook


    def my_exception_hook ( exctype, value, traceback ):
        # Print the error and traceback
        print(exctype, value, traceback)
        # Call the normal Exception hook after
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)


    sys.excepthook = my_exception_hook

    app = QApplication(sys.argv)
    labels = ['label1', 'label2', 'Window title']
    items = [('item {}'.format(i+1), i) for i in range(25)]

    ItemChoice = ItemEdit(labels, items)
    ItemChoice.resize(500, 300)

    # ItemChoice.setup_view()

    ItemChoice.show()
    sys.exit(app.exec_())

