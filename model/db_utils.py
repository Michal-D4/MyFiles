Selects = {'TREE':
               ('WITH x(DirID, Path, ParentID, level) AS (SELECT DirID, Path, ParentID, 0 as level',
                'FROM Dirs WHERE DirID = {} and PlaceId = {}',
                'FROM Dirs WHERE ParentID = {} and PlaceId = {}',
                ' '.join(('UNION ALL SELECT t.DirID, t.Path, t.ParentID,',
                          'x.level + 1 as lvl FROM x INNER JOIN Dirs AS t',
                          'ON t.ParentID = x.DirID')),
                'and lvl <= {}) SELECT * FROM x order by ParentID desc, Path;',
                ') SELECT * FROM x order by ParentID desc, Path;'),
           'PLACES': 'select * from Places;',   # PlaceId starts with 0, where as other IDs with 1
           'IS_EXIST': 'select * from Places where Place = ?;',
           'EXT': ' '.join(('select ExtID+1000, Extension as title, GroupID',
                            'as ID from Extensions UNION select GroupID,',
                            'GroupName as title, 0 as ID from ExtGroups',
                            'order by ID desc, title;')),
           'HAS_EXT': 'select count(*) from Extensions where Extension = ?;',
           'EXT_IN_FILES': 'select FileID from Files where ExtID = ?;',
           'TAGS': 'select Tag, TagID from Tags order by Tag;',
           'AUTHORS': 'select Author, AuthorID from Authors order by Author;',
           'PLACE_IN_DIRS': 'select DirId from Dirs where PlaceId = ?;',
           'FILE_TAGS': '',
           'FILE_AUTHORS': ' '.join(('select Author from Authors where AuthorID in',
                                     'select AuthorID from FileAuthor where FileID = ?;')),
           'FILE_COMMENT': '',
           'FILES_CUR_DIR': ' '.join(('select FileID, DirID, CommentID, FileName, Year,',
                                      'Pages, Size from Files where DirId = ?;'))
           }

Insert = {'PLACES': 'insert into Places (Place, Title) values(?, ?);',
          'EXT': 'insert into Extensions (Extension, GroupID) values (:ext, 0);',
          'TAGS': 'insert into Tags (Tag) values (:tag);',
          'AUTHORS': 'insert into Authors (Author) values (:author);'}

Update = {'PLACES': 'update Places set Title = ? where PlaceId = ?;',
          'REMOVAL_DISK_INFO': 'update Places set Place = ? where PlaceId = ?;'}

Delete = {'EXT': 'delete from Extensions where ExtID = ?;',
          'PLACES': 'delete from Places where PlaceId = ?;'}

class DBUtils:
    """Different methods for select, update and insert information into/from DB"""

    def __init__(self, connection):
        self.conn = connection
        self.curs = connection.cursor()

    def dir_tree_select(self, dir_id, level, place_id):
        """
        Select tree of directories starting from dir_id up to level
        :param dir_id: - starting directory, 0 - from root
        :param level: - max level of tree, 0 - all levels
        :return: cursor of directories
        """
        sql = self.generate_sql(dir_id, level, place_id)

        self.curs.execute(sql)

        return self.curs

    def generate_sql(self, dir_id, level, place_id):
        tree_sql = Selects['TREE']
        tmp = (tree_sql[0], tree_sql[1].format(dir_id, place_id),
               tree_sql[2].format(dir_id, place_id), tree_sql[3],
               tree_sql[4].format(level), tree_sql[5])
        cc = [(0, 2, 3, 5),
              (0, 1, 3, 5),
              (0, 2, 3, 4),
              (0, 1, 3, 4)]
        i = (level > 0)*2 + (dir_id > 0)    # 00 = 0, 01 = 1, 10 = 2, 11 = 3
        sql = ' '.join([tmp[j] for j in cc[i]])
        return sql

    def select_other(self, sql, params=()):
        # print('|---> select_other', sql, params)
        # print(Selects[sql])
        self.curs.execute(Selects[sql], params)
        return self.curs

    def insert_other(self, sql, data):
        # print(Insert[sql], data)
        self.curs.execute(Insert[sql], data)
        jj = self.curs.lastrowid
        self.conn.commit()
        return jj

    def update_other(self, sql, data):
        # print('DBUtils.update_other data:', data)
        # print(Update[sql])
        self.curs.execute(Update[sql], data)
        self.conn.commit()

    def delete_other(self, sql, data):
        # print('DBUtils.delete_other data:', data)
        # print(Delete[sql])
        self.curs.execute(Delete[sql], data)
        self.conn.commit()
