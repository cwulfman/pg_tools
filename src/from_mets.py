# from_mets.py
#
# Script to derive a minimal XML document from a digital object
# defined by a METS file.

from pathlib import Path

from models.mets import Volume, Page

vol_dir = Path("/Users/wulfmanc/odrive/princeton/Patrologia_Graeca/32101007506148")

v:Volume = Volume(vol_dir)
p:Page = v.pages[55]
