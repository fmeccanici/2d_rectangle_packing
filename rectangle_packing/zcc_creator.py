from rectangle_packing.helper import Helper

import xml.etree.cElementTree as ET
from xml.etree.ElementTree import ElementTree

import ezdxf
from datetime import datetime
from xml.dom import minidom
import copy

class ZccCreator(object):
    def __init__(self, material, file_name):
        self.zcc_path = Helper.createAndGetFolderOnDesktop('zcc')
        self.setMaterial(material)
        self.setFileName(file_name)
        self.createInitialTemplate()

    def setMaterial(self, material):
        self.material = material

    def getMaterial(self):
        return self.material
    
    def setFileName(self, file_name):
        self.file_name = file_name

    def getFileName(self):
        return self.file_name

    def createInitialTemplate(self):
        self.createRoot()

        self.addJob()
        self.addMeta()
        self.addDescription()
        self.addPriority()
        self.addCreation()

        self.addMaterial()
        
    def createRoot(self):
        self.root = ET.Element("ZCC_cmd", {"MessageID": "887", "CommandID": "jobdescription", 
        "xsi:noNamespaceSchemaLocation": "file:ZCC_cmd.xsd", "Version": "3026",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance", "xmlns:zcc": "www.zund.com/ZCC"})
    
    def addJob(self):
        self.job = ET.SubElement(self.root, "Job", {"Name": self.file_name + ".zcc"})

    def addMeta(self):
        self.meta = ET.SubElement(self.job, "Meta", {"Reserved": "9809"})

    def addDescription(self):                
        self.description = ET.SubElement(self.meta, "Description")
        self.description.text = "Stacker output"

    def addPriority(self):
        self.priority = ET.SubElement(self.meta, "Priority")
        self.priority.text = "Low"

    def addMaterial(self):
        self.material = ET.SubElement(self.job, "Material", {"Name": self.getMaterial()})

    def addCreation(self):
        self.creation = ET.SubElement(self.meta, "Creation", {"Name": "Cut Editor", 
        "Version": "3.2.6.9", "Date": Helper.getDateTimeZcc()})

    def fillXmlWithLineTo(self, x, y):
        ET.SubElement(self.outline, "LineTo", {"X": str(int(x)), "Y": str(int(y))})

    def fillXmlWithMoveTo(self, x, y):
        ET.SubElement(self.outline, "MoveTo", {"X": str(int(x)), "Y": str(int(y))})

    def addGrid(self, grid):
        self.geometry = ET.SubElement(self.job, "Geometry")

        for r in grid.getStackedRectangles():
            rectangle = copy.deepcopy(r)
            rectangle.toPrimeCenterFormat()
            self.addRectangleLabel(rectangle)

        for line in grid.lines_without_overlap:

            self.addOutline()

            self.addLineGeometry(line)
            self.addThruCutLayer()

        self.addOutline()
        self.fillXmlWithLargeHorizontalLineAtTop(grid)

    # coupage
    def addRectangle(self, rectangle):
        self.geometry = ET.SubElement(self.job, "Geometry")
        rectangle.toPrimeCenterFormat()
        self.addOutline()

        self.addRectangleGeometry(rectangle)
        self.addThruCutLayer()
        self.addRectangleLabel(rectangle)

    def addLineGeometry(self, line):
        self.fillXmlWithMoveTo(line.start_point[0], line.start_point[1])
        # self.fillXmlWithLineTo(line.start_point[0], line.start_point[1])
        self.fillXmlWithLineTo(line.end_point[0], line.end_point[1])

    def addRectangleGeometry(self, rectangle):
        self.fillXmlWithMoveTo(rectangle.getBottomLeft()[0], rectangle.getBottomLeft()[1])
        self.fillXmlWithLineTo(rectangle.getBottomRight()[0], rectangle.getBottomRight()[1])
        self.fillXmlWithLineTo(rectangle.getTopRight()[0], rectangle.getTopRight()[1])
        self.fillXmlWithLineTo(rectangle.getTopLeft()[0], rectangle.getTopLeft()[1])
        self.fillXmlWithLineTo(rectangle.getBottomLeft()[0], rectangle.getBottomLeft()[1])

    def addThruCutLayer(self):
        self.fillXmlWithMethod(self.outline, "Thru-cut", "0")
    
    def fillXmlWithMethod(self, parent, method_type, name):
        ET.SubElement(parent, "Method", {"Type": method_type, "Name": name})
        
    def addRectangleLabel(self, rectangle):
        self.label = ET.SubElement(self.geometry, "Label", {"Text": rectangle.getClientName(), 
        "Height": "100.00", "Angle": "0.000", "Deformation": "1.000"})
        self.label_position = ET.SubElement(self.label, "Position", {"X": str(round(rectangle.getBottomLeft()[0])), "Y": str(round(rectangle.getTopLeft()[1]))})
        self.label_method = ET.SubElement(self.label, "Method", {"Type": "{none}", "Name": "TEXT"})
    

    def addOutline(self):
        self.outline = ET.SubElement(self.geometry, "Outline")

    def fillXmlWithLargeHorizontalLineAtTop(self, grid):
        y_start = Helper.toMillimeters(grid.getHighestVerticalPoint())
        x_start = 0
        y_end = Helper.toMillimeters(grid.getHighestVerticalPoint())
        x_end = Helper.toMillimeters(grid.getWidth() + 20)

        # x/y swapped for prime center
        self.fillXmlWithMoveTo(y_start, x_start)
        self.fillXmlWithLineTo(y_end, x_end)
        self.addThruCutLayer()
        
    def addLabel(self):
        self.label = ET.SubElement(self.geometry, "Label", {"Text": self.coupage.getClientName(), 
        "Height": "100.00", "Angle": "0.000", "Deformation": "1.000"})
        self.label_position = ET.SubElement(self.label, "Position", {"X": "0.000", "Y": str(round(self.coupage.getWidth()*10, 3))})
        self.label_method = ET.SubElement(self.label, "Method", {"Type": "{none}", "Name": "TEXT"})
    
    def addMethods(self):
        self.methods = ET.SubElement(self.job, "Methods")
        self.method_register = ET.SubElement(self.methods, "Method",
        {"Type": "Register", "Color": "000000", 
        "RegistrationType": "borderFrontRight"})
        self.method_thru_cut = ET.SubElement(self.methods, "Method",
        {"Type": "Thru-cut", "Color": "0000ff", 
        "AllowReverseDirection": "false",
        "Name": "0", "CuttingMode": "standard"})
        self.method_none = ET.SubElement(self.methods, "Method",
        {"Type": "{none}", "Color": "808080", 
        "AllowReverseDirection": "false",
        "Name": "TEXT"})

    def save(self):
        self.addMethods()

        xmlstr = minidom.parseString(ET.tostring(self.root)).toprettyxml(indent = "   ", encoding='UTF-8')
        with open(self.getZccPath() + self.getFileName() + ".zcc", 'wb+') as f:
            f.write(xmlstr)

    def getZccPath(self):
        return Helper.createAndGetFolderOnDesktop('zcc')
