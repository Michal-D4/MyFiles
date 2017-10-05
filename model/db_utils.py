import sqlite3

Selects = {'TREE': ('''WITH x(DirID, Path, ParentID, level) AS
 (SELECT DirID, Path, ParentID, 0 as level''',
            'FROM Dirs WHERE DirID = {}',
            'FROM Dirs WHERE ParentID = {}',
            '''UNION ALL
 SELECT t.DirID, t.Path, t.ParentID, x.level + 1 as lvl
 FROM x INNER JOIN Dirs AS t
 ON t.ParentID = x.DirID''',
            'and lvl <= {} ) SELECT * FROM x;',
            ') SELECT * FROM x;'
                    ),
        'PLACES': 'select * from myPlaces;',
           'EXT': 'select * from Extensions'
           }

Insert = {'PLACES': '''insert into myPlaces (myPlaceId, myPlace, Title)
 values(?, ?, ?);'''}

Update = {'PLACES': 'update myPlaces set Title = ? where myPlaceId = ?;',
          }


TREE_SQL = ('''WITH x(DirID, Path, ParentID, level) AS
 (SELECT DirID, Path, ParentID, 0 as level''',
            'FROM Dirs WHERE DirID = {}',
            'FROM Dirs WHERE ParentID = {}',
            '''UNION ALL
 SELECT t.DirID, t.Path, t.ParentID, x.level + 1 as lvl
 FROM x INNER JOIN Dirs AS t
 ON t.ParentID = x.DirID''',
            'and lvl <= {} ) SELECT * FROM x;',
            ') SELECT * FROM x;'
            )

PLACES = 'select * from myPlaces;'

class DBUtils:
    """Different methods for select, update and insert information into/from DB"""

    # def __init__(self, connection_string='test_database.sqlite'):
    #     self.connect = sqlite3.connect(connection_string,
    #                                 detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    def __init__(self, connection):
        self.conn = connection
        self.curs = connection.cursor()

    def dir_tree_select(self, dir_id, level):
        """
        Select tree of directories starting from dir_id up to level
        :param dir_id: - starting directory, 0 - from root
        :param level: - max level of tree, 0 - all levels
        :return: cursor of directories
        """
        sql = self.generate_sql(dir_id, level)

        self.curs.execute(sql)

        return self.curs

    def generate_sql(self, dir_id, level):
        tmp = (TREE_SQL[0], TREE_SQL[1].format(dir_id), TREE_SQL[2].format(dir_id),
               TREE_SQL[3], TREE_SQL[4].format(level), TREE_SQL[5])
        cc = [(0, 2, 3, 5),
              (0, 1, 3, 5),
              (0, 2, 3, 4),
              (0, 1, 3, 4)]
        i = (level > 0)*2 + (dir_id > 0)
        sql = ' '.join([tmp[j] for j in cc[i]])
        return sql

    def select_other(self, sql):
        print(Selects[sql])
        self.curs.execute(Selects[sql])
        return self.curs

    def insert_other(self, sql, data):
        print(Insert[sql])
        print(data)
        self.curs.execute(Insert[sql], data)
        self.conn.commit()

    def update_other(self, sql, data):
        print(Update[sql])
        print('DBUtils.update_other data:', data)
        self.curs.execute(Update[sql], data)
        self.conn.commit()
