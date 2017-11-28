# view/item_edit.py

from PyQt5.QtWidgets import QDialog
from view.ui_items_edit import Ui_ItemChoice
from controller.my_qt_model import TableModel


class ItemEdit(QDialog):
    def __init__(self, labels, items, parent=None):
        super(ItemEdit, self).__init__(parent)
        self.view = Ui_ItemChoice()
        self.view.setupUi(self)

        self.view.label_1.setText(labels[0])
        self.view.label_2.setText(labels[1])
        self.setWindowTitle(labels[2])

        self.list_items = items

        aa = max(items, key=lambda t: len(t))
        self.max_width = self.view.items.fontMetrics().boundingRect(aa).width() + 10
        w = self.view.items.size().width()
        col_no = w // self.max_width
        print('|---> __init__:', col_no, w, self.max_width)
        self.setup_model(col_no)

        self.view.items.resizeEvent = self.resize_event

    def resize_event(self, event):
        w = event.size().width()
        # w_old = event.
        col_no = w // self.max_width
        print('|---> resize_event', w, col_no, self.view.items.model().columnCount())
        if col_no != self.view.items.model().columnCount():
            self.setup_model(col_no)

    def setup_model(self, col_no):
        row_no = len(self.list_items) // col_no + 1
        aa = []
        for i in range(row_no):
            aa.append(tuple(self.list_items[i * col_no:(i + 1) * col_no]))
        model = TableModel(parent=self.view.items)
        model.setColumnCount(col_no)
        for a in aa:
            model.append_row(a)
        self.view.items.setModel(model)
        for i in range(1, col_no):
            self.view.items.header().resizeSection(i, self.max_width)
            print('width of col {}'.format(i), self.view.items.columnWidth(i), self.max_width)

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
    items = ['item {}'.format(i+1) for i in range(25)]

    ItemChoice = ItemEdit(labels, items)
    ItemChoice.resize(100, 300)
    ItemChoice.show()
    sys.exit(app.exec_())

