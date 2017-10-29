import socket
import psutil
import ctypes
import os

from PyQt5.QtWidgets import QMessageBox, QFileDialog
from view.main_flow import MainFlow

class Places:
    NOT_REMOVAL, NOT_DEFINED, MOUNTED, NOT_MOUNTED = range(4)

    def __init__(self, parent):
        self.conrtoller = parent
        self._view = parent.get_places_view()
        self._dbu = parent.get_db_utils()
        self._places = []
        self._curr_place = ()
        self._mount_point = ''

    def get_curr_place(self):
        return self._curr_place

    def get_mount_point(self):
        return self._mount_point

    def is_disk_mounted(self):
        """
        Has side effect - saves mount point in self._mount_point
        :return: NOT_DEFINED, NOT_REMOVAL, MOUNTED, NOT_MOUNTED
        """
        idx = self._view.currentIndex()
        place_info = self._places[idx][1]
        if not place_info:      # impossible to check if mounted
            return self.NOT_DEFINED

        loc = socket.gethostname()
        if place_info == loc:   # always mounted
            return self.NOT_REMOVAL

        self._mount_point = Places._get_mount_point(place_info)
        if self._mount_point:   # mount point exists
            return self.MOUNTED

        return self.NOT_MOUNTED

    @staticmethod
    def is_removable(device):
        parts = psutil.disk_partitions()
        removable = next(x.opts for x in parts if x.device == device)
        return removable == 'rw,removable'

    def populate_cb_places(self):
        self._view.blockSignals(True)
        self._view.clear()
        plc = self._dbu.select_other('PLACES')
        self._places = list(plc)
        if self._places:
            self._view.addItems((x[2] for x in self._places))

            loc = socket.gethostname()
            idx = next(i for i in range(0, len(self._places)) if self._places[i][1] == loc)

            self._curr_place = (idx, self._places[idx])
            self._view.setCurrentIndex(idx)

        self._view.blockSignals(False)

    def about_change_place(self, data):
        """
        :param data: tuple (index in view, current text in view)
        :return: None
        """
        prev_id = self._curr_place[0]
        idx = self._view.currentIndex()
        if data[0] >= len(self._places):
            self._add_place(data)
        else:
            self._change_place(data)
        if prev_id != self._curr_place[0]:
            self.conrtoller.on_change_data('dirTree', (self._curr_place[1][0],))

    def update_disk_info(self, root):
        """
        Update only if 1) info is missing (NOT_DEFINED)
        and if 2) the place is not registered yet in data base
        :param root: any path, used only volume - mount point
        :return: True / False
        """
        if self.is_disk_mounted() == self.NOT_DEFINED:
            disk_info = self._get_disk_info(root)

            if self.is_not_exist(disk_info):
                self._dbu.update_other('REMOVAL_DISK_INFO', (disk_info, self._curr_place[1][0]))
                self._curr_place = (self._curr_place[0],
                                    (self._curr_place[1][0], disk_info, self._curr_place[1][2]))
                self._places[self._curr_place[0]] = self._curr_place[1]
                return True

        return False

    def _get_disk_info(self, root):
        """
        :param root: any path, used only volume - mount point
        :return: label of disk if removal, otherwise - computer name
        """
        disk = psutil.os.path._getvolumepathname(root)

        if self.is_removable(disk):
            disk_info = self._get_vol_name(disk)  # disk label
        else:
            disk_info = socket.gethostname()  # computer name
        return disk_info

    def is_not_exist(self, disk_info):
        res = self._dbu.select_other('IS_EXIST', (disk_info,)).fetchone()
        return res is None

    def _change_place(self, data):
        """
        Check if selected place is available
        Ask for confirmation for switch to unavailable place/storage
        Save current item in self.curr_place if confirmed or available
        :param data: only first item is used, it contains current index
        :return: None
        """
        if self.is_disk_mounted() == self.NOT_MOUNTED:
            res = self._ask_switch_to_unavailable_storage(data)
            if res == 0:                # Ok button
                self._curr_place = (data[0], self._places[data[0]])
            elif res == 1:              # Remove button
                self._remove_current_place()
            else:                       # Cancel - return to prev.place
                self._view.blockSignals(True)
                self._view.setCurrentIndex(self._curr_place[0])
                self._view.blockSignals(False)
        else:                           # switches to new place silently
            self._curr_place = (data[0], self._places[data[0]])

    def _remove_current_place(self):
        idx = self._view.currentIndex()
        if self._not_in_dirs(self._places[idx][0]):
            self._view.blockSignals(True)
            self._view.removeItem(idx)
            self._dbu.delete_other('PLACES', (self._places[idx][0],))
            self._view.setCurrentIndex(self._curr_place[0])
            self._view.blockSignals(False)

    def _not_in_dirs(self, place_id):
        """
        Check if there is reference from Dirs table to place_id
        :param place_id:
        :return:
        """
        res = self._dbu.select_other('PLACE_IN_DIRS', (place_id,)).fetchone()
        return res is None

    def _add_place(self, data):
        """
        :param data: tuple (index in view, current text in view)
        :return: None
        """
        res = self._ask_rename_or_new()
        if res == 0:                # add new
            self._add_new(data)
        elif res == 1:              # rename
            self._rename_place((self._curr_place[0], data[1]))
        else:                       # cancel
            self._view.blockSignals(True)
            self._view.removeItem(self._view.currentIndex())
            self._view.setCurrentIndex(self._curr_place[0])
            self._view.blockSignals(False)

    def _add_new(self, data):
        """
        :param data: tuple (index in view, current text in view)
        :return: None
        """
        jj = self._dbu.insert_other('PLACES', ('', data[1]))
        self._curr_place = (self._view.currentIndex(), (jj, '', data[1]))
        self._places.append(self._curr_place[1])
        root = QFileDialog.getExistingDirectory(parent=self._view,
                                                caption='Select root folder')
        if root:
            self.update_disk_info(root)

    def _rename_place(self, data):
        """
        :param data: tuple (index in view, current text in view)
        :return: None
        """
        self._curr_place = (self._curr_place[0],
                            (self._curr_place[1][0],
                             self._curr_place[1][1], data[1]))
        self._places[self._curr_place[0]] = self._curr_place[1]

        self._view.blockSignals(True)

        self._view.clear()

        self._view.addItems((x[2] for x in self._places))

        self._view.setCurrentIndex(self._curr_place[0])
        self._view.setCurrentText(data[1])

        self._view.blockSignals(False)

        self._dbu.update_other('PLACES', (data[1], self._curr_place[0]))

    @staticmethod
    def _ask_rename_or_new():
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.addButton('Add new', QMessageBox.ActionRole)
        box.addButton('Rename', QMessageBox.ActionRole)
        box.addButton('Cancel', QMessageBox.RejectRole)
        res = box.exec_()
        return res

    @staticmethod
    def _ask_switch_to_unavailable_storage(data):
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.setText('The storage {} is not available'.format(data[1]))
        box.addButton('Ok', QMessageBox.AcceptRole)
        box.addButton('Remove', QMessageBox.ActionRole)
        box.addButton('Cancel', QMessageBox.RejectRole)
        res = box.exec_()
        return res

    @staticmethod
    def _get_mount_point(place_info):
        parts = psutil.disk_partitions()
        removables = (x.mountpoint for x in parts if x.opts == 'rw,removable')

        for mount_point in removables:
            if place_info == Places._get_vol_name(mount_point):
                return mount_point
        return ''

    @staticmethod
    def _get_vol_name(mount_point):
        """
        Only for windows
        :param mount_point:
        :return: volume label
        """
        if os.name == "nt":
            kernel32 = ctypes.windll.kernel32
            volume_name_buffer = ctypes.create_unicode_buffer(1024)
            if kernel32.GetVolumeInformationW(ctypes.c_wchar_p(mount_point),
                                              volume_name_buffer,
                                              ctypes.sizeof(volume_name_buffer),
                                              None, None, None, None, 0) > 0:
                return volume_name_buffer.value
            return ''
        else:
            return ''
