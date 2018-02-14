# model/helpers.py
import os
from collections import namedtuple
from PyQt5.QtGui import QFontDatabase

Fields = namedtuple('Fields', 'fields headers indexes')
MimeTypes = ["application/x-folder-list",
             "application/x-file-list",
             "application/x-folder-list/can-move"]
opt = {'AppFont': QFontDatabase.systemFont(QFontDatabase.GeneralFont)}
# AppFont = QFontDatabase.systemFont(QFontDatabase.GeneralFont)


def get_file_extension(file_name):
    if file_name.rfind('.') > 0:
        return str.lower(file_name.rpartition('.')[2])
    return ''


def get_parent_dir(path):
    return path.rpartition(os.altsep)[0]

