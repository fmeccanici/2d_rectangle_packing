import unittest
import sys

from rectangle_packing.stacker import Stacker
from rectangle_packing.rectangle import Rectangle
from rectangle_packing.stacked_grid import StackedGrid
from rectangle_packing.database_manager import DatabaseManager

class StackerTest(unittest.TestCase):

    def setUp(self):
        self.rectangle = Rectangle(width=50, height=50, name="123456", brand="kokos", grid_width=100)
        self.db_manager = DatabaseManager()

    def tearDown(self):
        pass

    def testClearDatabase(self):
        self.db_manager.clearDatabase()

    def testClearNewOrders(self):
        self.db_manager.clearNewOrders()
    
if __name__ == '__main__':
    unittest.main()