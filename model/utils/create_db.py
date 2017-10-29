import sqlite3
import socket


OBJ_DEFS = (
    '''
CREATE TABLE IF NOT EXISTS Files (
FileID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
DirID INTEGER NOT NULL,
ExtID INTEGER,
PlaceId INTEGER,
FileName TEXT,
CommentID INTEGER,
Year INTEGER,
Pages INTEGER,
Size INTEGER,
FOREIGN KEY(DirID) REFERENCES Dirs(DirID),
FOREIGN KEY(CommentID) REFERENCES Comments(CommentID),
FOREIGN KEY(ExtID) REFERENCES Extensions(ExtID)
);
    ''',
    '''
CREATE TABLE IF NOT EXISTS Authors (
AuthorID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Author TEXT
);
    ''',
    '''
CREATE TABLE IF NOT EXISTS FileAuthor (
FileID INTEGER NOT NULL,
AuthorID INTEGER NOT NULL
);
    ''',
    'CREATE UNIQUE INDEX IF NOT EXISTS FileAuthorIdx1 ON FileAuthor(FileID, AuthorID);',
    'CREATE INDEX IF NOT EXISTS FileAuthorIdx2 ON FileAuthor(AuthorID);',
    '''
CREATE TABLE IF NOT EXISTS Tags (
TagID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Tag TEXT
);
    ''',
    '''
CREATE TABLE IF NOT EXISTS FileTag (
 FileID INTEGER NOT NULL,
 TagID INTEGER NOT NULL
);
    ''',
    'CREATE UNIQUE INDEX IF NOT EXISTS FileTagIdx1 ON FileTag(FileID, TagID);',
    'CREATE INDEX IF NOT EXISTS FileTagIdx2 ON FileTag(TagID);',
    '''
CREATE TABLE IF NOT EXISTS Places (
PlaceId INTEGER NOT NULL PRIMARY KEY,
Place TEXT,
Title TEXT
);
    ''',
    '''
CREATE TABLE IF NOT EXISTS Dirs (
DirID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Path TEXT,
PlaceId INTEGER,
ParentID INTEGER,
FOREIGN KEY(ParentID) REFERENCES Dirs(DirID)
);
    ''',
    '''
-- Extension may be included only in one Group
CREATE TABLE IF NOT EXISTS Extensions (
ExtID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Extension TEXT,
GroupID INTEGER
);
    ''',
    'CREATE INDEX IF NOT EXISTS ExtIdx ON Extensions(GroupID);',
    '''
CREATE TABLE IF NOT EXISTS ExtGroups (
GroupID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
GroupName TEXT
);
    ''',
    '''
CREATE TABLE IF NOT EXISTS Comments (
CommentID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Comment TEXT
); ''',
    'CREATE INDEX IF NOT EXISTS Dirs_PlaceId ON Dirs(PlaceId, DirID);',
    'CREATE INDEX IF NOT EXISTS Dirs_ParentID ON Dirs(ParentID);',
    'CREATE INDEX IF NOT EXISTS Files_ExtID ON Files(PlaceId, ExtID);',
    'CREATE INDEX IF NOT EXISTS Files_DirID ON Files(PlaceId, DirID);'
)


def create_all_objects(conn_param):
    cursor = conn_param.cursor()
    for obj in OBJ_DEFS:
        try:
            cursor.execute(obj)
        except sqlite3.Error as err:
            print("An error occurred:", err.args[0])
            print(obj)

    set_initial_place(conn_param)


def set_initial_place(conn_param):
    cursor = conn_param.cursor()
    loc = socket.gethostname()
    cursor.execute('''insert into Places (PlaceId, Place, Title)    
        values (:id, :place, :title)''', (0, loc, loc))
    conn_param.commit()


if __name__ == "__main__":
    BASE_FILE = "..//..//new_db.sqlite"
    IT_IS = sqlite3.connect(BASE_FILE)
    create_all_objects(IT_IS)
