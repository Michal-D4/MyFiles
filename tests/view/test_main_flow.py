import sys
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

from controller.my_controller import MyController
from model.utils import load_db_data
from model.utils import create_db

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


class TestControler(TestCase):
    def setUp(self):
        self._controller = MyController(None)

        # self._controller.connect_to_db(':memory:')
        # self._connection = self._controller.get_connection()  # this method removed

        create_db.create_all_objects(self._connection)

        load_db = load_db_data.LoadDBData(self._connection, (0, '', ''))
        load_db.load_data(LOAD_DATA_IN_RANDOM_ORDER)

    def tearDown(self):
        self._connection.close()

    def test_populate_directory_tree(self):
        # todo - mock of  1) dir_tree = self.dbu.dir_tree_select(dir_id=0, level=0)
        #                 2) model = TreeModel(dir_tree)
        #                 3) self.view.ui_main.dirTree.setModel(model)
        #    only check that all them are called once
         self._controller._populate_directory_tree()

