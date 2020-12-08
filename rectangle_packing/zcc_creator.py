from helper import Helper

import xml.etree.cElementTree as ET
import ezdxf
from datetime import datetime
from xml.dom import minidom

class ZccCreator(object):
    def __init__(self, coupage):
        self.zcc_path = Helper.createAndGetFolderOnDesktop('zcc')
        self.coupage = coupage

        Helper.createFolderOnDesktop("zcc")

        self.dxf_path = Helper.createAndGetDxfFolder()
        self.dxf_file_name = self.coupage.getDxfFileName()
        self.dxf = ezdxf.readfile(self.dxf_path + self.dxf_file_name)
        self.createInitialTemplate()

    def createInitialTemplate(self):
        self.root = ET.Element("ZCC_cmd", {"MessageID": "jobdescription", 
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

    def save(self):

        xmlstr = minidom.parseString(ET.tostring(self.root)).toprettyxml(indent = "   ", encoding='UTF-8')
        with open(self.getZccPath() + self.dxf_file_name + ".zcc", 'wb+') as f:
            f.write(xmlstr)
        
    def getZccPath(self):
        today = Helper.getDateTimeToday()
        desktop = Helper.getDesktopPath()

        return desktop + "/zcc/" + today + "/"

if __name__ == "__main__":
    zcc_creator = ZccCreator()
    zcc_creator.save()
  