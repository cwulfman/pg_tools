# from_mets.py
#
# Script to derive a minimal XML document from a digital object
# defined by a METS file.

from pathlib import Path
from lxml import etree
from models.mets import Volume
 

namespaces = {
    'mets' : "http://www.loc.gov/METS/",
    'xlink' : "http://www.w3.org/1999/xlink"
    }

vol_dir = Path("/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148")

# xml_files = list(vol_dir.glob("*.xml"))
# mets_file = xml_files[0]

# mets_doc = etree.parse(mets_file)

# hdr = mets_doc.xpath('//mets:metsHdr', namespaces=namespaces)

# txt_files = mets_doc.xpath("//mets:file[@IMETYPE='text/plain']", namespaces=namespaces)

# text_file = txt_files[0]

# text_hash:dict = {}
# key = text_file.xpath('@ID', namespaces=namespaces)
# file = text_file.xpath('mets:FLocat/@xlink:href', namespaces=namespaces)


v = Volume(vol_dir)
p = v.pages[55]
