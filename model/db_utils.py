Selects = {'TREE': ('''WITH x(DirID, Path, ParentID, level) AS
 (SELECT DirID, Path, ParentID, 0 as level''',
                    'FROM Dirs WHERE DirID = {}',
                    'FROM Dirs WHERE ParentID = {}',
                    '''UNION ALL
 SELECT t.DirID, t.Path, t.ParentID, x.level + 1 as lvl
 FROM x INNER JOIN Dirs AS t
 ON t.ParentID = x.DirID''',
                    'and lvl <= {} ) SELECT * FROM x;',
                    ') SELECT * FROM x order by ParentID desc, Path;'),
           'PLACES': 'select * from myPlaces;',
           'EXT': '''select ExtID+1000, Extension as title, GroupID as ID from Extensions 
           UNION select GroupID, GroupName as title, 0 as ID from ExtGroups
           order by ID desc, title;''',
           'HAS_EXT': 'select count(*) from Extensions where Extension = ?;',
           'EXT_IN_FILES': 'select FileID from Files where ExtID = ?;'}

Insert = {'PLACES': '''insert into myPlaces (myPlaceId, myPlace, Title) values(?, ?, ?);''',
          'EXT': '''insert into Extensions (Extension, GroupID) values (:ext, 0);''', }

Update = {'PLACES': 'update myPlaces set Title = ? where myPlaceId = ?;', }

Delete = {'EXT': 'delete from Extensions where ExtID = ?;', }

class DBUtils:
    """Different methods for select, update and insert information into/from DB"""

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
        tree_sql = Selects['TREE']
        tmp = (tree_sql[0], tree_sql[1].format(dir_id), tree_sql[2].format(dir_id),
               tree_sql[3], tree_sql[4].format(level), tree_sql[5])
        cc = [(0, 2, 3, 5),
              (0, 1, 3, 5),
              (0, 2, 3, 4),
              (0, 1, 3, 4)]
        i = (level > 0)*2 + (dir_id > 0)
        sql = ' '.join([tmp[j] for j in cc[i]])
        return sql

    def select_other(self, sql, params=()):
        self.curs.execute(Selects[sql], params)
        return self.curs

    def insert_other(self, sql, data):
        self.curs.execute(Insert[sql], data)
        jj = self.curs.lastrowid
        self.conn.commit()
        return jj

    def update_other(self, sql, data):
        print(Update[sql])
        print('DBUtils.update_other data:', data)
        self.curs.execute(Update[sql], data)
        self.conn.commit()

    def delete_other(self, sql, data):
        print(Delete[sql])
        print('DBUtils.delete_other data:', data)
        self.curs.execute(Delete[sql], data)
        self.conn.commit()
