# view/sel_opt.py

from collections import namedtuple

from PyQt5.QtWidgets import QDialog
from view.ui_sel_opt import Ui_SelOpt
# from controller.my_controller import MyController


class SelOpt(QDialog):
    def __init__(self, controller, parent=None):
        super(SelOpt, self).__init__(parent)
        self.ui = Ui_SelOpt()
        self.ui.setupUi(self)

        self.ctrl = controller

        self.ext = ''
        self.tags = ''
        self.authors = ''

        self.ui.chAuthor.stateChanged.connect(self.author_toggle)
        self.ui.chDate.stateChanged.connect(self.date_toggle)
        self.ui.chDirs.stateChanged.connect(self.dir_toggle)
        self.ui.chExt.stateChanged.connect(self.ext_toggle)
        self.ui.chTags.stateChanged.connect(self.tag_togle)

    def author_toggle(self):
        state = self.ui.chAuthor.isChecked()
        self.ui.eAuthors.setEnabled(state)
        if state and not self.ui.eAuthors.text():
            self.ui.eAuthors.setText(self.ctrl.get_selected_items(self.ctrl.view.authorsList))
        else:
            self.ui.eAuthors.setText('')

    def date_toggle(self):
        state = self.ui.chDate.isChecked()
        self.ui.eDate.setEnabled(state)
        self.ui.dateAfter.setEnabled(state)
        self.ui.dateBefore.setEnabled(state)
        self.ui.dateBook.setEnabled(state)
        self.ui.dateFile.setEnabled(state)

        if not state:
            self.ui.eDate.setText('')

    def dir_toggle(self):
        if self.ui.chDirs.isChecked():
            self.ui.lDir.setText(self.ctrl.get_selected_items(self.ctrl.view.dirTree))
            if self.ui.lDir.text():
                self.ui.sbLevel.setEnabled(True)
        else:
            self.ui.lDir.setText('')
            self.ui.sbLevel.setEnabled(False)

    def ext_toggle(self):
        if self.ui.chExt.isChecked():
            self.ui.eExt.setEnabled(True)
            self.ui.eExt.setText(self.ctrl.get_selected_items(self.ctrl.view.extList))
        else:
            self.ui.eExt.setEnabled(False)
            self.ui.eExt.setText('')

    def tag_togle(self):
        state = self.ui.chTags.isChecked()
        self.ui.tagAll.setEnabled(state)
        self.ui.tagAny.setEnabled(state)
        self.ui.eTags.setEnabled(state)
        if state:
            self.ui.eTags.setText(self.ctrl.get_selected_items(self.ctrl.view.tagsList))
        else:
            self.ui.eTags.setText('')

    def get_result(self):
        # result = namedtuple('result', ['folder', ['path', 'level'],
        #                                'extension', 'tags', ['all', 'list'],
        #                                'authors', 'date', ['book', 'after']])
        result = namedtuple('result', ['dir', 'extension', 'tags', 'authors', 'date'])
        res = result(dir=(self.ui.chDirs.isChecked(), self.ui.sbLevel.text()),
                     extension=(self.ui.chExt.isChecked() and
                                self.ui.eExt.text().strip() != ''),
                     tags=((self.ui.chTags.isChecked() and
                            self.ui.eTags.text().strip() != ''),
                           self.ui.tagAll.isChecked()),
                     authors=(self.ui.chAuthor.isChecked() and
                              self.ui.eAuthors.text().strip() != ''),
                     date=(self.ui.chDate.isChecked(), self.ui.eDate.text(),
                           self.ui.dateFile.isChecked(), self.ui.dateAfter.isChecked()))
        return res

