import sys
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

from view.main_flow import *
from model.utils import create_db
from model.utils import load_db_data
from controller.my_controller import MyController

from PyQt5.QtWidgets import QApplication, QTreeWidgetItemIterator
#from PyQt5.QtGui import
from PyQt5.QtTest import QTest

LOAD_DATA = (r'f:\Docs\A.Блок.txt',
             r'f:\Docs\Box\Блок.docx',
             r'f:\Docs\Python\А.Блок.docx',
             r'f:\Docs\Box\main\on.docx',
             r'f:\Docs\Python\main.docx',
             r'd:\Doc2\Java\fuf\dum.a',
             r'd:\Doc2\Java\some.txt',
             r'f:\Docs\triton\sec\boo.no'
             )

LOAD_DATA_IN_RANDOM_ORDER = (r'd:\Doc2\Java\fuf\dum.a',
                             r'f:\Docs\Python\main.docx',
                             r'd:\Doc2\Java\some.txt',
                             r'f:\Docs\Box\main\on.docx',
                             r'f:\Docs\triton\sec\boo.no',
                             r'f:\Docs\A.Блок.txt',
                             r'f:\Docs\Python\А.Блок.docx',
                             r'f:\Docs\Box\Блок.docx'
                             )

app = QApplication(sys.argv)

class FakeOpenDialog():
    def __init__(self):
        pass

    def exec_(self):
        return QDialog.Accepted

    def get_file_name(self):
        return ':memory:'

    def skip_open_dialog(self):
        return True

    def get_init_data(self):
        '''
        :return: init_data: list of 3 items:
            1 - skipThisWindow flag, 0 or 2; 2 - skip
            2 - index of last used DB
            3 - list of DBs
        '''
        return [2, 0, []]


class TestMainFlow(TestCase):
    def setUp(self):
        dlg = FakeOpenDialog()
        my_app = MainFlow(open_dialog=dlg)

        _controller = MyController(my_app)
        # my_app.open_DB_request.connect(_controller.on_open_DB_request)
        # my_app.populate_view.connect(_controller.on_populate_view)

        my_app.first_open_data_base()

        # self._connection = _controller.get_connection()

        load_db = load_db_data.LoadDBData(self._connection, (0, '', ''))

        load_db.load_data(LOAD_DATA_IN_RANDOM_ORDER)

    def tearDown(self):
        self._connection.close()

    # def test_open_data_base(self):
    #     self.assertEqual(self.main_flow.init_data, [2, 0, [':memory:']])

    def test_populate_tree(self):
        self.main_flow.populate_tree()

