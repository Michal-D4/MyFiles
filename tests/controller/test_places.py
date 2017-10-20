import unittest
from unittest.mock import Mock, patch, call

import psutil
import ctypes

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
    @patch.object(Places, '_add_place')
    def test_about_change_place(self, mock_add_place, mock_change_place):
        data = (0, 'place 1')

        # if data[0] >= len of list of places, then call _add_place
        #  now list is empty
        self.tested_places.about_change_place(data)
        mock_add_place.assert_called_once_with(data)

        self.tested_places._places.append(data)

        #  now len of list = 1 --> call _change_place
        self.tested_places.about_change_place(data)
        mock_change_place.assert_called_once_with(data)

    @patch.object(Places, '_ask_switch_to_unavailable_storage')
    @patch.object(Places, 'is_place_available')
    def test__change_place(self, mock_is_place_available,
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

    def test__rename_place(self):
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
    def test__add_place(self, mock_ask_rename_or_new, mock_rename_place):

        mock_ask_rename_or_new.side_effect = (0, 1, 2, 3)

        self.tested_places._add_place((1, 'data'))
        self.mock_dbu.insert_other.assert_called_once_with('PLACES', (1, 'data', 'data'))

        self.tested_places._add_place((1, 'data'))
        mock_rename_place.assert_called_once_with((1, 'data'))

        self.tested_places._add_place((1, 'data'))
        self.mock_view.removeItem.assert_called_once()

    @patch.object(Places, '_get_mount_point')
    @patch('controller.places.socket')
    def test_is_place_available(self, mock_socket, mock_get_mount_point):
        self.mock_dbu.select_other.return_value = ((1, 'inner name1', 3),
                                                   (4, 'inner name2', 6))
        self.mock_view.currentIndex.side_effect = (1, 0, 0)
        mock_socket.gethostname.return_value = 'inner name2'
        mock_get_mount_point.side_effect = ('mount_point', '')

        self.tested_places.populate_cb_places()

        res = self.tested_places.is_place_available()
        self.assertTrue(res, msg='Current place is current computer, but not!!!')
        mount_point = self.tested_places.get_mount_point()
        self.assertEqual(mount_point, '', msg='Initial mount point is empty, but not!!!')

        res = self.tested_places.is_place_available()
        self.assertTrue(res, msg='Current plase is removable disk, which is mounted. But not!!!')
        mount_point = self.tested_places.get_mount_point()
        self.assertNotEqual(mount_point, '',
                            msg='Mounted removable disk. But does not have mount point!!!')

        res = self.tested_places.is_place_available()
        self.assertFalse(res, msg='Removal disk is not mounted. But available!!!')
        mount_point = self.tested_places.get_mount_point()
        self.assertEqual(mount_point, '',
                         msg='Removal disk is not mounted. But have mount point!!!')

    @patch('controller.places.socket')
    def test_get_curr_place(self, mock_socket):
        self.mock_dbu.select_other.return_value = ((1, 'inner name1', 3),
                                                   (4, 'inner name2', 6))

        mock_socket.gethostname.return_value = 'inner name2'

        self.tested_places.populate_cb_places()

        res = self.tested_places.get_curr_place()

        self.assertEqual(res, (4, 'inner name2', 6))

    @patch('controller.places.psutil', spec_set=psutil)
    def test_is_removable(self, mock_disk_partitions):
        mock_disk_partitions.disk_partitions.return_value = [
            psutil._common.sdiskpart('device1', 'mountpoint1', 'fs1', 'rw,removable'),
            psutil._common.sdiskpart('device2', 'mountpoint2', 'fs2', 'opts2')]

        res = self.tested_places.is_removable(device='device1')
        self.assertTrue(res)

        res = self.tested_places.is_removable(device='device2')
        self.assertFalse(res)

    @patch.object(Places, '_get_vol_name')
    @patch('controller.places.psutil', spec_set=psutil)
    def test__get_mount_point(self, mock_disk_partitions, mock_get_vol_name):
        mock_disk_partitions.disk_partitions.return_value = [
            psutil._common.sdiskpart('device1', 'mountpoint1', 'fs1', 'rw,removable'),
            psutil._common.sdiskpart('device2', 'mountpoint2', 'fs2', 'opts2')]

        mock_get_vol_name.return_value = 'place1'

        res = self.tested_places._get_mount_point(place_info='place1')
        self.assertEqual(res, 'mountpoint1')

        res = self.tested_places._get_mount_point(place_info='place2')
        self.assertEqual(res, '')

        # no removable disk
        mock_disk_partitions.disk_partitions.return_value = [
            psutil._common.sdiskpart('device1', 'mountpoint1', 'fs1', 'opts1'),
            psutil._common.sdiskpart('device2', 'mountpoint2', 'fs2', 'opts2')]

        res = self.tested_places._get_mount_point(place_info='place2')
        self.assertEqual(res, '')

    @patch('controller.places.ctypes', spec_set=ctypes)
    def test__get_vol_name(self, mock_ctypes):
        mock_ctypes.windll.kernel32.GetVolumeInformationW.side_effect = (1, 0)
        mock_ctypes.create_unicode_buffer().value = 'vol_name'

        res = Places._get_vol_name('any')   # GetVolumeInformationW: RC = 1
        self.assertEqual(res, 'vol_name')

        res = Places._get_vol_name('any')   # GetVolumeInformationW: RC = 0
        self.assertEqual(res, '')

