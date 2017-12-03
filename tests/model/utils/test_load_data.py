import unittest
import sqlite3

from unittest.mock import Mock

from model.utils import create_db
from model.utils import load_db_data

LOAD_DATA = (r'f:\Docs\Box\Блок.docx',
             r'f:\Docs\A.Блок.txt',
             r'f:\Docs\Python\main.docx',
             r'd:\Doc2\Java\some.txt',
             r'f:\Docs\Python\А.Блок.docx')

LOAD_DATA_IN_RANDOM_ORDER = (r'f:\Docs\Python\main.docx',
                             r'd:\Doc2\Java\fuf\dum.a',
                             r'd:\Doc2\Java\some.txt',
                             r'f:\Docs\Box\main\on.docx',
                             r'f:\Docs\triton\sec\boo.no',
                             r'f:\A.Блок.txt',
                             r'f:\Docs\Python\А.Блок.docx',
                             r'f:\Docs\Box\Блок.docx'
                             )

class TestLoadData2(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(':memory:')

        mock_socket = Mock()
        create_db.socket = mock_socket
        mock_socket.gethostname.return_value = 'My place'
        create_db.create_all_objects(self.connection)
        curr_place = ('test_place', 'Title')
        self.load_db = load_db_data.LoadDBData(self.connection, curr_place)

    def tearDown(self):
        self.connection.close()

    def test_search_closest_parent_empty_db(self):
        res = self.load_db.search_closest_parent(r'f:\Docs')
        self.assertTupleEqual(res, (0, ''), msg='Found parent in the empty DB')

    def test_search__closest_parent_found(self):
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs', 'id': '0',
                                 'placeId': self.load_db.place_id})
        res = self.load_db.search_closest_parent(r'f:\Docs\box')
        self.assertTupleEqual(res, (1, 'f:\\Docs'), msg='Not found when parent exist')

    def test_search__closest_parent_not_found(self):
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs', 'id': '0',
                                 'placeId': self.load_db.place_id})
        res = self.load_db.search_closest_parent(r'f:\Doc\box')
        self.assertTupleEqual(res, (0, ''), msg='Found when parent not exist')

    def test_search_closest_parent_already_exist(self):
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs', 'id': '0',
                                 'placeId': self.load_db.place_id})
        res = self.load_db.search_closest_parent(r'f:\Docs')
        self.assertTupleEqual(res, (1, 'f:\\Docs'), msg='Not found when the path exist')

    def test_parent_id_for_child(self):
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs', 'id': '0',
                                 'placeId': self.load_db.place_id})
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs\box\cox', 'id': '1',
                                 'placeId': self.load_db.place_id})
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs\box\fox', 'id': '1',
                                 'placeId': self.load_db.place_id})
        res = self.load_db.parent_id_for_child(r'f:\Docs\box')
        self.assertEqual(res, 1, 'Not found but exist')

    def test_parent_id_for_child_not_exist(self):
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Doc\box', 'id': '0',
                                 'placeId': self.load_db.place_id})
        res = self.load_db.parent_id_for_child(r'f:\Docs')
        self.assertEqual(res, -1, 'Not found but exist')

    def test_change_parent(self):
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs', 'id': '0',
                                 'placeId': self.load_db.place_id})
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs\box\cox', 'id': '1',
                                 'placeId': self.load_db.place_id})
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs\box\fox', 'id': '1',
                                 'placeId': self.load_db.place_id})
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs\box', 'id': '1',
                                 'placeId': self.load_db.place_id})

        self.load_db.change_parent(4, r'f:\Docs\box')

        test_data = ((1, r'f:\Docs', 1, 0),
                     (2, r'f:\Docs\box\cox', 1, 4),
                     (3, r'f:\Docs\box\fox', 1, 4),
                     (4, r'f:\Docs\box', 1, 1))
        res = self.connection.execute("select * from Dirs;")
        aa = tuple(res)
        self.assertTupleEqual(aa, test_data)

    def test_change_parent_special(self):
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs\box\cox', 'id': '0',
                                 'placeId': self.load_db.place_id})
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs\box\fox', 'id': '0',
                                 'placeId': self.load_db.place_id})
        self.connection.execute(load_db_data.INSERT_DIR,
                                {'path': r'f:\Docs\box', 'id': '0',
                                 'placeId': self.load_db.place_id})

        self.load_db.change_parent(3, r'f:\Docs\box')

        test_data = ((1, r'f:\Docs\box\cox', 1, 3),
                     (2, r'f:\Docs\box\fox', 1, 3),
                     (3, r'f:\Docs\box', 1, 0))
        res = self.connection.execute("select * from Dirs;")
        aa = tuple(res)
        self.assertTupleEqual(aa, test_data)

    def test_insert_dirs_first(self):
        jj = self.load_db.insert_dir(r'f:\Docs')
        self.assertEqual(jj, 1, 'The dir "f:\Docs" was not inserted')

        jj = self.load_db.insert_dir(r'f:\Docs')
        self.assertEqual(jj, 1, r'The dir "f:\Docs" was inserted twice')

    def test_insert_extension(self):
        jj = self.load_db.insert_extension('Блок.txt')
        self.assertEqual(jj, (1, 'txt'))

        curs = self.connection.cursor()
        curs.execute('select * from Extensions;')
        self.assertEqual(tuple(curs), ((1, 'txt', 0),))

    def test_insert_extension_file_without_extension(self):
        jj = self.load_db.insert_extension('Блок')
        self.assertEqual(jj, (0, ''))

        jj = self.load_db.insert_extension('.Блок')
        self.assertEqual(jj, (0, ''))
        curs = self.connection.cursor()

        curs.execute('select * from Extensions;')
        self.assertEqual(tuple(curs), ())

    def test_insert_extension_with_2_dots(self):
        jj = self.load_db.insert_extension('.Блок.txt')
        self.assertEqual(jj, (1, 'txt'))
        jj = self.load_db.insert_extension('A.Блок.txt')
        self.assertEqual(jj, (1, 'txt'))
        curs = self.connection.cursor()

    def test_insert_file(self):
        self.load_db.insert_file(1, LOAD_DATA[0])
        curs = self.connection.cursor()

        curs.execute('select FileID, DirID, FileName, ExtId from Files;')
        self.assertEqual(tuple(curs), ((1, 1, "Блок.docx", 1),))

        curs.execute('select * from Extensions;')
        self.assertEqual(tuple(curs), ((1, "docx", 0),))

    def test_insert_file_2_times(self):
        self.load_db.insert_file(1, LOAD_DATA[0])
        self.load_db.insert_file(1, LOAD_DATA[0])
        curs = self.connection.cursor()

        curs.execute('select * from Extensions;')
        self.assertEqual(tuple(curs), ((1, "docx", 0),))

        curs.execute('select FileID, DirID, FileName, ExtId from Files;')
        self.assertEqual(tuple(curs), ((1, 1, "Блок.docx", 1),))

    def test_insert_file_without_extension(self):
        self.load_db.insert_file(1, 'f:\Docs\Блок')
        self.load_db.insert_file(1, 'f:\Docs\.Блок')
        curs = self.connection.cursor()

        curs.execute('select * from Extensions;')
        self.assertEqual(tuple(curs), ())

        curs.execute('select FileID, DirID, FileName, ExtId from Files;')
        self.assertEqual(tuple(curs), ((1, 1, "Блок", 0), (2, 1, ".Блок", 0)))

    def test_insert_file_with_2_dots(self):
        self.load_db.insert_file(1, 'f:\Docs\.Блок.txt')
        self.load_db.insert_file(1, 'f:\Docs\A.Блок.txt')
        curs = self.connection.cursor()

        curs.execute('select * from Extensions;')
        self.assertEqual(tuple(curs), ((1, 'txt', 0),))

        curs.execute('select FileID, DirID, FileName, ExtId from Files;')
        self.assertEqual(tuple(curs), ((1, 1, ".Блок.txt", 1), (2, 1, "A.Блок.txt", 1)))

    def test_load_data_2_files(self):
        self.load_db.load_data(LOAD_DATA[:2])

        curs = self.connection.cursor()
        curs.execute('select * from Dirs;')
        self.assertEqual(tuple(curs),
                         ((1, 'f:\\Docs\\Box', 1, 2), (2, 'f:\\Docs', 1, 0)))

        curs.execute('select FileID, DirID, FileName, ExtID from Files;')
        self.assertEqual(tuple(curs),
                         ((1, 1, "Блок.docx", 1), (2, 2, 'A.Блок.txt', 2)))

    def test_load_data_5_files(self):
        self.load_db.load_data(LOAD_DATA)

        curs = self.connection.cursor()
        curs.execute('select * from Dirs;')
        aa = tuple(curs)
        self.assertEqual(aa,
                         ((1, r'f:\Docs\Box', 1, 2),
                          (2, r'f:\Docs', 1, 0),
                          (3, r'f:\Docs\Python', 1, 2),
                          (4, r'd:\Doc2\Java', 1, 0))
                         )

        curs.execute('select FileID, DirID, FileName, ExtID from Files;')
        aa = tuple(curs)
        self.assertEqual(aa,
                         ((1, 1, 'Блок.docx', 1),
                          (2, 2, 'A.Блок.txt', 2),
                          (3, 3, 'main.docx', 1),
                          (4, 4, 'some.txt', 2),
                          (5, 3, 'А.Блок.docx', 1)))

        curs.execute('select * from Extensions;')
        aa = tuple(curs)
        self.assertEqual(aa, ((1, 'docx', 0), (2, 'txt', 0)))

    def test_load_data_dirs_in_random_order(self):
        self.load_db.load_data(LOAD_DATA_IN_RANDOM_ORDER)

        curs = self.connection.cursor()
        curs.execute('select * from Dirs;')
        aa = tuple(curs)
        self.assertEqual(aa,
                         ((1, r'f:\Docs\Python', 1, 6),
                          (2, r'd:\Doc2\Java\fuf', 1, 3),
                          (3, r'd:\Doc2\Java', 1, 0),
                          (4, r'f:\Docs\Box\main', 1, 7),
                          (5, r'f:\Docs\triton\sec', 1, 6),
                          (6, 'f:', 1, 0),
                          (7, r'f:\Docs\Box', 1, 6))
                         )

