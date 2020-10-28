import unittest
import sys

from rectangle import Rectangle

class StackedGridTest(unittest.TestCase):

    def setUp(self):
        self.rectangle_1 = Rectangle(100, 100, 1)
        self.rectangle_2 = Rectangle(200, 100, 1)
        self.rectangle_3 = Rectangle(198, 100, 1)
        self.rectangle_4 = Rectangle(100, 100, 1)

    def tearDown(self):
        pass

    def testGetWidth(self):
        self.assertEqual(self.rectangle_1.getWidth(), 100)
        self.assertEqual(self.rectangle_2.getWidth(), 200)
        self.assertEqual(self.rectangle_3.getWidth(), 198)

    def testGetHeight(self):
        self.assertEqual(self.rectangle_1.getHeight(), 100)
        self.assertEqual(self.rectangle_2.getHeight(), 100)
        self.assertEqual(self.rectangle_3.getHeight(), 100)

    def testGetArea(self):
        self.assertEqual(self.rectangle_1.getArea(), 10000)
        self.assertEqual(self.rectangle_2.getArea(), 20000)
        self.assertEqual(self.rectangle_3.getArea(), 19800)

    def testSetPosition(self):
        self.rectangle_1.setPosition([999, 99])
        self.rectangle_2.setPosition([100, 100])
        self.rectangle_3.setPosition([99, 50])

        self.assertEqual(self.rectangle_1.getPosition()[0], 999)
        self.assertEqual(self.rectangle_2.getPosition()[0], 100)
        self.assertEqual(self.rectangle_3.getPosition()[0], 99)

    def testGetBottomRight(self):
        self.rectangle_1.setPosition([50, 50])
        self.rectangle_2.setPosition([100, 100])
        self.rectangle_3.setPosition([99, 50])

        self.assertEqual(self.rectangle_1.getBottomRight()[0], 100)
        self.assertEqual(self.rectangle_1.getBottomRight()[1], 0)

        self.assertEqual(self.rectangle_2.getBottomRight()[0], 200)
        self.assertEqual(self.rectangle_2.getBottomRight()[1], 50)

        self.assertEqual(self.rectangle_3.getBottomRight()[0], 198)
        self.assertEqual(self.rectangle_3.getBottomRight()[1], 0)

        self.rectangle_1.setPosition([100, 100])
        self.rectangle_2.setPosition([200, 200])
        self.rectangle_3.setPosition([198, 100])

        self.assertEqual(self.rectangle_1.getBottomRight()[0], 150)
        self.assertEqual(self.rectangle_1.getBottomRight()[1], 50)

        self.assertEqual(self.rectangle_2.getBottomRight()[0], 300)
        self.assertEqual(self.rectangle_2.getBottomRight()[1], 150)

        self.assertEqual(self.rectangle_3.getBottomRight()[0], 297)
        self.assertEqual(self.rectangle_3.getBottomRight()[1], 50)


    def testGetTopLeft(self):
        self.rectangle_1.setPosition([50, 50])
        self.rectangle_2.setPosition([100, 100])
        self.rectangle_3.setPosition([99, 50])

        self.assertEqual(self.rectangle_1.getTopLeft()[0], 0)
        self.assertEqual(self.rectangle_1.getTopLeft()[1], 100)

        self.assertEqual(self.rectangle_2.getTopLeft()[0], 0)
        self.assertEqual(self.rectangle_2.getTopLeft()[1], 150)

        self.assertEqual(self.rectangle_3.getTopLeft()[0], 0)
        self.assertEqual(self.rectangle_3.getTopLeft()[1], 100)

        self.rectangle_1.setPosition([100, 100])
        self.rectangle_2.setPosition([200, 200])
        self.rectangle_3.setPosition([198, 100])

        self.assertEqual(self.rectangle_1.getTopLeft()[0], 50)
        self.assertEqual(self.rectangle_1.getTopLeft()[1], 150)

        self.assertEqual(self.rectangle_2.getTopLeft()[0], 100)
        self.assertEqual(self.rectangle_2.getTopLeft()[1], 250)

        self.assertEqual(self.rectangle_3.getTopLeft()[0], 99)
        self.assertEqual(self.rectangle_3.getTopLeft()[1], 150)

    def testIntersection(self):
        self.rectangle_1.setPosition([50, 50])
        self.rectangle_4.setPosition([149, 50])
        self.assertTrue(self.rectangle_1.intersection(self.rectangle_4))

        self.rectangle_1.setPosition([50, 50])
        self.rectangle_4.setPosition([150, 50])
        self.assertFalse(self.rectangle_1.intersection(self.rectangle_4))

        self.rectangle_1.setPosition([50, 50])
        self.rectangle_4.setPosition([50, 149])
        self.assertTrue(self.rectangle_1.intersection(self.rectangle_4))

        self.rectangle_1.setPosition([50, 50])
        self.rectangle_4.setPosition([50, 150])
        self.assertFalse(self.rectangle_1.intersection(self.rectangle_4))

        self.rectangle_1.setPosition([50, 50])
        self.rectangle_4.setPosition([250, 50])
        self.assertFalse(self.rectangle_1.intersection(self.rectangle_4))

    def testRotation(self):
        self.rectangle_3.rotate()
        self.assertEqual(self.rectangle_3.getWidth(), 100)
        self.assertEqual(self.rectangle_3.getHeight(), 198)
        self.rectangle_3.rotate()
        self.assertEqual(self.rectangle_3.getWidth(), 198)
        self.assertEqual(self.rectangle_3.getHeight(), 100)

if __name__ == '__main__':
    unittest.main()