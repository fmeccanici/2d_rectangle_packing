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
from rectangle import Rectangle

import pandas as pd
import numpy as np

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
        self.left_side_layout = QHBoxLayout()
        self.buttons_layout = QVBoxLayout()
        self.grid_orders_layout = QVBoxLayout()
        
        self.createButtonsLayout()
        self.createButtonEvents()

        grid_number = 1
        self.createGridHtmlViewer(grid_number)
        self.createGridOrdersLayout()

        self.grid_drawing = QtWidgets.QLabel()

        # TODO relative to window size
        self.canvas_width = 450
        self.canvas_height = 900
        self.max_rectangle_width = 200 #cm
        self.max_rectangle_height = 1500 #cm
        
        self.previous_rectangle = None

        self.canvas = QPixmap(self.canvas_width, self.canvas_height)
        color = QColor(255, 255, 255)
        self.canvas.fill(color)
        self.grid_drawing.setPixmap(self.canvas)

        # self.left_side_layout.addWidget(self.grid_drawing)

        self.createGridOrdersEvents()

        self.main_layout.addWidget(self.grid_drawing)
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
        self.updateCodeStatus("Stacking started")

        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)

        self.unstacked_rectangles = self.db_manager.getUnstackedRectangles()
        self.unstacked_rectangles = self.stacker.computeRectangleOrderArea(self.unstacked_rectangles)

        for i, rectangle in enumerate(self.unstacked_rectangles):
            print("Stacking rectangle " + str(i) + " out of " + str(len(self.unstacked_rectangles)))

            if not self.stacker.stackingStopped():
                try:
                    self.stacker.computeStackingPositionAndUpdateDatabase(rectangle, grid)
                    self.refreshGrid()
                    self.refreshNewOrders()
                    self.updateCodeStatus("Order " + str(rectangle.getName()) + " stacked")

                except InvalidGridPositionError:
                    print("Rectangle does not fit")
                    self.updateCodeStatus("Order " + str(rectangle.getName()) + " does not fit")
            else:
                self.updateCodeStatus("Stacking stopped")
                break

        self.updateCodeStatus("Stacking stopped")

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

        grid_orders_groupbox = QGroupBox("Orders in grid")
        grid_orders_layout = QGridLayout()

        grid_orders_layout.addWidget(self.list_widget_orders, 0, 0)

        order_width_label = QLabel("Width")
        order_height_label = QLabel("Height")

        self.width_line_edit = QLineEdit()
        self.height_line_edit = QLineEdit()

        grid_orders_layout.addWidget(order_width_label, 1, 0)
        grid_orders_layout.addWidget(self.width_line_edit, 2, 0)

        grid_orders_layout.addWidget(order_height_label, 3, 0)
        grid_orders_layout.addWidget(self.height_line_edit, 4, 0)

        grid_orders_groupbox.setLayout(grid_orders_layout)


        self.grid_orders_layout.addWidget(grid_orders_groupbox)

        self.unstacked_orders_group_box = QGroupBox("New orders")
        unstacked_order_width_label = QLabel("Width")
        unstacked_order_height_label = QLabel("Height")
        
        self.unstacked_orders_layout = QGridLayout()
        self.unstacked_orders_layout.addWidget(self.list_widget_new_orders, 0, 0)

        self.unstacked_order_width_line_edit = QLineEdit()
        self.unstacked_order_height_line_edit = QLineEdit()

        self.unstacked_orders_layout.addWidget(unstacked_order_width_label, 1, 0)
        self.unstacked_orders_layout.addWidget(self.unstacked_order_width_line_edit, 2, 0)        
        self.unstacked_orders_layout.addWidget(unstacked_order_height_label, 3, 0)
        self.unstacked_orders_layout.addWidget(self.unstacked_order_height_line_edit, 4, 0)

        self.unstacked_orders_group_box.setLayout(self.unstacked_orders_layout)
        self.grid_orders_layout.addWidget(self.unstacked_orders_group_box)

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
        """
        n = 5
        unstacked_rectangles = self.stacker.generateRandomRectangles(n)
        self.stacker.addToDatabase(unstacked_rectangles)
        self.refreshNewOrders()
        """
        
        file_name = "/home/fmeccanici/Documents/2d_rectangle_packing/documents/paklijst.xlsx"

        df = pd.read_excel(file_name, sheet_name=None)
        df = df['Paklijst']
        df = df.drop([0, 1, 2, 3])
        df.columns = ['Aantal', 'Merk', 'Omschrijving', 'Breedte', 'Lengte', 'Orderdatum', 'Coupage/Batch', 'Ordernummer', 'Klantnaam']

        orders = df[['Breedte', 'Lengte', 'Ordernummer']]

        unstacked_rectangles = []
        for index, row in orders.iterrows():

            # try:
            #     width = float(row['Breedte'])

            # except ValueError:
            #     width = row['Breedte']

            #     print("Width string has comma")
            #     behind_comma = width.split(',')[0]
            #     after_comma = width.split(',')[1]
            #     width = float(behind_comma + '.' + after_comma)
            
            # try:
            #     height = float(row['Lengte'])

            # except ValueError:
                
            #     height = str(row['Lengte'])
            #     print("Height string has comma")

            #     behind_comma = height.split(',')[0]
            #     after_comma = height.split(',')[1]
            #     width = float(behind_comma + '.' + after_comma)

            try:
                width = row['Breedte'].split(',')[0] + '.' + row['Breedte'].split(',')[1]
                print(width)
            except IndexError:
                width = row['Breedte'].split(',')[0]
            except AttributeError:
                width = row['Breedte']

            try:
                height = row['Lengte'].split(',')[0] + '.' + row['Lengte'].split(',')[1]
                print(height)
            except IndexError:
                height = row['Lengte'].split(',')[0]
            except AttributeError:
                height = row['Lengte']

            name = row['Ordernummer']

            width = float(width)
            height = float(height)
            rectangle = Rectangle(width, height, name)
            unstacked_rectangles.append(rectangle)

        self.stacker.addToDatabase(unstacked_rectangles)
        self.refreshNewOrders()

        # names = [x.getName() for x in unstacked_rectangles]
        # print(sorted(names))
        # print(len(names))
        # print(len(np.unique(names)))
        

    def onLoadOrdersClick(self):
        self.loadOrders()

    def onMakeDatabaseBackupClick(self):
        self.db_manager.makeBackup()

    def onExportClick(self):
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)
        
        if self.export_dxf_radio_button.isChecked():
            grid.toPrimeCenterFormatDxf()
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
            list_widget_current = self.list_widget_cut_grids
            list_widget_next = self.list_widget_grids

        elif current_grid_state == 'uncut':
            list_widget_current = self.list_widget_grids
            list_widget_next = self.list_widget_cut_grids

        grid_number = int(list_widget_current.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)
        
        if current_grid_state == 'cut':
            grid.setUncut()
        elif current_grid_state == 'uncut':
            grid.setCut()

        self.db_manager.updateGrid(grid)

        item = list_widget_current.findItems(list_widget_current.currentItem().text(), Qt.MatchExactly)
        row = list_widget_current.row(item[0])
        list_widget_current.takeItem(row)
        list_widget_next.addItem(item[0])

    def onDoubleClickOrder(self):
        self.updateOrder('stacked')

    def onDoubleClickNewOrder(self):
        self.updateOrder('unstacked')
    
    def updateOrder(self, order_state='stacked'):
        if order_state == 'stacked':
            list_widget = self.list_widget_orders
        elif order_state == 'unstacked':
            list_widget = self.list_widget_new_orders

        rectangle_number = int(list_widget.currentItem().text().split(' ')[1])
        rectangle = self.db_manager.getRectangle(rectangle_number)

        if rectangle.isStacked():
            if self.previous_rectangle is not None:
                self.drawRectangle(self.previous_rectangle)

            self.drawRectangle(rectangle, color=Qt.red)
            self.current_rectangle = rectangle_number
            self.previous_rectangle = rectangle

        self.updateWidthHeight(rectangle)

    def updateWidthHeight(self, rectangle):
        if rectangle.isStacked():
            self.width_line_edit.setText(str(rectangle.getWidth()) + 'cm')
            self.height_line_edit.setText(str(rectangle.getHeight()) + 'cm')
        else:
            self.unstacked_order_width_line_edit.setText(str(rectangle.getWidth()) + 'cm')
            self.unstacked_order_height_line_edit.setText(str(rectangle.getHeight()) + 'cm')

    def onDoubleClickGrid(self):
        self.refreshGrid()
        self.previous_rectangle = None
        self.width_line_edit.setText("")
        self.height_line_edit.setText("")
        
    def onDoubleClickCutGrid(self):
        self.refreshCutGrid()

    def createGridOrdersEvents(self):
        self.list_widget_orders.itemDoubleClicked.connect(self.onDoubleClickOrder)
        self.list_widget_new_orders.itemDoubleClicked.connect(self.onDoubleClickNewOrder)

        self.list_widget_grids.itemDoubleClicked.connect(self.onDoubleClickGrid)
        self.list_widget_cut_grids.itemDoubleClicked.connect(self.onDoubleClickCutGrid)

    def updateCodeStatus(self, text):
        self.code_status_line_edit.setText(text)

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
        code_status_label = QLabel("Status")
        self.code_status_line_edit = QLineEdit()

        layout.addWidget(code_status_label)
        layout.addWidget(self.code_status_line_edit)

        group_box.setLayout(layout)
        self.buttons_layout.addWidget(group_box)

        self.cut_button = QPushButton("Cut")
        self.uncut_button = QPushButton("Uncut")

        self.buttons_layout.addWidget(self.cut_button)
        self.buttons_layout.addWidget(self.uncut_button)


        self.buttons_layout.addStretch()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    clock = RectanglePackingGui()
    clock.show()
    sys.exit(app.exec_())