import sys
import os

from PyQt5 import QtWebEngineWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem)

from database_manager import DatabaseManager

class RectanglePackingGui(QWidget):
    def __init__(self, parent=None):
        super(RectanglePackingGui, self).__init__(parent)
        # Other classes
        self.db_manager = DatabaseManager()
        
        # GUI related stuff
        self.main_layout = QHBoxLayout()
        self.buttons_layout = QVBoxLayout()
        self.grid_orders_layout = QVBoxLayout()
        
        self.createButtonsLayout()
        self.createGridOrdersLayout()
        grid_number = 2
        self.createGridHtmlViewer(grid_number)
        
        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.addLayout(self.grid_orders_layout)

        self.setLayout(self.main_layout)

    def createGridHtmlViewer(self, grid_number):
        self.grid_html_viewer = QtWebEngineWidgets.QWebEngineView()
        self.grid_html_viewer.load(QUrl().fromLocalFile(
            os.path.split(os.path.abspath(__file__))[0] + '/plots/stacked_grid_' + str(grid_number) + '.html'
        ))

        self.buttons_layout.addWidget(self.grid_html_viewer)

    def createGridOrdersLayout(self):
        list_widget_grids = QListWidget() 
        list_widget_item = QListWidgetItem("Grid 1") 
        list_widget_grids.addItem(list_widget_item) 

        self.grid_orders_layout.addWidget(list_widget_grids)

        list_widget_orders = QListWidget() 
        list_widget_item = QListWidgetItem("Order 999") 

        list_widget_orders.addItem(list_widget_item)

        self.grid_orders_layout.addWidget(list_widget_orders)


    def createButtonsLayout(self):

        export_to_dxf_button = QPushButton("Export to DXF")
        self.buttons_layout.addWidget(export_to_dxf_button)

        load_grid_button = QPushButton("Load")
        self.buttons_layout.addWidget(load_grid_button)

        start_stacking_button = QPushButton("Start stacking")
        self.buttons_layout.addWidget(start_stacking_button)

        cut_button = QPushButton("Cut")
        self.buttons_layout.addWidget(cut_button)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    clock = RectanglePackingGui()
    clock.show()
    sys.exit(app.exec_())