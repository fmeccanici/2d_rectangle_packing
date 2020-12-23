# my own classes
from rectangle_packing.database_manager import DatabaseManager
from rectangle_packing.grid import Grid
from rectangle_packing.stacker import Stacker
from rectangle_packing.rectangle import Rectangle
from rectangle_packing.excel_parser import ExcelParser
from rectangle_packing.helper import Helper

# external dependencies
import sys, time
import os
from PyQt5 import QtWebEngineWidgets, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QThreadPool, QRunnable, pyqtSlot, QRect, QThread
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
                             QDialog)
from PyQt5.QtGui import QPainter, QBrush, QPen, QPixmap, QColor
import pandas as pd
import numpy as np



# used to trigger a popup window from other thread
# has to be in main thread to be executed without failing
class PopupWindowTriggerThread(QThread):    
    finished_stacking_signal = pyqtSignal(bool)
    def __init__(self, parent=None):
        super(PopupWindowTriggerThread, self).__init__(parent=parent)
        self.finished_stacking = False
    
    def setFinishedStacking(self, finished_stacking):
        self.finished_stacking = finished_stacking

    def run(self):
        while True:
            if self.finished_stacking:
                self.finished_stacking_signal.emit(True)
                self.finished_stacking = False
            time.sleep(10)
            
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

