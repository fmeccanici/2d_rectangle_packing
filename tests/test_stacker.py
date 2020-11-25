import unittest
unittest.TestLoader.sortTestMethodsUsing = None
import sys, os

from rectangle_packing.stacker import *
from rectangle_packing.rectangle import *
from rectangle_packing.grid import *
from rectangle_packing.excel_parser import *

class StackerTest(unittest.TestCase):

    def setUp(self):
        self.stacker = Stacker()
        self.rectangle = Rectangle(width=50, height=50, name="123456", brand="kokos", grid_width=100)
        self.rectangle_1 = Rectangle(width=50, height=80, name=1)
        self.rectangle_2 = Rectangle(width=50, height=80, name=2)
        self.excel_path = os.getcwd() + "/tests/test_paklijsten/"
        self.rectangle_3 = Rectangle(100, 100, 1)
        self.rectangle_4 = Rectangle(200, 100, 2)
        self.rectangle_5 = Rectangle(198, 100, 3)
        self.rectangle_6 = Rectangle(100, 100, 4)
        self.rectangle_7 = Rectangle(100, 100, 5)
        self.rectangle_8 = Rectangle(200, 750, 6)
        self.rectangle_9 = Rectangle(200, 750, 7)

        self.grid_1 = Grid(200, 1500, 1)

    def tearDown(self):
        pass

    def testStart1(self):
        file_name = "paklijst2.xlsx"

        self.stacker.setExcelParser(self.excel_path, file_name)
        self.stacker.db_manager.clearDatabase()
        self.stacker.loadOrdersAndAddToDatabase()
        self.stacker.start()

        rectangle1 = self.stacker.db_manager.getRectangle("1")
        rectangle2 = self.stacker.db_manager.getRectangle("2")
        rectangle3 = self.stacker.db_manager.getRectangle("3")

        # should be stacked next to each other
        self.assertEqual(rectangle2.getPosition()[0], 25)
        self.assertEqual(rectangle2.getPosition()[1], 40)

        self.assertEqual(rectangle1.getPosition()[0], 75)
        self.assertEqual(rectangle1.getPosition()[1], 40)

    def testStart2(self):
        file_name = "paklijst3.xlsx"

        self.stacker.setExcelParser(self.excel_path, file_name)
        self.stacker.db_manager.clearDatabase()
        self.stacker.loadOrdersAndAddToDatabase()
        self.stacker.start()

        rectangle1 = self.stacker.db_manager.getRectangle("1")
        rectangle2 = self.stacker.db_manager.getRectangle("2")
        rectangle3 = self.stacker.db_manager.getRectangle("3")

        # should be stacked next to each other
        self.assertEqual(rectangle2.getPosition()[0], 25)
        self.assertEqual(rectangle2.getPosition()[1], 40)
        self.assertEqual(rectangle1.getPosition()[0], 75)
        self.assertEqual(rectangle1.getPosition()[1], 40)

    def testComputeStackingPosition1(self):
        self.stacker = Stacker()
        self.grid_1.empty()
        self.stacker.setGrid(self.grid_1)
        self.stacker.setRectangle(self.rectangle_3)
        stacking_position = self.stacker.computeStackingPosition()

        self.assertEqual(stacking_position[0], 50)
        self.assertEqual(stacking_position[1], 50)

    def testComputeStackingPosition2(self):
        self.grid_1.empty()
        self.stacker.setGrid(self.grid_1)
        self.stacker.setRectangle(self.rectangle_4)
        stacking_position = self.stacker.computeStackingPosition()
        self.assertEqual(stacking_position[0], 100)
        self.assertEqual(stacking_position[1], 50)

    def testComputeStackingPosition3(self):
        self.grid_1.empty()
        self.stacker.setGrid(self.grid_1)
        self.stacker.setRectangle(self.rectangle_5)
        stacking_position = self.stacker.computeStackingPosition()
        self.assertEqual(stacking_position[0], 99)
        self.assertEqual(stacking_position[1], 50)

    def testComputeStackingPosition4(self):
        self.grid_1.empty()
        self.stacker.setGrid(self.grid_1)
        self.stacker.setRectangle(self.rectangle_3)
        stacking_position = self.stacker.computeStackingPosition()
        self.rectangle_3.setPosition(stacking_position)
        self.grid_1.addRectangle(self.rectangle_3)
        self.assertEqual(stacking_position[0], 50)
        self.assertEqual(stacking_position[1], 50)
        self.stacker.setRectangle(self.rectangle_6)
        stacking_position = self.stacker.computeStackingPosition()
        self.assertEqual(stacking_position[0], 150)
        self.assertEqual(stacking_position[1], 50)

    def testComputeStackingPosition5(self):
        self.grid_1.empty()
        self.stacker.setGrid(self.grid_1)
        self.stacker.setRectangle(self.rectangle_3)
        stacking_position = self.stacker.computeStackingPosition()
        self.rectangle_3.setPosition(stacking_position)
        self.grid_1.addRectangle(self.rectangle_3)
        self.assertEqual(stacking_position[0], 50)
        self.assertEqual(stacking_position[1], 50)
        self.stacker.setRectangle(self.rectangle_6)
        stacking_position = self.stacker.computeStackingPosition()
        self.rectangle_6.setPosition(stacking_position)
        self.grid_1.addRectangle(self.rectangle_6)
        self.stacker.setRectangle(self.rectangle_7)
        stacking_position = self.stacker.computeStackingPosition()
        
        self.assertEqual(stacking_position[0], 50)
        self.assertEqual(stacking_position[1], 150)

    def testComputeStackingPosition6(self):
        self.grid_1.empty()
        self.stacker.setGrid(self.grid_1)
        self.stacker.setRectangle(self.rectangle_8)
        stacking_position = self.stacker.computeStackingPosition()
        self.rectangle_8.setPosition(stacking_position)
        self.grid_1.addRectangle(self.rectangle_8)
        self.stacker.setRectangle(self.rectangle_9)
        stacking_position = self.stacker.computeStackingPosition()
        
        self.assertEqual(stacking_position[0], 100)
        self.assertEqual(stacking_position[1], 1125)
        
        
if __name__ == '__main__':
    unittest.main()