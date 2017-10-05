import sqlite3
import socket


OBJ_DEFS = (
    '''
CREATE TABLE IF NOT EXISTS Files (
FileID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
DirID INTEGER NOT NULL,
ExtID INTEGER,
AuthorID INTEGER,
TagID INTEGER,
FileName TEXT,
CommentID INTEGER,
Year INTEGER,
Pages INTEGER,
Size INTEGER,
FOREIGN KEY(DirID) REFERENCES Dirs(DirID),
FOREIGN KEY(AuthorID) REFERENCES FileAuthor(AuthorID),
FOREIGN KEY(TagID) REFERENCES FileTag(TagID),
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
    '''
CREATE UNIQUE INDEX IF NOT EXISTS FileAuthorIdx1 ON FileAuthor(FileID, AuthorID);
    ''',
    '''
CREATE INDEX IF NOT EXISTS FileAuthorIdx2 ON FileAuthor(AuthorID);
    ''',
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
    '''
CREATE UNIQUE INDEX IF NOT EXISTS FileTagIdx1 ON FileTag(FileID, TagID);
    ''',
    '''
CREATE INDEX IF NOT EXISTS FileTagIdx2 ON FileTag(TagID);
    ''',
    '''
CREATE TABLE IF NOT EXISTS myPlaces (
myPlaceId INTEGER NOT NULL PRIMARY KEY,
myPlace TEXT,
Title TEXT
);
    ''',
    '''
CREATE TABLE IF NOT EXISTS Dirs (
DirID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Path TEXT,
myPlaceId INTEGER,
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
    '''
CREATE INDEX IF NOT EXISTS ExtIdx ON Extensions(GroupID);
    ''',
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
);
    ''',
    '''
CREATE INDEX IF NOT EXISTS Dirs_myPlaceId ON Dirs(myPlaceId, DirID);
    ''',
    '''
CREATE INDEX IF NOT EXISTS Dirs_ParentID ON Dirs(ParentID);
    ''',
    '''
CREATE INDEX IF NOT EXISTS Files_ExtID ON Files(ExtID);
    ''',
    '''
CREATE INDEX IF NOT EXISTS Files_CommentID ON Files(CommentID);
    ''',
    '''
CREATE INDEX IF NOT EXISTS Files_TagID ON Files(TagID);
    ''',
    '''
CREATE INDEX IF NOT EXISTS Files_AuthorID ON Files(AuthorID);
    ''',
    '''
CREATE INDEX IF NOT EXISTS Files_DirID ON Files(DirID);
    '''
)


def create_all_objects(connection):
    cursor = connection.cursor()
    for d in OBJ_DEFS:
        try:
            cursor.execute(d)
        except sqlite3.Error as e:
            print("An error occurred:", e.args[0])
            print(d)

    set_initial_place(connection)

def set_initial_place(connection):
    cursor = connection.cursor()
    loc = socket.gethostname()
    # print('create_db.set_initial_place', loc)
    cursor.execute('''insert into myPlaces (myPlaceId, myPlace, Title)    
    values (:id, :place, :title)''', (0, loc, loc))
    loc2 = cursor.lastrowid
    connection.commit()


if __name__ == "__main__":
    db_name_ = "..//..//new_db.sqlite"
    connection = sqlite3.connect(db_name_)
    create_all_objects(connection)
