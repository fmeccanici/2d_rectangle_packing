import unittest
import sys

from rectangle_packing.stacker import *
from rectangle_packing.rectangle import *
from rectangle_packing.grid import *
from rectangle_packing.excel_parser import *

class StackerTest(unittest.TestCase):

    def setUp(self):
        self.excel_parser = ExcelParser()
        self.excel_path = os.getcwd() + "/tests/test_paklijsten/"
    def tearDown(self):
        pass

    def testLoadOrders1(self):
        file_name = "paklijst1.xlsx"
        self.excel_parser.setPath(self.excel_path)
        self.excel_parser.setFileName(file_name)

        self.assertEqual(len(self.excel_parser.getUnstackedRectangles()), 33)

    def testLoadOrders2(self):
        path = os.getcwd() + "/tests/test_paklijsten/"
        file_name = "paklijst_empty.xlsx"
        self.excel_parser.setPath(path)
        self.excel_parser.setFileName(file_name)

        self.assertRaises(EmptyExcelError, self.excel_parser.getUnstackedRectangles)

if __name__ == '__main__':
    unittest.main()