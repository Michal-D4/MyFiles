# controller/places.py

import socket
import psutil
import ctypes
import os

from PyQt5.QtWidgets import QMessageBox, QFileDialog


class Places:
    NOT_REMOVAL, NOT_DEFINED, MOUNTED, NOT_MOUNTED = (1, 2, 4, 8)

    def __init__(self, parent):
        self.controller = parent
        self._view = parent.get_places_view()
        self._dbu = parent.get_db_utils()
        self._places = []           # list of (PlaceId, Place, Title)
        self._curr_place = ()       # (index, (PlaceId, Place, Title), place_state)
        self._mount_point = ''

    def get_curr_place(self):
        return self._curr_place

    def get_mount_point(self):
        return self._mount_point

    def get_disk_state(self):
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
        """
        :param device:  Disk letter / mount point
        :return: bool
        """
        parts = psutil.disk_partitions()
        removable = next(x.opts for x in parts if x.device == device)
        return removable == 'rw,removable'

    def populate_cb_places(self):
        self._view.blockSignals(True)
        self._view.clear()
        plc = self._dbu.select_other('PLACES').fetchall()
        self._places = plc
        if self._places:
            self._view.addItems((x[2] for x in self._places))

            loc = socket.gethostname()
            try:
                idx = next(i for i in range(0, len(self._places)) if self._places[i][1] == loc)
            except StopIteration:
                idx = -1

            if idx >= 0:
                self._curr_place = (idx, self._places[idx], Places.NOT_REMOVAL)
                self._view.setCurrentIndex(idx)
            else:
                self._curr_place = (0, plc[0], Places.NOT_DEFINED)

        self._view.blockSignals(False)

    def about_change_place(self):
        """
        :param data: tuple (index in view, current text in view)
        :return: None
        """
        prev_id = self._curr_place[0]
        idx = self._view.currentIndex()
        place_title = self._view.currentText()
        if idx >= len(self._places):
            self._add_place((idx, place_title))
        else:
            self._change_place((idx, place_title))
        if prev_id != self._curr_place[0]:
            self.controller.on_change_data('dirTree')

    def update_place_name(self, root):
        """
        Update only if 1) info is missing (NOT_DEFINED)
        and if 2) the place is not registered yet in data base
        :param root: any path, used only "volume letter"/"mount point"
        :return: True / False
        """
        if self.get_disk_state() == self.NOT_DEFINED:
            place_info = self.get_place_name(root)

            if self.is_not_registered_place(place_info[0]):
                self._dbu.update_other('PLACE', (place_info[0], self._curr_place[1][0]))
                self._curr_place = (self._curr_place[0],
                                    (self._curr_place[1][0], place_info[0],
                                     self._curr_place[1][2]), place_info[1])
                self._places[self._curr_place[0]] = self._curr_place[1]
                return True

        return False

    def get_place_name(self, root):
        """
        :param root: any path, used only volume - mount point
        :return: label of disk if removal, otherwise - computer name
        """
        disk = psutil.os.path._getvolumepathname(root)

        if self.is_removable(disk):
            place_name = (self._get_vol_name(disk), self.MOUNTED)    # disk label
        else:
            place_name = (socket.gethostname(), self.NOT_REMOVAL)    # computer name
        return place_name

    def is_not_registered_place(self, place_name):
        """
        Check if exists in DB
        :param place_name: "name of computer" or "label of USB"
        :return: bool
        """
        res = self._dbu.select_other('IS_EXIST', (place_name,)).fetchone()
        return res is None

    def _change_place(self, data):
        """
        Check if selected place is available
        Ask for confirmation for switch to unavailable place/storage
        Save current item in self.curr_place if confirmed or available
        :param data: (current index in combobox, text of current item - Title)
        :return: None
        """
        if self.get_disk_state() == self.NOT_MOUNTED:
            res = self._ask_switch_to_unavailable_storage(data)
            if res == 0:                # Ok button
                self._curr_place = (data[0], self._places[data[0]], self.NOT_MOUNTED)
            elif res == 1:              # Remove button
                self._remove_current_place()
            else:                       # Cancel - return to prev.place
                self._view.blockSignals(True)
                self._view.setCurrentIndex(self._curr_place[0])
                self._view.blockSignals(False)
        else:                           # switches to new place silently
            print('|---> _change_place - disk state:', self.get_disk_state())
            self._curr_place = (data[0], self._places[data[0]], self.get_disk_state())

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
        :param place_id: PlaceId from DB
        :return: bool
        """
        res = self._dbu.select_other('PLACE_IN_DIRS', (place_id,)).fetchone()
        return res is None

    def _add_place(self, data):
        """
        :param data: (index in combobox, current text in combobox)
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
        :param data: (index in combobox, current text in combobox)
        :return: None
        """
        jj = self._dbu.insert_other('PLACES', ('', data[1]))
        self._curr_place = (self._view.currentIndex(), (jj, '', data[1]), self.NOT_DEFINED)
        self._places.append(self._curr_place[1])
        root = QFileDialog.getExistingDirectory(parent=self._view,
                                                caption='Select root folder')
        if root:
            self.update_place_name(root)

    def _rename_place(self, data):
        """
        :param data: (index in combobox, current text in combobox)
        :return: None
        """
        self._curr_place = (self._curr_place[0],
                            (self._curr_place[1][0],
                             self._curr_place[1][1], data[1]),
                            self._curr_place[2])
        self._places[self._curr_place[0]] = self._curr_place[1]

        self._view.blockSignals(True)

        self._view.clear()

        self._view.addItems((x[2] for x in self._places))

        self._view.setCurrentIndex(self._curr_place[0])
        self._view.setCurrentText(data[1])

        self._view.blockSignals(False)

        self._dbu.update_other('PLACE_TITLE', (data[1], self._curr_place[1][0]))

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
    def _get_mount_point(place_name):
        """
        Get mount point for removal place
        :param place_name: "computer name" or "USB label"
        :return: mount_point
        """
        parts = psutil.disk_partitions()
        removables = (x.mountpoint for x in parts if x.opts == 'rw,removable')

        for mount_point in removables:
            if place_name == Places._get_vol_name(mount_point):
                return mount_point.split(os.sep)[0]
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
