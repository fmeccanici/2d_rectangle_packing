from rectangle import Rectangle
from stacked_grid import StackedGrid
from database_manager import DatabaseManager

import random
import time

class Error(Exception):
    """Base class for other exceptions"""
    pass

class InvalidGridPositionError(Error):
    """Raised when rectangle has invalid grid position"""
    pass

class GridFullError(Error):
    """Raised when grid is full"""
    pass

class Stacker(object):
    def __init__(self):
        self.db_manager = DatabaseManager()
        # grid = StackedGrid(width=200, height=1500, name=1)
        # self.db_manager.addGrid(grid)
        self.grids = self.db_manager.getGrids()

        print("Grids present: ")

        for grid in self.grids:
            print(grid.getName())

        self.unstacked_rectangles = []

        self.min_rectangle_width = 100 #cm
        self.min_rectangle_height = 50 #cm
        self.max_rectangle_width = 200 #cm
        self.max_rectangle_height = 1500 #cm

    def addToDatabase(self, rectangles):
        for rectangle in rectangles:
            self.db_manager.addRectangle(rectangle)

    def computeStackingPositionAndUpdateDatabase(self, rectangle):
        try:
            for grid in self.grids:
                print([x.getName() for x in self.db_manager.getRectangles(grid)])

                if not grid.isFull():
                    stacking_position = grid.computeStackingPosition(rectangle)
                    rectangle.setPosition(stacking_position)
                    
                    if stacking_position[0] != grid.getWidth() and stacking_position[1] != grid.getHeight():
                        rectangle.setStacked()
                        rectangle.setGridNumber(grid.getName())

                        grid.addRectangle(rectangle)
                        self.db_manager.updateRectangle(rectangle)

                    else:
                        raise InvalidGridPositionError
                
                elif grid.isFull() and self.grids[-1].getName() == grid.getName():
                    print("Grid full")
                    print("Create new grid")

                    grid = StackedGrid(width=200, height=1500, name=self.grids[-1].getName() + 1)
                    self.grids.append(grid)
                    
                    stacking_position = grid.computeStackingPosition(rectangle)
                    rectangle.setPosition(stacking_position)
                    
                    if stacking_position[0] != grid.getWidth() and stacking_position[1] != grid.getHeight():
                        rectangle.setStacked()
                        rectangle.setGridNumber(grid.getName())

                        grid.addRectangle(rectangle)
                        self.db_manager.updateRectangle(rectangle)

                    else:
                        raise InvalidGridPositionError

                elif grid.isFull() and self.grids[-1].getName() != grid.getName():
                    print("Grid full")
                    print("Continue to next grid")

                    continue

        
        except InvalidGridPositionError:
            print("Could not fit rectangle in grid!")

    def computeRectangleOrderArea(self, rectangles):
        
        areas = [x.getArea() for x in rectangles]
        indices_descending_order = sorted(range(len(areas)), key=lambda k: areas[k])
        rectangles_descending_area_order = []
        for idx in indices_descending_order:
            rectangles_descending_area_order.append(rectangles[idx])

        return list(reversed(rectangles_descending_area_order))

    def generateRandomRectangles(self, amount):
        rectangles = []
        random.seed(41)
        for i in range(amount):
            width = random.randrange(self.min_rectangle_width, self.max_rectangle_width, 2)
            height = random.randrange(self.min_rectangle_height, self.max_rectangle_height/2, 2)

            r = Rectangle(width, height, name=i)
            rectangles.append(r)
        return rectangles

    def start(self):
        t_start = time.time()

        n = 20
        self.unstacked_rectangles = self.generateRandomRectangles(n)
        self.addToDatabase(self.unstacked_rectangles)

        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()

        if len(self.unstacked_rectangles) > 4:
            self.unstacked_rectangles = self.computeRectangleOrderArea(self.unstacked_rectangles)

            for i, rectangle in enumerate(self.unstacked_rectangles):
                print("Rectangle " + str(rectangle.getName()))
                self.computeStackingPositionAndUpdateDatabase(rectangle)

            # self.plot()
            # self.toDxf()
        
            t_stop = time.time() - t_start
            print("Time: " + str(round(t_stop)) + " seconds")

if __name__ == "__main__":
    stacker = Stacker()
    stacker.start()