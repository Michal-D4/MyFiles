# view/main_flow.py

from PyQt5.QtWidgets import QMainWindow, QWidget, QComboBox, QMenu, QTreeView
from PyQt5.QtCore import pyqtSignal, QSettings, QVariant, QSize, Qt, QModelIndex, QUrl
from PyQt5.QtGui import QMouseEvent

from view.my_db_choice import MyDBChoice
from view.ui_new_view import Ui_MainWindow


class MainFlow(QMainWindow):
    change_data_signal = pyqtSignal(str, tuple)   # str - name of Widget, tuple - data
    scan_files_signal = pyqtSignal()

    def __init__(self, parent=None, open_dialog=MyDBChoice):
        QWidget.__init__(self, parent)
        self.ui_main = Ui_MainWindow()
        self.ui_main.setupUi(self)

        self.restore_setting()

        self.ui_main.actionOpenDB.triggered.connect(lambda: self.open_dialog.exec_())
        self.ui_main.actionScanFiles.triggered.connect(lambda: self.scan_files_signal.emit())
        self.ui_main.actionGetFiles.triggered.connect(self.go)

        self.ui_main.cb_places.currentIndexChanged.connect(self.change_place)
        self.ui_main.filesList.clicked.connect(self.file_changed)
        self.ui_main.filesList.resizeEvent = self.resize_event

        self.ui_main.filesList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui_main.filesList.customContextMenuRequested.connect(self._file_pop_menu)

        self.ui_main.commentField.anchorClicked.connect(self.ref_clicked)

        self.open_dialog = open_dialog

        lines = ['9999-99-99 99', 'Pages 99', '9 999 999 999 ']
        self.widths = [self.ui_main.filesList.fontMetrics().boundingRect(line).width() for line in lines]

    def ref_clicked(self, argv_1):
        self.ui_main.commentField.setSource(QUrl())
        self.change_data_signal.emit(argv_1.toString(), ())

    def resize_event(self, event):
        """
        Resize columns width of file list
        :param event:
        :return:
        """
        self.ui_main.filesList.blockSignals(True)
        w = event.size().width()
        ww = [sum(self.widths)] + self.widths
        if w > ww[0]*2:
            ww[0] = w - ww[0]
        for k in range(4):
            self.ui_main.filesList.setColumnWidth(k, ww[k])
        self.ui_main.filesList.blockSignals(False)

    def _file_pop_menu(self, pos):
        menu = QMenu(self)
        action1 = menu.addAction('Delete')
        action2 = menu.addAction('Open')
        action3 = menu.addAction('Open folder')
        action = menu.exec_(self.ui_main.filesList.mapToGlobal(pos))
        if action:
            print('|---> _file_pop_menu', action.text())
            self.change_data_signal.emit(action.text(), ())

    def file_changed(self, curr_idx: QModelIndex):
        idx_ = self.ui_main.filesList.model().data(curr_idx, Qt.UserRole)
        self.change_data_signal.emit('commentField', idx_)

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

    def go(self):
        # todo - implement file selection according selected ext., authors, tags, root
        print('go ====>')
        params = ()
        self.change_data_signal.emit('advanced_file_list', params)

    def first_open_data_base(self):
        """
        Open DB when application starts
        :return:
        """
        if not self.open_dialog.skip_open_dialog():
            self.open_dialog.exec_()
        else:
            self.open_dialog.emit_open_dialog()
        self.ui_main.dirTree.mousePressEvent = self.mousePressEvent

    def mousePressEvent(self, event: QMouseEvent):
        """
        Deselect all when click on empty place
        :param event:
        :return:
        """
        self.ui_main.dirTree.clearSelection()
        QTreeView.mousePressEvent(self.ui_main.dirTree, event)

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

