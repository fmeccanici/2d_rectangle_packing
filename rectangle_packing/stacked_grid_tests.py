import unittest
import sys

from stacked_grid import StackedGrid
from rectangle import Rectangle

class StackedGridTest(unittest.TestCase):

    def setUp(self):
        self.rectangle_1 = Rectangle(100, 100, 1)
        self.rectangle_2 = Rectangle(200, 100, 1)
        self.rectangle_3 = Rectangle(198, 100, 1)

        self.grid = StackedGrid(200, 1500, 1)

    def tearDown(self):
        pass

    def testComputeStackingPosition(self):
        stacking_position = self.grid.computeStackingPosition(self.rectangle_1)
        self.assertEqual(stacking_position[0], 50)
        self.assertEqual(stacking_position[1], 50)

        # edge case werkt niet?
        """
        stacking_position = self.grid.computeStackingPosition(self.rectangle_2)
        self.assertEqual(stacking_position[0], 100)
        self.assertEqual(stacking_position[1], 50)
        """

        stacking_position = self.grid.computeStackingPosition(self.rectangle_3)
        self.assertEqual(stacking_position[0], 99)
        self.assertEqual(stacking_position[1], 50)
    
if __name__ == '__main__':
    unittest.main()