from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QSettings, QVariant, QSize, Qt

from view.my_db_choice import MyDBChoice
from view.ui_new_view import Ui_MainWindow


class MainFlow(QtWidgets.QMainWindow):
    populate_view_signal = pyqtSignal(str)        # str - name of Widget
    change_data_signal = pyqtSignal(str, tuple)   # str - name of Widget, tuple - data
    scan_files_signal = pyqtSignal()
    ext_list_change_signal = pyqtSignal(str)      # str = 'add' or 'remove'

    def __init__(self, parent=None, open_dialog=MyDBChoice):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui_main = Ui_MainWindow()
        self.ui_main.setupUi(self)

        self.ui_main.cb_places = QtWidgets.QComboBox()
        self.ui_main.toolBar.addWidget(self.ui_main.cb_places)

        self.restore_setting()

        # self.ui_main.goButton.clicked.connect(self.go)
        # self.ui_main.buttonAdd.clicked.connect(self.add_extension)
        # self.ui_main.buttonRemove.clicked.connect(self.remove_extension)
        self.ui_main.actionOpenDB.triggered.connect(self.open_data_base)
        self.ui_main.actionScanFiles.triggered.connect(self.scan_files)

        self.ui_main.cb_places.currentIndexChanged.connect(self.change_place)
        self.ui_main.dirTree.doubleClicked.connect(self.dir_changed)

        self.open_dialog = open_dialog

    def dir_changed(self, signal):
        print('|---> MainFlow.dir_changed')
        print(type(signal))
        pass

    def change_place(self, idx):
        self.change_data_signal.emit('cb_places', (idx, self.ui_main.cb_places.currentText()))

    def restore_setting(self):
        settings = QSettings('myorg', 'myapp')
        if settings.contains("MainFlow/Size"):
            size = settings.value("MainFlow/Size", QSize(600, 500))
            self.resize(size)
            position = settings.value("MainFlow/Position")
            self.move(position)
            self.restoreState(settings.value("MainFlow/State"))
            self.restoreState(settings.value("MainFlow/State"))
            self.ui_main.splitter_files.restoreState(settings.value("FilesSplitter"))
            self.ui_main.opt_splitter.restoreState(settings.value("OptSplitter"))
            self.ui_main.main_splitter.restoreState(settings.value("MainSplitter"))
        else:
            self.ui_main.main_splitter.setStretchFactor(0, 2)
            self.ui_main.main_splitter.setStretchFactor(1, 5)
            self.ui_main.main_splitter.setStretchFactor(2, 1)

            self.ui_main.splitter_files.setStretchFactor(0, 5)
            self.ui_main.splitter_files.setStretchFactor(1, 2)

    def scan_files(self):
        self.scan_files_signal.emit()

    def add_extension(self):
        print('|---> MainFlow.add_extension')
        self.ext_list_change_signal.emit('add')

    def remove_extension(self):
        # removing is possible only if there is no files with this extension
        print('|---> MainFlow.remove_extension')
        self.ext_list_change_signal.emit('remove')

    def go(self):
        print('go ====>')

    def populate_all(self):
        print('|---> MainFlow.populate_all')
        self.populate_view_signal.emit('all')

    def populate_tree(self):
        print('|---> MainFlow.populate_tree')
        self.populate_view_signal.emit('dirTree')

    def open_data_base(self):
        self.open_dialog.exec_()

    def first_open_data_base(self):
        if not self.open_dialog.skip_open_dialog():
            print('MainFlow.first_open_data_base ===> run open_data_base')
            self.open_data_base()
        else:
            print('MainFlow.first_open_data_base ===> connect to recent used DB')
            self.open_dialog.emit_open_dialog()

    def closeEvent(self, event):
        settings = QSettings('myorg', 'myapp')
        settings.setValue("MainFlow/Size", QVariant(self.size()))
        settings.setValue("MainFlow/Position",
                          QVariant(self.pos()))
        settings.setValue("MainFlow/State",
                          QVariant(self.saveState()))
        settings.setValue("FilesSplitter",
                          QVariant(self.ui_main.splitter_files.saveState()))
        settings.setValue("OptSplitter",
                          QVariant(self.ui_main.opt_splitter.saveState()))
        settings.setValue("MainSplitter",
                          QVariant(self.ui_main.main_splitter.saveState()))
        # event.accept()
        super(MainFlow, self).closeEvent(event)

