import unittest
import sqlite3

from model.db_utils import *
from unittest.mock import MagicMock, Mock
from unittest.mock import patch, call
from model.utils import create_db
from model.utils import load_db_data
from controller.my_qt_model import TreeModel, MyListModel
from controller import my_controller


class TestMyController(unittest.TestCase):
    def setUp(self):
        app = Mock()
        self.controller = my_controller.MyController(app)

    def tearDown(self):
        # self.connection.close()
        pass

    @patch('controller.my_controller.os.walk')
    def test_yield_files(self, mock_os_walk):
        mock_os_walk.return_value = [('1', ('2', '3'), ('4.txt', '5.chm', '7.doc')),
                                     ('2', ('8', '9'), ('10.txt', '6.com'))]
        aa = my_controller.yield_files('root', 'txt, .chm,  jpg')
        bb = tuple(aa)
        test_data = ('1\\4.txt', '1\\5.chm', '2\\10.txt')
        self.assertTupleEqual(bb, test_data)

    @patch('controller.my_controller.os.walk')
    def test_yield_files_no_extensions(self, mock_os_walk):
        mock_os_walk.return_value = [('1', ('2', '3'), ('4.txt', '5.chm', '7.doc')),
                                     ('2', ('8', '9'), ('10.txt', '6.com'))]
        aa = my_controller.yield_files('root', '')
        bb = tuple(aa)
        test_data = ('1\\4.txt', '1\\5.chm', '1\\7.doc', '2\\10.txt', '2\\6.com')
        self.assertTupleEqual(bb, test_data)

    @patch('controller.my_controller.QInputDialog')
    @patch('controller.my_controller.MyController.remove_extension')
    @patch('controller.my_controller.MyController.add_extension')
    def test_on_ext_list_change_add(self, mock_add, mock_remove, mock_dialog):
        mock_dialog.getText.return_value = ('', 1)
        self.controller.on_ext_list_change('add')
        mock_dialog.getText.assert_called_once()
        mock_add.assert_called_once()
        mock_remove.assert_not_called()

    @patch('controller.my_controller.QInputDialog')
    @patch('controller.my_controller.MyController.remove_extension')
    @patch('controller.my_controller.MyController.add_extension')
    def test_on_ext_list_change_remove(self, mock_add, mock_remove, mock_dialog):
        mock_dialog.getText.return_value = ('', 1)
        self.controller.on_ext_list_change('remove')
        mock_remove.assert_called_once()
        mock_add.assert_not_called()

    def test_add_extension(self):
        '''
        check called_with for
        1) dbu.select_other
        2) dbu.insert_other
        3) model.appendData
        4) model.createIndex
        5) extList.setCurrentIndex
        '''
        self.controller.dbu = Mock()

        mock_select_other = Mock()
        self.controller.dbu.select_other.return_value = mock_select_other
        mock_select_other.fetchone.return_value = (0,)

        self.controller.dbu.insert_other.return_value = 1

        mock_view_extList = Mock()
        self.controller.view.extList = mock_view_extList
        mock_model = Mock()
        mock_view_extList.model.return_value = mock_model
        mock_model.rowCount.return_value = 1
        mock_model.createIndex.return_value = 'created index'

        self.controller.add_extension('pdf')

        self.controller.dbu.select_other.assert_called_with('HAS_EXT', ('pdf',))
        self.controller.dbu.insert_other.assert_called_with('EXT', {'ext': 'pdf'})
        mock_model.appendData.assert_called_with(('pdf', 1))
        mock_model.createIndex.assert_called_with(0, 0, 0)
        mock_view_extList.setCurrentIndex.assert_called_with('created index')

    def test_allowed_removal(self):
        pass

    def test_remove_extension(self):
        pass

    def test_on_open_db(self):
        pass

    def test_on_populate_view(self):
        pass

    def test_populate_cb_places(self):
        pass

    def test_on_change_data(self):
        pass

    def test_add_place(self):
        pass

    def test_rename_place(self):
        pass

    def test_ask_rename_or_new(self):
        pass

    def test_populate_ext_list(self):
        pass

    def test_populate_tag_list(self):
        pass

    def test_populate_author_list(self):
        pass

    def test_populate_file_list(self):
        pass

    def test_populate_comment_field(self):
        pass

    def test_populate_all_widgets(self):
        pass

    def test_populate_directory_tree(self):
        pass

    def test_on_scan_files(self):
        pass


