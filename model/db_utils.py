# model/db_utils.py

Selects = {'TREE':
               ('WITH x(DirID, Path, ParentID, level) AS (SELECT DirID, Path, ParentID, 0 as level',
                'FROM Dirs WHERE DirID = {} and PlaceId = {}',
                'FROM Dirs WHERE ParentID = {} and PlaceId = {}',
                ' '.join(('UNION ALL SELECT t.DirID, t.Path, t.ParentID,',
                          'x.level + 1 as lvl FROM x INNER JOIN Dirs AS t',
                          'ON t.ParentID = x.DirID')),
                'and lvl <= {}) SELECT * FROM x order by ParentID desc, Path;',
                ') SELECT * FROM x order by ParentID desc, Path;'),
           'PLACES': 'select * from Places;',
           'PLACE_IN_DIRS': 'select DirId from Dirs where PlaceId = ?;',
           'IS_EXIST': 'select * from Places where Place = ?;',
           'EXT': ' '.join(('select Extension as title, ExtID+1000, GroupID',
                            'as ID from Extensions UNION select GroupName as title,',
                            'GroupID, 0 as ID from ExtGroups',
                            'order by ID desc, title;')),
           'HAS_EXT': 'select count(*) from Extensions where Extension = ?;',
           'EXT_IN_FILES': 'select FileID from Files where ExtID = ?;',
           'TAGS': 'select Tag, TagID from Tags order by Tag;',
           'FILE_TAGS': ' '.join(('select Tag, TagID from Tags where TagID in',
                                  '(select TagID from FileTag where FileID = ?);')),
           'TAG_FILES': 'select * from FileTag where TagID=:tag_id;',
           'TAGS_BY_NAME': 'select Tag, TagID from Tags where Tag in ("{}");',
           'TAG_FILE': 'select * from FileTag where FileID = ? and TagID =?;',
           'AUTHORS': 'select Author, AuthorID from Authors order by Author;',
           'FILE_AUTHORS': ' '.join(('select Author, AuthorID from Authors where AuthorID in',
                                     '(select AuthorID from FileAuthor where FileID = ?);')),
           'AUTHOR_FILES': 'select * from FileAuthor where AuthorID=:author_id;',
           'AUTHORS_BY_NAME': 'select Author, AuthorID from Authors where Author in ("{}");',
           'AUTHOR_FILE': 'select * from FileAuthor where FileID = ? and AuthorID =?;',
           'FILE_COMMENT': 'select Comment from Comments where CommentID = ?;',
           'FILES_CURR_DIR': ' '.join(('select FileID, DirID, CommentID, FileName, Year,',
                                      'Pages, Size from Files where DirId = ?;'))
           }

Insert = {'PLACES': 'insert into Places (Place, Title) values(?, ?);',
          'EXT': 'insert into Extensions (Extension, GroupID) values (:ext, 0);',
          'AUTHORS': 'insert into Authors (Author) values (:author);',
          'AUTHOR_FILE': 'insert into FileAuthor (AuthorID, FileID) values (:author_id, :file_id);',
          'TAGS': 'insert into Tags (Tag) values (:tag);',
          'TAG_FILE': 'insert into FileTag (TagID, FileID) values (:tag_id, :file_id);'}

Update = {'PLACE_TITLE': 'update Places set Title = :title where PlaceId = :place_id;',
          'PLACE': 'update Places set Place = ? where PlaceId = ?;'}

Delete = {'EXT': 'delete from Extensions where ExtID = ?;',
          'PLACES': 'delete from Places where PlaceId = ?;',
          'AUTHOR_FILE': 'delete from FileAuthor where AuthorID=:author_id and FileID=:file_id;',
          'AUTHOR': 'delete from Authors where AuthorID=:author_id;',
          'TAG_FILE': 'delete from FileTag where TagID=:tag_id and FileID=:file_id;',
          'TAG': 'delete from Tags where TagID=:tag_id;'}

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
        sql = DBUtils.generate_sql(dir_id, level, place_id)

        self.curs.execute(sql)

        return self.curs

    @staticmethod
    def generate_sql(dir_id, level, place_id):
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
        print('|---> select_other', sql, params)
        self.curs.execute(Selects[sql], params)
        return self.curs

    def select_other2(self, sql, params=()):
        print('|---> select_other2', sql, params)
        print(Selects[sql].format(params))
        self.curs.execute(Selects[sql].format(params))
        return self.curs

    def insert_other(self, sql, data):
        print('|---> insert_other', sql, data)
        self.curs.execute(Insert[sql], data)
        jj = self.curs.lastrowid
        self.conn.commit()
        return jj

    def update_other(self, sql, data):
        # print('|---> update_other:', sql, data)
        self.curs.execute(Update[sql], data)
        self.conn.commit()

    def delete_other(self, sql, data):
        print('|---> delete_other:', sql, data)
        self.curs.execute(Delete[sql], data)
        self.conn.commit()
