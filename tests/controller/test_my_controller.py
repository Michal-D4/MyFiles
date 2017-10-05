import unittest

from model.db_utils import *
from unittest.mock import MagicMock, Mock
from unittest.mock import patch, call
from model.utils import create_db
from model.utils import load_db_data
from controller.my_qt_model import TreeModel, MyListModel
from controller import my_controller


class TestMyController(unittest.TestCase):
    def setUp(self):
        # members: _connection, curr_place, dbu, places, view
        pass

    def tearDown(self):
        pass

    @patch('controller.my_controller.os.walk')
    def test_yield_files(self, mock_os_walk):
        mock_os_walk.return_value = [('1', ('2', '3'), ('4.txt', '5.chm', '7.doc')),
                                     ('2', ('8', '9'), ('10.txt', '6.com'))]
        aa = my_controller.yield_files(r'd:\Users\mihal\R\Doc', ('txt', 'chm', 'jpg'))
        bb = tuple(aa)
        test_data = ('1\\4.txt', '1\\5.chm', '2\\10.txt')
        self.assertTupleEqual(bb, test_data)

    def test_on_ext_list_change(self):
        pass

    def test_add_extension(self):
        pass

    def test_remove_extension(self):
        pass

    def test_allowed_removal(self):
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


