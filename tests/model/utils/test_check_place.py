import unittest
import sqlite3

from unittest.mock import Mock

from model.utils import create_db
from model.utils import load_db_data


class TestCheckPlace(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(':memory:')

        mock_socket = Mock()
        create_db.socket = mock_socket
        mock_socket.gethostname.return_value = 'My place'
        create_db.create_all_objects(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_check_place(self):
        conn = self.connection
        curr_place = (1, 'test_place', 'test_place')
        load_db = load_db_data.LoadDBData(conn, curr_place)

        self.assertEqual(load_db.place_id, 1)

        tt = conn.execute('select * from myPlaces').fetchall()
        pp = tuple(tt)
        self.assertEqual(pp, ((0, 'My place', 'My place'), curr_place))
        conn.close()

