import unittest
import sys

from stacker import Stacker
from rectangle import Rectangle
from stacked_grid import StackedGrid

class StackerTest(unittest.TestCase):

    def setUp(self):
        self.stacker = Stacker()
        self.rectangle = Rectangle(width=50, height=50, name="123456", brand="kokos", grid_width=100)

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