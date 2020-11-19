import unittest
import sys

from stacker import *
from rectangle import *
from stacked_grid import *
from excel_parser import *

class StackerTest(unittest.TestCase):

    def setUp(self):
        self.excel_parser = ExcelParser()

    def tearDown(self):
        pass

    def testLoadOrders1(self):
        path = "./test_paklijsten/"
        file_name = "paklijst1.xlsx"
        self.excel_parser.setPath(path)
        self.excel_parser.setFileName(file_name)

        self.assertEqual(len(self.excel_parser.getOrders()), 33)

    def testLoadOrders2(self):
        path = "./test_paklijsten/"
        file_name = "paklijst_empty.xlsx"
        self.excel_parser.setPath(path)
        self.excel_parser.setFileName(file_name)

        self.assertRaises(EmptyExcelError, self.excel_parser.getOrders)


if __name__ == '__main__':
    unittest.main()