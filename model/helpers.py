# model/helpers.py


def get_file_extension(file_name):
    if file_name.rfind('.') > 0:
        return str.lower(file_name.rpartition('.')[2])
    return ''

