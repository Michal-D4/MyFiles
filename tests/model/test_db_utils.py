import unittest

from model.db_utils import *
# from unittest.mock import MagicMock, Mock
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
        create_db.create_all_objects(self.connection)

        load_db = load_db_data.LoadDBData(self.connection, (0, 'place', 'title'))

        load_db.load_data(LOAD_DATA)

        self.dbu = DBUtils(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_generate_sql_0_0(self):
        sql = self.dbu.generate_sql(0, 0)
        self.assertEqual(sql, '''WITH x(DirID, Path, ParentID, level) AS
 (SELECT DirID, Path, ParentID, 0 as level FROM Dirs WHERE ParentID = 0 UNION ALL
 SELECT t.DirID, t.Path, t.ParentID, x.level + 1 as lvl
 FROM x INNER JOIN Dirs AS t
 ON t.ParentID = x.DirID ) SELECT * FROM x;''')

    def test_generate_sql_0_1(self):
        sql = self.dbu.generate_sql(0, 1)
        self.assertEqual(sql, '''WITH x(DirID, Path, ParentID, level) AS
 (SELECT DirID, Path, ParentID, 0 as level FROM Dirs WHERE ParentID = 0 UNION ALL
 SELECT t.DirID, t.Path, t.ParentID, x.level + 1 as lvl
 FROM x INNER JOIN Dirs AS t
 ON t.ParentID = x.DirID and lvl <= 1 ) SELECT * FROM x;''')

    def test_generate_sql_1_0(self):
        sql = self.dbu.generate_sql(1, 0)
        self.assertEqual(sql, '''WITH x(DirID, Path, ParentID, level) AS
 (SELECT DirID, Path, ParentID, 0 as level FROM Dirs WHERE DirID = 1 UNION ALL
 SELECT t.DirID, t.Path, t.ParentID, x.level + 1 as lvl
 FROM x INNER JOIN Dirs AS t
 ON t.ParentID = x.DirID ) SELECT * FROM x;''')

    def test_generate_sql_1_1(self):
        sql = self.dbu.generate_sql(1, 1)
        self.assertEqual(sql, '''WITH x(DirID, Path, ParentID, level) AS
 (SELECT DirID, Path, ParentID, 0 as level FROM Dirs WHERE DirID = 1 UNION ALL
 SELECT t.DirID, t.Path, t.ParentID, x.level + 1 as lvl
 FROM x INNER JOIN Dirs AS t
 ON t.ParentID = x.DirID and lvl <= 1 ) SELECT * FROM x;''')

    def test_dir_tree_select_level_0_root_1(self):
        '''level = 0 means all levels'''
        cursor = self.dbu.dir_tree_select(2, 0)
        self.assertIsNotNone(cursor)

        aa = tuple(cursor)
        self.assertEqual(aa, ((2, 'f:\\Docs', 0, 0),
                              (1, 'f:\\Docs\\Box', 2, 1),
                              (4, 'f:\\Docs\\Python', 2, 1),
                              (3, 'f:\\Docs\\Python\\main', 4, 2)))

    def test_dir_tree_select_level_1_root_1(self):
        cursor = self.dbu.dir_tree_select(2, 1)
        self.assertIsNotNone(cursor)

        aa = tuple(cursor)
        self.assertEqual(aa, ((2, 'f:\\Docs', 0, 0),
                              (1, 'f:\\Docs\\Box', 2, 1),
                              (4, 'f:\\Docs\\Python', 2, 1)))

    def test_dir_tree_select_level_0_root_0(self):
        '''level = 0 means all levels'''
        cursor = self.dbu.dir_tree_select(0, 0)
        self.assertIsNotNone(cursor)

        aa = tuple(cursor)
        self.assertEqual(aa, ((2, 'f:\\Docs', 0, 0),
                              (5, 'd:\\Doc2\\Java', 0, 0),
                              (1, 'f:\\Docs\\Box', 2, 1),
                              (4, 'f:\\Docs\\Python', 2, 1),
                              (3, 'f:\\Docs\\Python\\main', 4, 2)))

    def test_dir_tree_select_level_1_root_0(self):
        cursor = self.dbu.dir_tree_select(0, 1)
        self.assertIsNotNone(cursor)

        aa = tuple(cursor)
        self.assertEqual(aa, ((2, 'f:\\Docs', 0, 0),
                              (5, 'd:\\Doc2\\Java', 0, 0),
                              (1, 'f:\\Docs\\Box', 2, 1),
                              (4, 'f:\\Docs\\Python', 2, 1)))


if __name__ == '__main__':
    unittest.main()
