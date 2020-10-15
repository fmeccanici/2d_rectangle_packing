import sys
import os

from PyQt5 import QtWebEngineWidgets, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QThreadPool, QRunnable, pyqtSlot, QRect
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem, QMainWindow)
from PyQt5.QtGui import QPainter, QBrush, QPen, QPixmap, QColor

from database_manager import DatabaseManager
from stacked_grid import StackedGrid
from stacker import Stacker, InvalidGridPositionError

# class that enables multithreading with Qt
class Worker(QRunnable):
    '''
    Worker thread
    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    # use custom function 
    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        self.fn(*self.args, **self.kwargs)

class RectanglePackingGui(QWidget):
    def __init__(self, parent=None):
        super(RectanglePackingGui, self).__init__(parent)
        # Other classes
        self.db_manager = DatabaseManager()
        self.stacker = Stacker()

        # Multithreading
        self.threadpool = QThreadPool()

        # GUI related stuff
        self.main_layout = QHBoxLayout()
        self.buttons_layout = QVBoxLayout()
        self.grid_orders_layout = QVBoxLayout()
        
        self.createButtonsLayout()
        self.createButtonEvents()

        grid_number = 1
        self.createGridHtmlViewer(grid_number)
        self.createGridOrdersLayout()

        self.grid_drawing = QtWidgets.QLabel()
        self.canvas_width = 400
        self.canvas_height = 800
        self.max_rectangle_width = 200 #cm
        self.max_rectangle_height = 1500 #cm

        self.canvas = QPixmap(self.canvas_width, self.canvas_height)
        color = QColor(255, 255, 255);
        self.canvas.fill(color)
        self.grid_drawing.setPixmap(self.canvas)

        self.buttons_layout.addWidget(self.grid_drawing)

        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.addLayout(self.grid_orders_layout)

        self.setLayout(self.main_layout)

    def drawGrid(self, grid):
        self.grid_drawing.setPixmap(self.canvas)
        
        rectangles = grid.getStackedRectangles()
        for rectangle in rectangles:
            self.drawRectangle(rectangle)

    def drawRectangle(self, rectangle):
        painter = QPainter(self.grid_drawing.pixmap())
        painter.setPen(QPen(Qt.black, 5, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.green, Qt.DiagCrossPattern))

        x = rectangle.getPosition()[0] - rectangle.getWidth()/2
        y = rectangle.getPosition()[1] + rectangle.getHeight()/2
        width = rectangle.getWidth() 
        height = rectangle.getHeight() 

        y = self.max_rectangle_height - y 

        x = x / self.max_rectangle_width * self.canvas_width
        y = y / self.max_rectangle_height * self.canvas_height

        width = width / self.max_rectangle_width * self.canvas_width
        height = height / self.max_rectangle_height * self.canvas_height

        painter.drawRect(x, y, width, height)

        painter.end()
        
        self.grid_drawing.update()

    def useMultithread(self, function):
        worker = Worker(function)
        self.threadpool.start(worker)

    def onStartStackingClick(self):

        # n = 5
        # self.unstacked_rectangles = self.stacker.generateRandomRectangles(n)
        # self.stacker.addToDatabase(self.unstacked_rectangles)
        
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)

        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()

        for rectangle in self.unstacked_rectangles:
            try:
                self.stacker.computeStackingPositionAndUpdateDatabase(rectangle, grid)
                # grid.plot()
                # self.buttons_layout.removeWidget(self.grid_html_viewer)
                # self.createGridHtmlViewer(grid_number)
                self.drawRectangle(rectangle)
                # self.drawGrid(grid)
            except InvalidGridPositionError:
                print("Rectangle does not fit")

    def removeAllOrderItems(self):
        for i in range(self.list_widget_orders.count()):

            self.list_widget_orders.takeItem(i)

    def onLoadGridClick(self):
        self.buttons_layout.removeWidget(self.grid_html_viewer)
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        
        grid = self.db_manager.getGrid(grid_number)
        # self.createGridHtmlViewer(grid_number)
        self.drawGrid(grid)
        self.removeAllOrderItems()

        for rectangle in grid.getStackedRectangles():
            list_widget_item = QListWidgetItem("Order " + str(rectangle.getName())) 
            self.list_widget_orders.addItem(list_widget_item) 

    def createGridHtmlViewer(self, grid_number):
        self.grid_html_viewer = QtWebEngineWidgets.QWebEngineView()
        self.grid_html_viewer.load(QUrl().fromLocalFile(
            os.path.split(os.path.abspath(__file__))[0] + '/plots/stacked_grid_' + str(grid_number) + '.html'
        ))

        # self.buttons_layout.addWidget(self.grid_html_viewer)

    def createGridOrdersLayout(self):
        self.list_widget_grids = QListWidget() 
        self.list_widget_orders = QListWidget() 

        grids = self.db_manager.getGridsNotCut()

        for grid in grids:
            list_widget_item = QListWidgetItem("Grid " + str(grid.getName())) 
            self.list_widget_grids.addItem(list_widget_item) 

        self.grid_orders_layout.addWidget(self.list_widget_grids)
        self.grid_orders_layout.addWidget(self.list_widget_orders)

    def createButtonEvents(self):
        self.load_grid_button.clicked.connect(self.onLoadGridClick)
        self.start_stacking_button.clicked.connect(self.onStartStackingClick)

    def createButtonsLayout(self):

        self.export_to_dxf_button = QPushButton("Export to DXF")
        self.buttons_layout.addWidget(self.export_to_dxf_button)

        self.load_grid_button = QPushButton("Load")
        self.buttons_layout.addWidget(self.load_grid_button)

        self.start_stacking_button = QPushButton("Start stacking")
        self.buttons_layout.addWidget(self.start_stacking_button)

        self.cut_button = QPushButton("Cut")

        self.buttons_layout.addWidget(self.cut_button)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    clock = RectanglePackingGui()
    clock.show()
    sys.exit(app.exec_())