# model/helpers.py
import os
from collections import namedtuple

Fields = namedtuple('Fields', 'fields headers indexes')
MimeTypes = ["application/x-folder-list", "application/x-file-list"]


def get_file_extension(file_name):
    if file_name.rfind('.') > 0:
        return str.lower(file_name.rpartition('.')[2])
    return ''


def get_parent_dir(path):
    return path.rpartition(os.altsep)[0]

