import unittest
from unittest.mock import Mock
from unittest.mock import patch

from controller import my_controller
from controller.my_qt_model import MyListModel
from model.db_utils import *


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

    def test_on_open_db ( self ):
        mock_populate = Mock()
        self.controller.populate_all_widgets = mock_populate
        mock_sqlite3 = Mock(spec_set=sqlite3)
        my_controller.sqlite3 = mock_sqlite3
        mock_create_db = Mock()
        my_controller.create_db = mock_create_db

        self.controller.on_open_db('my file', True)

        mock_sqlite3.connect.assert_called_with('my file', detect_types=3)
        mock_create_db.create_all_objects.assert_called_once()
        mock_populate.assert_called_once()

        self.controller.on_open_db('my file', False)
        mock_create_db.create_all_objects.assert_called_once()

    def test_on_populate_view(self):
        mock_populate_all_widgets = Mock()
        self.controller.populate_all_widgets = mock_populate_all_widgets
        mock_populate_directory_tree = Mock()
        self.controller.populate_directory_tree = mock_populate_directory_tree
        mock_populate_ext_list = Mock()
        self.controller.populate_ext_list = mock_populate_ext_list
        mock_populate_tag_list = Mock()
        self.controller.populate_tag_list = mock_populate_tag_list
        mock_populate_author_list = Mock()
        self.controller.populate_author_list = mock_populate_author_list
        mock_populate_file_list = Mock()
        self.controller.populate_file_list = mock_populate_file_list
        mock_populate_comment_field = Mock()
        self.controller.populate_comment_field = mock_populate_comment_field
        mock_populate_cb_places = Mock()
        self.controller.populate_cb_places = mock_populate_cb_places

        self.controller.on_populate_view('nothing')
        mock_populate_all_widgets.assert_not_called()
        mock_populate_directory_tree.assert_not_called()
        mock_populate_ext_list.assert_not_called()
        mock_populate_tag_list.assert_not_called()
        mock_populate_author_list.assert_not_called()
        mock_populate_file_list.assert_not_called()
        mock_populate_comment_field.assert_not_called()
        mock_populate_cb_places.assert_not_called()

        self.controller.on_populate_view('all')
        mock_populate_all_widgets.assert_called_once()

        self.controller.on_populate_view('dirTree')
        mock_populate_directory_tree.assert_called_once()

        self.controller.on_populate_view('extList')
        mock_populate_ext_list.assert_called_once()

        self.controller.on_populate_view('tagsList')
        mock_populate_tag_list.assert_called_once()

        self.controller.on_populate_view('authorsList')
        mock_populate_author_list.assert_called_once()

        self.controller.on_populate_view('filesList')
        mock_populate_file_list.assert_called_once()

        self.controller.on_populate_view('commentField')
        mock_populate_comment_field.assert_called_once()

        self.controller.on_populate_view('cb_places')
        mock_populate_cb_places.assert_called_once()

    # ask_rename_or_new - contains QMessageBox() only - nothing to test
    # def test_ask_rename_or_new(self):
    #     pass

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


