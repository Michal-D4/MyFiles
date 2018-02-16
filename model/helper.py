# model/helpers.py
import os
from collections import namedtuple
from PyQt5.QtGui import QFontDatabase

# Shared things
# immutable
EXT_ID_INCREMENT = 100000
Fields = namedtuple('Fields', 'fields headers indexes')
MimeTypes = ["application/x-folder-list",
             "application/x-file-list",
             "application/x-folder-list/virtual"]
DropNoAction, DropCopyFolder, DropMoveFolder, DropCopyFile, DropMoveFile = range(5)
real_folder, file, virtual_folder = range(3)

# mutable
Shared = {'AppFont': QFontDatabase.systemFont(QFontDatabase.GeneralFont),
          'AppWindow': None,
          'Controller': None,
          'DB choice dialog': None,
          'DB connection': None,
          'DB utility': None}


def get_file_extension(file_name):
    if file_name.rfind('.') > 0:
        return str.lower(file_name.rpartition('.')[2])
    return ''


def get_parent_dir(path):
    return path.rpartition(os.altsep)[0]