class Gui(QWidget):
    def __init__(self, parent=None):
        super(Gui, self).__init__(parent)
        # Other classes
        self.db_manager = DatabaseManager()
        self.stacker = Stacker()
        self.initExcel()

        # Multithreading
        self.threadpool = QThreadPool()
        self.popup_window_trigger_thread = PopupWindowTriggerThread(self)
        self.popup_window_trigger_thread.finished_stacking_signal.connect(self.displayPopupWindowFinishedStacking)
        self.popup_window_trigger_thread.start()
        
        # Create all the layouts and button events
        self.createButtonsLayout()
        self.createButtonEvents()
        self.createGridOrdersLayout()
        self.createGridDrawing()
        self.createGridOrdersEvents()

        self.createMainLayout()
        self.setLayout(self.main_layout)

        self.refreshNewOrders()

    def initExcel(self):
        desktop = Helper.getDesktopPath()
        path = desktop + "/paklijsten/"
        file_name = "paklijst.xlsx"
        self.excel_parser = ExcelParser(data_logger=self.stacker.getDataLogger(), path=path, file_name=file_name, sheet_name='Paklijst')
        self.stacker.setExcelParser(path=path, file_name=file_name)

    # this creates the middle side of the GUI
    def createButtonsLayout(self):
        self.buttons_layout = QVBoxLayout()

        group_box = QGroupBox("Grid")
        self.export_button = QPushButton("Export")
        self.export_dxf_radio_button = QRadioButton("DXF")
        self.export_pdf_radio_button = QRadioButton("PDF")
        self.export_html_radio_button = QRadioButton("HTML")
        self.export_pdf_radio_button.setChecked(True)
        self.create_grid_button = QPushButton("Create new")

        grid_layout = QGridLayout()
        grid_layout.addWidget(self.export_button, 0, 0)
        grid_layout.addWidget(self.export_dxf_radio_button, 1, 0)
        grid_layout.addWidget(self.export_pdf_radio_button, 2, 0)
        grid_layout.addWidget(self.export_html_radio_button, 1, 1)
        grid_layout.addWidget(self.create_grid_button, 3, 0)
        
        self.load_orders_button = QPushButton("Load new orders")
        self.clear_orders_button = QPushButton("Clear new orders")

        self.excel_file_line_edit = QLineEdit("tjeerd2.xlsm")
        
        self.grid_color_label = QLabel("Color")
        self.grid_color_line_edit = QLineEdit("Naturel")

        self.grid_brand_label = QLabel("Brand")
        self.grid_brand_line_edit = QLineEdit("Kokos")

        grid_layout.addWidget(self.grid_color_label, 4, 0)
        grid_layout.addWidget(self.grid_brand_label, 4, 1)

        grid_layout.addWidget(self.grid_color_line_edit, 5, 0)
        grid_layout.addWidget(self.grid_brand_line_edit, 5, 1)
        
        self.create_grid_grid_width_label = QLabel("Width")
        self.create_grid_grid_width_line_edit = QLineEdit("100")

        grid_layout.addWidget(self.create_grid_grid_width_label, 6, 0)
        grid_layout.addWidget(self.create_grid_grid_width_line_edit, 7, 0)

        self.cut_button = QPushButton("Cut")
        self.uncut_button = QPushButton("Uncut")
        grid_layout.addWidget(self.cut_button, 8, 0)
        grid_layout.addWidget(self.uncut_button, 9, 0)

        self.empty_grid_button = QPushButton("Empty")
        self.remove_grid_button = QPushButton("Remove")

        grid_layout.addWidget(self.empty_grid_button, 8, 1)
        grid_layout.addWidget(self.remove_grid_button, 9, 1)

        group_box.setLayout(grid_layout)
        self.buttons_layout.addWidget(group_box)
        
        self.make_database_backup_button = QPushButton("Make database backup")
        self.clear_database_button = QPushButton("Clear database")

        self.buttons_layout.addWidget(self.load_orders_button)
        self.buttons_layout.addWidget(self.excel_file_line_edit)
        self.buttons_layout.addWidget(self.clear_orders_button)

        self.buttons_layout.addWidget(self.make_database_backup_button)
        self.buttons_layout.addWidget(self.clear_database_button)

        group_box = QGroupBox("Stacking")
        layout = QVBoxLayout()
        self.start_stacking_button = QPushButton("Start")
        self.stop_stacking_button = QPushButton("Stop")
        self.start_stacking_automatic_button = QPushButton("Automatic")
        
        standard_orders_layout = QGridLayout()
        self.standard_orders_label = QLabel("Standard orders")
        self.standard_order_60_80_checkbox = QCheckBox("60 x 80")
        self.standard_order_60_80_checkbox.setChecked(True)
        self.standard_order_100_80_checkbox = QCheckBox("100 x 80")
        self.standard_order_50_80_checkbox = QCheckBox("50 x 80")
        self.standard_order_40_70_checkbox = QCheckBox("40 x 70")

        layout.addWidget(self.start_stacking_button)
        layout.addWidget(self.stop_stacking_button)
        layout.addWidget(self.start_stacking_automatic_button)
        layout.addWidget(self.standard_orders_label)
        
        standard_orders_layout.addWidget(self.standard_order_60_80_checkbox, 0, 0)
        standard_orders_layout.addWidget(self.standard_order_100_80_checkbox, 1, 0)
        standard_orders_layout.addWidget(self.standard_order_50_80_checkbox, 0, 1)
        standard_orders_layout.addWidget(self.standard_order_40_70_checkbox, 1, 1)
        layout.addLayout(standard_orders_layout)

        self.fill_orders_with_smaller_in_larger_grid_widths_radiobutton = QRadioButton("Fill orders with smaller grid widths in larger ones")
        self.fill_orders_with_smaller_in_larger_grid_widths_radiobutton.setChecked(True)
        layout.addWidget(self.fill_orders_with_smaller_in_larger_grid_widths_radiobutton)

        code_status_label = QLabel("Status")
        self.code_status_line_edit = QLineEdit()

        layout.addWidget(code_status_label)
        layout.addWidget(self.code_status_line_edit)

        group_box.setLayout(layout)
        self.buttons_layout.addWidget(group_box)

        self.buttons_layout.addStretch()

    def createButtonEvents(self):
        self.create_grid_button.clicked.connect(self.onCreateGridClick)
        self.empty_grid_button.clicked.connect(self.onEmptyGridClick)
        self.remove_grid_button.clicked.connect(self.onRemoveGridClick)

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

    def useMultithread(self, function):
        worker = Worker(function)
        self.threadpool.start(worker)

    def onCreateGridClick(self):
        brand = self.grid_brand_line_edit.text()
        width = self.create_grid_grid_width_line_edit.text()
        color = self.grid_color_line_edit.text()
        grid = self.db_manager.createUniqueGrid(width=width, brand=brand, color=color)

        list_widget_item = QListWidgetItem("Grid " + str(grid.getName())) 
        self.list_widget_grids.addItem(list_widget_item) 

        self.list_widget_grids.repaint()

    def onEmptyGridClick(self):
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)

        self.db_manager.emptyGrid(grid)
        self.refreshGrids()
        self.refreshNewOrders()

    def refreshNewOrders(self):
        self.removeAllNewOrderItems()
        unstacked_rectangles = self.db_manager.getUnstackedRectangles()
        
        for rectangle in unstacked_rectangles:
            list_widget_item = QListWidgetItem("Order " + str(rectangle.getName())) 
            self.list_widget_new_orders.addItem(list_widget_item) 
    
    def removeAllNewOrderItems(self):
        self.list_widget_new_orders.clear()

    def removeAllOrderItems(self):
        self.list_widget_orders.clear()
    
    def refreshGrids(self):
        grids = self.db_manager.getGridsNotCut()

        self.list_widget_grids.clear()

        for grid in grids:
            list_widget_item = QListWidgetItem("Grid " + str(grid.getName())) 
            self.list_widget_grids.addItem(list_widget_item) 

    def onRemoveGridClick(self):
        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)
        self.removeGridItem(remove_completely=True)

    def onStartStackingClick(self):
        self.loadOrders()
        self.stacker.startStacking()

        grid_number = int(self.list_widget_grids.currentItem().text().split(' ')[1])
        grid = self.db_manager.getGrid(grid_number)
        self.updateCodeStatus("Stacking started for grid " + str(grid_number))
        self.stacker.setGrid(grid)
        self.setFillParameters()
        self.stacker.start(automatic=False)
        self.refreshGrid(grid_number)
        self.refreshNewOrders()
        self.updateCodeStatus("Done with stacking grid " + str(grid_number) + "!")
    
    def updateCodeStatus(self, text):
        self.code_status_line_edit.setText(text)

    def onStopStackingClick(self):
        self.stacker.stopStacking()

    def onStartStackingAutomaticClick(self):
        self.setFillParameters()
        self.loadOrdersCreateNecessaryGridsAndStartStacking()        
        
        # signal thread that we should execute popup window 
        self.popup_window_trigger_thread.setFinishedStacking(True)
        
    def displayPopupWindowFinishedStacking(self):
        self.popup_window = QMessageBox()
        popup_message = ""
        popup_message += str(self.stacker.getDataLogger().getSuccessfullyStackedRectangles()) + "/" + str(self.stacker.getDataLogger().getTotalRectanglesToStack()) + " succesfully stacked orders \n \n"
        popup_message += "Total execution time is " + str(round(self.stacker.getDataLogger().getTotalExecutionTime()/60, 2)) + "min \n \n"
        popup_message += str(self.stacker.getDataLogger().getAmountOfErrors()) + " errors occured: \n"
        if self.stacker.getDataLogger().getAmountOfErrors() > 0:
            for error in self.stacker.getDataLogger().getErrorData():
                popup_message += str(error) + "\n"

        self.popup_window.setText(popup_message)
        self.popup_window.setIcon(QMessageBox.Information)
        self.popup_window.setWindowTitle("Stacker finished")

        # https://stackoverflow.com/questions/6087887/bring-window-to-front-raise-show-activatewindow-don-t-work
        self.popup_window.setWindowState(self.popup_window.windowState() & ~Qt.WindowActive)
        self.popup_window.show()
        self.popup_window.activateWindow()
        
    def setFillParameters(self):
        standard_sizes = []
        if self.standard_order_60_80_checkbox.isChecked():
            standard_sizes.append((60, 80))
        if self.standard_order_100_80_checkbox.isChecked():
            standard_sizes.append((100, 80))        
        if self.standard_order_50_80_checkbox.isChecked():
            standard_sizes.append((50, 80))
        if self.standard_order_40_70_checkbox.isChecked():
            standard_sizes.append((40, 70))
        self.stacker.setStandardSizesToFill(standard_sizes)

        if self.fill_orders_with_smaller_in_larger_grid_widths_radiobutton.isChecked():
            self.stacker.setFillOrdersWithSmallerGridWidths(True)
        else:
            self.stacker.setFillOrdersWithSmallerGridWidths(False)

    def loadOrdersCreateNecessaryGridsAndStartStacking(self):
        self.updateCodeStatus("Creating grids, stacking and exporting. Please wait...")
        self.stacker.start(automatic=True)
        self.refreshGrids()
        self.refreshNewOrders()
        self.updateCodeStatus("Done with automatic stacking!")

    def onLoadOrdersClick(self):
        self.loadOrders()
    
    def loadOrders(self):
        file_name = self.excel_file_line_edit.text()
        desktop = Helper.getDesktopPath() 
        path = desktop + "/paklijsten/"

        self.excel_parser.setFileName(file_name)
        self.stacker.setExcelParser(path=path, file_name=file_name)

        unstacked_rectangles = self.excel_parser.getUnstackedRectangles()
        self.db_manager.addRectangles(unstacked_rectangles)
        self.refreshNewOrders()
    
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
            self.stacker.convertRectanglesToMillimetersOptimizeAndExportGrid()
        elif self.export_pdf_radio_button.isChecked():
            grid.toPdf()
        elif self.export_html_radio_button.isChecked():
            grid.toHtml()

    def onCutClick(self):
        self.removeGridItem('uncut')

    def onUncutClick(self):
        self.removeGridItem('cut')

    def removeGridItem(self, current_grid_state='uncut', remove_completely=False):
        
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

        if not remove_completely:
            self.db_manager.updateGrid(grid)
        else:
            self.db_manager.removeGrid(grid)

        item = list_widget_current.findItems(list_widget_current.currentItem().text(), Qt.MatchExactly)
        row = list_widget_current.row(item[0])
        list_widget_current.takeItem(row)
        
        if not remove_completely:
            list_widget_next.addItem(item[0])

    def createGridOrdersLayout(self):
        self.grid_orders_layout = QVBoxLayout()

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

    def createGridDrawing(self):
        self.grid_drawing = QtWidgets.QLabel()

        # TODO relative to window size
        self.canvas_width, self.canvas_height = 200, 1000
        self.max_rectangle_width, self.max_rectangle_height = Rectangle.getMaximumSize() #cm
        
        self.previous_rectangle = None

        self.canvas = QPixmap(self.canvas_width, self.canvas_height)
        color = QColor(255, 255, 255)
        self.canvas.fill(color)
        self.grid_drawing.setPixmap(self.canvas)

    def createGridOrdersEvents(self):
        self.list_widget_orders.itemDoubleClicked.connect(self.onDoubleClickOrder)
        self.list_widget_new_orders.itemDoubleClicked.connect(self.onDoubleClickNewOrder)

        self.list_widget_grids.itemDoubleClicked.connect(self.onDoubleClickGrid)
        self.list_widget_cut_grids.itemDoubleClicked.connect(self.onDoubleClickCutGrid)

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

    def refreshGrid(self, grid_number):        
        grid = self.db_manager.getGrid(grid_number)
        stacked_rectangles = grid.getStackedRectangles()
        self.stacker.setGrid(grid)
        
        self.uncut_color_line_edit.setText(grid.getColor())
        self.uncut_width_line_edit.setText(str(grid.getWidth()))
        self.uncut_brand_line_edit.setText(str(grid.getBrand()))

        self.drawGrid(grid)
        self.removeAllOrderItems()

        for rectangle in stacked_rectangles:
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

        x = int(x / self.max_rectangle_width * self.canvas_width)
        y = int(y / self.max_rectangle_height * self.canvas_height)

        width = int(width / self.max_rectangle_width * self.canvas_width)
        height = int(height / self.max_rectangle_height * self.canvas_height)

        painter.drawRect(x, y, width, height)

        painter.end()
        
        self.grid_drawing.update()
        QApplication.processEvents()

    def createMainLayout(self):
        # GUI is separated into three parts
        # Most left is the grid drawing
        # middle are all the buttons
        # right are the orders in the grids and unstacked orders
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.grid_drawing)
        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.addLayout(self.grid_orders_layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    clock = Gui()
    clock.show()
    sys.exit(app.exec_())