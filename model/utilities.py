# model/utilities.py
import datetime

PLUS_EXT_ID = 1000

Selects = {'TREE':
               ('WITH x(DirID, Path, ParentID, level) AS (SELECT DirID, Path, ParentID, 0 as level',
                'FROM Dirs WHERE DirID = {} and PlaceId = {}',
                'FROM Dirs WHERE ParentID = {} and PlaceId = {}',
                ' '.join(('UNION ALL SELECT t.DirID, t.Path, t.ParentID,',
                          'x.level + 1 as lvl FROM x INNER JOIN Dirs AS t',
                          'ON t.ParentID = x.DirID')),
                'and lvl <= {}) SELECT * FROM x order by ParentID desc, Path;',
                ') SELECT * FROM x order by ParentID desc, Path;'),
           'DIR_IDS':
               ('WITH x(DirID, Path, ParentID, level) AS (SELECT DirID, Path, ParentID, 0 as level',
                'FROM Dirs WHERE DirID = {} and PlaceId = {}',
                'FROM Dirs WHERE ParentID = {} and PlaceId = {}',
                ' '.join(('UNION ALL SELECT t.DirID, t.Path, t.ParentID,',
                          'x.level + 1 as lvl FROM x INNER JOIN Dirs AS t',
                          'ON t.ParentID = x.DirID')),
                'and lvl <= {}) SELECT DirID FROM x order by DirID;',
                ') SELECT DirID FROM x order by DirID;'),
           'FILE_IDS_ALL_TAG': ' '.join(('select FileID from FileTag where TagID in ({})',
                                         'group by FileID having count(*) = {};')),
           'PLACES': 'select * from Places;',
           'PLACE_IN_DIRS': 'select DirId from Dirs where PlaceId = ?;',
           'PATH': 'select Path, PlaceId from Dirs where DirID = ?;',
           'IS_EXIST': 'select * from Places where Place = ?;',
           'EXT': ' '.join(('select Extension as title, ExtID+{}, GroupID'.format(PLUS_EXT_ID),
                            'as ID from Extensions UNION select GroupName as title,',
                            'GroupID, 0 as ID from ExtGroups',
                            'order by ID desc, title;')),
           'HAS_EXT': 'select count(*) from Extensions where Extension = ?;',
           'EXT_ID_IN_GROUP': 'select ExtID from Extensions where GroupID = ?;',
           'EXT_IN_GROUP': 'select Extension, ExtID from Extensions where GroupID = ?;',
           'EXT_IN_FILES': 'select FileID from Files where ExtID = ?;',
           'FILE_INFO': ' '.join(('select A.FileName || " " || COALESCE(B.BookTitle, "")',
                                  '|| " " || COALESCE(B.Comment, ""), A.FileID from',
                                  'Files A left join Comments B on B.CommentID = A.CommentID',
                                  'where A.ExtID in ({}) and NOT EXISTS (select * from FileTag',
                                  'where FileID = A.FileID and TagID = {});')),
           'TAGS': 'select Tag, TagID from Tags order by Tag COLLATE NOCASE;',
           'FILE_TAGS': ' '.join(('select Tag, TagID from Tags where TagID in',
                                  '(select TagID from FileTag where FileID = ?);')),
           'TAG_FILES': 'select * from FileTag where TagID=:tag_id;',
           'TAGS_BY_NAME': 'select Tag, TagID from Tags where Tag in ("{}");',
           'TAG_FILE': 'select * from FileTag where FileID = ? and TagID =?;',
           'FILE_IDS_ANY_TAG': 'select FileID from FileTag where TagID in ({}) order by FileID;',
           'AUTHORS': 'select Author, AuthorID from Authors order by Author COLLATE NOCASE;',
           'FILE_AUTHORS': ' '.join(('select Author, AuthorID from Authors where AuthorID in',
                                     '(select AuthorID from FileAuthor where FileID = ?);')),
           'AUTHOR_FILES': 'select * from FileAuthor where AuthorID=:author_id;',
           'AUTHORS_BY_NAME': 'select Author, AuthorID from Authors where Author in ("{}");',
           'AUTHOR_FILE': 'select * from FileAuthor where FileID = ? and AuthorID =?;',
           'FILE_IDS_AUTHORS': 'select FileID from FileAuthor where AuthorID in ({});',
           'FILE_COMMENT': 'select Comment, BookTitle from Comments where CommentID = ?;',
           'ADV_SELECT':
                (
                    'and DirID in ({})',
                    'and ExtID in ({})',
                    'and FileID in ({})',
                    'and FileDate > {}',
                    'and IssueDate > {}',
                    ' '.join(('select FileName, FileDate, Pages, Size, IssueDate,',
                              'Opened, Commented, FileID, DirID, CommentID, ExtID,',
                              'PlaceId from Files where PlaceId = {}'))
                ),
           'FILES_CURR_DIR': ' '.join(('select FileName, FileDate, Pages, Size, IssueDate,',
                                       'Opened, Commented, FileID, DirID, CommentID, ExtID,',
                                       'PlaceId from Files where DirId = ?;')),
           'FAVORITES': ' '.join(('select FileName, FileDate, Pages, Size, IssueDate, Opened,',
                                  'Commented, FileID, DirID, CommentID, ExtID, PlaceId from',
                                  'Files where FileID in (select FileID from Favorites);')),
           'ISSUE_DATE': 'select IssueDate from Files where FileID = ?;'
           }

