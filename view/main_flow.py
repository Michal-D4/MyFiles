# view/main_flow.py

from PyQt5.QtWidgets import QMainWindow, QWidget, QMenu
from PyQt5.QtCore import pyqtSignal, QSettings, QVariant, QSize, Qt, QUrl, QEvent

from view.my_db_choice import MyDBChoice
from view.ui_new_view import Ui_MainWindow


class MainFlow(QMainWindow):
    change_data_signal = pyqtSignal(str)   # str - name of action
    scan_files_signal = pyqtSignal()

    def __init__(self, parent=None, open_dialog=MyDBChoice):
        QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.old_size = None
        self.old_pos = None
        self.restore_setting()

        self.set_actions()

        self.set_menus()

        self.setup_context_menu()

        self.open_dialog = open_dialog

    def set_actions(self):
        self.ui.actionOpenDB.triggered.connect(
            lambda: self.open_dialog.exec_())
        self.ui.actionScanFiles.triggered.connect(
            lambda: self.scan_files_signal.emit())
        self.ui.actionGetFiles.triggered.connect(
            lambda: self.change_data_signal.emit('get_sel_files'))
        self.ui.actionFavorites.triggered.connect(
            lambda: self.change_data_signal.emit('Favorites'))

        self.ui.cb_places.currentIndexChanged.connect(self.change_place)
        self.ui.commentField.anchorClicked.connect(self.ref_clicked)
        self.ui.filesList.doubleClicked.connect(
            lambda: self.change_data_signal.emit('File_doubleClicked'))

        self.ui.filesList.resizeEvent = self.resize_event

    def set_menus(self):
        menu = QMenu(self)
        change_font = menu.addAction('Change Font')
        set_fields = menu.addAction('Set fields')
        self.ui.btnOption.setMenu(menu)
        change_font.triggered.connect(lambda: self.change_data_signal.emit('change_font'))
        set_fields.triggered.connect(lambda: self.change_data_signal.emit('Set fields'))

        menu2 = QMenu(self)
        sel_opt = menu2.addAction('Selection options')
        self.ui.btnGetFiles.setMenu(menu2)
        sel_opt.triggered.connect(lambda: self.change_data_signal.emit('Selection options'))

    def calc_collumns_width(self):
        lines = ['9999-99-99 99', 'Pages 99', '9 999 999 999 ']
        return [self.ui.filesList.fontMetrics().boundingRect(line).width() for line in lines]

    def setup_context_menu(self):
        self.ui.filesList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.filesList.customContextMenuRequested.connect(self._file_menu)

        self.ui.extList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.extList.customContextMenuRequested.connect(self._ext_menu)

        self.ui.tagsList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tagsList.customContextMenuRequested.connect(self._tag_menu)

        self.ui.authorsList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.authorsList.customContextMenuRequested.connect(self._author_menu)

        self.ui.dirTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.dirTree.customContextMenuRequested.connect(self._dir_menu)

    def _file_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Open')
        menu.addAction('Open folder')
        menu.addAction('Add to favorites')
        menu.addAction('Delete')
        menu.addSeparator()
        menu.addAction('Copy file name')
        menu.addAction('Copy full path')
        menu.addSeparator()
        menu.addAction('Copy file')
        menu.addAction('Move file')
        menu.addAction('Delete file')
        action = menu.exec_(self.ui.filesList.mapToGlobal(pos))
        if action:
            self.change_data_signal.emit(action.text())

    def _ext_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Remove unused')
        menu.addAction('Create group')
        action = menu.exec_(self.ui.extList.mapToGlobal(pos))
        if action:
            act = 'Ext {}'.format(action.text())
            self.change_data_signal.emit(act)

    def _tag_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Remove unused')
        menu.addAction('Scan in names')
        menu.addAction('Rename')
        action = menu.exec_(self.ui.tagsList.mapToGlobal(pos))
        if action:
            act = 'Tag {}'.format(action.text())
            self.change_data_signal.emit(act)

    def _author_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Remove unused')
        action = menu.exec_(self.ui.authorsList.mapToGlobal(pos))
        if action:
            act = 'Author {}'.format(action.text())
            self.change_data_signal.emit(act)

    def _dir_menu(self, pos):
        menu = QMenu(self)
        menu.addAction('Rescan dir')
        action = menu.exec_(self.ui.dirTree.mapToGlobal(pos))
        if action:
            act = 'Dirs {}'.format(action.text())
            self.change_data_signal.emit(act)

    def ref_clicked(self, argv_1):
        self.ui.commentField.setSource(QUrl())
        self.change_data_signal.emit(argv_1.toString())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.old_size = event.oldSize()
        settings = QSettings()
        settings.setValue("MainFlow/Size", QVariant(self.size()))

    def resize_event(self, event):
        widths = self.calc_collumns_width()
        old_width = event.oldSize().width()
        w = event.size().width()
        w1 = self.ui.filesList.width()
        if w != self.old_size.width():
            self.ui.filesList.blockSignals(True)
            ww = [sum(widths)] + widths
            if w > ww[0]*2:
                ww[0] = w - ww[0]
            else:
                ww[0] = w * 0.75
            for k in range(4):
                self.ui.filesList.setColumnWidth(k, ww[k])
            self.ui.filesList.blockSignals(False)

        super().resizeEvent(event)

    def changeEvent(self, event, **kwargs):
        if event.type() == QEvent.WindowStateChange:
            settings = QSettings()
            if event.oldState() == Qt.WindowMaximized:
                settings.setValue("MainFlow/isFullScreen", QVariant(False))
            elif event.oldState() == Qt.WindowNoState and \
                    self.windowState() == Qt.WindowMaximized:
                settings.setValue("MainFlow/isFullScreen", QVariant(True))
                if self.old_size:
                    settings.setValue("MainFlow/Size", QVariant(self.old_size))
                if self.old_pos:
                    settings.setValue("MainFlow/Position", QVariant(self.old_pos))
        else:
            super().changeEvent(event)

    def moveEvent(self, event):
        self.old_pos = event.oldPos()
        settings = QSettings()
        settings.setValue("MainFlow/Position", QVariant(self.pos()))
        super().moveEvent(event)

    def change_place(self, idx):
        self.change_data_signal.emit('Change place')

    def restore_setting(self):
        settings = QSettings()
        if settings.contains("MainFlow/Size"):
            size = settings.value("MainFlow/Size", QSize(640, 480))
            self.resize(size)
            position = settings.value("MainFlow/Position")
            self.move(position)
            self.restoreState(settings.value("MainFlow/State"))
            self.restoreState(settings.value("MainFlow/State"))
            self.ui.splitter_files.restoreState(settings.value("FilesSplitter"))
            self.ui.opt_splitter.restoreState(settings.value("OptSplitter"))
            self.ui.main_splitter.restoreState(settings.value("MainSplitter"))
            if settings.value("MainFlow/isFullScreen", False, type=bool):
                self.showMaximized()
        else:
            self.ui.main_splitter.setStretchFactor(0, 2)
            self.ui.main_splitter.setStretchFactor(1, 5)
            self.ui.main_splitter.setStretchFactor(2, 1)

            self.ui.splitter_files.setStretchFactor(0, 5)
            self.ui.splitter_files.setStretchFactor(1, 2)

    def first_open_data_base(self):
        """
        Open DB when application starts
        :return:
        """
        if not self.open_dialog.skip_open_dialog():
            self.open_dialog.exec_()
        else:
            self.open_dialog.emit_open_dialog()

    def closeEvent(self, event):
        self.open_dialog.save_init_data()
        settings = QSettings()
        settings.setValue("MainFlow/State", QVariant(self.saveState()))
        settings.setValue("FilesSplitter", QVariant(self.ui.splitter_files.saveState()))
        settings.setValue("OptSplitter", QVariant(self.ui.opt_splitter.saveState()))
        settings.setValue("MainSplitter", QVariant(self.ui.main_splitter.saveState()))
        super(MainFlow, self).closeEvent(event)

