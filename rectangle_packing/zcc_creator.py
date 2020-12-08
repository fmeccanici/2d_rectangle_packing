from helper import Helper

import xml.etree.cElementTree as ET
import ezdxf
from datetime import datetime
from xml.dom import minidom

class ZccCreator(object):
    def __init__(self, path=Helper.getDesktopPath()+'/grids/zcc_test/', 
                dxf_file_name="10h_Forbo Coral_4721_Dhr. van Schie_120351181_coupage.dxf"):
        Helper.createFolderOnDesktop("zcc")

        self.dxf_path = path
        self.dxf_file_name = dxf_file_name
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
        xmlstr = minidom.parseString(ET.tostring(self.root)).toprettyxml(indent = "   ")
        print(self.getZccPath() + self.dxf_file_name + ".zcc")
        with open(self.getZccPath() + self.dxf_file_name + ".zcc", 'w+') as f:
            f.write(xmlstr)

        # tree = ET.ElementTree(self.root)
        # tree.write(self.getZccPath() + self.dxf_file_name + ".zcc", xml_declaration=True, encoding='utf-8')
        print(xmlstr)
        
    def getZccPath(self):
        today = Helper.getDateTimeToday()
        desktop = Helper.getDesktopPath()

        return desktop + "/zcc/" + today + "/"

if __name__ == "__main__":
    zcc_creator = ZccCreator()
    zcc_creator.save()
  