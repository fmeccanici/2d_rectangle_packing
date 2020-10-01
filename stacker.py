from rectangle import Rectangle
from stacked_grid import StackedGrid
from database_manager import DatabaseManager

class Stacker(object):
    def __init__(self):
        self.db_manager = DatabaseManager()
        # grid = StackedGrid(width=200, height=1500, name=1)
        # self.db_manager.addGrid(grid)
        self.db_manager.getGrids()


if __name__ == "__main__":
    stacker = Stacker()