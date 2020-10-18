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
        
        self.previous_rectangle = None

        self.canvas = QPixmap(self.canvas_width, self.canvas_height)
        color = QColor(255, 255, 255);
        self.canvas.fill(color)
        self.grid_drawing.setPixmap(self.canvas)

        self.buttons_layout.addWidget(self.grid_drawing)

        self.createGridOrdersEvents()

        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.addLayout(self.grid_orders_layout)
        self.refreshNewOrders()

        self.setLayout(self.main_layout)

    def drawGrid(self, grid):
        self.grid_drawing.setPixmap(self.canvas)
        
        rectangles = grid.getStackedRectangles()
        for rectangle in rectangles:
            self.drawRectangle(rectangle)

    def drawRectangle(self, rectangle, color=Qt.green):
        painter = QPainter(self.grid_drawing.pixmap())
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QBrush(color, Qt.DiagCrossPattern))

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
        QApplication.processEvents()

    def useMultithread(self, function):
        worker = Worker(function)
        self.threadpool.start(worker)

    def onStartStackingClick(self):
        self.stacker.startStacking()

        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)

        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()

        for rectangle in self.unstacked_rectangles:

            if not self.stacker.stackingStopped():
                try:
                    self.stacker.computeStackingPositionAndUpdateDatabase(rectangle, grid)
                    self.refreshGrid()
                    self.refreshNewOrders()
                except InvalidGridPositionError:
                    print("Rectangle does not fit")
            else:
                break

    def onStopStackingClick(self):
        self.stacker.stopStacking()
        
    def refreshGrid(self):
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        
        grid = self.db_manager.getGrid(grid_number)

        self.drawGrid(grid)
        self.removeAllOrderItems()

        for rectangle in grid.getStackedRectangles():
            list_widget_item = QListWidgetItem("Order " + str(rectangle.getName())) 
            self.list_widget_orders.addItem(list_widget_item) 
        
        QApplication.processEvents()

    def refreshCutGrid(self):
        grid_number = int(self.list_widget_cut_grids.currentItem().text().split(' ')[1])
        
        grid = self.db_manager.getGrid(grid_number)

        self.drawGrid(grid)
        self.removeAllOrderItems()

        for rectangle in grid.getStackedRectangles():
            list_widget_item = QListWidgetItem("Order " + str(rectangle.getName())) 
            self.list_widget_orders.addItem(list_widget_item) 
        
        QApplication.processEvents()

    def removeAllOrderItems(self):
        self.list_widget_orders.clear()

    def onLoadGridClick(self):
        self.refreshGrid()
        
    def createGridHtmlViewer(self, grid_number):
        self.grid_html_viewer = QtWebEngineWidgets.QWebEngineView()
        self.grid_html_viewer.load(QUrl().fromLocalFile(
            os.path.split(os.path.abspath(__file__))[0] + '/plots/stacked_grid_' + str(grid_number) + '.html'
        ))

        # self.buttons_layout.addWidget(self.grid_html_viewer)

    def createGridOrdersLayout(self):
        self.list_widget_grids = QListWidget() 
        self.list_widget_cut_grids = QListWidget() 

        self.list_widget_orders = QListWidget() 
        self.list_widget_new_orders = QListWidget() 


        grids = self.db_manager.getGridsNotCut()

        for grid in grids:
            list_widget_item = QListWidgetItem("Grid " + str(grid.getName())) 
            self.list_widget_grids.addItem(list_widget_item) 

        cut_grids = self.db_manager.getGridsCut()

        for grid in cut_grids:
            list_widget_item = QListWidgetItem("Grid " + str(grid.getName())) 
            self.list_widget_cut_grids.addItem(list_widget_item) 

        cut_uncut_group_box = QGroupBox("")

        self.cut_uncut_layout = QGridLayout()
        grids_label = QLabel("Uncut grids")
        self.cut_uncut_layout.addWidget(grids_label, 0, 0)
        self.cut_uncut_layout.addWidget(self.list_widget_grids, 1, 0)
        
        cut_grids_label = QLabel("Cut grids")
        self.cut_uncut_layout.addWidget(cut_grids_label, 0, 1)
        self.cut_uncut_layout.addWidget(self.list_widget_cut_grids, 1, 1)
        
        cut_uncut_group_box.setLayout(self.cut_uncut_layout)

        self.grid_orders_layout.addWidget(cut_uncut_group_box)

        grid_orders_label = QLabel("Orders in grid")
        self.grid_orders_layout.addWidget(grid_orders_label)
        self.grid_orders_layout.addWidget(self.list_widget_orders)

        unstacked_orders_label = QLabel("New orders")
        self.grid_orders_layout.addWidget(unstacked_orders_label)
        self.grid_orders_layout.addWidget(self.list_widget_new_orders)

    def refreshNewOrders(self):
        self.removeAllNewOrderItems()
        unstacked_rectangles = self.db_manager.getUnstackedRectangles()
        
        for rectangle in unstacked_rectangles:
            list_widget_item = QListWidgetItem("Order " + str(rectangle.getName())) 
            self.list_widget_new_orders.addItem(list_widget_item) 
        

    def removeAllNewOrderItems(self):
        self.list_widget_new_orders.clear()

    def onCreateGridClick(self):
        grid = self.db_manager.createUniqueGrid()

        list_widget_item = QListWidgetItem("Grid " + str(grid.getName())) 
        self.list_widget_grids.addItem(list_widget_item) 

        self.list_widget_grids.repaint()

    def createButtonEvents(self):
        # self.load_grid_button.clicked.connect(self.onLoadGridClick)
        self.create_grid_button.clicked.connect(self.onCreateGridClick)
        self.empty_grid_button.clicked.connect(self.onEmptyGridClick)

        self.start_stacking_button.clicked.connect(lambda: self.useMultithread(self.onStartStackingClick))
        self.stop_stacking_button.clicked.connect(lambda: self.useMultithread(self.onStopStackingClick))

        self.load_orders_button.clicked.connect(self.onLoadOrdersClick)
        self.make_database_backup_button.clicked.connect(self.onMakeDatabaseBackupClick)
        self.export_button.clicked.connect(self.onExportClick)
        self.cut_button.clicked.connect(self.onCutClick)
        self.uncut_button.clicked.connect(self.onUncutClick)

    def onEmptyGridClick(self):
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)

        self.db_manager.emptyGrid(grid)
        
        self.refreshNewOrders()

    def loadOrders(self):
        n = 5
        unstacked_rectangles = self.stacker.generateRandomRectangles(n)
        self.stacker.addToDatabase(unstacked_rectangles)
        self.refreshNewOrders()

    def onLoadOrdersClick(self):
        self.loadOrders()

    def onMakeDatabaseBackupClick(self):
        self.db_manager.makeBackup()

    def onExportClick(self):
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)
        
        if self.export_dxf_radio_button.isChecked():
            grid.toDxf()
        elif self.export_pdf_radio_button.isChecked():
            grid.toPdf()
        elif self.export_html_radio_button.isChecked():
            grid.plot()

    def onCutClick(self):
        self.removeGridItem('uncut')

    def onUncutClick(self):
        self.removeGridItem('cut')

    def removeGridItem(self, current_grid_state='uncut'):
        if current_grid_state == 'cut':
            list_widget = self.list_widget_cut_grids
        elif current_grid_state == 'uncut':
            list_widget = self.list_widget_grids

        grid_number = int(list_widget.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)
        grid.setUncut()

        self.db_manager.updateGrid(grid)

        item = list_widget.findItems(self.list_widget_cut_grids.currentItem().text(), Qt.MatchExactly)
        row = list_widget.row(item[0])
        list_widget.takeItem(row)
        list_widget.addItem(item[0])

    def onDoubleClickOrder(self):
        # item = self.list_widget_orders.findItems(self.current_rectangle, Qt.MatchExactly)
        # self.list_widget_orders.takeItem(item)
        
        rectangle_number = int(self.list_widget_orders.currentItem().text().split(' ')[1])
        rectangle = self.db_manager.getRectangle(rectangle_number)

        if self.previous_rectangle is not None:
            self.drawRectangle(self.previous_rectangle)

        self.drawRectangle(rectangle, color=Qt.red)
        self.current_rectangle = rectangle_number

        self.previous_rectangle = rectangle

    def onDoubleClickGrid(self):
        self.refreshGrid()
        self.previous_rectangle = None
    
    def onDoubleClickCutGrid(self):
        self.refreshCutGrid()

    def createGridOrdersEvents(self):
        self.list_widget_orders.itemDoubleClicked.connect(self.onDoubleClickOrder)
        self.list_widget_grids.itemDoubleClicked.connect(self.onDoubleClickGrid)
        self.list_widget_cut_grids.itemDoubleClicked.connect(self.onDoubleClickCutGrid)

    def createButtonsLayout(self):
        group_box = QGroupBox("Export grid")
        self.export_button = QPushButton("Export")
        self.export_dxf_radio_button = QRadioButton("DXF")
        self.export_pdf_radio_button = QRadioButton("PDF")
        self.export_html_radio_button = QRadioButton("HTML")
        self.export_pdf_radio_button.setChecked(True)

        export_grid = QGridLayout()
        export_grid.addWidget(self.export_button, 0, 0)
        export_grid.addWidget(self.export_dxf_radio_button, 1, 0)
        export_grid.addWidget(self.export_pdf_radio_button, 2, 0)
        export_grid.addWidget(self.export_html_radio_button, 1, 1)

        group_box.setLayout(export_grid)

        self.buttons_layout.addWidget(group_box)
        
        self.load_orders_button = QPushButton("Load new orders")
        # self.load_grid_button = QPushButton("Load")
        self.create_grid_button = QPushButton("Create new grid")
        self.empty_grid_button = QPushButton("Empty grid")

        self.make_database_backup_button = QPushButton("Make database backup")

        # self.buttons_layout.addWidget(self.load_grid_button)
        self.buttons_layout.addWidget(self.create_grid_button)
        self.buttons_layout.addWidget(self.empty_grid_button)

        self.buttons_layout.addWidget(self.load_orders_button)
        self.buttons_layout.addWidget(self.make_database_backup_button)

        group_box = QGroupBox("Stacking")
        layout = QVBoxLayout()
        self.start_stacking_button = QPushButton("Start")
        self.stop_stacking_button = QPushButton("Stop")
        layout.addWidget(self.start_stacking_button)
        layout.addWidget(self.stop_stacking_button)
        group_box.setLayout(layout)
        self.buttons_layout.addWidget(group_box)

        self.cut_button = QPushButton("Cut")
        self.uncut_button = QPushButton("Uncut")

        self.buttons_layout.addWidget(self.cut_button)
        self.buttons_layout.addWidget(self.uncut_button)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    clock = RectanglePackingGui()
    clock.show()
    sys.exit(app.exec_())