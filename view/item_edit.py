# view/item_edit.py

import re
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QEvent, QPersistentModelIndex, QItemSelectionModel
from view.ui_items_edit import Ui_ItemChoice
from controller.my_qt_model import TableModel2


class ItemEdit(QDialog):
    def __init__(self, titles, items, selected_items, parent=None):
        super(ItemEdit, self).__init__(parent)
        self.view = Ui_ItemChoice()
        self.view.setupUi(self)

        self.view.label_1.setText(titles[0])
        self.view.label_2.setText(titles[1])
        self.setWindowTitle(titles[2])

        self.list_items = items
        self.sel_items = selected_items
        self.sel_indexes = []

        model = TableModel2(parent=self.view.items)
        self.view.items.setModel(model)

        if self.list_items:
            aa = max(items, key=lambda t: len(t[0]))[0]
            self.max_width = self.view.items.fontMetrics().boundingRect(aa).width() + 20
        else:
            self.max_width = 20

        self.view.items.resizeEvent = self.resize_event
        self.view.items.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            for model_index in self.sel_indexes:
                self.view.items.selectionMode().select(model_index, QItemSelectionModel.Select)
            return -1
        if event.type() == QEvent.FocusOut:
            for model_index in self.view.items.selectionModel().selectedRows():
                self.sel_indexes.append(QPersistentModelIndex(model_index))
            return -1
        return super(ItemEdit, self).eventFilter(obj, event)

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
        id2 = deselected.indexes()
        if id2:
            for jj in id2:
                # txt = re.sub(' '.join((',', self.view.items.model().data(jj))), '', txt)
                txt = re.sub(self.view.items.model().data(jj), '', txt)
            if set(txt).issubset(' ,'):
                txt = ''

        idx = selected.indexes()
        if idx:
            for jj in idx:
                tt = self.view.items.model().data(jj)
                if tt:
                    txt = ', '.join((txt, tt)) if txt else tt

        txt = re.sub(',,', ',', txt)

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
    sel_items = [items[2], items[7]]

    ItemChoice = ItemEdit(labels, items, sel_items)
    ItemChoice.resize(500, 300)

    # ItemChoice.setup_view()

    ItemChoice.show()
    sys.exit(app.exec_())

