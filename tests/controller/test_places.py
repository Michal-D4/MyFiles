import unittest
from unittest.mock import Mock, patch, call

from controller.places import Places
from model.db_utils import DBUtils

from PyQt5.QtWidgets import QComboBox


class TestPlaces(unittest.TestCase):
    def setUp(self):
        self.mock_view = Mock(spec_set=QComboBox)
        self.mock_dbu = Mock(spec_set=DBUtils)
        self.tested_places = Places(self.mock_view, self.mock_dbu)

    def tearDown(self):
        pass

    @patch.object(Places, '_change_place')
    def test_about_change_place_call_change_place(self, mock_change_place):
        data = (0, 'place 1')
        self.tested_places._places.append(data)

        self.tested_places.about_change_place(data)
        mock_change_place.assert_called_once_with(data)

    @patch.object(Places, '_add_place')
    def test_about_change_place_call_add_place(self, mock_add_place):
        data = (0, 'place 1')

        self.tested_places.about_change_place(data)
        mock_add_place.assert_called_once_with(data)

    @patch.object(Places, '_ask_switch_to_unavailable_storage')
    @patch.object(Places, 'is_place_available')
    def test_change_place(self, mock_is_place_available,
                            mock_ask_switch_to_unavailable_storage):
        self.tested_places._places = [(0, 'in', 'out'), ]
        self.tested_places._curr_place = (0, 'in', 'out')

        mock_is_place_available.side_effect = (True, False, False)
        mock_ask_switch_to_unavailable_storage.side_effect = (0, 1)

        self.tested_places._change_place((0, 'data'))
        mock_is_place_available.assert_called_once()
        mock_ask_switch_to_unavailable_storage.assert_not_called()

        self.tested_places._change_place((0, 'data'))
        mock_ask_switch_to_unavailable_storage.assert_called_once()

        self.tested_places._change_place((0, 'data'))
        self.mock_view.setCurrentIndex.assert_called_once_with(0)

    def test_rename_place(self):
        self.tested_places._places = [(0, 'a', 'a')]
        self.tested_places._curr_place = (0, 'a', 'a')

        self.tested_places._rename_place((1, 'data'))
        self.mock_view.removeItem.assert_called_once()
        self.mock_dbu.update_other.assert_called_once_with('PLACES', ('data', 0))

    @patch('controller.places.socket')
    def test_populate_cb_places(self, mock_socket):
        self.mock_dbu.select_other.return_value = ((1, 'inner name1', 3),
                                                   (4, 'inner name2', 6))

        mock_socket.gethostname.return_value = 'inner name2'

        self.tested_places.populate_cb_places()
        self.mock_dbu.select_other.assert_called_once_with('PLACES')
        self.mock_view.addItems.assert_called_once()
        self.mock_view.clear.assert_has_calls([call.cb_places.clear(), ])
        self.assertEqual(self.mock_view.blockSignals.mock_calls,
                         [call.blockSignals(True),
                          call.blockSignals(False)])

    @patch.object(Places, '_rename_place')
    @patch.object(Places, '_ask_rename_or_new')
    def test_add_place(self, mock_ask_rename_or_new, mock_rename_place):

        mock_ask_rename_or_new.side_effect = (0, 1, 2, 3)

        self.tested_places._add_place((1, 'data'))
        self.mock_dbu.insert_other.assert_called_once_with('PLACES', (1, 'data', 'data'))

        self.tested_places._add_place((1, 'data'))
        mock_rename_place.assert_called_once_with((1, 'data'))

        self.tested_places._add_place((1, 'data'))
        self.mock_view.removeItem.assert_called_once()

    def test_is_place_available_yes(self):
        res = self.tested_places.is_place_available()
        self.assertTrue(res)

    # def test_is_place_available_no(self):
    #     res = self.tested_places.is_place_available()
    #     self.assertFalse(res)

    def test_get_curr_place(self):
        self.mock_dbu.select_other.return_value = ((1, 2, 3), (4, 5, 6))

        self.tested_places.populate_cb_places()

        res = self.tested_places.get_curr_place()

        self.assertEqual(res, (1, 2, 3))
