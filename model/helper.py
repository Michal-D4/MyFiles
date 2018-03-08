# model/helper.py
import os
from collections import namedtuple
from PyQt5.QtGui import QFontDatabase

# Shared things
# immutable
EXT_ID_INCREMENT = 100000
Fields = namedtuple('Fields', 'fields headers indexes')

real_folder, virtual_folder, file_real, file_virtual = range(4)
MimeTypes = ["application/x-folder-list",
             "application/x-folder-list/virtual",
             "application/x-file-list",
             "application/x-file-list/virtual"]

DropNoAction, DropCopyFolder, DropMoveFolder, DropCopyFile, DropMoveFile = (0, 1, 2, 4, 8)


# mutable
Shared = {'AppFont': QFontDatabase.systemFont(QFontDatabase.GeneralFont),
          'AppWindow': None,
          'Controller': None,
          'DB choice dialog': None,
          'DB connection': None,
          'DB utility': None,
          'Places': None}


def get_file_extension(file_name):
    if file_name.rfind('.') > 0:
        return str.lower(file_name.rpartition('.')[2])
    return ''


def get_parent_dir(path):
    return path.rpartition(os.altsep)[0]


def show_message(message, time=3000):
    Shared['AppWindow'].ui.statusbar.showMessage(message, time)

