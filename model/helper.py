# model/helpers.py
import os
from collections import namedtuple
from PyQt5.QtGui import QFontDatabase

# Shared things

# immutable
Fields = namedtuple('Fields', 'fields headers indexes')
MimeTypes = {"real-folder": "application/x-folder-list",
             "file": "application/x-file-list",
             "virtual-folder": "application/x-folder-list/virtual"}
DropCopyFolder, DropMoveFolder, DropCopyFile, DropMoveFile = range(4)

# mutable
opt = {'AppFont': QFontDatabase.systemFont(QFontDatabase.GeneralFont)}


def get_file_extension(file_name):
    if file_name.rfind('.') > 0:
        return str.lower(file_name.rpartition('.')[2])
    return ''


def get_parent_dir(path):
    return path.rpartition(os.altsep)[0]

