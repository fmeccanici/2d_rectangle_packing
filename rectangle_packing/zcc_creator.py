import xml.etree.cElementTree as ET
import ezdxf
from datetime import date

class ZccCreator(object):
    def __init__(self, path, dxf_file_name):
        self.today = date.today()
        self.dxf = ezdxf.readfile(path+dxf_file_name)
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
        "Version": "3.2.6.9", "Date": "2020-12-08T09:30:05"})


    def save(self):
        tree = ET.ElementTree(self.root)
        tree.write('test.dxf.zcc', xml_declaration=True, encoding='utf-8')


if __name__ == "__main__":
    zcc_creator = ZccCreator()
    zcc_creator.save()
  