Insert = {'PLACES': 'insert into Places (Place, Title) values(?, ?);',
          'FAVORITES': 'insert into Favorites (FileID) values (?);',
          'COMMENT': 'insert into Comments (Comment, BookTitle) values (?, ?);',
          'EXT': 'insert into Extensions (Extension, GroupID) values (:ext, 0);',
          'EXT_GROUP': 'insert into ExtGroups (GroupName) values (?);',
          'AUTHORS': 'insert into Authors (Author) values (:author);',
          'AUTHOR_FILE': 'insert into FileAuthor (AuthorID, FileID) values (:author_id, :file_id);',
          'TAGS': 'insert into Tags (Tag) values (:tag);',
          'TAG_FILE': 'insert into FileTag (TagID, FileID) values (:tag_id, :file_id);'}

Update = {'PLACE_TITLE': 'update Places set Title = :title where PlaceId = :place_id;',
          'PLACE': 'update Places set Place = ? where PlaceId = ?;',
          'EXT_GROUP': 'update Extensions set GroupID = ? where ExtID = ?;',
          'ISSUE_DATE': 'update Files set IssueDate = ? where FileID = ?;',
          'BOOK_TITLE': 'update Comments set BookTitle = ? where CommentID = ?;',
          'COMMENT': 'update Comments set Comment = ? where CommentID = ?;',
          'FILE_COMMENT': 'update Files set CommentID = ? where FileID = ?;',
          'PAGES': 'update Files set Pages = ? where FileID = ?;',
          'OPEN_DATE': "update Files set Opened = ? where FileID = ?;",
          'COMMENT_DATE': "update Files set Commented = date('now') where FileID = ?;",
          'UPDATE_TAG': 'update Tags set Tag = ? where TagID = ?;'
          }

Delete = {'EXT': 'delete from Extensions where ExtID = ?;',
          'UNUSED_EXT_GROUP': ' '.join(('delete from ExtGroups where NOT EXISTS (',
                                        'select * from Extensions where GroupID =',
                                        'ExtGroups.GroupID);')),
          'UNUSED_AUTHORS': ' '.join(('delete from Authors where NOT EXISTS (select *',
                                      'from FileAuthor where AuthorID = Authors.AuthorID);')),
          'UNUSED_TAGS': ' '.join(('delete from Tags where NOT EXISTS (select *',
                                   'from FileTag where TagID = Tags.TagID);')),
          'UNUSED_EXT': ' '.join(('delete from Extensions where NOT EXISTS (select *',
                                  'from Files where ExtID = Extensions.ExtID);')),
          'FAVORITES': 'delete from Favorites where FileID = ?',
          'PLACES': 'delete from Places where PlaceId = ?;',
          'COMMENT': 'delete from Comments where CommentID = ?;',
          'FILE': 'delete from Files where FileID = ?;',
          'AUTHOR_FILE': 'delete from FileAuthor where AuthorID=:author_id and FileID=:file_id;',
          'AUTHOR': 'delete from Authors where AuthorID=:author_id;',
          'AUTHOR_FILE_BY_FILE': 'delete from FileAuthor where FileID=?;',
          'TAG_FILE': 'delete from FileTag where TagID=:tag_id and FileID=:file_id;',
          'TAG_FILE_BY_FILE': 'delete from FileTag where FileID = ?;',
          'TAG': 'delete from Tags where TagID=:tag_id;',
          'DEL_EMPTY_DIRS': ' '.join(('delete from Dirs where Fake = 0 and NOT EXISTS (select *',
                                      'from Files where DirID = Dirs.DirID);'))
          }


