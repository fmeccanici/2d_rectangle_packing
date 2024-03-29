import unittest
import sys

from rectangle_packing.grid import Grid
from rectangle_packing.rectangle import Rectangle

class GridTest(unittest.TestCase):

    def setUp(self):

        self.rectangle_4 = Rectangle(50, 80, 4)
        self.rectangle_5 = Rectangle(50, 80, 5)

        self.grid_1 = Grid(200, 1500, 1)
        self.grid_2 = Grid(100, 100, 2)
        self.grid_3 = Grid(100, 80, 3)

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
        self.grid_2 = Grid(100, 100, 2)

        self.rectangle_4.setPosition([25, 40])
        self.rectangle_5.setPosition([24, 40])

        self.grid_2.addRectangle(self.rectangle_4)
        self.assertFalse(self.grid_2.isValidPosition(self.rectangle_5))

        self.rectangle_5.setPosition([76, 40])
        self.assertFalse(self.grid_2.isValidPosition(self.rectangle_5))


if __name__ == '__main__':
    unittest.main()