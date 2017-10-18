import unittest

from model.db_utils import *
from unittest.mock import MagicMock, Mock
from unittest.mock import patch, call
from controller.my_qt_model import TreeModel, MyListModel
from controller import my_controller
from model.db_utils import DBUtils


class TestMyControllerViewDbu(unittest.TestCase):
    def setUp(self):
        app = Mock()
        self.controller = my_controller.MyController(app)

        self.mock_view = Mock()
        self.controller.view = self.mock_view

        self.mock_dbu = Mock(spec_set=DBUtils)
        self.controller.dbu = self.mock_dbu

    def tearDown(self):
        # self.connection.close()
        pass

    def test_populate_ext_list(self):
        self.mock_dbu.select_other.return_value = [('e1', 1), ('e2', 2)]

        mock_model_class = Mock()
        my_controller.MyListModel = mock_model_class
        mock_model_obj = Mock(spec_set=MyListModel)
        mock_model_class.return_value = mock_model_obj

        self.controller._populate_ext_list()
        self.mock_dbu.select_other.assert_called_once_with('EXT')
        # mock_model_obj.append_row.assert_called_with((1, 'e1')) # only last call tested
        mock_model_obj.append_row.assert_called_with((2, 'e2'))
        self.mock_view.extList.setModel.assert_called_once()

    def test_populate_tag_list(self):
        pass

    def test_populate_author_list(self):
        pass

    def test_populate_file_list(self):
        pass

    def test_populate_comment_field(self):
        pass

    @patch('controller.my_controller.TreeModel', spec_set=TreeModel)
    def test_populate_directory_tree(self, mock_model):
        mock_model.return_value = 'model'

        self.controller._populate_directory_tree()
        self.mock_dbu.dir_tree_select.assert_called_once_with(dir_id=0, level=0)
        mock_model.assert_called_once()
        self.mock_view.dirTree.setModel.assert_called_once_with('model')



