from rectangle_packing.helper import Helper
from rectangle_packing.rectangle import Rectangle
from rectangle_packing.grid import Grid

import xml.etree.cElementTree as ET
from xml.etree.ElementTree import ElementTree

import ezdxf
from datetime import datetime
from xml.dom import minidom
import copy

class ZccCreator(object):
    def __init__(self, grid=Grid(), coupage=Rectangle()):
        self.zcc_path = Helper.createAndGetFolderOnDesktop('zcc')
        self.grid = grid
        self.coupage = coupage

        Helper.createAndGetFolderOnDesktop("zcc")

    def setGrid(self, grid):
        self.grid = grid

    def getGrid(self):
        return self.grid

    def setCoupage(self, coupage):
        self.coupage = coupage

    def getCoupage(self):
        return self.coupage

    def createCoupageZcc(self):
        self.createInitialTemplate()
        self.addMaterial()
        self.addCoupageGeometry()
        self.addLabel()
        self.addRegister()

    def createGridZcc(self):
        self.createInitialTemplate()
        self.addMaterial()
        self.addGridGeometry()
        self.addRegister()

    def fillXmlWithLineTo(self, x, y):
        ET.SubElement(self.outline, "LineTo", {"X": str(int(x)), "Y": str(int(y))})

    def fillXmlWithMoveTo(self, x, y):
        ET.SubElement(self.outline, "MoveTo", {"X": str(int(x)), "Y": str(int(y))})

    def fillXmlWithMethod(self, parent, method_type, name):
        ET.SubElement(parent, "Method", {"Type": method_type, "Name": name})
        
    def createInitialTemplate(self):
        self.root = ET.Element("ZCC_cmd", {"MessageID": "887", "CommandID": "jobdescription", 
        "xsi:noNamespaceSchemaLocation": "file:ZCC_cmd.xsd", "Version": "3026",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance", "xmlns:zcc": "www.zund.com/ZCC"})
        self.job = ET.SubElement(self.root, "Job", {"Name": self.dxf_file_name + "-1.zcc"})
        self.meta = ET.SubElement(self.job, "Meta", {"Reserved": "9809"})
        
        self.description = ET.SubElement(self.meta, "Description")
        self.description.text = "DXF Import"

        self.priority = ET.SubElement(self.meta, "Priority")
        self.priority.text = "Low"

        self.creation = ET.SubElement(self.meta, "Creation", {"Name": "Cut Editor", 
        "Version": "3.2.6.9", "Date": Helper.getDateTimeZcc()})

    def addMaterial(self):
        self.material = ET.SubElement(self.job, "Material", {"Name": self.coupage.getMaterial()})
    
    def addCoupageGeometry(self):
        self.geometry = ET.SubElement(self.job, "Geometry")
        self.outline = ET.SubElement(self.geometry, "Outline")
        self.fillXmlWithMoveTo(0, 0)
        self.fillXmlWithLineTo(round(self.coupage.getHeight()*10, 3), 0)
        self.fillXmlWithLineTo(round(self.coupage.getHeight()*10, 3), round(self.coupage.getWidth()*10, 3))
        self.fillXmlWithLineTo(round(self.coupage.getHeight()*10, 3), round(self.coupage.getWidth()*10, 3))
        self.fillXmlWithLineTo(0, round(self.coupage.getWidth()*10, 3))
        self.fillXmlWithLineTo(0, 0)
        self.fillXmlWithMethod(self.outline, "Thru-cut", "0")
    
    def addGridGeometry(self):
        self.geometry = ET.SubElement(self.job, "Geometry")

        for r in self.grid.getStackedRectangles():
            rectangle = copy.deepcopy(r)
            print("before")
            print(rectangle.getTopLeft())
            rectangle.toPrimeCenterFormat()
            print("after")
            print(rectangle.getTopLeft())
            self.outline = ET.SubElement(self.geometry, "Outline")

            self.fillXmlWithMoveTo(rectangle.getBottomLeft()[0], rectangle.getBottomLeft()[1])
            self.fillXmlWithLineTo(rectangle.getBottomRight()[0], rectangle.getBottomRight()[1])
            self.fillXmlWithLineTo(rectangle.getTopRight()[0], rectangle.getTopRight()[1])
            self.fillXmlWithLineTo(rectangle.getTopLeft()[0], rectangle.getTopLeft()[1])
            self.fillXmlWithLineTo(rectangle.getBottomLeft()[0], rectangle.getBottomLeft()[1])
            
            self.label = ET.SubElement(self.geometry, "Label", {"Text": rectangle.getClientName(), 
            "Height": "100.00", "Angle": "0.000", "Deformation": "1.000"})
            self.label_position = ET.SubElement(self.label, "Position", {"X": str(round(rectangle.getBottomLeft()[0])), "Y": str(round(rectangle.getTopLeft()[1]))})
            self.label_method = ET.SubElement(self.label, "Method", {"Type": "{none}", "Name": "TEXT"})

        self.outline = ET.SubElement(self.geometry, "Outline")
        self.fillXmlWithLargeHorizontalLineAtTop()

    def fillXmlWithLargeHorizontalLineAtTop(self):

        y_start = Helper.toMillimeters(self.grid.getHighestVerticalPoint())
        x_start = 0
        y_end = Helper.toMillimeters(self.grid.getHighestVerticalPoint())
        x_end = Helper.toMillimeters(self.grid.getWidth() + 20)

        # x/y swapped for prime center
        self.fillXmlWithMoveTo(y_start, x_start)
        self.fillXmlWithLineTo(y_end, x_end)
        
    def addLabel(self):
        self.label = ET.SubElement(self.geometry, "Label", {"Text": self.coupage.getClientName(), 
        "Height": "100.00", "Angle": "0.000", "Deformation": "1.000"})
        self.label_position = ET.SubElement(self.label, "Position", {"X": "0.000", "Y": str(round(self.coupage.getWidth()*10, 3))})
        self.label_method = ET.SubElement(self.label, "Method", {"Type": "{none}", "Name": "TEXT"})
    
    def addRegister(self):
        self.methods = ET.SubElement(self.job, "Methods")
        self.method_register = ET.SubElement(self.methods, "Method", \
        {"Type": "Register", "Color": "000000", 
        "RegistrationType": "borderFrontRight"})
    
    def save(self, binary=True, string=True, grid=False, coupage=True):
        if coupage:
            self.dxf_path = Helper.createAndGetDxfFolder()
            self.dxf_file_name = self.coupage.getDxfFileName()
            # self.dxf = ezdxf.readfile(self.dxf_path + "/" + self.dxf_file_name)

            self.createCoupageZcc()

            if string:
                xmlstr = minidom.parseString(ET.tostring(self.root)).toprettyxml(indent = "   ", encoding='UTF-8')
                with open(self.getZccPath() + self.coupage.getDxfFileName() + ".zcc", 'wb+') as f:
                    f.write(xmlstr)
            if binary:
                tree = ElementTree(self.root)
                tree.write(open(self.getBinPath() + self.coupage.getDxfFileName() + ".zcc.BIN", 'wb+'))

        if grid:
            self.dxf_path = Helper.createAndGetDxfFolder()
            self.dxf_file_name = self.grid.getDxfFileName()
            # self.dxf = ezdxf.readfile(self.dxf_path + "/" + self.dxf_file_name)
            
            self.createGridZcc()
            xmlstr = minidom.parseString(ET.tostring(self.root)).toprettyxml(indent = "   ", encoding='UTF-8')
            with open(self.getZccPath() + self.grid.getDxfFileName() + ".zcc", 'wb+') as f:
                f.write(xmlstr)

    def getZccPath(self):
        return Helper.createAndGetFolderOnDesktop('zcc')
    
    def getBinPath(self):
        return Helper.createAndGetFolderOnDesktop('bin')
