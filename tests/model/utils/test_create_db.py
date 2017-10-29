import unittest
import sqlite3
from model.utils import create_db

TEST_DATA = (
(('''CREATE TABLE Files (
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
)''',),
('CREATE TABLE sqlite_sequence(name,seq)',),
('''CREATE TABLE Authors (
AuthorID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Author TEXT
)''',),
('''CREATE TABLE FileAuthor (
FileID INTEGER NOT NULL,
AuthorID INTEGER NOT NULL
)''',),
('CREATE UNIQUE INDEX FileAuthorIdx1 ON FileAuthor(FileID, AuthorID)',),
('CREATE INDEX FileAuthorIdx2 ON FileAuthor(AuthorID)',),
('''CREATE TABLE Tags (
TagID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Tag TEXT
)''',),
('''CREATE TABLE FileTag (
 FileID INTEGER NOT NULL,
 TagID INTEGER NOT NULL
)''',),
('CREATE UNIQUE INDEX FileTagIdx1 ON FileTag(FileID, TagID)',),
('CREATE INDEX FileTagIdx2 ON FileTag(TagID)',),
('''CREATE TABLE Places (
PlaceId INTEGER NOT NULL PRIMARY KEY,
Place TEXT,
Title TEXT
)''',),
('''CREATE TABLE Dirs (
DirID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Path TEXT,
PlaceId INTEGER,
ParentID INTEGER,
FOREIGN KEY(ParentID) REFERENCES Dirs(DirID)
)''',),
('''CREATE TABLE Extensions (
ExtID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Extension TEXT,
GroupID INTEGER
)''',),
('CREATE INDEX ExtIdx ON Extensions(GroupID)',),
('''CREATE TABLE ExtGroups (
GroupID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
GroupName TEXT
)''',),
('''CREATE TABLE Comments (
CommentID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
Comment TEXT
)''',),
('CREATE INDEX Dirs_PlaceId ON Dirs(PlaceId, DirID)',),
('CREATE INDEX Dirs_ParentID ON Dirs(ParentID)',),
('CREATE INDEX Files_ExtID ON Files(PlaceId, ExtID)',),
('CREATE INDEX Files_DirID ON Files(PlaceId, DirID)',))
)


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(':memory:')

    def tearDown(self):
        self.connection.close()

    def test_create_db(self):
        create_db.create_all_objects(self.connection)
        rr = self.connection.cursor()
        pp = rr.execute('select sql from sqlite_master;')
        tt = tuple(pp)
        # print(tt)
        self.assertTupleEqual(tt, TEST_DATA)


if __name__ == '__main__':
    unittest.main()
