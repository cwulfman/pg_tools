from pathlib import Path
import json
from lxml import etree

xml_file = "/Users/wulfmanc/gh/cwulfman/pg_tools/volmap.xml"
tree = etree.parse(xml_file)

vols = []

xml_vols = tree.xpath('/vols/vol')

for vol in xml_vols:
    volinfo = {}
    volinfo['number'] = vol.xpath('@num')
    volinfo['barcode'] = vol.xpath('@gnum')
    print(volinfo)
    vols.append(volinfo)


outpath = Path("/Users/wulfmanc/gh/cwulfman/pg_tools/volmap.json")
with outpath.open('w+') as f:
    json.dump(vols, f)
