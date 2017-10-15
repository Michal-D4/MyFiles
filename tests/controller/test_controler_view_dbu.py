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

    def test_populate_cb_places ( self ):
        self.mock_dbu.select_other.return_value = ((1, 2, 3), (4, 5, 6))

        self.controller.populate_cb_places()
        self.mock_view.cb_places.addItems.assert_called_once()

    def test_add_place(self):
        mock_ask_rename_or_new = Mock()
        mock_ask_rename_or_new.side_effect = (0, 1, 2, 3)
        self.controller.ask_rename_or_new = mock_ask_rename_or_new

        self.controller.rename_place = Mock()  # addItems is also called here

        self.controller.add_place((1, 'data'))
        self.mock_dbu.insert_other.assert_called_with('PLACES', (1, 'data', 'data'))

        self.controller.add_place((1, 'data'))

        self.controller.add_place((1, 'data'))

        self.controller.add_place((0, 'data'))
        self.mock_view.cb_places.addItems.assert_called_once()

    def test_rename_place(self):
        self.controller.places = [(1, 'a', 'a')]
        self.controller.curr_place = (1, 'a', 'a')

        self.controller.rename_place((1, 'data'))
        self.mock_view.cb_places.addItems.assert_called_once()
        self.mock_dbu.update_other.assert_called_with('PLACES', ('data', 0))

    def test_populate_ext_list(self):
        self.mock_dbu.select_other.return_value = [('e1', 1), ('e2', 2)]

        mock_model_class = Mock()
        my_controller.MyListModel = mock_model_class
        mock_model_obj = Mock(spec_set=MyListModel)
        mock_model_class.return_value = mock_model_obj

        self.controller.populate_ext_list()
        self.mock_dbu.select_other.assert_called_once_with('EXT')
        # mock_model_obj.append_row.assert_called_with((1, 'e1')) # only last call tested
        mock_model_obj.append_row.assert_called_with((2, 'e2'))
        self.mock_view.extList.setModel.assert_called_once()