class DBUtils:
    """Different methods for select, update and insert information into/from DB"""
    def __init__(self):
        self.conn = None
        self.curs = None

    def set_connection(self, connection):
        self.conn = connection
        self.curs = connection.cursor()

    def advanced_selection(self, param, cur_place_id):
        # print('|---> advanced_selection', param)

        sql = self.generate_adv_sql(cur_place_id, param)
        # print(sql)

        self.curs.execute(sql)
        return self.curs

    @staticmethod
    def generate_adv_sql(cur_place_id, param):
        # print(Selects['ADV_SELECT'])
        # print('cur_place_id:', cur_place_id)
        # print(param)
        res_sql = [Selects['ADV_SELECT'][5].format(cur_place_id)]

        if param.dir.use:           # select files by directory tree
            res_sql.append(Selects['ADV_SELECT'][0].format(param.dir.list))

        if param.extension.use and param.extension.list:    # by extension
            res_sql.append(Selects['ADV_SELECT'][1].format(param.extension.list))

        if param.tags.use and param.authors.use:        # by tags and authors
            t1 = set(param.tags.list.split(','))
            t2 = set(param.authors.list.split(','))
            tmp = t1.intersection(t2)
            if tmp:
                res_sql.append(Selects['ADV_SELECT'][2].format(','.join(tmp)))

        elif param.tags.use and param.tags.list:        # tags, authors not used
            res_sql.append(Selects['ADV_SELECT'][2].format(param.tags.list))

        elif param.authors.use and param.authors.list:  # authors, tags not used
            res_sql.append(Selects['ADV_SELECT'][2].format(param.authors.list))

        if param.date.use:              # by date
            tt = datetime.date.today()
            tt = tt.replace(year=tt.year - int(param.date.date))
            if param.date.file_date:    # date of file
                res_sql.append(Selects['ADV_SELECT'][3].format(tt))
            else:                       # date of book issue
                res_sql.append(Selects['ADV_SELECT'][4].format(tt))

        res_sql.append(';')
        sql = ' '.join([clause for clause in res_sql])
        return sql

    def dir_tree_select(self, dir_id, level, place_id):
        """
        Select tree of directories starting from dir_id up to level
        :param dir_id: - starting directory, 0 - from root
        :param level: - max level of tree, 0 - all levels
        :param place_id:
        :return: cursor of directories
        """
        sql = DBUtils.generate_sql(dir_id, level, place_id)

        self.curs.execute(sql)

        return self.curs

    def dir_ids_select(self, dir_id, level, place_id):
        """
        Select tree of directories starting from dir_id up to level
        :param dir_id: - starting directory, 0 - from root
        :param level: - max level of tree, 0 - all levels
        :param place_id:
        :return: list of directories ids
        """
        sql = DBUtils.generate_sql(dir_id, level, place_id, sql='DIR_IDS')

        self.curs.execute(sql)

        return self.curs.fetchall()

    @staticmethod
    def generate_sql(dir_id, level, place_id, sql='TREE'):
        tree_sql = Selects[sql]
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
        self.curs.execute(Selects[sql], params)
        return self.curs

    def select_other2(self, sql, params=()):
        # print('|---> select_other2', sql, params)
        # print(Selects[sql].format(*params))
        self.curs.execute(Selects[sql].format(*params))
        return self.curs

    def insert_other(self, sql, data):
        # print('|---> insert_other', sql, data)
        self.curs.execute(Insert[sql], data)
        jj = self.curs.lastrowid
        self.conn.commit()
        # print('  comment_id:', jj)
        return jj

    def update_other(self, sql, data):
        # print('|---> update_other:', sql, data)
        self.curs.execute(Update[sql], data)
        self.conn.commit()

    def delete_other(self, sql, data):
        # print('|---> delete_other:', sql, data)
        self.curs.execute(Delete[sql], data)
        self.conn.commit()
