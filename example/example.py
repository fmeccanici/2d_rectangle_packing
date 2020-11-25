from rectangle_packing.grid import Grid
from rectangle_packing.stacker import Stacker
from rectangle_packing.rectangle import Rectangle
from rectangle_packing.excel_parser import ExcelParser
from rectangle_packing.database_manager import DatabaseManager

if __name__ == "__main__":
    stacker = Stacker()
    excel_parser = ExcelParser("./example/paklijsten/", "paklijst.xlsx")
    grid = Grid(name="0", width=130, height=1500, brand="Ambiant", color="2400.0205")
    grid.setDxfDrawing("./example/grids/", "example.dxf")
    db_manager = DatabaseManager()
    
    db_manager.clearDatabase()
    rectangles = excel_parser.getUnstackedRectangles()
    db_manager.addRectangles(rectangles)
    stacker.setGrid(grid)
    stacker.start(automatic=False)
    