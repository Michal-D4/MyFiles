# view/item_edit.py

import re
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QItemSelectionModel
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
        self.sel_indexes = [self.list_items.index(item) for item in selected_items]

        model = TableModel2(parent=self.view.items)
        self.view.items.setModel(model)

        if self.list_items:
            len_ = max([len(item) for item in items])
            len_ = len_ if len_ > 1 else 2
            self.max_width = self.view.items.fontMetrics().boundingRect('W'*len_).width()
        else:
            self.max_width = 20

        self.view.items.resizeEvent = self.resize_event

    def get_result( self ):
        return self.view.in_field.toPlainText()

    def resize_event(self, event):
        w = event.size().width()
        col_no = w // self.max_width
        if col_no != self.view.items.model().columnCount():
            self._setup_model(col_no)

    def selection_changed(self, selected, deselected):
        """
        Changed selection in self.view.table_items
        :param selected:   QList<QModelIndex>
        :param deselected: QList<QModelIndex>
        :return: None
        """
        txt = self.view.in_field.toPlainText()
        id2 = deselected.indexes()
        if id2:
            for jj in id2:
                tt = self.view.items.model().data(jj)
                if tt:
                    txt = re.sub(tt, '', txt)
                    self.sel_indexes.remove(self.list_items.index(tt))
            if set(txt).issubset(' ,'):
                txt = ''
            else:
                txt = txt.strip(' ,')

        idx = selected.indexes()
        if idx:
            for jj in idx:
                tt = self.view.items.model().data(jj)
                if tt:
                    txt = ', '.join((txt, tt)) if txt else tt
                    self.sel_indexes.append(self.list_items.index(tt))

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
        self.set_selection(col_no)

    def set_selection(self, col_no):
        self.view.items.selectionModel().clearSelection()
        self.view.in_field.setText('')
        model = self.view.items.model()
        tmp = self.sel_indexes.copy()
        self.sel_indexes.clear()
        for idx in tmp:
            row_, col_ = divmod(idx, col_no)
            index_ = model.index(row_, col_)
            self.view.items.selectionModel().select(index_, QItemSelectionModel.Select)


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
    labels = ['label1', 'label2', 'Window title']
    table_items = ['item {}'.format(i + 1) for i in range(25)]
    sel_items = [table_items[2], table_items[7]]

    ItemChoice = ItemEdit(labels, table_items, sel_items)
    ItemChoice.resize(500, 300)

    # ItemChoice.setup_view()

    ItemChoice.show()
    print(ItemChoice.get_result())
    sys.exit(app.exec_())

