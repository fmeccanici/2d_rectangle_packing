import unittest
import sys

from rectangle_packing.stacked_grid import StackedGrid
from rectangle_packing.rectangle import Rectangle

class StackedGridTest(unittest.TestCase):

    def setUp(self):
        self.rectangle_1 = Rectangle(100, 100, 1)
        self.rectangle_2 = Rectangle(200, 100, 2)
        self.rectangle_3 = Rectangle(198, 100, 3)
        self.rectangle_4 = Rectangle(50, 80, 4)
        self.rectangle_5 = Rectangle(50, 80, 5)

        self.grid_1 = StackedGrid(200, 1500, 1)
        self.grid_2 = StackedGrid(100, 100, 2)
        self.grid_3 = StackedGrid(100, 80, 3)

    def tearDown(self):
        pass

    def testIsOutOfGrid(self):
        self.rectangle_4.setPosition([25, 40])
        self.assertFalse(self.grid_2.isOutOfGrid(self.rectangle_4))
        self.grid_2.addRectangle(self.rectangle_4)
        
        self.rectangle_5.setPosition([75, 40])
        self.assertFalse(self.grid_2.isOutOfGrid(self.rectangle_5))

        self.rectangle_5.setPosition([76, 40])
        self.assertTrue(self.grid_2.isOutOfGrid(self.rectangle_5))

        self.rectangle_5.setPosition([75, 40])
        self.assertFalse(self.grid_3.isOutOfGrid(self.rectangle_5))

        self.rectangle_5.setPosition([75, 41])
        self.assertTrue(self.grid_3.isOutOfGrid(self.rectangle_5))

    def testIsValidPosition(self):
        self.grid_2 = StackedGrid(100, 100, 2)
        self.rectangle_4 = Rectangle(50, 80, 4)
        self.rectangle_5 = Rectangle(50, 80, 5)

        self.rectangle_4.setPosition([25, 40])
        self.rectangle_5.setPosition([24, 40])

        self.grid_2.addRectangle(self.rectangle_4)
        self.assertFalse(self.grid_2.isValidPosition(self.rectangle_5))

        self.rectangle_5.setPosition([76, 40])
        self.assertFalse(self.grid_2.isValidPosition(self.rectangle_5))
    
if __name__ == '__main__':
    unittest.main()