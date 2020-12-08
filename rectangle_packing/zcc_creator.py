from rectangle_packing.helper import Helper

import xml.etree.cElementTree as ET
from xml.etree.ElementTree import ElementTree

import ezdxf
from datetime import datetime
from xml.dom import minidom

class ZccCreator(object):
    def __init__(self, coupage):
        self.zcc_path = Helper.createAndGetFolderOnDesktop('zcc')
        self.coupage = coupage

        Helper.createAndGetFolderOnDesktop("zcc")

        self.dxf_path = Helper.createAndGetDxfFolder()
        self.dxf_file_name = self.coupage.getDxfFileName()
        self.dxf = ezdxf.readfile(self.dxf_path + "/" + self.dxf_file_name)
        self.createInitialTemplate()
        self.addMaterial()
        self.addGeometry()
        self.addLabel()
        self.addRegister()
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

        # self.material = ET.SubElement(self.job, "Material", {"Name": self.coupage.getBrand(), 
        # "GUID": '{8323b713-b552-4e06-974a-d41fc21723e2}'})
        # self.material_setting = ET.SubElement(self.material, "MaterialSettings", {"Thickness": "9"})
        # self.parameter_vacuum_level = ET.SubElement(self.material_setting, "Parameter", {"Id": "VacuumLevel", 
        # "TypeId": "98", "Value": "0"})
        # self.parameter_use_prev_page_trans = ET.SubElement(self.material_setting, "Parameter", {"Id": "UsePrevPageTrans", 
        # "TypeId": "189", "Value": "0"})
        # self.parameter_feed_compensation = ET.SubElement(self.material_setting, "Parameter", {"Id": "FeedCompensation", 
        # "TypeId": "166", "Value": "0"})
    
    def addGeometry(self):
        self.geometry = ET.SubElement(self.job, "Geometry")
        self.outline = ET.SubElement(self.geometry, "Outline")
        self.move_to = ET.SubElement(self.outline, "MoveTo", {"X": "0.000", "Y": "0.000"})
        self.line_to1 = ET.SubElement(self.outline, "LineTo", {"X": str(round(self.coupage.getHeight()*10, 3)), "Y": "0.000"})
        self.line_to2 = ET.SubElement(self.outline, "LineTo", {"X": str(round(self.coupage.getHeight()*10, 3)), "Y": str(round(self.coupage.getWidth()*10, 3))})
        self.line_to3 = ET.SubElement(self.outline, "LineTo", {"X": "0.000", "Y": str(round(self.coupage.getWidth()*10, 3))})
        self.line_to4 = ET.SubElement(self.outline, "LineTo", {"X": "0.000", "Y": "0.000"})
        self.method = ET.SubElement(self.outline, "Method", {"Type": "Thru-cut", "Name": "0"})
    
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
    
    def save(self, binary=True, string=True):
        if string:
            xmlstr = minidom.parseString(ET.tostring(self.root)).toprettyxml(indent = "   ", encoding='UTF-8')
            with open(self.getZccPath() + self.dxf_file_name + ".zcc", 'wb+') as f:
                f.write(xmlstr)
        if binary:
            tree = ElementTree(self.root)
            tree.write(open(self.getBinPath() + self.dxf_file_name + ".zcc.BIN", 'wb+'))
        
    def getZccPath(self):
        return Helper.createAndGetFolderOnDesktop('zcc')
    
    def getBinPath(self):
        return Helper.createAndGetFolderOnDesktop('bin')

  