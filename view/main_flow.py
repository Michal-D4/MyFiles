from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QSettings, QVariant, QSize, Qt

from view.my_db_choice import MyDBChoice
from view.ui_new_view import Ui_MainWindow


class MainFlow(QtWidgets.QMainWindow):
    change_data_signal = pyqtSignal(str, tuple)   # str - name of Widget, tuple - data
    scan_files_signal = pyqtSignal()

    def __init__(self, parent=None, open_dialog=MyDBChoice):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui_main = Ui_MainWindow()
        self.ui_main.setupUi(self)

        self.ui_main.cb_places = QtWidgets.QComboBox()
        self.ui_main.cb_places.setEditable(True)
        self.ui_main.toolBar.addWidget(self.ui_main.cb_places)

        self.restore_setting()

        self.ui_main.actionOpenDB.triggered.connect(self.open_data_base)
        self.ui_main.actionScanFiles.triggered.connect(self.scan_files)
        self.ui_main.actionGetFiles.triggered.connect(self.go)

        self.ui_main.cb_places.currentIndexChanged.connect(self.change_place)
        self.ui_main.dirTree.clicked.connect(self.dir_changed)

        self.open_dialog = open_dialog

    def dir_changed(self, curr_idx):
        dir_idx = self.ui_main.dirTree.model().data(curr_idx, Qt.UserRole)[0]
        self.change_data_signal.emit('filesList', (dir_idx,))

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

    def go(self):
        print('go ====>')

    def open_data_base(self):
        self.open_dialog.exec_()

    def first_open_data_base(self):
        if not self.open_dialog.skip_open_dialog():
            self.open_data_base()
        else:
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

