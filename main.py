import sys
import os

from PyQt5 import QtWebEngineWidgets, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QThreadPool, QRunnable, pyqtSlot, QRect
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem, QMainWindow)
from PyQt5.QtGui import QPainter, QBrush, QPen, QPixmap, QColor

from rectangle_packing.database_manager import DatabaseManager
from rectangle_packing.stacked_grid import StackedGrid
from rectangle_packing.stacker import Stacker, InvalidGridPositionError
from rectangle_packing.rectangle import Rectangle
from rectangle_packing.excel_parser import ExcelParser

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
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') 
        path = desktop + "/paklijsten/"
        
        file_name = "paklijst.xlsx"

        self.excel_parser = ExcelParser(path, file_name)
        self.stacker.setExcelParser(path, file_name)

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
        print(x,y)
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

    def onStartStackingAutomaticClick(self):
        self.loadOrdersCreateNecessaryGridsAndStartStacking()

    def loadOrdersCreateNecessaryGridsAndStartStacking(self):
        self.updateCodeStatus("Creating grids, stacking and exporting. Please wait...")
        self.stacker.start()
        self.refreshGrids()
        self.refreshNewOrders()
        self.updateCodeStatus("Done with automatic stacking!")

    def onStartStackingClick(self):
        self.loadOrders()
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

                    if (grid.getBrand() == rectangle.getBrand()) and (grid.getColor() == rectangle.getColor()) and (grid.getWidth() == rectangle.getGridWidth()):
                        self.stacker.computeStackingPositionAndUpdateDatabase(rectangle, grid)
                        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])

                        self.refreshGrid(grid_number)
                        self.refreshNewOrders()
                        self.updateCodeStatus("Order " + str(rectangle.getName()) + " stacked")
                    else:
                        print("Colors don't match")
                        self.updateCodeStatus("Order has color " + str(rectangle.getColor()) + ", grid has color " + str(grid.getColor()))
                except InvalidGridPositionError:
                    print("Rectangle does not fit")
                    self.updateCodeStatus("Order " + str(rectangle.getName()) + " does not fit")
            else:
                self.updateCodeStatus("Stacking stopped")
                break

        self.updateCodeStatus("Stacking stopped")

    def onStopStackingClick(self):
        self.stacker.stopStacking()
        
    def refreshGrid(self, grid_number):        
        grid = self.db_manager.getGrid(grid_number)

        self.uncut_color_line_edit.setText(grid.getColor())
        self.uncut_width_line_edit.setText(str(grid.getWidth()))
        self.uncut_brand_line_edit.setText(str(grid.getBrand()))

        self.drawGrid(grid)
        self.removeAllOrderItems()

        for rectangle in grid.getStackedRectangles():
            list_widget_item = QListWidgetItem("Order " + str(rectangle.getName())) 
            self.list_widget_orders.addItem(list_widget_item) 
        
        QApplication.processEvents()

    def refreshCutGrid(self):
        grid_number = int(self.list_widget_cut_grids.currentItem().text().split(' ')[1])
        
        grid = self.db_manager.getGrid(grid_number)

        self.cut_color_line_edit.setText(grid.getColor())
        self.cut_width_line_edit.setText(str(grid.getWidth()))
        self.cut_brand_line_edit.setText(str(grid.getBrand()))

        self.drawGrid(grid)
        self.removeAllOrderItems()

        for rectangle in grid.getStackedRectangles():
            list_widget_item = QListWidgetItem("Order " + str(rectangle.getName())) 
            self.list_widget_orders.addItem(list_widget_item) 
        
        QApplication.processEvents()

    def removeAllOrderItems(self):
        self.list_widget_orders.clear()

    def onLoadGridClick(self):
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        self.refreshGrid(grid_number)


    def refreshGrids(self):
        grids = self.db_manager.getGridsNotCut()

        self.list_widget_grids.clear()

        for grid in grids:
            list_widget_item = QListWidgetItem("Grid " + str(grid.getName())) 
            self.list_widget_grids.addItem(list_widget_item) 

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
        
        cut_color_label = QLabel("Color")
        cut_width_label = QLabel("Width")
        cut_brand_label = QLabel("Brand")

        self.cut_color_line_edit = QLineEdit()
        self.cut_width_line_edit = QLineEdit()
        self.cut_brand_line_edit = QLineEdit()

        uncut_color_label = QLabel("Color")
        uncut_width_label = QLabel("Width")
        uncut_brand_label = QLabel("Brand")

        self.uncut_color_line_edit = QLineEdit()
        self.uncut_width_line_edit = QLineEdit()
        self.uncut_brand_line_edit = QLineEdit()

        self.cut_uncut_layout.addWidget(cut_color_label, 2, 1)
        self.cut_uncut_layout.addWidget(self.cut_color_line_edit, 3, 1)
        self.cut_uncut_layout.addWidget(cut_width_label, 4, 1)        
        self.cut_uncut_layout.addWidget(self.cut_width_line_edit, 5, 1)
        self.cut_uncut_layout.addWidget(cut_brand_label, 6, 1)        
        self.cut_uncut_layout.addWidget(self.cut_brand_line_edit, 7, 1)

        self.cut_uncut_layout.addWidget(uncut_color_label, 2, 0)
        self.cut_uncut_layout.addWidget(self.uncut_color_line_edit, 3, 0)
        self.cut_uncut_layout.addWidget(uncut_width_label, 4, 0)
        self.cut_uncut_layout.addWidget(self.uncut_width_line_edit, 5, 0)
        self.cut_uncut_layout.addWidget(uncut_brand_label, 6, 0)        
        self.cut_uncut_layout.addWidget(self.uncut_brand_line_edit, 7, 0)

        
        cut_uncut_group_box.setLayout(self.cut_uncut_layout)
        self.grid_orders_layout.addWidget(cut_uncut_group_box)

        grid_orders_groupbox = QGroupBox("Orders in grid")
        grid_orders_layout = QGridLayout()

        grid_orders_layout.addWidget(self.list_widget_orders, 0, 0)

        order_width_label = QLabel("Width")
        order_height_label = QLabel("Height")
        order_color_label = QLabel("Color")
        order_grid_width_label = QLabel("Grid width")
        order_brand_label = QLabel("Brand")

        self.width_line_edit = QLineEdit()
        self.height_line_edit = QLineEdit()
        self.color_line_edit = QLineEdit()
        self.grid_width_line_edit = QLineEdit()
        self.brand_line_edit = QLineEdit()

        grid_orders_layout.addWidget(order_width_label, 1, 0)
        grid_orders_layout.addWidget(self.width_line_edit, 2, 0)

        grid_orders_layout.addWidget(order_height_label, 3, 0)
        grid_orders_layout.addWidget(self.height_line_edit, 4, 0)

        grid_orders_layout.addWidget(order_color_label, 1, 1)
        grid_orders_layout.addWidget(self.color_line_edit, 2, 1)

        grid_orders_layout.addWidget(order_grid_width_label, 3, 1)
        grid_orders_layout.addWidget(self.grid_width_line_edit, 4, 1)

        grid_orders_layout.addWidget(order_brand_label, 5, 1)
        grid_orders_layout.addWidget(self.brand_line_edit, 6, 1)


        grid_orders_groupbox.setLayout(grid_orders_layout)


        self.grid_orders_layout.addWidget(grid_orders_groupbox)

        self.unstacked_orders_group_box = QGroupBox("New orders")
        unstacked_order_width_label = QLabel("Width")
        unstacked_order_height_label = QLabel("Height")
        unstacked_order_color_label = QLabel("Color")
        unstacked_order_grid_width_label = QLabel("Grid width")
        unstacked_order_brand_label = QLabel("Brand")

        self.unstacked_orders_layout = QGridLayout()
        self.unstacked_orders_layout.addWidget(self.list_widget_new_orders, 0, 0)

        self.unstacked_order_width_line_edit = QLineEdit()
        self.unstacked_order_height_line_edit = QLineEdit()
        self.unstacked_order_color_line_edit = QLineEdit()
        self.unstacked_order_grid_width_line_edit = QLineEdit()
        self.unstacked_order_brand_line_edit = QLineEdit()

        self.unstacked_orders_layout.addWidget(unstacked_order_width_label, 1, 0)
        self.unstacked_orders_layout.addWidget(self.unstacked_order_width_line_edit, 2, 0)        
        self.unstacked_orders_layout.addWidget(unstacked_order_height_label, 3, 0)
        self.unstacked_orders_layout.addWidget(self.unstacked_order_height_line_edit, 4, 0)

        self.unstacked_orders_layout.addWidget(unstacked_order_color_label, 1, 1)
        self.unstacked_orders_layout.addWidget(self.unstacked_order_color_line_edit, 2, 1)
        self.unstacked_orders_layout.addWidget(unstacked_order_grid_width_label, 3, 1)
        self.unstacked_orders_layout.addWidget(self.unstacked_order_grid_width_line_edit, 4, 1)

        self.unstacked_orders_layout.addWidget(unstacked_order_brand_label, 5, 1)
        self.unstacked_orders_layout.addWidget(self.unstacked_order_brand_line_edit, 6, 1)

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
        brand = 'kokos'
        if self.grid_width1_radio_button.isChecked():
            width = 100
        elif self.grid_width2_radio_button.isChecked():
            width = 200

        if self.color_antraciet_radio_button.isChecked():
            color = 'antraciet'
        elif self.color_blauw_radio_button.isChecked():
            color = 'blauw'
        elif self.color_bordeaux_radio_button.isChecked():
            color = 'bordeaux'
        elif self.color_bruin_radio_button.isChecked():
            color = 'bruin'
        elif self.color_bruin_terra_radio_button.isChecked():
            color = 'bruin-terra'
        elif self.color_grijs_radio_button.isChecked():
            color = 'grijs'
        elif self.color_naturel_radio_button.isChecked():
            color = 'naturel'
        elif self.color_rood_bordeaux_radio_button.isChecked():
            color = 'rood-bordeaux'
        elif self.color_rood_radio_button.isChecked():
            color = 'rood'
        elif self.color_terra_radio_button.isChecked():
            color = 'terra'
        elif self.color_zwart_grijs_radio_button.isChecked():
            color = 'zwart-grijs'
        elif self.color_zwart_radio_button.isChecked():
            color = 'zwart'

        print("color = " + str(color))
        grid = self.db_manager.createUniqueGrid(width=width, brand=brand, color=color)

        list_widget_item = QListWidgetItem("Grid " + str(grid.getName())) 
        self.list_widget_grids.addItem(list_widget_item) 

        self.list_widget_grids.repaint()

    def createButtonEvents(self):
        # self.load_grid_button.clicked.connect(self.onLoadGridClick)
        self.create_grid_button.clicked.connect(self.onCreateGridClick)
        self.empty_grid_button.clicked.connect(self.onEmptyGridClick)

        self.start_stacking_button.clicked.connect(lambda: self.useMultithread(self.onStartStackingClick))
        self.stop_stacking_button.clicked.connect(lambda: self.useMultithread(self.onStopStackingClick))
        self.start_stacking_automatic_button.clicked.connect(lambda: self.useMultithread(self.onStartStackingAutomaticClick))

        self.load_orders_button.clicked.connect(self.onLoadOrdersClick)
        self.clear_orders_button.clicked.connect(self.onClearNewOrdersClick)

        self.make_database_backup_button.clicked.connect(self.onMakeDatabaseBackupClick)
        self.clear_database_button.clicked.connect(self.onClearDatabaseClick)

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
        file_name = self.excel_file_line_edit.text()
        # path = os.getcwd() + "/paklijsten/"
        desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') 
        path = desktop + "/paklijsten/"

        self.excel_parser.setFileName(file_name)
        self.stacker.setExcelParser(path, file_name)
        
        unstacked_rectangles = self.excel_parser.getOrders()

        self.stacker.addToDatabase(unstacked_rectangles)
        self.refreshNewOrders()

        # names = [x.getName() for x in unstacked_rectangles]
        # print(sorted(names))
        # print(len(names))
        # print(len(np.unique(names)))
        

    def onLoadOrdersClick(self):
        self.loadOrders()

    def onClearNewOrdersClick(self):
        self.db_manager.clearNewOrders()
        self.refreshNewOrders()

    def onMakeDatabaseBackupClick(self):
        self.db_manager.makeBackup()

    def onClearDatabaseClick(self):
        self.db_manager.clearDatabase()
        self.refreshGrids()
        self.refreshNewOrders()

    def onExportClick(self):
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number, for_cutting=True)
        
        if self.export_dxf_radio_button.isChecked():
            # grid.toPrimeCenterFormatDxf()
            # grid.toDxf()
            self.stacker.optimizeAndExportGrid(grid)

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

        rectangle_number = str(list_widget.currentItem().text().split(' ')[1])
        rectangle = self.db_manager.getRectangle(rectangle_number, for_cutting=True)

        if rectangle.isStacked():
            if self.previous_rectangle is not None:
                self.drawRectangle(self.previous_rectangle)

            self.drawRectangle(rectangle, color=Qt.red)
            self.current_rectangle = rectangle_number
            self.previous_rectangle = rectangle

        self.updateWidthHeightColorGridWidthBrand(rectangle)
        
    def updateWidthHeightColorGridWidthBrand(self, rectangle):
        if rectangle.isStacked():
            self.width_line_edit.setText(str(rectangle.getWidth() * 10) + 'mm')
            self.height_line_edit.setText(str(rectangle.getHeight() * 10) + 'mm')
            self.color_line_edit.setText(str(rectangle.getColor()))
            self.grid_width_line_edit.setText(str(rectangle.getGridWidth()))
            self.brand_line_edit.setText(str(rectangle.getBrand()))

        else:
            self.unstacked_order_width_line_edit.setText(str(rectangle.getWidth() * 10) + 'mm')
            self.unstacked_order_height_line_edit.setText(str(rectangle.getHeight() * 10) + 'mm')
            self.unstacked_order_color_line_edit.setText(str(rectangle.getColor()))
            self.unstacked_order_grid_width_line_edit.setText(str(rectangle.getGridWidth()))
            self.unstacked_order_brand_line_edit.setText(str(rectangle.getBrand()))

    def onDoubleClickGrid(self):
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])

        self.refreshGrid(grid_number)
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
        self.clear_orders_button = QPushButton("Clear new orders")

        self.excel_file_line_edit = QLineEdit("paklijst_bug_2_aantal_ambiant.xlsx")
        
        self.create_grid_button = QPushButton("Create new grid")
        self.color_naturel_radio_button = QRadioButton("Naturel")
        self.color_naturel_radio_button.setChecked(True)
        self.color_zwart_radio_button = QRadioButton("Zwart")
        self.color_antraciet_radio_button = QRadioButton("Antraciet")
        self.color_grijs_radio_button = QRadioButton("Grijs")
        self.color_rood_radio_button = QRadioButton("Rood")
        self.color_bruin_terra_radio_button = QRadioButton("Bruin-Terra")
        self.color_zwart_grijs_radio_button = QRadioButton("Zwart-Grijs")
        self.color_rood_bordeaux_radio_button = QRadioButton("Rood-Bordeaux")
        self.color_terra_radio_button = QRadioButton("Terra")
        self.color_bordeaux_radio_button = QRadioButton("Bordeaux")
        self.color_blauw_radio_button = QRadioButton("Blauw")
        self.color_bruin_radio_button = QRadioButton("Bruin")
        self.color_buttons_layout = QGridLayout()
        self.color_buttons_layout.addWidget(self.color_naturel_radio_button, 0, 0)
        self.color_buttons_layout.addWidget(self.color_zwart_radio_button, 1, 0)
        self.color_buttons_layout.addWidget(self.color_antraciet_radio_button, 2, 0)
        self.color_buttons_layout.addWidget(self.color_grijs_radio_button, 0, 1)
        self.color_buttons_layout.addWidget(self.color_rood_radio_button, 1, 1)
        self.color_buttons_layout.addWidget(self.color_bruin_terra_radio_button, 2, 1)
        self.color_buttons_layout.addWidget(self.color_zwart_grijs_radio_button, 0, 2)
        self.color_buttons_layout.addWidget(self.color_rood_bordeaux_radio_button, 1, 2)
        self.color_buttons_layout.addWidget(self.color_terra_radio_button, 2, 2)
        self.color_buttons_layout.addWidget(self.color_bordeaux_radio_button, 0, 3)
        self.color_buttons_layout.addWidget(self.color_blauw_radio_button, 1, 3)
        self.color_buttons_layout.addWidget(self.color_bruin_radio_button, 2, 3)
        self.color_buttons_groupbox = QGroupBox("Colors")
        self.color_buttons_groupbox.setLayout(self.color_buttons_layout)
        
        self.grid_width_groupbox = QGroupBox("Width")
        self.grid_width_layout = QGridLayout()
        self.grid_width1_radio_button = QRadioButton("100cm")
        self.grid_width2_radio_button = QRadioButton("200cm")
        self.grid_width1_radio_button.setChecked(True)
        self.grid_width_layout.addWidget(self.grid_width1_radio_button, 0, 0)
        self.grid_width_layout.addWidget(self.grid_width2_radio_button, 1, 0)
        self.grid_width_groupbox.setLayout(self.grid_width_layout)

        self.empty_grid_button = QPushButton("Empty grid")

        self.make_database_backup_button = QPushButton("Make database backup")
        self.clear_database_button = QPushButton("Clear database")


        # self.buttons_layout.addWidget(self.load_grid_button)
        self.buttons_layout.addWidget(self.create_grid_button)
        self.buttons_layout.addWidget(self.color_buttons_groupbox)
        self.buttons_layout.addWidget(self.grid_width_groupbox)

        self.buttons_layout.addWidget(self.empty_grid_button)

        self.buttons_layout.addWidget(self.load_orders_button)
        self.buttons_layout.addWidget(self.clear_orders_button)

        self.buttons_layout.addWidget(self.excel_file_line_edit)

        self.buttons_layout.addWidget(self.make_database_backup_button)
        self.buttons_layout.addWidget(self.clear_database_button)

        group_box = QGroupBox("Stacking")
        layout = QVBoxLayout()
        self.start_stacking_button = QPushButton("Start")
        self.stop_stacking_button = QPushButton("Stop")
        self.start_stacking_automatic_button = QPushButton("Automatic")

        layout.addWidget(self.start_stacking_button)
        layout.addWidget(self.stop_stacking_button)
        layout.addWidget(self.start_stacking_automatic_button)

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