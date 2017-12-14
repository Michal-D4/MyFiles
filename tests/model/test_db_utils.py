import sqlite3
import unittest

from model.db_utils import *
from unittest.mock import Mock
from model.utils import create_db
from model.utils import load_db_data

LOAD_DATA = (r'f:\Docs\Box\Блок.docx',
             r'f:\Docs\A.Блок.txt',
             r'f:\Docs\Python\main\on.docx',
             r'f:\Docs\Python\main.docx',
             r'd:\Doc2\Java\some.txt',
             r'f:\Docs\Python\А.Блок.docx')


class TestDDBUtils(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(':memory:')

        mock_socket = Mock()
        create_db.socket = mock_socket
        mock_socket.gethostname.return_value = 'My place'
        create_db.create_all_objects(self.connection)

        load_db = load_db_data.LoadDBData(self.connection, ('place', 'title'))
        load_db.load_data(LOAD_DATA)

        self.dbu = DBUtils()
        self.dbu.set_connection(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_generate_sql_0_0(self):
        sql = self.dbu.generate_sql(0, 0, 0)
        self.assertEqual(sql, ' '.join(('WITH x(DirID, Path, ParentID, level) AS',
                                        '(SELECT DirID, Path, ParentID, 0 as level',
                                        'FROM Dirs WHERE ParentID = 0 and PlaceId = 0',
                                        'UNION ALL SELECT t.DirID, t.Path, t.ParentID,',
                                        'x.level + 1 as lvl FROM x INNER JOIN Dirs AS t',
                                        'ON t.ParentID = x.DirID ) SELECT * FROM x order',
                                        'by ParentID desc, Path;')))

    def test_generate_sql_0_1(self):
        sql = self.dbu.generate_sql(0, 1, 0)
        self.assertEqual(sql, ' '.join(('WITH x(DirID, Path, ParentID, level) AS',
                                        '(SELECT DirID, Path, ParentID, 0 as level',
                                        'FROM Dirs WHERE ParentID = 0 and PlaceId = 0',
                                        'UNION ALL SELECT t.DirID, t.Path, t.ParentID,',
                                        'x.level + 1 as lvl FROM x INNER JOIN Dirs AS t',
                                        'ON t.ParentID = x.DirID and lvl <= 1)',
                                        'SELECT * FROM x order by ParentID desc, Path;')))

    def test_generate_sql_1_0(self):
        sql = self.dbu.generate_sql(1, 0, 0)
        self.assertEqual(sql, ' '.join(('WITH x(DirID, Path, ParentID, level) AS',
                                        '(SELECT DirID, Path, ParentID, 0 as level',
                                        'FROM Dirs WHERE DirID = 1 and PlaceId = 0',
                                        'UNION ALL SELECT t.DirID, t.Path, t.ParentID,',
                                        'x.level + 1 as lvl FROM x INNER JOIN Dirs',
                                        'AS t ON t.ParentID = x.DirID ) SELECT *',
                                        'FROM x order by ParentID desc, Path;')))

    def test_generate_sql_1_1(self):
        sql = self.dbu.generate_sql(1, 1, 0)
        self.assertEqual(sql, ' '.join(('WITH x(DirID, Path, ParentID, level) AS',
                                        '(SELECT DirID, Path, ParentID, 0 as level',
                                        'FROM Dirs WHERE DirID = 1 and PlaceId = 0',
                                        'UNION ALL SELECT t.DirID, t.Path, t.ParentID,',
                                        'x.level + 1 as lvl FROM x INNER JOIN Dirs AS t',
                                        'ON t.ParentID = x.DirID and lvl <= 1)',
                                        'SELECT * FROM x order by ParentID desc, Path;')))

    def test_dir_tree_select_level_0_root_1(self):
        cursor = self.dbu.dir_tree_select(2, 0, 1)
        self.assertIsNotNone(cursor)

        aa = tuple(cursor)
        self.assertEqual(aa, ((3, 'f:\\Docs\\Python\\main', 4, 2),
                              (1, 'f:\\Docs\\Box', 2, 1),
                              (4, 'f:\\Docs\\Python', 2, 1),
                              (2, 'f:\\Docs', 0, 0)))

    def test_dir_tree_select_level_1_root_1(self):
        cursor = self.dbu.dir_tree_select(2, 1, 1)
        self.assertIsNotNone(cursor)

        aa = tuple(cursor)
        self.assertEqual(aa, ((1, 'f:\\Docs\\Box', 2, 1),
                              (4, 'f:\\Docs\\Python', 2, 1),
                              (2, 'f:\\Docs', 0, 0)))

    def test_dir_tree_select_level_0_root_0(self):
        cursor = self.dbu.dir_tree_select(0, 0, 1)
        self.assertIsNotNone(cursor)

        aa = tuple(cursor)
        self.assertEqual(aa, ((3, 'f:\\Docs\\Python\\main', 4, 2),
                              (1, 'f:\\Docs\\Box', 2, 1),
                              (4, 'f:\\Docs\\Python', 2, 1),
                              (5, 'd:\\Doc2\\Java', 0, 0),
                              (2, 'f:\\Docs', 0, 0)))

    def test_dir_tree_select_level_1_root_0(self):
        cursor = self.dbu.dir_tree_select(0, 1, 1)
        self.assertIsNotNone(cursor)

        aa = tuple(cursor)
        self.assertEqual(aa, ((1, 'f:\\Docs\\Box', 2, 1),
                              (4, 'f:\\Docs\\Python', 2, 1),
                              (5, 'd:\\Doc2\\Java', 0, 0),
                              (2, 'f:\\Docs', 0, 0))
)

    def test_select_other_PLACES(self):
        cursor = self.dbu.select_other('PLACES')
        aa = tuple(cursor)
        self.assertEqual(aa, ((0, 'My place', 'My place'), (1, 'place', 'title')),
                         msg='The 2 places inserted on SetUp')

    def test_select_other_EXT(self):
        cursor = self.dbu.select_other('EXT')
        aa = tuple(cursor)
        self.assertEqual(aa, ((1001, 'docx', 0), (1002, 'txt', 0)))

    def test_select_other_HAS_EXT(self):
        cursor = self.dbu.select_other('HAS_EXT', ('docx', ))
        aa = tuple(cursor)
        self.assertEqual(aa, ((1,),))

        cursor = self.dbu.select_other('HAS_EXT', ('dummy', ))
        aa = tuple(cursor)
        self.assertEqual(aa, ((0,),))

    def test_select_other_EXT_IN_FILES(self):
        cursor = self.dbu.select_other('EXT_IN_FILES', (1, ))
        aa = tuple(cursor)
        self.assertEqual(aa, ((1,), (3,), (4,), (6,)))

        cursor = self.dbu.select_other('EXT_IN_FILES', (0, ))
        aa = tuple(cursor)
        self.assertEqual(aa, ())

    def test_select_other_IS_EXIST(self):
        cursor = self.dbu.select_other('IS_EXIST', ('My place', ))
        aa = tuple(cursor)
        self.assertEqual(aa, ((0, 'My place', 'My place'),),
                         msg="'My place' is s first place inserted on SetUp")

        cursor = self.dbu.select_other('IS_EXIST', ('Your place', ))
        aa = tuple(cursor)
        self.assertEqual(aa, ())

    def test_insert_other_PLACES(self):
        res = self.dbu.insert_other('PLACES', ('new disk', 'new place'))
        self.assertEqual(res, 2, msg='2 places inserted on SetUp, must be 2, but not!!!')

    def test_insert_select_other_TAGS(self):
        cursor = self.dbu.select_other('TAGS')
        aa = tuple(cursor)
        self.assertEqual(aa, ())

        res = self.dbu.insert_other('TAGS', ('tag1',))
        self.assertEqual(res, 1, msg='First record, but returned {}'.format(res))
        cursor = self.dbu.select_other('TAGS')
        aa = tuple(cursor)
        self.assertEqual(aa, (('tag1', 1),))

        res = self.dbu.insert_other('TAGS', ('tag2',))
        self.assertEqual(res, 2, msg='Second record, but returned {}'.format(res))
        cursor = self.dbu.select_other('TAGS')
        aa = tuple(cursor)
        self.assertEqual(aa, (('tag1', 1), ('tag2', 2)))

    def test_insert_select_other_AUTHORS(self):
        cursor = self.dbu.select_other('AUTHORS')
        aa = tuple(cursor)
        self.assertEqual(aa, ())

        res = self.dbu.insert_other('AUTHORS', ('Author 1',))
        self.assertEqual(res, 1, msg='First record, but returned {}'.format(res))
        cursor = self.dbu.select_other('AUTHORS')
        aa = tuple(cursor)
        self.assertEqual(aa, (('Author 1', 1),))

        res = self.dbu.insert_other('AUTHORS', ('Author 2',))
        self.assertEqual(res, 2, msg='Second record, but returned {}'.format(res))
        cursor = self.dbu.select_other('AUTHORS')
        aa = tuple(cursor)
        self.assertEqual(aa, (('Author 1', 1), ('Author 2', 2)))


if __name__ == '__main__':
    unittest.main()
